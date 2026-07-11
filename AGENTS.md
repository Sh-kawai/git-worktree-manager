# Codex 作業ルール

このリポジトリは、複数の Git worktree を `git-worktree/` 配下に置くための親リポジトリです。

このリポジトリ自体は、`git-worktree/` 内の各プロジェクトの仕様、業務ルール、実装詳細を管理対象にしません。

## 作業対象

- このリポジトリで扱うのは、worktree 配置を支える管理ファイルとスクリプトに限定する。
- `git-worktree/` 配下の中身は、原則としてこのリポジトリの作業対象外とする。
- `_shared/common/` と `_shared/worktrees/` 配下の実データは、原則としてこのリポジトリの作業対象外とする。
- 各 worktree 内の `CLAUDE.md`、`AGENTS.md`、README、実装ファイルは、その worktree 側のルールとして扱い、この親リポジトリの判断材料にしない。

## Git 管理

- このリポジトリでは、管理用ファイルだけを Git に含める。
- `git-worktree/`、`_shared/common/`、`_shared/worktrees/`、`docs/` の中身は `.gitkeep` を除き追跡しない。
- `.worktree-shared.toml` はローカル設定として扱い、Git には含めない。
- 共有用のひな形は `.worktree-shared.sample.toml` として管理する。

## 編集前承認

- ファイル編集の前に、必ず変更方針を提示する。
- ユーザーの明示的な承認を得るまで、ファイル作成・編集・削除を行わない。
- 承認前に許可されるのは、ファイル構成確認、検索、読み取り、Git 状態確認のみ。

## シークレット

- `.env`、`.env.*`、秘密鍵ファイルは読まない。
- API キー、DB パスワード、トークン、社内認証情報を出力しない。

## コードコメント

- 新規追加・変更するコードコメントは日本語で書く。

## Git 操作

- ユーザーの未コミット変更を勝手に戻さない。
- `git reset --hard`、`git checkout --`、`rm` などの破壊的操作は、ユーザーの明示承認なしに実行しない。
- GitHub へ共有する変更は、原則として `git-worktree/` 配下の `feat/*` ブランチ worktree で作成する。
