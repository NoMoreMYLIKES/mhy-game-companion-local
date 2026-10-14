"""Shared official widget protocol, attribution and stale-result regression tests."""
import asyncio
import hashlib
import json
import os
import shutil
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import genshin


class WidgetTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.gettempdir()).resolve() / ('gcl_widget_' + uuid.uuid4().hex)
        self.home.mkdir()
        self.addCleanup(shutil.rmtree, self.home)
        from server import auth, core, mihoyo, widget
        self.auth, self.core, self.mihoyo, self.widget = auth, core, mihoyo, widget
        patcher = mock.patch.object(core, 'DATA', self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        with core.db() as con:
            self.assertEqual(Path(con.execute('PRAGMA database_list').fetchone()[2]).resolve(), self.home / 'app.db')
        self.roles = {'genshin': {'uid': '100000001', 'server': 'cn_gf01', 'name': 'Test'},
                      'zzz': {'uid': '10000002', 'server': 'prod_gf_cn', 'name': 'Test'}}
        core.put('device', {'id': 'test-device', 'fp': 'test-fingerprint'})
        self.token = 'v2_' + 'x' * 30
        self.app = {'aid': '123', 'mid': 'test-mid-123', 'stoken': self.token, 'identity': auth.identity()}
        self.login()
        auth.cancel()
        self.addCleanup(auth.cancel)
        auth.RENEWED.clear()
        self.addCleanup(auth.RENEWED.clear)
        widget.ROLE_CHECKS.clear()
        self.addCleanup(widget.ROLE_CHECKS.clear)

    def login(self, **extra):
        self.core.save_secret('mihoyo', {'cookies': {'ltuid': '123', 'ltoken': 'test-login'}, 'app': self.app,
                                         'accounts': self.roles, 'generation': 'test-login', **extra})

    def bound_roles(self, game):
        a = self.roles[game]
        return [SimpleNamespace(game=self.mihoyo.GAMES[game], uid=int(a['uid']), server=a['server'])]

    def read(self, game, response, roles=None):
        self.widget.ROLE_CHECKS.clear()  # each read looks the roles up
        client = SimpleNamespace(get_game_accounts=mock.AsyncMock(return_value=roles if roles is not None else self.bound_roles(game)))
        with mock.patch.object(self.widget, 'exchange', mock.AsyncMock(return_value=response)), \
                mock.patch.object(self.mihoyo, 'client', return_value=client):
            return asyncio.run(self.widget.note(game))

    def test_one_grant_serves_both_games_without_exposing_secrets(self):
        self.assertTrue(self.mihoyo.logged_in())
        public = json.dumps(self.auth.state())
        self.assertNotIn(self.token, public)
        self.assertNotIn('identity', public)
        self.assertNotIn(self.token, (self.home / 'app.db').read_bytes().decode(errors='ignore'))
        if os.name == 'nt':
            self.assertNotIn(self.token, (self.home / 'mihoyo.dpapi.json').read_text())

    def test_uidless_widgets_require_unique_live_role_for_each_game(self):
        for game, value, expected in (
            ('genshin', {'current_resin': 26, 'max_resin': 200}, (26, 200)),
            ('zzz', {'energy': {'progress': {'current': 40, 'max': 240}}}, (40, 240)),
        ):
            with self.subTest(game=game):
                self.assertEqual(self.read(game, value), expected)
                valid = self.bound_roles(game)
                wrong = [SimpleNamespace(game=self.mihoyo.GAMES[game], uid=100000003, server=valid[0].server)]
                for roles in ([], wrong, valid + wrong):
                    with self.assertRaises(ValueError):
                        self.read(game, value, roles)

    def test_role_lookup_is_reused_until_the_login_changes_or_it_expires(self):
        client = SimpleNamespace(get_game_accounts=mock.AsyncMock(return_value=self.bound_roles('genshin')))
        with mock.patch.object(self.widget, 'exchange', mock.AsyncMock(return_value={'current_resin': 26, 'max_resin': 200})), \
                mock.patch.object(self.mihoyo, 'client', return_value=client):
            for _ in range(2):
                self.assertEqual(asyncio.run(self.widget.note('genshin')), (26, 200))
            self.assertEqual(client.get_game_accounts.await_count, 1)
            self.core.save_secret('mihoyo', {**self.core.load_secret('mihoyo'), 'generation': 'another login'})
            asyncio.run(self.widget.note('genshin'))
            self.assertEqual(client.get_game_accounts.await_count, 2)
            login, _ = self.widget.ROLE_CHECKS['genshin']
            self.widget.ROLE_CHECKS['genshin'] = (login, time.monotonic() - self.widget.ROLE_CHECK_SECONDS - 1)
            asyncio.run(self.widget.note('genshin'))
            self.assertEqual(client.get_game_accounts.await_count, 3)

    def test_response_role_and_region_must_match(self):
        value = {'uid': '100000001', 'region': 'cn_gf01', 'current_resin': 0, 'max_resin': 200}
        self.assertEqual(self.read('genshin', value), (0, 200))
        for fields in ({'uid': '100000002'}, {'region': 'cn_qd01'}, {'region': None}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.read('genshin', {**value, **fields})

    def test_unknown_or_invalid_stamina_never_becomes_zero(self):
        for game in self.roles:
            for current, cap in ((None, 200), (12, None), ('12', 200), (True, 200), (201, 200), (0, 0)):
                value = {'current_resin': current, 'max_resin': cap} if game == 'genshin' else {'energy': {'progress': {'current': current, 'max': cap}}}
                with self.subTest(game=game, current=current, cap=cap), self.assertRaises(ValueError):
                    self.read(game, value)
        for value in ({}, {'energy': None}, {'energy': {'progress': []}}):
            with self.assertRaises(ValueError):
                self.read('zzz', value)

    def test_widget_wire_contract_and_no_web_cookies(self):
        for game in self.roles:
            a = self.roles[game]
            value = {'uid': a['uid'], 'server': a['server'], 'current_resin': 17, 'max_resin': 200,
                     'energy': {'progress': {'current': 17, 'max': 240}}}
            with mock.patch.object(self.widget, 'exchange', mock.AsyncMock(return_value=value)) as call:
                self.assertEqual(asyncio.run(self.widget.note(game))[0], 17)
            url, headers = call.call_args.args
            self.assertEqual(url, self.auth.WIDGETS[game])
            self.assertEqual(headers['x-rpc-client_type'], '5')
            self.assertEqual(headers['x-rpc-device_id'], 'test-device')
            self.assertEqual(set(call.call_args.kwargs['cookies']), {'stuid', 'stoken', 'mid'})
            self.assertNotIn('params', call.call_args.kwargs)
            t, r, digest = headers['ds'].split(',')
            salt = genshin.constants.DS_SALT[genshin.Region.CHINESE]
            self.assertEqual(digest, hashlib.md5(f'salt={salt}&t={t}&r={r}&b=&q='.encode()).hexdigest())

    def test_logout_during_read_discards_sample_and_health(self):
        for game in self.roles:
            async def exchange(*args, **kwargs):
                self.mihoyo.logout()
                return {'uid': self.roles[game]['uid'], 'server': self.roles[game]['server'],
                        'current_resin': 17, 'max_resin': 200, 'energy': {'progress': {'current': 17, 'max': 240}}}
            self.login()
            with mock.patch.object(self.widget, 'exchange', exchange):
                self.assertIn('error', self.mihoyo.refresh_notes(game, force=True))
            self.assertIsNone(self.core.latest_sample(game))
            self.assertEqual(self.mihoyo.health('stamina-' + game), {})

    def test_role_lookup_with_lapsed_cookies_renews_them_and_keeps_the_sample(self):
        lapsed = genshin.GenshinException({'retcode': -100, 'message': ''})
        client = SimpleNamespace(get_game_accounts=mock.AsyncMock(side_effect=[lapsed, self.bound_roles('zzz')]))
        fresh = {'ltuid': '123', 'ltoken': 'renewed-login'}
        with mock.patch.object(self.widget, 'exchange', mock.AsyncMock(return_value={'energy': {'progress': {'current': 40, 'max': 240}}})), \
                mock.patch.object(self.mihoyo, 'client', return_value=client), \
                mock.patch.object(self.auth, 'derive_cookies', mock.AsyncMock(return_value=fresh)):
            self.assertEqual(self.mihoyo.refresh_notes('zzz', force=True), {'current': 40, 'cap': 240})
        self.assertEqual(self.mihoyo.cookies(), fresh)
        self.assertEqual(self.core.latest_sample('zzz')['source'], 'source_widget')
        self.assertTrue(self.mihoyo.health('stamina-zzz')['ok'])

    def test_failure_preserves_previous_sample_and_uses_source_backoff(self):
        self.core.add_sample('zzz', 44, 240, 'source_widget')
        before = self.core.latest_sample('zzz')
        with mock.patch.object(self.widget, 'note', mock.AsyncMock(side_effect=genshin.GenshinException({'retcode': -10001}))) as read:
            self.assertIn('error', self.mihoyo.refresh_notes('zzz', force=True))
            self.assertTrue(self.mihoyo.refresh_notes('zzz')['deferred'])
            self.assertEqual(read.await_count, 1)
        self.assertEqual(self.core.latest_sample('zzz'), before)
        self.assertFalse(self.mihoyo.health('stamina-zzz')['ok'])

    def test_selecting_role_keeps_shared_grant_but_rejects_inflight_read(self):
        before = self.auth.credentials()
        other = {**self.roles['zzz'], 'uid': '10000003'}
        self.login(candidates={'zzz': [self.roles['zzz'], other]})
        async def exchange(*args, **kwargs):
            self.mihoyo.select_account('zzz', other['uid'])
            return {'uid': self.roles['zzz']['uid'], 'server': self.roles['zzz']['server'],
                    'energy': {'progress': {'current': 17, 'max': 240}}}
        with mock.patch.object(self.widget, 'exchange', exchange):
            self.assertIn('error', self.mihoyo.refresh_notes('zzz', force=True))
        self.assertEqual(self.auth.credentials(), before)
        self.assertIsNone(self.core.latest_sample('zzz'))

    def test_website_only_login_reads_no_stamina(self):
        saved = self.core.load_secret('mihoyo')
        saved.pop('app')
        self.core.save_secret('mihoyo', saved)
        with mock.patch.object(self.widget, 'note', side_effect=AssertionError('no grant')):
            self.assertIn('error', self.mihoyo.refresh_notes('zzz', force=True))
        self.assertIsNone(self.core.latest_sample('zzz'))


if __name__ == '__main__':
    unittest.main()
