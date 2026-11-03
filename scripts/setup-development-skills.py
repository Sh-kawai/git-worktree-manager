#!/usr/bin/env python3
"""develop内の共有skillを親のCodex・Claude Codeから参照する。

使い方: python3 scripts/setup-development-skills.py [--apply] [--backup-existing]
既定は確認のみ。--applyはdevelopにskillが揃った後に指定する。
通常ファイルと異なるリンクは、--backup-existing指定時だけ退避して置き換える。
共有元、developのGit状態、ユーザーのグローバル設定は変更しない。
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile


def collect_links(parent: Path) -> list[tuple[Path, Path]]:
    """developの正本から両ツール用のリンク計画を作り、必須skillを確認する。"""
    source = parent / 'git-worktree/develop/.agents/skills'
    required = {'feature-development', 'grilling', 'tdd', 'recipe-pr-review', 'codebase-design'}
    names = {path.parent.name for path in source.glob('*/SKILL.md') if path.is_file()}
    missing = required - names
    if missing:
        raise ValueError('developへの取り込み待ち: ' + ', '.join(sorted(missing)))
    return [(parent / entry / name, source / name)
            for entry in ('.agents/skills', '.claude/skills') for name in sorted(names)]


def is_current(destination: Path, source: Path) -> bool:
    """既存リンクが意図した共有元を指しているか確認する。"""
    return destination.is_symlink() and destination.resolve() == source.resolve()


def apply_links(parent: Path, links: list[tuple[Path, Path]], backup_existing: bool) -> None:
    """衝突を事前確認し、承認された既存入口は退避して相対リンクを作る。"""
    conflicts = [destination for destination, source in links
                 if os.path.lexists(destination) and not is_current(destination, source)]
    if conflicts and not backup_existing:
        raise ValueError('既存入口を保持しました。退避して切り替える場合は--backup-existingを指定: '
                         + ', '.join(str(path.relative_to(parent)) for path in conflicts))
    backup = None
    if conflicts:
        backup_root = parent / '.agents/skill-backups'
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix='before-develop-', dir=backup_root))
    for destination, source in links:
        if is_current(destination, source):
            continue
        if destination in conflicts:
            saved = backup / destination.relative_to(parent)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(saved))
            print(f'退避: {saved.relative_to(parent)}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.path.relpath(source, destination.parent), target_is_directory=True)
        print(f'設定: {destination.relative_to(parent)}')


def main() -> int:
    """引数を処理し、確認またはリンクの有効化を実行する。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='リンクを有効化する')
    parser.add_argument('--backup-existing', action='store_true', help='衝突する入口を退避して切り替える')
    args = parser.parse_args()
    parent = Path(__file__).resolve().parents[1]
    try:
        links = collect_links(parent)
        for destination, source in links:
            state = '設定済み' if is_current(destination, source) else (
                '既存入口あり' if os.path.lexists(destination) else '新規')
            print(f'{state}: {destination.relative_to(parent)} -> {source.relative_to(parent)}')
        if args.apply:
            apply_links(parent, links, args.backup_existing)
        return 0
    except ValueError as error:
        print(error)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
