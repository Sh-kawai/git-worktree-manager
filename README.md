# git-worktree-manager

Git worktree をまとめて配置するための親リポジトリです。

このリポジトリは、`git-worktree/` 配下に置く各 worktree の中身や業務ルールを管理しません。管理するのは、worktree の置き場所、共有データのリンク設定、補助スクリプト、Codex 用の作業ルールだけです。

## ディレクトリ構成

```text
.
├── AGENTS.md
├── README.md
├── .gitignore
├── .worktree-shared.sample.toml
├── .codex/
├── scripts/
├── docs/
├── _shared/
│   ├── common/
│   └── worktrees/
└── git-worktree/
```

## Git で管理するもの

- `AGENTS.md`
- `README.md`
- `.gitignore`
- `.worktree-shared.sample.toml`
- `.codex/`
- `scripts/`
- `docs/.gitkeep`
- `_shared/common/.gitkeep`
- `_shared/worktrees/.gitkeep`
- `git-worktree/.gitkeep`

## Git で管理しないもの

- `git-worktree/` 配下の各 worktree
- `_shared/common/` 配下の共有データ
- `_shared/worktrees/` 配下の worktree 別データ
- `docs/` 配下のローカルメモや一時資料
- `.worktree-shared.toml`
- `.env` や秘密鍵などの認証情報

## 初期設定

共有リンク設定を使う場合は、サンプルをコピーしてローカル設定を作成します。

```bash
cp .worktree-shared.sample.toml .worktree-shared.toml
```

`.worktree-shared.toml` はローカル設定として扱い、Git には含めません。

## 新しい worktree を作る

```bash
scripts/new-worktree.sh feat/example
```

デフォルトでは、次のようなディレクトリが作成されます。

```text
git-worktree/feat-example
```

作成後、`.worktree-shared.toml` に定義された共有パスが symlink として設定されます。

## 既存 worktree に共有リンクを適用する

```bash
scripts/setup-worktree-shared.sh git-worktree/develop
```

既に通常ファイルや通常ディレクトリがある場所は上書きしません。必要なデータを `_shared/` 側へ移動してから再実行してください。

## GitHub に push する

この親リポジトリは private repository として作成します。ローカルディレクトリ名と GitHub repository 名は一致していなくて構いません。

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
gh repo create git-worktree-manager --private --source=. --remote=origin --push
```

`gh` を使わない場合は、GitHub で private repository を作成してから remote を追加します。

```bash
git remote add origin git@github.com:<user>/<repo>.git
git push -u origin main
```
