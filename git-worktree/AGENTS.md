# Codex 作業ルール

このディレクトリは、実作業用の Git worktree を置く場所です。

この `AGENTS.md` は、各 worktree の Git repository には含めず、親リポジトリ側で管理します。`main` や `develop` などの基準ブランチ側に同じルールを書くと、その project repository の tracked file になってしまうためです。

## 作業対象

- `main/` と `develop/` は直接編集しない。
- `main/` と `develop/` は、原則として参照用の基準 worktree として扱う。
- プログラム変更は、`develop` から作成した `feat-*`、`fix-*`、`chore-*` などの作業用 worktree で行う。
- 作業用 worktree を新しく作る場合は、親ディレクトリの `scripts/new-worktree.sh` を使う。

## 編集前確認

- 編集前に、現在の作業場所が `main/` または `develop/` ではないことを確認する。
- 作業場所が `main/` または `develop/` の場合、調査だけに留め、編集前にユーザーへ作業用 worktree の指定または作成方針を確認する。
- 各 worktree 内に `AGENTS.md` や `CLAUDE.md` がある場合、その worktree 固有の実装ルールとして扱う。

## Git 操作

- ユーザーの未コミット変更を勝手に戻さない。
- `git reset --hard`、`git checkout --`、`rm` などの破壊的操作は、ユーザーの明示承認なしに実行しない。
- GitHub へ共有する変更は、原則として作業用 worktree から行う。
