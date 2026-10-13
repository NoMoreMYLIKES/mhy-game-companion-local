"""Smoke test verifying module imports, core functions, and source-code anonymization."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix='gcl_test_')
        os.environ['GCL_HOME'] = cls.temp_dir

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_imports(self):
        import server.core as core
        import server.goals as goals
        import server.materials as materials
        import server.mihoyo as mihoyo
        import server.notify as notify
        import server.planner as planner
        import server.runner as runner
        import server.scheduler as scheduler
        import server.tools as tools
        import server.web as web

        self.assertEqual(core.VERSION, '1.0.0')

    def test_source_code_anonymization(self):
        """No personal data in committed files: generic patterns plus an optional local denylist.

        Personal terms (names, UIDs, host names) go in tests/pii_denylist.txt, one per line.
        That file is git-ignored, so the terms themselves are never published.
        """
        import re
        patterns = {
            'email address': rb'[\w.+-]+@[\w-]+\.[\w.-]*[a-z]{2,}',
            'Windows user folder': rb'[a-z]:[\\/]+users[\\/]+(?!public\b)[^\\/\s"\']+',
            'Linux home folder': rb'/home/[a-z_][\w.-]*',
            'Tailscale host': rb'\.ts\.net\b',
            'private IP address': rb'\b(?:192\.168|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7]))\.\d{1,3}\.\d{1,3}\b',
        }
        denylist = PROJECT_ROOT / 'tests' / 'pii_denylist.txt'
        words = []
        if denylist.is_file():
            words = [w.strip().lower().encode() for w in denylist.read_text(encoding='utf-8').splitlines()
                     if w.strip() and not w.startswith('#')]
        checked = 0
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in ('.git', '.venv', '__pycache__', 'data', 'tests')]
            for f in files:
                if f.endswith(('.py', '.js', '.html', '.css', '.md', '.txt', '.bat', '.ps1', '.sh', '.json')):
                    path = Path(root) / f
                    content = path.read_bytes().lower()
                    for label, pattern in patterns.items():
                        match = re.search(pattern, content)
                        self.assertIsNone(match, f"Found {label} in {path}: {match and match.group()!r}")
                    for word in words:
                        self.assertNotIn(word, content, f"Found a denylisted term in {path}")
                    checked += 1
        self.assertGreater(checked, 10, "Should have checked at least 10 project source files")

    def test_backend_messages(self):
        """Every backend message has English and Chinese text with the same placeholders."""
        import re
        import string
        from server.i18n import MESSAGES
        fields = lambda text: {f for _, f, _, _ in string.Formatter().parse(text) if f}
        for key, texts in MESSAGES.items():
            self.assertEqual(len(texts), 2, key)
            self.assertTrue(all(texts), key)
            self.assertEqual(fields(texts[0]), fields(texts[1]), f"placeholders differ for {key}")
        used = set()
        for path in (PROJECT_ROOT / 'server').glob('*.py'):
            used |= set(re.findall(r"\btr\('([a-z0-9_]+)'\s*[,)]", path.read_text(encoding='utf-8')))
        self.assertFalse(used - set(MESSAGES), f"unknown message keys: {used - set(MESSAGES)}")

    def test_image_cache_is_bounded(self):
        """Only HTTPS images from official hosts are cached, and keys cannot leave data/assets."""
        from server import assets, core
        self.assertTrue(assets.allowed('https://act-webstatic.mihoyo.com/icon.png'))
        self.assertTrue(assets.allowed('https://upload-bbs.miyoushe.com/a.png'))
        self.assertFalse(assets.allowed('http://act-webstatic.mihoyo.com/icon.png'))
        self.assertFalse(assets.allowed('https://mihoyo.com.example.org/icon.png'))
        self.assertFalse(assets.allowed('https://example.org/mihoyo.com/icon.png'))
        self.assertIsNone(assets.file('../../etc/passwd'))
        self.assertIsNone(assets.file('genshin/character/../../secret'))
        assets.collect({'genshin/character/1': 'https://example.org/x.png', '../escape': 'https://act-webstatic.mihoyo.com/x.png'})
        self.assertEqual(core.get('asset_sources', {}), {})

    def test_paused_item_matches_ui_key(self):
        """The UI pauses items by their full key (goal id + item key)."""
        from server import materials
        goal = {'id': 'g1', 'game': 'zzz', 'name': 'X', 'category_order': ['level', 'talents', 'weapon'],
                'materials': [{'id': 'm1', 'name': 'Y', 'need': 5, 'owned': 0, 'remaining': 5, 'category': 'level'}],
                'paused': ['g1:manual:m1']}
        items = materials.items_for_goal(goal, {})
        self.assertEqual(items[0]['key'], 'g1:manual:m1')
        self.assertTrue(items[0]['paused'])

    def test_planner_empty(self):
        import server.planner as planner
        p = planner.plan('genshin')
        self.assertEqual(p['game'], 'genshin')
        self.assertIsNone(p['item'])

        p_zzz = planner.plan('zzz')
        self.assertEqual(p_zzz['game'], 'zzz')
        self.assertIsNone(p_zzz['item'])

    def test_i18n_symmetry_and_base(self):
        import re
        web_app = PROJECT_ROOT / 'web' / 'app.js'
        content = web_app.read_text(encoding='utf-8')
        en_match = re.search(r'en:\s*\{(.*?)\n  \},', content, re.DOTALL)
        zh_match = re.search(r'zh:\s*\{(.*?)\n  \}', content, re.DOTALL)
        self.assertIsNotNone(en_match, "I18N.en should exist")
        self.assertIsNotNone(zh_match, "I18N.zh should exist")

        en_keys = set(re.findall(r'^\s*([a-zA-Z0-9_]+):', en_match.group(1), re.M))
        zh_keys = set(re.findall(r'^\s*([a-zA-Z0-9_]+):', zh_match.group(1), re.M))
        self.assertEqual(en_keys, zh_keys, f"i18n keys must match symmetrically: {en_keys ^ zh_keys}")

        # English base language verification: index.html has lang="en"
        index_html = (PROJECT_ROOT / 'web' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<html lang="en">', index_html)

        # Check default lang in app.js is 'en'
        self.assertIn("localStorage.getItem('gcl_lang') || 'en'", content)


    def test_hosts_without_automation_plan_only(self):
        """On Linux, runs and the logon autostart are refused with a message, never attempted."""
        from unittest import mock
        import server.runner as runner
        import server.scheduler as scheduler
        import server.tools as tools
        from server.i18n import tr
        with mock.patch.object(tools, 'automation', return_value=False):
            with self.assertRaises(ValueError) as caught:
                runner.start_batch(['zzz'])
            self.assertEqual(str(caught.exception), tr('runs_need_windows'))
            self.assertFalse(runner.busy())
            with self.assertRaises(ValueError):
                scheduler.set_autostart(True)
            self.assertEqual(scheduler.set_autostart(False), '')
            self.assertFalse(scheduler.autostart_installed())

    @unittest.skipIf(os.name == 'nt', 'Windows protects credentials with DPAPI')
    def test_credentials_are_private_files(self):
        import stat
        import server.core as core
        core.save_secret('test-secret', {'value': 1})
        mode = stat.S_IMODE((core.DATA / 'test-secret.dpapi.json').stat().st_mode)
        self.assertEqual(mode, 0o600)
        self.assertEqual(core.load_secret('test-secret'), {'value': 1})
        self.assertFalse(core.DEFAULTS['notify']['channels']['toast']['enabled'])  # balloon tips need Windows

    @unittest.skipIf(os.name == 'nt', 'the shell scripts are for Linux')
    def test_shell_scripts(self):
        import subprocess
        for name in ('start.sh', 'stop.sh'):
            path = PROJECT_ROOT / name
            self.assertTrue(os.access(path, os.X_OK), f'{name} must be executable')
            self.assertNotIn(b'\r', path.read_bytes(), f'{name} must keep LF line endings')
            result = subprocess.run(['bash', '-n', str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        usage = subprocess.run(['bash', str(PROJECT_ROOT / 'start.sh'), '--help'], capture_output=True, text=True)
        self.assertEqual(usage.returncode, 0)
        self.assertIn('--service', usage.stdout)
        self.assertNotIn('set -u', usage.stdout)

    def test_captcha_verification_flow(self):
        """A 1034 on Real-Time Notes offers the captcha; a solved one's token reaches the notes request."""
        import base64
        import json
        from unittest import mock
        import genshin
        import server.core as core
        import server.mihoyo as mihoyo
        from server.i18n import tr
        raw = json.dumps({'cookies': {'ltuid_v2': '1', 'ltoken_v2': 'x'}}).encode()
        core.write_json(core.DATA / 'mihoyo.dpapi.json', {'encrypted': base64.b64encode(raw).decode()})
        core.put('accounts', {'genshin': {'uid': '100000001', 'name': 'T', 'server': 'cn_gf01'}})
        sent = {}

        class FakeClient:
            def __init__(self):
                self.custom_headers = {}

            async def get_genshin_notes(self, uid, autoauth=False):
                sent['challenge'] = self.custom_headers.get('x-rpc-challenge')
                sent['retry_version'] = self.custom_headers.get('x-rpc-app_version')
                raise genshin.GenshinException({'retcode': 1034, 'message': 'verification required'})

            async def request_hoyolab(self, url, method=None, params=None, data=None, headers=None):
                sent.update(url=url, method=method, data=data, headers=dict(self.custom_headers))
                return {'challenge': 'token-from-miyoushe'}

        async def no_fp():
            return {}

        with mock.patch.object(mihoyo, 'client', lambda game=None: FakeClient()), \
                mock.patch.object(mihoyo, '_ensure_fp', no_fp):
            self.assertIn('error', mihoyo.refresh_notes('genshin', force=True))
            self.assertTrue(mihoyo.health('notes-genshin')['captcha'])
            with self.assertRaises(ValueError) as caught:
                mihoyo.finish_verification('genshin', {'geetest_challenge': 'c'})
            self.assertEqual(str(caught.exception), tr('captcha_incomplete'))
            answer = {'geetest_challenge': 'c', 'geetest_validate': 'v', 'geetest_seccode': 'v|jordan'}
            mihoyo.finish_verification('genshin', answer)
        self.assertTrue(sent['url'].endswith('/card/wapi/verifyVerification'))
        self.assertEqual((sent['method'], sent['data']), ('POST', answer))
        self.assertEqual(sent['headers']['x-rpc-challenge_game'], '2')
        self.assertEqual(sent['headers']['x-rpc-app_version'], mihoyo.APP_VERSION)  # the record page's identity
        self.assertEqual(sent['challenge'], 'token-from-miyoushe')  # the retry carried the token
        self.assertEqual(sent['retry_version'], mihoyo.APP_VERSION)


if __name__ == '__main__':
    unittest.main()
