# 共有Skillのセットアップ

共有skillの正本は `git-worktree/develop/.agents/skills/` です。開発・レビューは子リポジトリの作業ブランチで行い、developへ取り込んでローカルのdevelop worktreeを更新します。developは直接編集しません。

親のCodex用入口は `.agents/skills/<名前>`、Claude Code用入口は `.claude/skills/<名前>` とし、同じ正本への相対リンクを使います。リンク先の更新は即反映されるため、develop内の未コミット編集も影響します。skillの保管場所と作業対象は別なので、依頼時は対象worktreeを指定してください。

取り込み後、まず次のコマンドで共有元と既存入口を確認します。

```bash
python3 scripts/setup-development-skills.py
```

問題がなければ `--apply` を付けてリンクを有効化します。既存入口と衝突すると上書きせず停止します。既存skillを保持して切り替える場合は、確認後に次を実行します。

```bash
python3 scripts/setup-development-skills.py --apply --backup-existing
```

退避先は `.agents/skill-backups/before-develop-*/` です。既存の `feature-development` もここに保持されます。developに必須skillがない段階では、入口を変更せず「取り込み待ち」と表示します。

他のメンバーがskillを追加した場合も、developを更新して同じコマンドを実行すると新しい入口を追加できます。共有元から削除されたskillの入口は自動削除しません。利用中の入口と依存関係を確認してから整理してください。

設定後は新しいチャットでskillの検出元を確認します。Codexでは `$feature-development`、Claude Codeでは `/feature-development` で利用できます。同名の個人用skillやプラグインとの重複にも注意してください。

新規の親のリンクと退避データは各自のローカル設定としてGit管理から除外します。既存の `feature-development/SKILL.md` は親で追跡済みのため、切替時にはGit差分が出ます。ローカル入口へ移行する際の追跡解除は利用者が行ってください（スクリプトはGit操作をしません）。Gitで共有する正本は子リポジトリ内に置きます。
