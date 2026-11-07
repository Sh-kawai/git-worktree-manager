# git-worktree-manager

Git worktree をまとめて配置するための親リポジトリです。

このリポジトリは、`git-worktree/` 配下に置く各 worktree の中身や業務ルールを管理しません。管理するのは、worktree の置き場所、共有データのリンク設定、補助スクリプト、Codex 用の作業ルールだけです。

## Codex 用文書の責務

- `AGENTS.md`: 親管理リポジトリで常に守る作業範囲と安全規則
- `git-worktree/AGENTS.md`: `main`・`develop` を参照専用にするなど、worktree 配置上の追加規則
- 各 worktree の `AGENTS.md`: その製品リポジトリ固有の常時適用ルール
- `.codex/guides/`: 特定の作業でだけ参照する、親管理リポジトリ独自の Codex 用ガイド

`.codex/guides/` は Codex が自動で読み込む予約ディレクトリではありません。必要なガイドは `AGENTS.md` に記載した条件付きリンクから参照します。

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

## AI運用セット

既存の厳格設定は維持し、プロジェクトごとに厳格版・自律版を選べます。設定・AIの権限範囲・作業手順を一括生成します。未選択時は厳格版です。

```sh
python3 scripts/setup-project.py --policy autonomous
python3 scripts/setup-project.py --policy autonomous --apply
```

選択内容と生成物はローカル専用です。更新時は引数なしで前回の選択を使います。手編集を検出すると全体の適用を止めます。導入・製品側の参照・更新手順は[運用セットの説明](.codex/templates/README.md)を参照してください。

## 初期設定

共有リンク設定を使う場合は、サンプルをコピーしてローカル設定を作成します。

```bash
cp .worktree-shared.sample.toml .worktree-shared.toml
```

`.worktree-shared.toml` はローカル設定として扱い、Git には含めません。

各`[[link]]`の`path`はworktree内の参照名です。任意の`source`で、共有領域（`shared`なら`common/`、`per_worktree`なら該当worktreeの領域）内の相対的な格納先を指定できます。省略時は`path`と同じ名前、`source = "."`なら領域の直下を参照します。

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

## 共有Skillのセットアップ

親プロジェクトから develop の共有Skillを利用するには、[共有Skillのセットアップガイド](.codex/guides/development-skills.md)を参照してください。
