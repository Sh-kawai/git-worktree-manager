# 運用セット

正本はこのディレクトリへ集約する。strict・autonomousの各フォルダにconfig.toml.templateとpolicy.md、commonにworkflow.mdを置く。

## 選択と適用

親管理フォルダで実行する。既定は確認のみ。未選択時はstrict、以後は.project-policy.tomlに保存した選択を自動使用する。

```sh
python3 scripts/setup-project.py --policy autonomous
python3 scripts/setup-project.py --policy autonomous --apply
```

設定は.codex/config.toml、方針は.codex/guides/project-policy.md、共通手順は.codex/guides/project-workflow.mdへコピー生成する。Markdownも生成対象であり、テンプレートの直接参照にはしない。

## 製品側

製品のAGENTS.mdへ.codex/guides/project-policy.mdの参照を追加し、承認・Git操作・委任にその方針を適用する。未生成時は従来の厳格運用を維持する。仕様・掲載内容・検証規約は維持する。

```sh
python3 scripts/setup-project.py --worktree git-worktree/docs-example --apply
```

製品側では選択方針と共通手順を.codex/guides/project-policy.mdへコピー生成する。新規worktreeもAGENTS.mdが対応済みなら共通作成スクリプトが自動適用する。生成物はGit管理外。

## 更新と保護

引数なしで前回の選択に基づく更新予定を確認し、--applyで適用する。--policy strictで厳格版へ戻せる。生成物の独自編集を検出した場合は全体を事前停止し、強制上書きしない。既存設定・リンク先も保護する。

自律版はローカルコミットまで委任するが、push・PR・rebase・統合・削除・公開等は明示依頼を必要とする。厳格版は共通Gitガイドの承認範囲に従う。環境ファイル保護は両版で共通。exp作成時は親featを明示する。

適用後は新しいCodexチャットで権限を確認する。現在のチャットや管理者の制約は変更されない。

```sh
python3 -m unittest discover -s scripts/tests -v
```

## 共通の入口

AGENTS.mdとCLAUDE.mdは固定の共有ファイルとして管理し、テンプレート化・生成を行わない。CLAUDE.mdはAGENTS.mdを読み込む。AGENTS.mdは生成した方針・作業手順を参照し、厳格版・自律版の違いは参照先だけで切り替える。入口へ選択方針名を埋め込まない。

生成物はconfig.toml、方針・手順のMarkdown、選択と生成履歴のみ。製品側の固有規約も保持する。
