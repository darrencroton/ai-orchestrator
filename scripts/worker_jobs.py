#!/usr/bin/env python3
"""Manage tracked worker runs for ai-orchestrator.

This helper keeps worker artifacts in a unique per-run directory, records a
manifest, and provides status/wait/extract commands that do not rely on shell
variables surviving across separate shell invocations.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("/private/tmp/ai-orchestrator")
MANIFEST_NAME = "manifest.json"
LABEL_RE = re.compile(r"^\d{2}-[a-z0-9]+-[a-z0-9]+(?:-[a-z0-9]+)*(?:-r\d+)?$")
# Match line-based SECTION headers even when a model prefixes them with Markdown.
SECTION_RE = re.compile(r"^\s*(?:#+\s*)?SECTION:\s*([A-Za-z0-9_ -]+)\s*$", re.MULTILINE)


class WorkerJobsError(RuntimeError):
    """Raised for expected operational errors."""


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def process_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temp_path.replace(path)


def normalize_command(command: list[str]) -> list[str]:
    if command and command[0] == "--":
        return command[1:]
    return command


def normalize_section_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")


def validate_label(label: str) -> None:
    if LABEL_RE.fullmatch(label):
        return
    raise WorkerJobsError(
        "Worker label must match <nn>-<tool>-<subtask-slug>[-rN] in lowercase kebab-case, "
        f"for example 01-codex-trace-login or 03-claude-review-plan-r1: {label}"
    )


def manifest_path(run_dir: Path) -> Path:
    return run_dir / MANIFEST_NAME


def load_manifest(run_dir: Path) -> dict[str, Any]:
    path = manifest_path(run_dir)
    if not path.exists():
        raise WorkerJobsError(f"Run directory has no manifest: {run_dir}")
    return read_json(path)


def save_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    write_json(manifest_path(run_dir), manifest)


def ensure_manifest(run_dir: Path) -> dict[str, Any]:
    path = manifest_path(run_dir)
    if path.exists():
        return read_json(path)
    manifest = {
        "created_at": iso_now(),
        "run_dir": str(run_dir),
        "workers": {},
    }
    save_manifest(run_dir, manifest)
    return manifest


def derive_run_dir(root: Path, prefix: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return root / f"{prefix}-{stamp}-{os.getpid()}"


def worker_status(entry: dict[str, Any]) -> dict[str, Any]:
    pid = int(entry.get("pid", 0))
    status_file = Path(entry["status_file"])
    outfile = Path(entry["outfile"])
    errfile = Path(entry["errfile"])
    status_payload = read_json(status_file) if status_file.exists() else {}
    running = process_running(pid)
    returncode = status_payload.get("returncode")
    if running:
        state = "running"
    elif returncode not in (None, 0):
        state = "failed"
    elif returncode == 0:
        state = status_payload.get("state", "completed")
    elif status_payload.get("state") == "running":
        state = "stalled"
    else:
        state = status_payload.get("state", "finished")
    return {
        "label": entry["label"],
        "pid": pid,
        "tool": entry.get("tool"),
        "state": state,
        "running": running,
        "outfile": str(outfile),
        "outfile_exists": outfile.exists(),
        "outfile_size": outfile.stat().st_size if outfile.exists() else 0,
        "errfile": str(errfile),
        "errfile_exists": errfile.exists(),
        "errfile_size": errfile.stat().st_size if errfile.exists() else 0,
        "returncode": returncode,
        "started_at": entry.get("started_at"),
        "finished_at": status_payload.get("finished_at"),
        "command": entry.get("command", []),
    }


def find_section_blocks(text: str) -> list[tuple[str, int, int]]:
    matches = list(SECTION_RE.finditer(text))
    blocks: list[tuple[str, int, int]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks.append((normalize_section_name(match.group(1)), start, end))
    return blocks


def extract_sections(text: str, names: list[str]) -> str:
    wanted = {normalize_section_name(name) for name in names}
    blocks = find_section_blocks(text)
    if not blocks:
        return text
    parts = [text[start:end].rstrip() for name, start, end in blocks if name in wanted]
    return "\n\n".join(part for part in parts if part).strip() or text


def extract_best_text(entry: dict[str, Any]) -> str:
    outfile = Path(entry["outfile"])
    if outfile.exists() and outfile.stat().st_size > 0:
        return outfile.read_text()

    errfile = Path(entry["errfile"])
    if errfile.exists() and errfile.stat().st_size > 0:
        err_text = errfile.read_text()
        blocks = find_section_blocks(err_text)
        if blocks:
            return err_text[blocks[-1][1] :].strip()
        result_idx = err_text.rfind("RESULT:")
        if result_idx != -1:
            return err_text[result_idx:].strip()
        return err_text

    raise WorkerJobsError(f"No output available for worker {entry['label']}")


def command_init(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    run_dir = derive_run_dir(root, args.prefix)
    run_dir.mkdir(parents=True, exist_ok=False)
    ensure_manifest(run_dir)
    print(run_dir)
    return 0


def command_start(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_manifest(run_dir)

    label = args.label
    validate_label(label)
    if label in manifest["workers"]:
        raise WorkerJobsError(f"Worker label already exists in manifest: {label}")

    command = normalize_command(args.command)
    if not command:
        raise WorkerJobsError("No worker command supplied.")

    outfile = run_dir / f"{label}-out.txt"
    errfile = run_dir / f"{label}-err.txt"
    status_file = run_dir / f"{label}-status.json"
    wrapper_cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_runner",
        "--label",
        label,
        "--status-file",
        str(status_file),
        "--stdout",
        str(outfile),
        "--stderr",
        str(errfile),
        "--",
        *command,
    ]
    process = subprocess.Popen(
        wrapper_cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )

    manifest["workers"][label] = {
        "label": label,
        "tool": Path(command[0]).name,
        "pid": process.pid,
        "command": command,
        "outfile": str(outfile),
        "errfile": str(errfile),
        "status_file": str(status_file),
        "started_at": iso_now(),
    }
    save_manifest(run_dir, manifest)

    print(
        json.dumps(
            {
                "label": label,
                "pid": process.pid,
                "outfile": str(outfile),
                "errfile": str(errfile),
                "status_file": str(status_file),
                "run_dir": str(run_dir),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def iter_selected_workers(manifest: dict[str, Any], label: str | None) -> list[dict[str, Any]]:
    workers = manifest.get("workers", {})
    if label is None:
        return [workers[key] for key in sorted(workers)]
    if label not in workers:
        raise WorkerJobsError(f"Unknown worker label: {label}")
    return [workers[label]]


def command_status(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.run_dir).expanduser().resolve())
    statuses = [worker_status(entry) for entry in iter_selected_workers(manifest, args.label)]
    if args.json:
        print(json.dumps(statuses, indent=2, sort_keys=True))
        return 0
    for status in statuses:
        suffix = ""
        if status["returncode"] is not None:
            suffix = f" returncode={status['returncode']}"
        print(
            f"{status['label']}: state={status['state']} pid={status['pid']} "
            f"out={status['outfile_size']}B err={status['errfile_size']}B{suffix}"
        )
    return 0


def command_wait(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    deadline = None if args.timeout is None else time.time() + args.timeout
    while True:
        manifest = load_manifest(run_dir)
        statuses = [worker_status(entry) for entry in iter_selected_workers(manifest, args.label)]
        if not any(status["running"] for status in statuses):
            failed = [status for status in statuses if status["returncode"] not in (None, 0)]
            if args.json:
                print(json.dumps(statuses, indent=2, sort_keys=True))
            else:
                for status in statuses:
                    print(f"{status['label']}: state={status['state']} returncode={status['returncode']}")
            return 1 if failed else 0
        if deadline is not None and time.time() >= deadline:
            if args.json:
                print(json.dumps(statuses, indent=2, sort_keys=True))
            else:
                for status in statuses:
                    print(f"{status['label']}: state={status['state']} pid={status['pid']}")
            return 1
        time.sleep(args.interval)


def command_extract(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.run_dir).expanduser().resolve())
    entry = iter_selected_workers(manifest, args.label)[0]
    text = extract_best_text(entry)
    if args.sections:
        section_names = [part.strip() for part in args.sections.split(",") if part.strip()]
        if section_names:
            text = extract_sections(text, section_names)
    print(text.rstrip())
    return 0


def command_runner(args: argparse.Namespace) -> int:
    command = normalize_command(args.command)
    if not command:
        raise WorkerJobsError("Runner requires a worker command.")

    status_file = Path(args.status_file)
    stdout_path = Path(args.stdout)
    stderr_path = Path(args.stderr)
    status_file.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)

    with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
        child = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            close_fds=True,
        )
        write_json(
            status_file,
            {
                "label": args.label,
                "state": "running",
                "started_at": iso_now(),
                "child_pid": child.pid,
            },
        )
        returncode = child.wait()
    write_json(
        status_file,
        {
            "label": args.label,
            "state": "completed" if returncode == 0 else "failed",
            "started_at": read_json(status_file).get("started_at"),
            "finished_at": iso_now(),
            "child_pid": child.pid,
            "returncode": returncode,
        },
    )
    return returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worker_jobs.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a unique run directory.")
    init_parser.add_argument("--root", default=str(DEFAULT_ROOT))
    init_parser.add_argument("--prefix", default="run")
    init_parser.set_defaults(func=command_init)

    start_parser = subparsers.add_parser(
        "start",
        help="Start one tracked worker. The helper owns stdout/stderr capture; do not add shell redirections unless you explicitly wrap the command in /bin/sh -lc.",
    )
    start_parser.add_argument("--run-dir", required=True)
    start_parser.add_argument(
        "--label",
        required=True,
        help="Worker label in the form <nn>-<tool>-<subtask-slug>[-rN], e.g. 01-codex-trace-login.",
    )
    start_parser.add_argument("command", nargs=argparse.REMAINDER)
    start_parser.set_defaults(func=command_start)

    status_parser = subparsers.add_parser("status", help="Show worker status.")
    status_parser.add_argument("--run-dir", required=True)
    status_parser.add_argument("--label")
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=command_status)

    wait_parser = subparsers.add_parser("wait", help="Wait for workers to finish.")
    wait_parser.add_argument("--run-dir", required=True)
    wait_parser.add_argument("--label")
    wait_parser.add_argument("--timeout", type=float)
    wait_parser.add_argument("--interval", type=float, default=2.0)
    wait_parser.add_argument("--json", action="store_true")
    wait_parser.set_defaults(func=command_wait)

    extract_parser = subparsers.add_parser("extract", help="Read the best available worker output.")
    extract_parser.add_argument("--run-dir", required=True)
    extract_parser.add_argument("--label", required=True)
    extract_parser.add_argument(
        "--sections",
        help="Comma-separated section names to extract from matching SECTION header lines. If omitted, print the whole final outfile.",
    )
    extract_parser.set_defaults(func=command_extract)

    runner_parser = subparsers.add_parser("_runner", help=argparse.SUPPRESS)
    runner_parser.add_argument("--label", required=True)
    runner_parser.add_argument("--status-file", required=True)
    runner_parser.add_argument("--stdout", required=True)
    runner_parser.add_argument("--stderr", required=True)
    runner_parser.add_argument("command", nargs=argparse.REMAINDER)
    runner_parser.set_defaults(func=command_runner)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except WorkerJobsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
