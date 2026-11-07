#!/usr/bin/env bash
set -euo pipefail

# 作成方法と既定の配置・基準を表示する。
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
if [[ "$worktree_dir" != /* ]]; then
  worktree_dir="${PWD}/${worktree_dir}"
fi
if [[ "$(dirname "$worktree_dir")" != "${manager_root}/git-worktree" ]]; then
  echo "error: worktree must be directly under ${manager_root}/git-worktree" >&2
  exit 1
fi

case "$branch" in
  feat/*|exp/*|fix/*|chore/*|docs/*|test/*|refactor/*) ;;
  *)
    echo "error: branch should usually start with feat/, exp/, fix/, chore/, docs/, test/, or refactor/" >&2
    exit 1
    ;;
esac

# 検証ブランチは親featを明示し、developから誤って作らない。
if [[ "$branch" == exp/* && ( $# -lt 3 || "$base" != feat/* ) ]]; then
  echo "error: exp branches require an explicit feat/* base as the third argument" >&2
  exit 1
fi

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

# 方針参照に対応した製品では、保存済みの運用セットを新しい作業場所へ適用する。
if [[ -f "${worktree_dir}/AGENTS.md" ]] && grep -qF '.codex/guides/project-policy.md' "${worktree_dir}/AGENTS.md"; then
  "${PYTHON:-python3}" "${manager_root}/scripts/setup-project.py" \
    --worktree "git-worktree/$(basename "$worktree_dir")" --apply
else
  echo "note: AGENTS.mdに運用方針の参照がないため、サイト側の方針生成は省略しました。"
fi
