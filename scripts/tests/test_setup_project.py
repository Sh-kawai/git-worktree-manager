"""一時フォルダで運用セットの選択、更新、保護、worktree連携を検証する。"""
import json
import importlib.util
from unittest.mock import patch
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

SOURCE = Path(__file__).resolve().parents[2]


class SetupProjectTests(unittest.TestCase):
    """実ファイルを使い、利用者から見えるセットアップの動作を確認する。"""

    def setUp(self):
        """実プロジェクトに触れない最小の共通リポジトリを用意する。"""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ['scripts']:
            shutil.copytree(SOURCE / name, self.root / name)
        (self.root / '.codex').mkdir()
        shutil.copytree(SOURCE / '.codex/templates', self.root / '.codex/templates')

    def run_setup(self, *args, expected=0):
        """コマンドを実行し、終了コードと生成物を確認可能にする。"""
        result = subprocess.run(['python3', str(self.root / 'scripts/setup-project.py'), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_default_is_strict_and_preview_does_not_write(self):
        """未選択時はstrictで、確認だけでは実設定を作らない。"""
        self.assertIn('strict', self.run_setup().stdout)
        self.assertFalse((self.root / '.project-policy.toml').exists())
        self.assertFalse((self.root / '.codex/config.toml').exists())
        self.run_setup('--apply')
        self.assertEqual((self.root / '.codex/config.toml').read_bytes(),
                         (SOURCE / '.codex/templates/strict/config.toml.template').read_bytes())

    def test_saved_selection_switch_and_template_update(self):
        """選択を保存し、方針切替と正本の更新を同じ手順で反映する。"""
        self.run_setup('--policy', 'autonomous', '--apply')
        self.assertIn('autonomous', self.run_setup().stdout)
        config = tomllib.loads((self.root / '.codex/config.toml').read_text())
        self.assertEqual(config['approvals_reviewer'], 'auto_review')
        filesystem = config['permissions']['worktree-parent']['filesystem'][':workspace_roots']
        self.assertFalse(any('*' in key and access == 'write'
                             for key, access in filesystem.items()))
        template = self.root / '.codex/templates/autonomous/policy.md'
        template.write_text(template.read_text() + '\n更新確認\n')
        self.run_setup('--apply')
        self.assertIn('更新確認', (self.root / '.codex/guides/project-policy.md').read_text())
        self.run_setup('--policy', 'strict', '--apply')
        self.assertIn('strict', self.run_setup().stdout)

    def test_local_edit_blocks_every_output_and_selection_change(self):
        """生成物の手編集があれば、設定や選択だけを先に切り替えない。"""
        self.run_setup('--apply')
        target = self.root / '.codex/guides/project-policy.md'
        target.write_text('手編集')
        before = (self.root / '.codex/config.toml').read_bytes()
        self.run_setup('--policy', 'autonomous', '--apply', expected=1)
        self.assertEqual((self.root / '.codex/config.toml').read_bytes(), before)
        self.assertEqual(target.read_text(), '手編集')
        self.assertIn('strict', (self.root / '.project-policy.toml').read_text())

    def test_unknown_config_and_symlink_are_not_overwritten(self):
        """既存の独自設定と、別ファイルを指す出力先リンクを保護する。"""
        config = self.root / '.codex/config.toml'
        config.write_text('model = "local"')
        self.run_setup('--apply', expected=1)
        self.assertEqual(config.read_text(), 'model = "local"')
        config.unlink()
        other = self.root / 'other.toml'
        other.write_text('keep')
        config.symlink_to(other)
        self.run_setup('--apply', expected=1)
        self.assertEqual(other.read_text(), 'keep')

    def test_preserve_config_survives_updates_and_rejects_policy_switch(self):
        """案件固有の設定を保持し、更新後も設定を上書きせず方針切替を止める。"""
        config = self.root / '.codex/config.toml'
        original = b'model = "local"\n'
        config.write_bytes(original)
        self.run_setup('--preserve-config')
        self.assertFalse((self.root / '.project-policy.toml').exists())
        self.run_setup('--preserve-config', '--apply')
        self.run_setup('--apply')
        self.assertEqual(config.read_bytes(), original)
        self.assertIn('厳格運用', (self.root / '.codex/guides/project-policy.md').read_text())
        self.run_setup('--policy', 'autonomous', '--apply', expected=1)
        self.assertEqual(config.read_bytes(), original)
        self.assertIn('strict', (self.root / '.project-policy.toml').read_text())
        target = self.root / '.codex/guides/project-policy.md'
        target.write_text('手編集')
        self.run_setup('--apply', expected=1)
        self.assertEqual(target.read_text(), '手編集')

    def test_preserve_config_requires_valid_regular_config(self):
        """保持対象が未作成、不正なTOML、リンクの場合は生成前に停止する。"""
        self.run_setup('--preserve-config', '--apply', expected=1)
        config = self.root / '.codex/config.toml'
        config.write_text('invalid = [')
        self.run_setup('--preserve-config', '--apply', expected=1)
        config.unlink()
        other = self.root / 'other.toml'
        other.write_text('model = "local"')
        config.symlink_to(other)
        self.run_setup('--preserve-config', '--apply', expected=1)
        self.assertFalse((self.root / '.project-policy.toml').exists())

    def test_worktree_policy_is_generated_and_ignored(self):
        """製品固有のAGENTSを保持し、選択方針だけをローカルへ渡す。"""
        site = self.root / 'git-worktree/feat-example'
        site.mkdir(parents=True)
        subprocess.run(['git', 'init', str(site)], check=True, capture_output=True)
        instructions = '規約\n.codex/guides/project-policy.mdを読む\n'
        (site / 'AGENTS.md').write_text(instructions)
        self.run_setup('--policy', 'autonomous', '--worktree', 'git-worktree/feat-example', '--apply')
        self.assertEqual((site / 'AGENTS.md').read_text(), instructions)
        target = site / '.codex/guides/project-policy.md'
        self.assertIn('自律運用', target.read_text())
        result = subprocess.run(['git', '-C', str(site), 'check-ignore', '.codex/guides/project-policy.md'],
                                capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.run_setup('--policy', 'strict', '--apply')
        self.assertIn('厳格運用', target.read_text())

    def test_new_worktree_uses_saved_policy_automatically(self):
        """共通の作成スクリプトから保存済み方針が自動で引き継がれる。"""
        develop = self.root / 'git-worktree/develop'
        develop.mkdir(parents=True)
        subprocess.run(['git', 'init', '-b', 'develop', str(develop)], check=True, capture_output=True)
        (develop / 'AGENTS.md').write_text('.codex/guides/project-policy.mdを読む\n')
        subprocess.run(['git', '-C', str(develop), 'add', 'AGENTS.md'], check=True)
        subprocess.run(['git', '-C', str(develop), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                        'commit', '-m', 'fixture'], check=True, capture_output=True)
        (self.root / '.worktree-shared.toml').write_text('[shared]\nroot="_shared"\n')
        self.run_setup('--policy', 'autonomous', '--apply')
        result = subprocess.run(['bash', str(self.root / 'scripts/new-worktree.sh'), 'feat/automatic'],
                                capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        site = self.root / 'git-worktree/feat-automatic'
        self.assertIn('自律運用', (site / '.codex/guides/project-policy.md').read_text())
        shutil.rmtree(site)
        self.run_setup('--apply')
        state = json.loads((self.root / '.codex/template-state.json').read_text())
        self.assertEqual(state['worktrees'], [])

    def test_remote_config_changes_remain_compatible(self):
        """両版の秘密設定保護を揃え、サンプルまで禁止する旧指定を戻さない。"""
        strict = tomllib.loads((self.root / '.codex/templates/strict/config.toml.template').read_text())
        auto = tomllib.loads((self.root / '.codex/templates/autonomous/config.toml.template').read_text())
        strict_fs = strict['permissions']['worktree-parent']['filesystem'][':workspace_roots']
        auto_fs = auto['permissions']['worktree-parent']['filesystem'][':workspace_roots']
        self.assertEqual({k: v for k, v in strict_fs.items() if k.startswith('**/.env')},
                         {k: v for k, v in auto_fs.items() if k.startswith('**/.env')})
        self.assertNotIn('**/.env.*', auto_fs)
        self.assertEqual(strict['agents']['default_subagent_model'], 'gpt-6-luna')
        self.assertNotIn('default_subagent_model', auto['agents'])
        result = subprocess.run(['bash', str(self.root / 'scripts/new-worktree.sh'), 'exp/topic/check'],
                                cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('explicit feat/* base', result.stderr)

    def test_write_failure_rolls_back_completed_outputs(self):
        """途中の書き込み失敗でも、生成物と選択を以前の状態へ戻す。"""
        self.run_setup('--apply')
        spec = importlib.util.spec_from_file_location('fixture_setup', self.root / 'scripts/setup-project.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        original_write = module.atomic_write
        calls = 0

        def fail_once(path, content):
            """2件目だけ失敗させ、復旧処理は通常どおり実行する。"""
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected failure')
            original_write(path, content)

        with patch.object(module, 'atomic_write', fail_once), patch('sys.argv', ['setup-project.py', '--policy', 'autonomous', '--apply']):
            self.assertEqual(module.main(), 1)
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_invalid_output_parent_does_not_partially_apply(self):
        """ガイド出力先が不正なら実設定だけ先に変更しない。"""
        (self.root / '.codex/guides').write_text('keep')
        self.run_setup('--policy', 'autonomous', '--apply', expected=1)
        self.assertFalse((self.root / '.codex/config.toml').exists())
        self.assertFalse((self.root / '.project-policy.toml').exists())
        self.assertEqual((self.root / '.codex/guides').read_text(), 'keep')

    def test_policy_switch_does_not_modify_entry_documents(self):
        """方針を切り替えても固定の入口は生成・変更しない。"""
        originals = {'AGENTS.md': '共通規約\n', 'CLAUDE.md': '@AGENTS.md\n'}
        for name, content in originals.items():
            (self.root / name).write_text(content)
        for policy in ['strict', 'autonomous', 'strict']:
            self.run_setup('--policy', policy, '--apply')
            for name, content in originals.items():
                self.assertEqual((self.root / name).read_text(), content)
            state = json.loads((self.root / '.codex/template-state.json').read_text())
            self.assertNotIn('AGENTS.md', state['files'])
            self.assertNotIn('CLAUDE.md', state['files'])

    def test_invalid_selection_path_and_unprepared_site_stop(self):
        """不正な選択、外部パス、方針参照未導入の製品では適用しない。"""
        (self.root / '.project-policy.toml').write_text('policy = "unknown"')
        self.run_setup('--apply', expected=1)
        (self.root / '.project-policy.toml').unlink()
        self.run_setup('--worktree', '../outside', '--apply', expected=1)
        site = self.root / 'git-worktree/old-site'
        site.mkdir(parents=True)
        subprocess.run(['git', 'init', str(site)], check=True, capture_output=True)
        self.run_setup('--worktree', 'git-worktree/old-site', '--apply', expected=1)
        self.assertFalse((self.root / '.codex/config.toml').exists())


if __name__ == '__main__':
    unittest.main()
