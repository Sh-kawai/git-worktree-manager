#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/setup-worktree-shared.sh [worktree_dir]

Environment:
  WORKTREE_SHARED_ROOT    Parent directory that contains .worktree-shared.toml.
  WORKTREE_SHARED_CONFIG  Config file path. Defaults to $WORKTREE_SHARED_ROOT/.worktree-shared.toml.

This command links paths declared in .worktree-shared.toml into a worktree.
It never overwrites existing regular files or directories.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_root="$(cd "${script_dir}/.." && pwd)"
manager_root="${WORKTREE_SHARED_ROOT:-${default_root}}"
config_path="${WORKTREE_SHARED_CONFIG:-${manager_root}/.worktree-shared.toml}"
worktree_dir="${1:-$(pwd)}"

python_bin="${PYTHON:-python3}"

"${python_bin}" - "$manager_root" "$config_path" "$worktree_dir" <<'PY'
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tomllib


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def is_safe_relative_path(value: str) -> bool:
    path = pathlib.PurePosixPath(value)
    return (
        value
        and not path.is_absolute()
        and ".." not in path.parts
        and "\0" not in value
    )


manager_root = pathlib.Path(sys.argv[1]).resolve()
config_path = pathlib.Path(sys.argv[2]).resolve()
worktree_dir = pathlib.Path(sys.argv[3]).resolve()

if not config_path.exists():
    fail(f"config not found: {config_path}")
if not worktree_dir.exists():
    fail(f"worktree directory not found: {worktree_dir}")
if not worktree_dir.is_dir():
    fail(f"worktree path is not a directory: {worktree_dir}")

with config_path.open("rb") as handle:
    config = tomllib.load(handle)

shared = config.get("shared", {})
shared_root_name = shared.get("root", "_shared")
if not isinstance(shared_root_name, str) or not is_safe_relative_path(shared_root_name):
    fail("shared.root must be a safe relative path")

shared_root = manager_root / shared_root_name
common_root = shared_root / "common"
worktree_root = shared_root / "worktrees" / worktree_dir.name

links = config.get("link", [])
if not isinstance(links, list):
    fail("config must contain [[link]] entries")

changed = 0
skipped = 0
ignore_patterns: list[str] = []

for index, entry in enumerate(links, start=1):
    if not isinstance(entry, dict):
        fail(f"link #{index} must be a table")

    rel = entry.get("path")
    if not isinstance(rel, str) or not is_safe_relative_path(rel):
        fail(f"link #{index} has an unsafe path: {rel!r}")
    ignore_patterns.append(f"/{rel}")

    mode = entry.get("mode", "shared")
    if mode not in {"shared", "per_worktree"}:
        fail(f"link {rel!r} has unsupported mode: {mode!r}")

    kind = entry.get("kind", "dir")
    if kind not in {"dir", "file"}:
        fail(f"link {rel!r} has unsupported kind: {kind!r}")

    create = entry.get("create")
    if create is None:
        create = kind == "dir"
    if not isinstance(create, bool):
        fail(f"link {rel!r} create must be true or false")

    source = (common_root if mode == "shared" else worktree_root) / rel
    dest = worktree_dir / rel

    if kind == "dir":
        source.mkdir(parents=True, exist_ok=True)
    else:
        source.parent.mkdir(parents=True, exist_ok=True)
        if create and not source.exists():
            source.touch(mode=0o600, exist_ok=False)

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        dest_is_symlink = dest.is_symlink()
    except PermissionError as exc:
        print(f"skip: {dest} cannot be inspected: {exc}")
        skipped += 1
        continue

    if dest_is_symlink:
        try:
            current = pathlib.Path(os.readlink(dest))
            resolved = (dest.parent / current).resolve() if not current.is_absolute() else current.resolve()
        except PermissionError as exc:
            print(f"skip: {dest} symlink target cannot be inspected: {exc}")
            skipped += 1
            continue
        if resolved == source.resolve():
            print(f"ok: {dest} -> {source}")
            continue
        print(f"skip: {dest} is a symlink to {current}, expected {source}")
        skipped += 1
        continue

    try:
        dest_exists = dest.exists()
    except PermissionError as exc:
        print(f"skip: {dest} cannot be inspected: {exc}")
        skipped += 1
        continue

    if dest_exists:
        print(f"skip: {dest} already exists; migrate it manually before linking")
        skipped += 1
        continue

    relative_source = os.path.relpath(source, start=dest.parent)
    dest.symlink_to(relative_source, target_is_directory=(kind == "dir"))
    print(f"link: {dest} -> {relative_source}")
    changed += 1

begin_marker = "# BEGIN worktree-shared"
end_marker = "# END worktree-shared"


def update_git_exclude() -> bool:
    result = subprocess.run(
        ["git", "-C", str(worktree_dir), "rev-parse", "--git-path", "info/exclude"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        print(f"warn: could not update git exclude: {detail}", file=sys.stderr)
        return False

    exclude_text = result.stdout.strip()
    if not exclude_text:
        print("warn: could not update git exclude: empty exclude path", file=sys.stderr)
        return False

    exclude_path = pathlib.Path(exclude_text)
    if not exclude_path.is_absolute():
        exclude_path = worktree_dir / exclude_path

    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    if exclude_path.exists():
        current = exclude_path.read_text(encoding="utf-8")
    else:
        current = ""

    block_lines = [
        begin_marker,
        "# setup-worktree-shared.sh が自動生成。手動編集はこのブロック外で行う。",
        *sorted(set(ignore_patterns)),
        end_marker,
    ]
    block = "\n".join(block_lines) + "\n"

    lines = current.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.rstrip("\n") == begin_marker), None)
    end = next((i for i, line in enumerate(lines) if line.rstrip("\n") == end_marker), None)

    if start is not None and end is not None and start <= end:
        new_text = "".join(lines[:start]) + block + "".join(lines[end + 1 :])
    else:
        separator = "" if not current or current.endswith("\n") else "\n"
        new_text = current + separator + block

    if new_text != current:
        exclude_path.write_text(new_text, encoding="utf-8")
        print(f"exclude: updated {exclude_path}")
    else:
        print(f"exclude: ok {exclude_path}")
    return True


update_git_exclude()

if skipped:
    print(f"done: {changed} linked, {skipped} skipped")
    sys.exit(2)

print(f"done: {changed} linked")
PY
