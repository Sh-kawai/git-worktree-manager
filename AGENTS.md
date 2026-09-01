# Codex 作業ルール

このリポジトリは、複数の Git worktree を `git-worktree/` 配下に置くための親管理リポジトリです。ここでは、worktree 配置を支える管理ファイルとスクリプトだけを扱います。

## 作業範囲

- `git-worktree/` 配下の仕様、業務ルール、実装は、明示的に指定された worktree だけを対象にする。
- `_shared/common/` と `_shared/worktrees/` 配下の実データは、明示的な依頼がない限り操作しない。
- 指定された worktree は独立したリポジトリとして扱い、その中の `AGENTS.md` などを追加で適用する。

## worktree 内でのパス記載

- worktree 内の成果物では、その worktree から見えるパスだけを使用する。
- worktree のルート外へ移動する相対パス、worktree 外の絶対パス、親リポジトリ固有のディレクトリ名を書かない。
- worktree 内のシンボリックリンクから参照できる場合は、リンク先の物理パスではなく、`data/...` などリンクを起点とするパスを書く。
- worktree 内から参照できない外部ファイルへ言及する場合は、原則としてファイル名だけを書く。
- この規則は worktree 内の成果物に適用し、親リポジトリ自身の配置説明には適用しない。

## 編集前承認

- 編集前に変更方針を提示し、ユーザーの明示的な承認を得る。
- 承認前は、構成確認、検索、読み取り、Git 状態確認だけを行う。

## 安全な変更

- `.env`、`.env.*`、秘密鍵ファイルを読まない。
- API キー、DB パスワード、トークン、社内認証情報を出力しない。
- ユーザーの未コミット変更を保持し、変更対象と重なる場合は作業前に確認する。
- `git reset --hard`、`git checkout --`、`rm` などの破壊的操作は、対象と影響を示して明示承認を得てから行う。
- 新規追加・変更するコードコメントは日本語で書く。

## 条件付きガイド

- worktree の作成、配置、共有リンク、親リポジトリの Git 管理範囲を扱う場合は、作業前に [`.codex/guides/worktree-management.md`](.codex/guides/worktree-management.md) を読む。
- サブエージェントへ作業を委任する場合は、委任前に [`.codex/guides/subagent-policy.md`](.codex/guides/subagent-policy.md) を読む。