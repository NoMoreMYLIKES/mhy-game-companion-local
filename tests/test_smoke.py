"""Smoke test verifying module imports, core functions, and source-code anonymization."""
import os
import shutil
import subprocess
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
        # Scan tracked and publishable new files, including tests. Local diagnostics,
        # runtime data and browser captures follow Git's ignore rules.
        try:
            git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=PROJECT_ROOT,
                                               stderr=subprocess.DEVNULL).decode().strip()
            if Path(git_root).resolve() != PROJECT_ROOT.resolve():
                raise ValueError('Not the root of a Git checkout')
            names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                                             cwd=PROJECT_ROOT).decode().split('\0')
            paths = [PROJECT_ROOT / name for name in names if name]
        except (OSError, ValueError, subprocess.CalledProcessError):
            # Source archives have no Git metadata. Their runtime folders remain local.
            paths = []
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if d not in ('.git', '.venv', '__pycache__', 'data', 'scratch', '.playwright-mcp')]
                paths.extend(Path(root) / f for f in files if f != 'pii_denylist.txt')
        checked = 0
        for path in paths:
            if path.is_file() and path.suffix in ('.py', '.js', '.html', '.css', '.md', '.txt', '.bat', '.ps1', '.sh', '.json'):
                content = path.read_bytes().lower()
                for label, pattern in patterns.items():
                    self.assertIsNone(re.search(pattern, content), f"Found {label} in {path.relative_to(PROJECT_ROOT)}")
                for word in words:
                    self.assertFalse(word in content, f"Found a denylisted term in {path.relative_to(PROJECT_ROOT)}")
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

    def test_zzz_portrait_without_square_icon(self):
        """The upgrade guide leaves square_icon empty; the official square avatar address is used instead."""
        from types import SimpleNamespace
        from server import assets, mihoyo
        url = mihoyo.zzz_portrait(SimpleNamespace(id=1041, square_icon=None))
        self.assertTrue(url.endswith('/role_square_avatar_1041.png'))
        self.assertTrue(assets.allowed(url))
        given = 'https://act-webstatic.mihoyo.com/x/role_square_avatar_1041.png'
        self.assertEqual(mihoyo.zzz_portrait(SimpleNamespace(id=1041, square_icon=given)), given)

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

    def test_forecast_coffee_and_cap(self):
        """Today's coffee counts until a ZZZ batch of this game day ran; coffee above the cap is kept, not cut back."""
        from datetime import datetime
        from unittest import mock
        from server import core, planner
        home = Path(tempfile.mkdtemp(prefix='gcl_forecast_'))
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        now = datetime(2026, 10, 20, 4, 30, tzinfo=core.CN)  # after the 04:00 reset, before the 05:00 batch
        with mock.patch.object(core, 'DATA', home), mock.patch.object(core, 'now', return_value=now):
            core.save_settings({'schedule': {'enabled': True, 'times': ['05:00', '18:00'], 'games': ['zzz']},
                                'planning': {'zzz_coffee_forecast': 80}})
            core.add_sample('zzz', 240, 240, 'source_widget', core.stamp(now))
            rows = [r for r in planner.forecast(2)['rows'] if r['game'] == 'zzz']
            self.assertEqual((rows[0]['stamina'], rows[0]['coffee']), (320, 80))  # today's coffee, above the cap
            self.assertEqual(rows[1]['stamina'], 320)                               # kept until it is spent
            self.assertEqual(rows[1]['full_at'], core.stamp(now))                   # full since the reading
            core.save_run({'id': 'today', 'started': core.stamp(now), 'ended': core.stamp(now), 'source': 'manual',
                           'status': 'SUCCESS', 'games': [{'game': 'zzz', 'status': 'SUCCESS'}], 'notes': []})
            rows = [r for r in planner.forecast(2)['rows'] if r['game'] == 'zzz']
            self.assertEqual((rows[0]['stamina'], rows[0]['coffee']), (240, 0))    # that batch drank it
            self.assertEqual(rows[2]['coffee'], 80)                                 # the next game day's coffee

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

        # A page without its own choice takes the saved language, which is English by default
        from server import core
        self.assertIn("localStorage.getItem('gcl_lang') || null", content)
        self.assertIn("if (!CURRENT_LANG) adoptLang(next.settings?.ui?.lang);", content)
        self.assertEqual(core.DEFAULTS['ui']['lang'], 'en')

    def test_page_language_does_not_change_the_saved_one(self):
        """Server text follows each page's X-Lang; only the language switch (POST /api/lang) changes the saved one."""
        import json
        import threading
        import urllib.request
        from server import core, web
        from server.i18n import MESSAGES

        def daily(lang=None):
            request = urllib.request.Request(f'http://127.0.0.1:{port}/api/state', headers={'X-Lang': lang} if lang else {})
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read())['plans']['zzz']['daily']

        def switch(lang):
            request = urllib.request.Request(f'http://127.0.0.1:{port}/api/lang', data=json.dumps({'lang': lang}).encode(),
                                             headers={'X-GC': '1', 'Content-Type': 'application/json'}, method='POST')
            urllib.request.urlopen(request, timeout=60).close()

        httpd = web.ThreadingHTTPServer(('127.0.0.1', 0), web.Handler)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        was_ready = web.READY.is_set()
        web.READY.set()
        en, zh = MESSAGES['daily_onedragon']
        try:
            core.save_settings({'ui': {'lang': 'en'}})
            self.assertIn(zh, daily('zh'))
            self.assertIn(en, daily('en'))
            self.assertEqual(core.settings()['ui']['lang'], 'en')  # reading never changes the saved language
            self.assertIn(en, daily())                              # a page without a choice gets the saved one
            switch('zh')
            self.assertIn(zh, daily())
            self.assertIn(en, daily('en'))
        finally:
            core.save_settings({'ui': {'lang': 'en'}})
            if not was_ready:
                web.READY.clear()
            httpd.shutdown()
            httpd.server_close()


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


if __name__ == '__main__':
    unittest.main()
