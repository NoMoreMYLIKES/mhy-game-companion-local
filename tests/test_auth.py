"""One-scan login, CN token derivation and cancellation without network access."""
import asyncio
import hashlib
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import genshin


class AuthTest(unittest.TestCase):
    def setUp(self):
        from server import auth, core, mihoyo, widget
        self.auth, self.core, self.mihoyo, self.widget = auth, core, mihoyo, widget
        self.home = Path(tempfile.gettempdir()).resolve() / ('gcl_auth_' + uuid.uuid4().hex)
        self.home.mkdir()
        self.addCleanup(shutil.rmtree, self.home)
        patcher = mock.patch.object(core, 'DATA', self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        with core.db() as con:
            self.assertEqual(Path(con.execute('PRAGMA database_list').fetchone()[2]).resolve(), self.home / 'app.db')
        core.put('device', {'id': 'test-device', 'fp': 'test-fingerprint'})
        self.token = 'v2_' + 'x' * 30
        self.response = {'status': 'Confirmed', 'user_info': {'aid': '123', 'mid': 'test-mid-123'},
                         'tokens': [{'token_type': 1, 'token': self.token}]}
        self.grant = auth.parse_grant(self.response, auth.identity())
        self.cookies = {'ltuid': '123', 'ltoken': 'l' * 32, 'account_id': '123', 'cookie_token': 'c' * 32}
        self.roles = [SimpleNamespace(game=genshin.Game.GENSHIN, uid=100000001, server='cn_gf01', nickname='Test', server_name='Test'),
                      SimpleNamespace(game=genshin.Game.ZZZ, uid=10000002, server='prod_gf_cn', nickname='Test', server_name='Test')]
        self.candidates = {g: [{'uid': str(a.uid), 'server': a.server, 'name': a.nickname, 'server_name': a.server_name}]
                           for g, a in zip(('genshin', 'zzz'), self.roles)}
        auth.cancel()
        self.addCleanup(auth.cancel)
        self.addCleanup(mihoyo.PENDING.clear)

    def pending(self):
        row = {'run': 'test-run', 'binding': self.auth.binding()}
        self.auth.QR.update(status='creating', run=row['run'])
        return row

    def test_explicit_stoken_required_and_untrusted_fields_not_saved(self):
        for patch in ({'tokens': [{'token_type': 4, 'token': self.token}]},
                      {'tokens': self.response['tokens'] * 2}, {'need_realperson': True},
                      {'tokens': [{'token_type': 1, 'token': 'not-stoken'}]},
                      {'user_info': {'aid': '123'}}, {'user_info': {'aid': 'bad', 'mid': 'test-mid-123'}}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.auth.parse_grant({**self.response, **patch}, self.auth.identity())
        value = self.auth.parse_grant({**self.response, 'private_profile': 'discard-me'}, self.auth.identity())
        self.assertNotIn('private_profile', value)

    def test_cn_derivation_and_identity_do_not_use_overseas_exchange(self):
        responses = [{'ltoken': 'l' * 32}, {'uid': '123', 'cookie_token': 'c' * 32}]
        with mock.patch.object(self.auth, 'exchange', mock.AsyncMock(side_effect=responses)) as call:
            cookies = asyncio.run(self.auth.derive_cookies(self.grant))
        self.assertEqual(cookies, self.cookies)
        self.assertEqual([c.args[0] for c in call.call_args_list], [self.auth.LTOKEN, self.auth.COOKIE])
        for c in call.call_args_list:
            self.assertEqual(c.args[1]['x-rpc-device_id'], 'test-device')
            self.assertEqual(set(c.kwargs['cookies']), {'stuid', 'stoken', 'mid'})
            self.assertEqual(c.kwargs['params'], {'stoken': self.token})
            self.assertNotIn('body', c.kwargs)
        self.assertNotIn(self.token, json.dumps(cookies))

    def test_derivation_rejects_wrong_owner_and_missing_token(self):
        for responses in ([{'ltoken': 'l' * 32}, {'uid': '999', 'cookie_token': 'c' * 32}],
                          [{'ltoken': 'l' * 32, 'uid': '999'}, {'uid': '123', 'cookie_token': 'c' * 32}],
                          [{}, {'uid': '123', 'cookie_token': 'c' * 32}]):
            with mock.patch.object(self.auth, 'exchange', mock.AsyncMock(side_effect=responses)), self.assertRaises(ValueError):
                asyncio.run(self.auth.derive_cookies(self.grant))
        self.assertEqual(self.core.load_secret('mihoyo'), {})

    def test_one_confirmed_qr_installs_both_games_and_refreshes_both(self):
        calls = []
        async def exchange(url, headers, **kwargs):
            calls.append((url, headers, kwargs))
            if url == self.auth.CREATE:
                return {'url': 'https://user.mihoyo.com/qr/test', 'ticket': 'test-ticket-123'}
            if url == self.auth.QUERY:
                self.assertIn('<svg', self.auth.state()['svg'])
                return self.response
            if url == self.auth.LTOKEN:
                return {'ltoken': 'l' * 32}
            return {'uid': '123', 'cookie_token': 'c' * 32}
        client = SimpleNamespace(custom_headers={}, get_game_accounts=mock.AsyncMock(return_value=self.roles))
        with mock.patch.object(self.auth, 'exchange', exchange), \
                mock.patch.object(genshin, 'Client', return_value=client), \
                mock.patch.object(self.auth, 'identity', return_value=self.grant['identity']), \
                mock.patch.object(self.mihoyo, '_ensure_fp', mock.AsyncMock()), \
                mock.patch.object(self.mihoyo, 'refresh_notes', return_value={'current': 12, 'cap': 200}) as refresh:
            self.auth._worker(self.pending())
        self.assertEqual([c[0] for c in calls], [self.auth.CREATE, self.auth.QUERY, self.auth.LTOKEN, self.auth.COOKIE])
        self.assertEqual([c[1]['x-rpc-client_type'] for c in calls[:2]], ['3', '3'])
        self.assertEqual(self.mihoyo.cookies(), self.cookies)
        self.assertEqual(set(self.mihoyo.accounts()), {'genshin', 'zzz'})
        self.assertEqual(refresh.call_args_list, [mock.call('genshin', force=True), mock.call('zzz', force=True)])
        self.assertEqual(self.auth.state()['status'], 'confirmed')
        self.assertTrue(self.auth.state()['unified'])
        self.assertNotIn('svg', self.auth.state())
        self.assertNotIn(self.token, json.dumps(self.auth.state()))
        self.assertEqual(self.core.load_secret('widget'), {})

    def test_failed_derivation_does_not_replace_working_login(self):
        self.core.save_secret('mihoyo', {'cookies': self.cookies})
        before = self.core.load_secret('mihoyo')
        with mock.patch.object(self.auth, 'prepare', mock.AsyncMock(side_effect=OSError())), \
                mock.patch.object(self.mihoyo, 'refresh_notes') as refresh:
            self.auth._worker({**self.pending(), 'legacy': self.grant})
        self.assertEqual(self.auth.state()['status'], 'error')
        self.assertEqual(self.core.load_secret('mihoyo'), before)
        refresh.assert_not_called()

    def test_cancelled_or_replaced_login_cannot_be_installed(self):
        pending = self.pending()
        self.mihoyo.logout()
        with self.assertRaises(ValueError):
            self.auth.install(self.grant, self.cookies, self.candidates, pending['binding'], pending['run'])
        pending = self.pending()
        self.core.save_secret('mihoyo', {'cookies': {'ltuid': '999', 'ltoken': 'other'}})
        with self.assertRaises(ValueError):
            self.auth.install(self.grant, self.cookies, self.candidates, pending['binding'], pending['run'])
        self.assertEqual(self.mihoyo.cookies()['ltuid'], '999')

    def test_existing_app_grant_upgrade_needs_no_new_scan(self):
        self.core.save_secret('mihoyo', {'cookies': self.cookies})
        self.core.put('accounts', {g: rows[0] for g, rows in self.candidates.items()})
        a = self.mihoyo.accounts()['genshin']
        old_binding = hashlib.sha256(json.dumps({'cookies': self.cookies, 'uid': a['uid'], 'server': a['server']}, sort_keys=True).encode()).hexdigest()
        self.core.save_secret('widget', {**self.grant, 'binding': old_binding})
        with mock.patch.object(self.auth, 'prepare', mock.AsyncMock(return_value=(self.cookies, self.candidates))), \
                mock.patch.object(self.auth, 'exchange', side_effect=AssertionError('must reuse existing grant')), \
                mock.patch.object(self.mihoyo, 'refresh_notes', return_value={}):
            self.auth._worker({**self.pending(), 'legacy': self.widget.legacy_credentials()})
        self.assertTrue(self.auth.state()['unified'])
        self.assertTrue(self.widget.available())
        self.assertEqual(self.core.load_secret('widget'), {})

    def test_no_scan_reuse_for_other_account(self):
        self.core.save_secret('mihoyo', {'cookies': {'ltuid': '999', 'ltoken': 'other'}})
        self.core.save_secret('widget', {**self.grant, 'binding': 'old'})
        self.assertEqual(self.widget.legacy_credentials(), {})

    def test_role_discovery_failure_and_expired_qr_preserve_login(self):
        self.core.save_secret('mihoyo', {'cookies': self.cookies})
        before = self.core.load_secret('mihoyo')
        with mock.patch.object(self.auth, 'exchange', mock.AsyncMock(side_effect=genshin.GenshinException({'retcode': -3501}))), \
                mock.patch.object(self.mihoyo, '_ensure_fp', mock.AsyncMock()):
            self.auth._worker(self.pending())
        self.assertEqual(self.auth.state()['status'], 'expired')
        self.assertEqual(self.core.load_secret('mihoyo'), before)
        with mock.patch.object(self.auth, 'prepare', mock.AsyncMock(side_effect=TimeoutError())):
            self.auth._worker({**self.pending(), 'legacy': self.grant})
        self.assertEqual(self.core.load_secret('mihoyo'), before)

    def test_ambiguous_roles_require_selection_and_existing_selection_survives(self):
        other = {**self.candidates['zzz'][0], 'uid': '10000003'}
        self.candidates['zzz'].append(other)
        self.auth.install(self.grant, self.cookies, self.candidates, self.auth.binding())
        self.assertNotIn('zzz', self.mihoyo.accounts())
        self.mihoyo.select_account('zzz', other['uid'])
        self.auth.install(self.grant, self.cookies, self.candidates, self.auth.binding())
        self.assertEqual(self.mihoyo.accounts()['zzz']['uid'], other['uid'])
        self.assertTrue(self.auth.credentials())

    def test_source_failure_after_login_is_reported_without_requesting_another_scan(self):
        with mock.patch.object(self.auth, 'prepare', mock.AsyncMock(return_value=(self.cookies, self.candidates))), \
                mock.patch.object(self.mihoyo, 'refresh_notes', side_effect=[{}, {'error': 'Test source unavailable'}]):
            self.auth._worker({**self.pending(), 'legacy': self.grant})
        self.assertEqual(self.auth.state()['status'], 'confirmed')
        self.assertTrue(self.auth.state()['unified'])
        self.assertIn('Test source unavailable', self.auth.state()['reason'])

    def test_failed_atomic_save_keeps_previous_login_and_roles(self):
        before = {'cookies': self.cookies, 'accounts': {'genshin': self.candidates['genshin'][0]}}
        self.core.save_secret('mihoyo', before)
        with mock.patch.object(self.core, 'save_secret', side_effect=OSError('Test disk failure')), self.assertRaises(OSError):
            self.auth.install(self.grant, self.cookies, self.candidates, self.auth.binding())
        self.assertEqual(self.core.load_secret('mihoyo'), before)
        self.assertNotIn('zzz', self.mihoyo.accounts())

    def test_shared_bundle_roles_are_authoritative_over_legacy_database(self):
        self.core.put('accounts', {'genshin': {'uid': '100000009', 'server': 'cn_gf01'}})
        self.auth.install(self.grant, self.cookies, self.candidates, self.auth.binding())
        self.assertEqual(self.mihoyo.accounts()['genshin']['uid'], self.candidates['genshin'][0]['uid'])
        self.assertEqual(self.mihoyo.account_candidates(), self.candidates)

    def test_exchange_rejects_unapproved_hosts_before_io(self):
        with self.assertRaises(ValueError):
            asyncio.run(self.auth.exchange('https://example.invalid/account', {}, cookies={'stoken': self.token}))


if __name__ == '__main__':
    unittest.main()
