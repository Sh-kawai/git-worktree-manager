# Codex 作業ルール

このディレクトリは実作業用の Git worktree を置く場所です。このファイルは配置に由来する追加制約だけを定め、製品固有の規則は各 worktree 内の `AGENTS.md` に委ねます。

## worktree の選択

- `main/` と `develop/` は参照用の基準 worktree とし、直接編集しない。
- 実装や文書の変更は、ユーザーが指定した `feat-*`、`fix-*`、`chore-*` などの作業用 worktree で行う。
- 作業用 worktree が指定されていない場合は、編集前に対象または作成方針を確認する。
- 作業開始時に現在地と対象 worktree を照合し、基準 worktree でないことを確認できた時点で編集可能とする。

## 規則の適用

- 各 worktree を独立したリポジトリとして扱う。
- 各 worktree 内の `AGENTS.md` やその他の指示文書を追加で適用する。
- 親リポジトリの構成や外部パスを、worktree 内の成果物へ持ち込まない。
