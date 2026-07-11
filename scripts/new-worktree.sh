#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/new-worktree.sh <branch> [worktree_dir] [base]

Examples:
  scripts/new-worktree.sh feat/shared-data
  scripts/new-worktree.sh fix/results-path git-worktree/fix-results develop

Defaults:
  worktree_dir  ./git-worktree/<branch with "/" replaced by "-">
  base          develop

After git worktree creation, shared paths from .worktree-shared.toml are linked.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 3 ]]; then
  usage >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
manager_root="$(cd "${script_dir}/.." && pwd)"

branch="$1"
default_dir="${branch//\//-}"
worktree_dir="${2:-${manager_root}/git-worktree/${default_dir}}"
base="${3:-develop}"

case "$branch" in
  feat/*|fix/*|chore/*|docs/*|test/*|refactor/*) ;;
  *)
    echo "error: branch should usually start with feat/, fix/, chore/, docs/, test/, or refactor/" >&2
    exit 1
    ;;
esac

if [[ -e "$worktree_dir" ]]; then
  echo "error: worktree directory already exists: $worktree_dir" >&2
  exit 1
fi

source_worktree="${manager_root}/git-worktree/develop"
if [[ ! -d "$source_worktree" ]]; then
  echo "error: source worktree not found: $source_worktree" >&2
  exit 1
fi

git -C "$source_worktree" worktree add -b "$branch" "$worktree_dir" "$base"
WORKTREE_SHARED_ROOT="$manager_root" "${script_dir}/setup-worktree-shared.sh" "$worktree_dir"
