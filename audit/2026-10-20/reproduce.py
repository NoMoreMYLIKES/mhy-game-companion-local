"""Offline counterexamples. Failures describe expected behavior not met by the audited code.

Set GCL_HOME before launching Python; the runner refuses a production runtime.
No credentials are copied and all official calls, processes and notifications are stubbed.
"""
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest import mock
import uuid

SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
HOME = Path(os.environ['GCL_HOME']).resolve()
assert HOME != SOURCE / 'data' and not (HOME / 'mihoyo.dpapi.json').exists()
assert (HOME / 'AUDIT_RUNTIME').read_text(encoding='utf-8').strip() == 'synthetic'
HOME.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE / 'tests'))
from server import assets, core, gear, goals, inventory, materials, mihoyo, notify, planner, runner, web
from test_gear import full_gear
assert core.DATA.resolve() == HOME
with core.db() as con:
    assert Path(con.execute('pragma database_list').fetchone()[2]).resolve() == HOME / 'app.db'


class LogicAudit(unittest.TestCase):
    def setUp(self):
        home = HOME / (self._testMethodName + '-' + uuid.uuid4().hex[:6])
        home.mkdir()
        self.home = home
        p = mock.patch.object(core, 'DATA', home)
        p.start()
        self.addCleanup(p.stop)
        with core.db() as con:
            self.assertEqual(Path(con.execute('pragma database_list').fetchone()[2]).resolve(), home / 'app.db')
        core.save_settings({'paths': {'bettergi': str(home / 'bgi'), 'onedragon': str(home / 'od')},
                            'notify': {'channels': {'toast': {'enabled': False}}}})
        for obj, name, value in ((goals, 'queue_sync', lambda *a, **k: None),
                                 (notify, 'event', lambda *a, **k: None),
                                 (mihoyo, '_collect_icons', lambda *a: None)):
            p = mock.patch.object(obj, name, value)
            p.start()
            self.addCleanup(p.stop)
        planner._CTX.clear()
        inventory._CACHE.clear()
        runner.STATE.clear()
        runner.STOP.clear()

    def goal(self, gid='g1', game='zzz', **extra):
        g = {'id': gid, 'character_id': '1', 'name': gid, 'game': game, 'enabled': True, 'position': 1,
             'current': {'level': 60, 'weapon': 60, 'special': 10},
             'target': {'level': 60, 'weapon': 60, 'special': 12},
             'materials': [], 'allowance': {}, 'category_order': ['level', 'talents', 'weapon'],
             'paused': [], 'calc_at': '2026-10-20T00:00:00+08:00'}
        g.update(extra)
        core.save_goal(g)
        return g

    def chip(self):
        data = materials.dataset('zzz')['materials']
        high = next((k, v) for k, v in data.items() if v.get('kind') == 'chip' and v.get('tier') == 2)
        same = sorted(((k, v) for k, v in data.items() if v.get('kind') == 'chip' and v.get('group') == high[1]['group']),
                      key=lambda pair: pair[1]['tier'])
        return same

    def mat(self, entry, need, owned):
        mid, meta = entry
        return {'id': mid, 'name': meta['name'], 'need': need, 'owned': owned,
                'remaining': None if owned is None else max(0, need - owned),
                'category': 'talents', 'categories': ['talents']}

    def calculate(self, g, raw):
        async def request(*a, **k):
            self.request_body = k['body']
            return raw
        fake = types.SimpleNamespace(_request_upgrade_guide=request)
        with mock.patch.object(mihoyo, 'accounts', return_value={'zzz': {'uid': '10000002'}}), \
                mock.patch.object(mihoyo, 'client', return_value=fake):
            return mihoyo.calculate(g)

    def raw(self, row=None):
        return {'avatar_consume': [], 'weapon_consume': [], 'skill_consume': [] if row is None else [row],
                'user_owns_materials': {}}

    def result(self, game='genshin', **extra):
        r = {'game': game, 'status': 'FAILED', 'phase': 'goal', 'goal_id': None,
             'completed': None, 'errors': [], 'notes': []}
        r.update(extra)
        return r

    def item(self, game='genshin'):
        return {'key': 'g1:mat:1', 'goal_id': 'g1', 'goal': 'Test', 'label': 'Test stage',
                'unit': 'claim20' if game == 'genshin' else 'card', 'unit_label': 'units',
                'upper': 5, 'expected': 1, 'names': 'Test material', 'route': {'kind': 'domain', 'name': 'Test stage'}}

    def test_control_num_quantity(self):
        self.assertEqual(self.calculate(self.goal(), self.raw({'id': 1, 'name': 'Test', 'num': 45}))[0]['need'], 45)

    def test_calc_official_cnt_quantity(self):
        rows = self.calculate(self.goal(), self.raw({'id': 1, 'name': 'Test', 'cnt': 45}))
        self.assertEqual(rows[0]['need'], 45, 'official cnt=45 was silently decoded as zero')

    def test_calc_missing_quantity_rejected(self):
        with self.assertRaises(ValueError, msg='a missing quantity must not count as zero'):
            self.calculate(self.goal(), self.raw({'id': 1, 'name': 'Test'}))

    def test_calc_unknown_character_level_not_assumed_one(self):
        g = self.goal(current={'weapon': 60}, weapon_id='1')
        with self.assertRaises(ValueError, msg='unknown current level must block calculation rather than assume level 1'):
            self.calculate(g, self.raw())

    def test_series_zero_need_tier_stock_is_available(self):
        tiers = self.chip()
        rows = [self.mat(tiers[0], 0, 27), self.mat(tiers[2], 3, 0)]
        found = materials.items_for_goal(self.goal(materials=rows), {})
        self.assertEqual(found[0]['units'], 0, '27 low-tier units fully cover 3 high-tier units')

    def test_shared_stock_allocated_once_across_goals(self):
        row = self.mat(self.chip()[2], 10, 10)
        self.goal('first', materials=[row], position=1)
        self.goal('second', materials=[row], position=2)
        p = planner.plan('zzz')
        self.assertIsNotNone(p['item'], 'two goals need 20 in total but share a stock of only 10')

    def test_sync_does_not_undo_cancel(self):
        g = self.goal()
        def observed(_):
            goals.update(g['id'], {'enabled': False})
            return {'current': {'level': 60}}
        with mock.patch.object(mihoyo, 'observe', side_effect=observed), mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'])
        self.assertFalse(core.goal(g['id'])['enabled'], 'late sync resurrected a canceled goal')

    def test_sync_does_not_undo_target_edit(self):
        g = self.goal()
        def observed(_):
            goals.update(g['id'], {'target': {'special': 11}})
            return {'current': {'special': 10}}
        with mock.patch.object(mihoyo, 'observe', side_effect=observed), mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'])
        self.assertEqual(core.goal(g['id'])['target']['special'], 11)

    def test_sync_does_not_recreate_deleted_goal(self):
        g = self.goal()
        def observed(_):
            goals.remove(g['id'])
            return {'current': {'level': 60}}
        with mock.patch.object(mihoyo, 'observe', side_effect=observed), mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'])
        self.assertIsNone(core.goal(g['id']), 'late sync reinserted a deleted record')

    def test_target_edit_invalidates_old_material_plan(self):
        row = self.mat(self.chip()[2], 10, 0)
        g = self.goal(materials=[row])
        goals.update(g['id'], {'target': {'special': 10}})
        self.assertIsNone(planner.plan('zzz')['item'], 'old material plan still runs after target is lowered to current')

    def test_sync_keeps_user_target_below_current(self):
        g = self.goal(current={'level': 60}, target={'level': 50})
        with mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'], observe=False)
        self.assertEqual(core.goal(g['id'])['target']['level'], 50, 'a sync should not silently rewrite a saved target')

    def account_setup(self):
        old = {'uid': '10000002', 'server': 'prod_gf_cn'}
        new = {'uid': '10000003', 'server': 'prod_gf_cn'}
        core.save_secret('mihoyo', {'accounts': {'zzz': old}, 'candidates': {'zzz': [old, new]}})
        return old, new

    def test_account_switch_does_not_reuse_old_stamina(self):
        _, new = self.account_setup()
        core.add_sample('zzz', 180, 240, 'Test A')
        mihoyo.select_account('zzz', new['uid'])
        self.assertIsNone(planner.estimate('zzz'), 'account B inherited account A battery')

    def test_account_switch_does_not_reuse_old_equipment_cap(self):
        _, new = self.account_setup()
        core.save_settings({'planning': {'disc': {'enabled': True, 'cap': 10, 'mission': 'Test stage'}}})
        mihoyo.select_account('zzz', new['uid'])
        self.assertIsNotNone(planner.equipment('zzz').get('why'), 'old-account equipment authorization is executable for B')

    def test_goal_sync_rejects_old_account_reply(self):
        _, new = self.account_setup()
        g = self.goal(current={'level': 10})
        def observed(_):
            mihoyo.select_account('zzz', new['uid'])
            return {'current': {'level': 59}}
        with mock.patch.object(mihoyo, 'observe', side_effect=observed), mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'])
        self.assertEqual(core.goal(g['id'])['current']['level'], 10, 'old-account observation was committed after role switch')

    def test_preparation_failure_never_credits_historical_log(self):
        tool = self.home / 'dummy.exe'
        tool.write_bytes(b'not executable')
        old_log = self.home / 'old.log'
        old_log.write_text('使用 "原粹树脂", 数量: 20\n' + tools_terminal() + '\n', encoding='utf-8')
        item = self.item()
        p = {'item': item, 'phase': 'goal', 'reason': 'Test'}
        from server import tools, scanners
        with mock.patch.object(mihoyo, 'refresh_notes'), mock.patch.object(planner, 'plan', return_value=p), \
                mock.patch.object(tools, 'game_exe', return_value=tool), mock.patch.object(tools, 'tool_exe', return_value=tool), \
                mock.patch.object(tools, 'running', return_value=False), mock.patch.object(tools, 'kill_path'), \
                mock.patch.object(tools, 'bgi_prepare', side_effect=ValueError('configuration failed')), \
                mock.patch.object(tools, 'log_files', return_value=[old_log]), mock.patch.object(tools, 'restore_all', return_value=[]), \
                mock.patch.object(tools, 'launch_game', side_effect=AssertionError('must not launch')), \
                mock.patch.object(scanners, 'due', return_value=False), mock.patch.object(runner.time, 'sleep'):
            r = runner._run_game('test-run', 'genshin')
        self.assertNotEqual(r['status'], 'SUCCESS', f'preparation failed, but old logs credited completed={r["completed"]}')

    def test_restore_failure_cannot_be_success(self):
        r = runner._receipt(self.result(errors=['configuration restore failed']), 'genshin', None, tools_terminal(), None, False)
        self.assertNotEqual(r['status'], 'SUCCESS', 'restoration failure was suppressed by terminal marker')

    def test_unknown_zzz_completion_cannot_be_success(self):
        text = '指令[ 一条龙 ] 执行成功\n指令[ 体力刷本 ] 执行成功\n'
        r = runner._receipt(self.result('zzz'), 'zzz', self.item('zzz'), text, {'completed': None, 'reason': 'missing rows'}, False)
        self.assertNotEqual(r['status'], 'SUCCESS', 'missing per-plan evidence still yields a green successful run')

    def test_zzz_failure_after_success_is_final_failure(self):
        from server import tools
        parsed = tools.parse_zzz('指令[ 一条龙 ] 执行成功\n指令[ 一条龙 ] 执行失败\n')
        self.assertEqual(parsed['one_dragon'], 'failed', 'any earlier success overrides a later failure')

    def test_equipment_does_not_silently_skip_queue_head(self):
        core.save_settings({'planning': {'disc': {'enabled': True, 'cap': 10}}})
        rows = [{'goal_id': 'head', 'goal': 'Head', 'stage': None, 'set': 'Unknown', 'done': False,
                 'why': 'missing stage', 'owned_only': False},
                {'goal_id': 'tail', 'goal': 'Tail', 'stage': 'Known stage', 'set': 'Known', 'done': False,
                 'why': None, 'owned_only': False}]
        with mock.patch.object(planner, 'gear_queue', return_value=rows):
            eq = planner.equipment('zzz')
        self.assertNotEqual(eq['goal_id'], 'tail', 'unresolved head is silently bypassed')

    def test_forecast_preserves_fractional_recovery(self):
        at = datetime(2026, 10, 20, 0, 7, tzinfo=core.CN)
        core.add_sample('genshin', 0, 200, 'Test', '2026-10-20T00:01:00+08:00')
        core.save_settings({'schedule': {'times': ['00:09'], 'games': ['genshin']}})
        with mock.patch.object(core, 'now', return_value=at):
            first = planner.forecast(1)['rows'][0]
            expected = planner.estimate('genshin', core.parse(first['at']))['value']
        self.assertEqual(first['stamina'], expected, 'forecast loses recovery remainder between sample, now and slot')

    def test_forecast_deduplicates_schedule_times(self):
        core.save_settings({'schedule': {'times': ['05:00', '05:00'], 'games': ['zzz']}})
        rows = planner.forecast(1)['rows']
        self.assertEqual(len(rows), len({(r['game'], r['at']) for r in rows}), 'forecast counts duplicate slots twice')

    def test_schedule_enabled_without_times_rejected(self):
        with self.assertRaises(ValueError):
            core.save_settings({'schedule': {'enabled': True, 'times': []}})

    def test_schedule_enabled_without_games_rejected(self):
        with self.assertRaises(ValueError):
            core.save_settings({'schedule': {'enabled': True, 'games': []}})

    def test_boss_yield_zero_rejected(self):
        with self.assertRaises(ValueError, msg='zero yield will divide by zero when a boss material is planned'):
            core.save_settings({'planning': {'genshin_boss_yield': 0}})

    def test_negative_coffee_rejected(self):
        with self.assertRaises(ValueError, msg='negative coffee creates negative physical stamina in forecasts'):
            core.save_settings({'planning': {'zzz_coffee_forecast': -80}})

    def test_artifact_reward_units_are_not_battle_count(self):
        g = self.goal(game='genshin')
        item = self.item()
        item['upper'] = 2
        r = self.result(phase='equipment', goal_id=g['id'])
        runner._receipt(r, 'genshin', item, '使用 "原粹树脂", 数量: 40\n' + tools_terminal(), None, False)
        self.assertEqual(r['completed'], 2, 'the cumulative allowance must retain 20-resin reward units')
        self.assertEqual(core.get('equip_used:genshin'), 2)
        self.assertEqual(core.goal(g['id'])['gear_runs'], 1, 'one battle with a 40-resin claim is displayed as two runs')

    def test_inventory_cache_invalidates_same_second_goal_edit(self):
        at = datetime(2026, 10, 20, 1, 0, tzinfo=core.CN)
        with mock.patch.object(core, 'now', return_value=at):
            g = self.goal(gear=full_gear(), gear_target={'farm': True, 'score': 0})
            pieces = copy.deepcopy(g['gear']['discs'])
            for p in pieces:
                p.update(location=None, lock=False)
            inventory.save('zzz', pieces, 'Test')
            self.assertTrue(inventory.arrange('zzz')['goals'][g['id']]['done'])
            goals.update(g['id'], {'gear_target': {'farm': True, 'score': 100}})
            cached = inventory.arrange('zzz')['goals'][g['id']]['done']
            inventory._CACHE.clear()
            fresh = inventory.arrange('zzz')['goals'][g['id']]['done']
        self.assertEqual(cached, fresh, 'same-second target edit leaves a stale inventory completion cache')

    def test_inventory_never_borrows_equipped_duplicate_from_other_character(self):
        g = self.goal(gear=full_gear())
        p = copy.deepcopy(g['gear']['discs'][0])
        p.update(uid='foreign', location='AnotherCharacter', lock=False)
        self.assertFalse(inventory.available_to(g, p), 'matching stats do not make another character\'s equipped piece available')

    def test_assets_truncated_magic_is_not_cached_as_image(self):
        key = 'zzz/character/1'
        core.put('asset_sources', {key: 'https://act-webstatic.mihoyo.com/test.png'})
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = 'https://act-webstatic.mihoyo.com/test.png'
        response.headers.get_content_type.return_value = 'image/png'
        response.read.return_value = b'\x89PNG'
        with mock.patch.object(assets.urllib.request, 'urlopen', return_value=response):
            try:
                assets._download(key)
            except ValueError:
                pass
        self.assertIsNone(assets.file(key), 'a four-byte non-decodable image is cached permanently')

    def test_disabling_notification_channel_stops_queued_retry(self):
        core.save_settings({'notify': {'channels': {'toast': {'enabled': True}}}})
        # event() is muted globally for other tests; use a synthetic persisted outbox row here.
        with core.db() as con:
            con.execute('INSERT INTO outbox(id,created,payload,attempts,next_at) VALUES (?,?,?,0,?)',
                        ('test', core.stamp(), json.dumps({'channel': 'toast', 'title': 'Test', 'text': 'Test'}), core.stamp()))
        core.save_settings({'notify': {'channels': {'toast': {'enabled': False}}}})
        with mock.patch.object(notify, 'send') as send:
            notify.drain()
        send.assert_not_called()

    def test_failed_settings_request_does_not_partially_enable_schedule(self):
        from server import scheduler
        with mock.patch.object(scheduler, 'set_autostart', side_effect=ValueError('permission denied')):
            with self.assertRaises(ValueError):
                web.Handler.route(None, '/api/settings', {'settings': {'schedule': {'enabled': True, 'autostart': True}}})
        self.assertFalse(core.settings()['schedule']['enabled'], 'request failed but the real schedule has already been enabled')

    def test_failed_settings_request_does_not_commit_new_secret(self):
        with self.assertRaises(ValueError):
            web.Handler.route(None, '/api/settings', {'settings': {'schedule': {'times': ['invalid']}},
                                                    'secrets': {'password': 'synthetic-test-value'}})
        self.assertFalse(core.secrets_store().get('password'), 'an invalid settings request still stored its new secret')

    def test_control_rotated_log_is_read(self):
        from server import tools
        log = self.home / 'test.log'
        log.write_text('Old contents' * 200, encoding='utf-8')
        with mock.patch.object(tools, 'log_files', return_value=[log]):
            baseline = tools.log_baseline('genshin')
            log.write_text(tools_terminal(), encoding='utf-8')
            self.assertIn(tools_terminal(), tools.read_new('genshin', baseline))

    def test_control_wengine_level_zero_valid(self):
        self.assertEqual(goals._levels('zzz', {'weapon': 0}), {'weapon': 0})

    def test_control_unknown_stamina_remains_unknown(self):
        self.assertIsNone(planner.estimate('zzz'))

    def test_control_disabled_goal_never_planned(self):
        self.goal(enabled=False, materials=[self.mat(self.chip()[2], 10, 0)])
        self.assertIsNone(planner.plan('zzz')['item'])


def tools_terminal():
    from server import tools
    return tools.BGI_TERMINAL


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.cases = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.cases.append({'test': test._testMethodName, 'status': 'pass'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.cases.append({'test': test._testMethodName, 'status': 'failure', 'message': str(err[1])})

    def addError(self, test, err):
        super().addError(test, err)
        self.cases.append({'test': test._testMethodName, 'status': 'error', 'message': str(err[1])})


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LogicAudit))
    (HOME.parent / 'repro-results.json').write_text(json.dumps(result.cases, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.exit(not result.wasSuccessful())
