# Codex 作業ルール

このディレクトリは、Git worktree で作成したブランチ別フォルダを `git-worktree/` 配下にまとめる Codex 用の親ディレクトリです。

## CLAUDE.md の扱い

- Codex は、各 worktree 内の `CLAUDE.md` をプロジェクト知識・業務ルール・実装制約の詳細版として扱う。
- 実装、仕様判断、Oracle、機密データ、業務ルールに関係する作業では、該当 worktree の `CLAUDE.md` の必要範囲を参照する。
- トークン使用量を抑えるため、常に `CLAUDE.md` 全体を読むのではなく、作業に関係する章だけを参照する。
- この `AGENTS.md` と `CLAUDE.md` が矛盾する場合は、編集せずユーザーに確認する。

## 作業対象

- `git-worktree/main/` と `git-worktree/develop/` は直接編集しない。
- プログラム変更は、`git-worktree/develop` から作成した `feat/*` ブランチや `fix/*` の worktree で行う。
- 編集前に `pwd`、`git branch --show-current`、`git status --short` で作業場所と状態を確認する。
- 作業場所が `git-worktree/main/` または `git-worktree/develop/` の場合、調査だけに留め、編集前にユーザーへ作業用 `feat/*` や `fix/*` worktree の指定または作成方針を確認する。

## 編集前承認

- ファイル編集の前に、必ず変更方針を提示する。
- ユーザーの明示的な承認を得るまで、ファイル作成・編集・削除を行わない。
- 承認前に許可されるのは、ファイル構成確認、検索、読み取り、Git 状態確認のみ。

## シークレット

- `.env`、`.env.*`、秘密鍵ファイルは読まない。
- API キー、DB パスワード、トークン、社内認証情報を出力しない。
- 認証情報が必要な処理は、利用者のターミナルで 1Password CLI 経由で実行する。

## コードコメント

- 新規追加・変更するコードコメントは日本語で書く。

## Git 操作

- ユーザーの未コミット変更を勝手に戻さない。
- `git reset --hard`、`git checkout --`、`rm` などの破壊的操作は、ユーザーの明示承認なしに実行しない。
- GitHub へ共有する変更は、原則として `git-worktree/` 配下の `feat/*` ブランチ worktree で作成する。
