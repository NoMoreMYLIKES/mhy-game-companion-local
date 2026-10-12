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
                if f.endswith(('.py', '.js', '.html', '.css', '.md', '.txt', '.bat', '.ps1', '.json')):
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


if __name__ == '__main__':
    unittest.main()
