#!/usr/bin/env python3
"""運用セットを選択して生成する。Python 3.11以降、外部依存不要。

実行例: python3 scripts/setup-project.py --policy autonomous
適用例: python3 scripts/setup-project.py --policy autonomous --apply
サイトへの適用: 上記に --worktree git-worktree/feat-example を追加する。
引数なしではローカルの選択を使い、未選択ならstrict。既定は確認だけ。
選択は.project-policy.toml、生成履歴は.codex/template-state.jsonへ保存する。

案件固有の既存設定を保持する場合:
python3 scripts/setup-project.py --policy strict --preserve-config --apply
この選択は生成履歴に保存され、以後もconfig.tomlは更新しない。
設定は手動管理となり、テンプレートの更新は反映しない。
設定との不整合を避けるため、自律運用への切り替えは拒否する。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

POLICIES = ('strict', 'autonomous')


def digest(content: bytes) -> str:
    """生成済み内容を識別するハッシュを返す。"""
    return hashlib.sha256(content).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    """管理対象の相対パスを解決し、リンク経由の上書きを拒否する。"""
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'不正な管理パス: {relative}')
    current = root
    for part in path.parts:
        current /= part
        if current != root / path and current.exists() and not current.is_dir():
            raise ValueError(f'親パスがディレクトリではありません: {relative}')
        if current.is_symlink():
            raise ValueError(f'リンク経由の適用はできません: {relative}')
    return current


def read_state(root: Path) -> dict:
    """前回適用の生成履歴を読み、想定する構造か確認する。"""
    path = safe_path(root, '.codex/template-state.json')
    if not path.exists():
        return {'version': 1, 'files': {}, 'worktrees': []}
    state = json.loads(path.read_text())
    if (not isinstance(state, dict) or state.get('version') != 1
            or not isinstance(state.get('files'), dict)
            or not isinstance(state.get('worktrees'), list)
            or not all(isinstance(x, str) for x in state['worktrees'])):
        raise ValueError('生成履歴の形式が不正です')
    return state


def selected_policy(root: Path, explicit: str | None) -> str:
    """明示指定、保存済み選択、strictの順で方針を決める。"""
    path = safe_path(root, '.project-policy.toml')
    saved = tomllib.loads(path.read_text()) if path.exists() else {}
    policy = explicit or saved.get('policy', 'strict')
    if policy not in POLICIES:
        raise ValueError(f'未対応の運用方針: {policy!r}')
    return policy


def worktree_path(root: Path, relative: str) -> Path:
    """親配下にある実際のGit作業場所だけを適用対象として認める。"""
    path = safe_path(root, relative)
    if path.parent != root / 'git-worktree' or not path.is_dir():
        raise ValueError(f'git-worktree直下の作業場所を指定してください: {relative}')
    result = subprocess.run(['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True, check=False)
    if result.returncode or Path(result.stdout.strip()).resolve() != path:
        raise ValueError(f'Git作業場所を確認できません: {relative}')
    return path


def render(root: Path, policy: str, worktrees: list[str]) -> dict[str, bytes]:
    """設定・方針・作業手順を同じ選択から一括生成する。"""
    config_source = f'.codex/templates/{policy}/config.toml.template'
    config = safe_path(root, config_source).read_bytes()
    tomllib.loads(config.decode())
    policy_text = safe_path(root, f'.codex/templates/{policy}/policy.md').read_bytes()
    workflow = safe_path(root, '.codex/templates/common/workflow.md').read_bytes()
    outputs = {'.codex/config.toml': config, '.codex/guides/project-policy.md': policy_text,
               '.codex/guides/project-workflow.md': workflow}
    for relative in worktrees:
        site = worktree_path(root, relative)
        instructions = site / 'AGENTS.md'
        if not instructions.is_file() or '.codex/guides/project-policy.md' not in instructions.read_text():
            raise ValueError(f'先にAGENTS.mdへ運用方針の参照を追加してください: {relative}')
        outputs[f'{relative}/.codex/guides/project-policy.md'] = policy_text + b'\n' + workflow
    return outputs


def check_outputs(root: Path, outputs: dict[str, bytes], state: dict) -> list[str]:
    """すべての上書き対象を先に確認し、手編集や未管理ファイルを保護する。"""
    changes = []
    for relative, content in outputs.items():
        path = safe_path(root, relative)
        if path.exists():
            if not path.is_file():
                raise ValueError(f'通常ファイルではありません: {relative}')
            current = path.read_bytes()
            previous = state['files'].get(relative)
            if current != content and (previous is None or digest(current) != previous):
                raise ValueError(f'独自編集を保護するため全体の適用を停止しました: {relative}')
            if current == content:
                continue
        changes.append(relative)
    return changes


def atomic_write(path: Path, content: bytes) -> None:
    """同じフォルダ内の一時ファイルから置換して書き込みを完了する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def exclude_plan(root: Path, worktrees: list[str]) -> dict[Path, bytes]:
    """サイト側の生成方針をGit追跡から除外する追記内容を準備する。"""
    plans = {}
    for relative in worktrees:
        worktree = worktree_path(root, relative)
        result = subprocess.run(['git', '-C', str(worktree), 'rev-parse',
                                 '--git-path', 'info/exclude'], check=True,
                                capture_output=True, text=True)
        path = Path(result.stdout.strip())
        if not path.is_absolute():
            path = worktree / path
        path = path.absolute()
        # Gitが返す管理情報のリンクには書き込まない。
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError('Git除外ファイルにリンクが含まれています')
        current = plans.get(path, path.read_bytes() if path.exists() else b'')
        pattern = b'/.codex/guides/project-policy.md'
        if pattern not in current.splitlines():
            plans[path] = current.rstrip(b'\n') + b'\n' + pattern + b'\n'
    return plans


def main() -> int:
    """引数と全対象を検証し、既定では変更予定だけを表示する。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', choices=POLICIES)
    parser.add_argument('--worktree', action='append', default=[],
                        help='方針を適用するgit-worktree直下の相対パス。複数指定可能')
    parser.add_argument('--apply', action='store_true', help='確認済みの生成内容を適用する')
    parser.add_argument('--preserve-config', action='store_true',
                        help='既存設定を生成対象から外して保持する（厳格運用のみ、選択を保存）')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        state = read_state(root)
        policy = selected_policy(root, args.policy)
        preserve_config = args.preserve_config or state.get('preserve_config', False)
        if preserve_config:
            if policy != 'strict':
                raise ValueError('既存設定を保持する場合はstrictを指定してください')
            config_path = safe_path(root, '.codex/config.toml')
            if not config_path.is_file():
                raise ValueError('保持する既存の.codex/config.tomlがありません')
            tomllib.loads(config_path.read_text())
        # 人が削除済みのworktreeは登録から外し、残っている対象だけを更新する。
        retained = [p for p in state['worktrees'] if safe_path(root, p).exists()]
        worktrees = sorted(set(retained + args.worktree))
        outputs = render(root, policy, worktrees)
        if preserve_config:
            outputs.pop('.codex/config.toml')
        changes = check_outputs(root, outputs, state)
        excludes = exclude_plan(root, worktrees)
        print(f'運用方針: {policy}')
        if preserve_config:
            print('既存設定を保持: .codex/config.toml（設定の更新は手動管理）')
        for relative in changes:
            print(f'生成・更新: {relative}')
        if not args.apply:
            print('確認のみ。適用する場合は --apply を付けて再実行してください。')
            return 0
        # テンプレートと選択値はすべて検証後に書く。OS側で失敗した場合も再実行可能。
        selection = f'policy = "{policy}"\n'.encode()
        selection_path = safe_path(root, '.project-policy.toml')
        new_state = {'version': 1, 'policy': policy, 'worktrees': worktrees,
                     'preserve_config': preserve_config,
                     'files': {p: digest(c) for p, c in outputs.items()}}
        serialized = (json.dumps(new_state, ensure_ascii=False, indent=2) + '\n').encode()
        state_path = safe_path(root, '.codex/template-state.json')
        writes = dict(excludes)
        writes.update({safe_path(root, p): outputs[p] for p in changes})
        writes[selection_path] = selection
        writes[state_path] = serialized
        originals = {p: p.read_bytes() if p.exists() else None for p in writes}
        written = []
        try:
            for path, content in writes.items():
                if originals[path] == content:
                    continue
                atomic_write(path, content)
                written.append(path)
        except OSError:
            # 途中の書き込みに失敗しても方針・実設定を混在させない。
            for path in reversed(written):
                previous = originals[path]
                if previous is None:
                    path.unlink()
                else:
                    atomic_write(path, previous)
            raise
        print('適用完了。Codexの権限は新しいチャットで読み込み・実動作を確認してください。')
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
