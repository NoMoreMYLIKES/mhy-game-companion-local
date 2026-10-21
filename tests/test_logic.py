"""Business rules found broken by the logic audit of 2026-10-20 (audit/2026-10-20/REPORT.zh-CN.md, B01–B26),
and the ones found broken since.

Each audit test names the item it guards. Official calls, processes and notifications are stubbed; every
test runs in its own runtime folder.
"""
import copy
from datetime import datetime
import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'tests'))


class LogicTest(unittest.TestCase):
    def setUp(self):
        from server import core, goals, inventory, mihoyo, notify, planner, runner
        self.home = Path(tempfile.mkdtemp(prefix='gcl_logic_'))
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        for obj, name, value in ((core, 'DATA', self.home),
                                 (goals, 'queue_sync', lambda *a, **k: None),
                                 (notify, 'event', lambda *a, **k: None),
                                 (mihoyo, '_collect_icons', lambda *a: None)):
            patcher = mock.patch.object(obj, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        core.save_settings({'paths': {'bettergi': str(self.home / 'bgi'), 'onedragon': str(self.home / 'od')},
                            'notify': {'channels': {'toast': {'enabled': False}}}})
        planner._CTX.clear()
        inventory._CACHE.clear()
        runner.STATE.clear()
        runner.STOP.clear()

    # ------------------------------------------------ helpers
    def goal(self, gid='g1', game='zzz', **extra):
        from server import core
        g = {'id': gid, 'character_id': '1', 'name': gid, 'game': game, 'enabled': True, 'position': 1,
             'current': {'level': 60, 'weapon': 60, 'special': 10},
             'target': {'level': 60, 'weapon': 60, 'special': 12},
             'materials': [], 'allowance': {}, 'category_order': ['level', 'talents', 'weapon'],
             'paused': [], 'calc_at': '2026-10-20T00:00:00+08:00'}
        g.update(extra)
        core.save_goal(g)
        return g

    def chip(self):
        """A ZZZ skill chip series, lowest tier first."""
        from server import materials
        data = materials.dataset('zzz')['materials']
        high = next((k, v) for k, v in data.items() if v.get('kind') == 'chip' and v.get('tier') == 2)
        return sorted(((k, v) for k, v in data.items() if v.get('kind') == 'chip' and v.get('group') == high[1]['group']),
                      key=lambda pair: pair[1]['tier'])

    def mat(self, entry, need, owned, remaining='auto'):
        mid, info = entry
        if remaining == 'auto':
            remaining = None if owned is None else max(0, need - owned)
        return {'id': mid, 'name': info['name'], 'need': need, 'owned': owned, 'remaining': remaining,
                'category': 'talents', 'categories': ['talents']}

    def calculate(self, g, raw):
        from server import mihoyo
        async def request(*a, **k):
            self.body = k['body']
            return raw
        fake = types.SimpleNamespace(_request_upgrade_guide=request)
        with mock.patch.object(mihoyo, 'accounts', return_value={'zzz': {'uid': '10000002'}}), \
                mock.patch.object(mihoyo, 'client', return_value=fake):
            return mihoyo.calculate(g)

    def raw(self, *rows, owns=None):
        return {'avatar_consume': [], 'weapon_consume': [], 'skill_consume': list(rows), 'user_owns_materials': owns or {}}

    def result(self, game='genshin', **extra):
        r = {'game': game, 'status': 'FAILED', 'phase': 'goal', 'goal_id': None,
             'completed': None, 'errors': [], 'notes': []}
        r.update(extra)
        return r

    def item(self, game='genshin'):
        return {'key': 'g1:mat:1', 'goal_id': 'g1', 'goal': 'Test', 'label': 'Test stage',
                'unit': 'claim20' if game == 'genshin' else 'card', 'unit_label': 'units',
                'upper': 5, 'expected': 1, 'names': 'Test material', 'route': {'kind': 'domain', 'name': 'Test stage'}}

    def roles(self):
        from server import core
        old = {'uid': '10000002', 'server': 'prod_gf_cn'}
        new = {'uid': '10000003', 'server': 'prod_gf_cn'}
        core.save_secret('mihoyo', {'accounts': {'zzz': old}, 'candidates': {'zzz': [old, new]}})
        return old, new

    # ------------------------------------------------ B02, B07: what the calculator is asked and answers
    def test_b02_calculator_quantity_fields(self):
        row = {'id': 1, 'name': 'Test'}
        self.assertEqual(self.calculate(self.goal(), self.raw({**row, 'num': 45}))[0]['need'], 45)
        self.assertEqual(self.calculate(self.goal(), self.raw({**row, 'cnt': 45}))[0]['need'], 45)
        for bad in ({}, {'num': -1}, {'num': 'many'}, {'num': 4, 'cnt': 5}):
            with self.assertRaises(ValueError, msg=bad):  # never read as "nothing needed"
                self.calculate(self.goal(), self.raw({**row, **bad}))

    def test_b07_unknown_current_level_is_never_level_one(self):
        g = self.goal(current={'weapon': 60}, weapon_id='1')
        with self.assertRaises(ValueError):
            self.calculate(g, self.raw())
        g = self.goal(current={'level': 60, 'weapon': 60}, target={'level': 60, 'special': 12})
        with self.assertRaises(ValueError):  # a targeted skill whose level was never read
            self.calculate(g, self.raw())
        self.calculate(self.goal(current={'level': 60, 'weapon': 0}, weapon_id='1', target={'weapon': 10}), self.raw())
        self.assertEqual(self.body['weapon_info']['weapon_init_level'], 0)  # W-Engine level 0 is a real level

    def test_b22_target_below_current_is_kept_and_asks_for_nothing(self):
        from server import core, goals, mihoyo
        g = self.goal(current={'level': 60, 'special': 10}, target={'level': 50, 'special': 12})
        self.calculate(g, self.raw())
        self.assertEqual((self.body['avatar_level'], self.body['avatar_current_level']), (60, 60))
        with mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'], observe=False)
        self.assertEqual(core.goal(g['id'])['target']['level'], 50)

    def test_b04_series_stock_of_unneeded_tiers_is_kept(self):
        from server import materials
        tiers = self.chip()
        found = materials.items_for_goal(self.goal(materials=[self.mat(tiers[0], 0, 27), self.mat(tiers[2], 3, 0)]), {})
        self.assertEqual(found[0]['units'], 0)  # 27 low-tier units cover 3 high-tier ones
        rows = self.calculate(self.goal(), self.raw({'id': int(tiers[2][0]), 'name': 'High', 'num': 3},
                                                    owns={tiers[2][0]: 0, tiers[0][0]: 27}))
        low = next(r for r in rows if r['id'] == tiers[0][0])
        self.assertEqual((low['need'], low['owned']), (0, 27))  # the answer's stock of the series' other tier

    # ------------------------------------------------ B03: one stock, shared in goal order
    def test_b03_stock_serves_goals_once_in_order(self):
        from server import planner
        row = self.mat(self.chip()[2], 10, 10)
        self.goal('first', materials=[row], position=1)
        self.goal('second', materials=[row], position=2)
        p = planner.plan('zzz')
        self.assertEqual(p['item']['goal_id'], 'second')
        items = planner.items_by_goal('zzz')
        self.assertTrue(items['first'][0]['done'])
        self.assertGreater(items['second'][0]['units'], 0)

    def test_b03_genshin_stock_known_only_as_covered_is_unknown_for_the_next_goal(self):
        from server import materials, planner
        book = next(k for k, v in materials.dataset('genshin')['materials'].items() if materials.genshin_family(k))
        row = {'id': book, 'name': 'Book', 'need': 9, 'owned': None, 'remaining': 0, 'category': 'talents',
               'categories': ['talents']}
        self.goal('first', game='genshin', materials=[row], position=1)
        self.goal('second', game='genshin', materials=[row], position=2)
        second = planner.items_by_goal('genshin')['second'][0]
        self.assertIsNone(second['units'])  # each alone is covered; both together is not known
        self.assertEqual(second['note'], __import__('server.i18n', fromlist=['tr']).tr('note_shared_unknown'))
        lacking = {**row, 'remaining': 4}  # each lacks 4 of 9: the stock is exactly 5, and the first goal takes it
        self.goal('first', game='genshin', materials=[lacking], position=1)
        self.goal('second', game='genshin', materials=[lacking], position=2)
        items = planner.items_by_goal('genshin')
        self.assertEqual([m['remaining'] for m in items['first'][0]['materials']], [4])
        self.assertEqual([m['remaining'] for m in items['second'][0]['materials']], [9])

    def test_b03_disabled_goal_holds_no_stock(self):
        from server import planner
        row = self.mat(self.chip()[2], 10, 10)
        self.goal('first', materials=[row], position=1, enabled=False)
        self.goal('second', materials=[row], position=2)
        self.assertIsNone(planner.plan('zzz')['item'])

    # ------------------------------------------------ B05, B06, B08: a sync merges into the record as it is then
    def test_b05_late_sync_keeps_cancel_edit_and_delete(self):
        from server import core, goals, mihoyo
        g = self.goal()
        cases = {'cancel': lambda: goals.update(g['id'], {'enabled': False}),
                 'edit': lambda: goals.update(g['id'], {'target': {'special': 11}}),
                 'delete': lambda: goals.remove(g['id'])}
        for name, action in cases.items():
            self.goal()
            with mock.patch.object(mihoyo, 'observe', side_effect=lambda *a, **k: (action(), {'current': {'level': 60}})[1]), \
                    mock.patch.object(mihoyo, 'calculate', return_value=[]):
                result = goals.sync(g['id'])
            stored = core.goal(g['id'])
            if name == 'cancel':
                self.assertFalse(stored['enabled'])
            elif name == 'edit':
                self.assertEqual(stored['target']['special'], 11)
                self.assertEqual(stored['materials'], [])  # the answer for the old target is dropped
                self.assertTrue(stored['calc_stale'])
            else:
                self.assertIsNone(stored)
                self.assertIsNone(result)

    def test_b05_user_level_edit_during_sync_wins_over_the_reading(self):
        from server import core, goals, mihoyo
        g = self.goal(current={'level': 50, 'special': 10})
        def read(*a, **k):
            goals.update(g['id'], {'current': {'level': 55}})
            return {'current': {'level': 52, 'special': 11}}
        with mock.patch.object(mihoyo, 'observe', side_effect=read), mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'])
        self.assertEqual(core.goal(g['id'])['current']['level'], 55)

    def test_b06_changed_target_stops_the_old_plan_until_recalculated(self):
        from server import core, goals, mihoyo, planner
        g = self.goal(materials=[self.mat(self.chip()[2], 10, 0)])
        self.assertIsNotNone(planner.plan('zzz')['item'])
        goals.update(g['id'], {'target': {'special': 10}})
        p = planner.plan('zzz')
        self.assertIsNone(p['item'])
        self.assertTrue(any(w['why'] == __import__('server.i18n', fromlist=['tr']).tr('calc_stale') for w in p['waiting']))
        goals.update(g['id'], {'name': 'renamed'})  # not a calculation input: nothing more to wait for
        with mock.patch.object(mihoyo, 'calculate', return_value=[self.mat(self.chip()[2], 3, 0)]):
            goals.sync(g['id'], observe=False)
        self.assertFalse(core.goal(g['id'])['calc_stale'])
        self.assertIsNotNone(planner.plan('zzz')['item'])

    def test_b08_reply_for_a_role_no_longer_selected_is_dropped(self):
        from server import core, goals, mihoyo
        _, new = self.roles()
        g = self.goal(current={'level': 10}, account=core.account_key('zzz'))
        def read(*a, **k):
            mihoyo.select_account('zzz', new['uid'])
            return {'current': {'level': 59}}
        with mock.patch.object(mihoyo, 'observe', side_effect=read), mock.patch.object(mihoyo, 'calculate', return_value=[]):
            goals.sync(g['id'])
        self.assertEqual(core.goal(g['id'])['current']['level'], 10)

    def test_b08_other_roles_data_is_not_planned_and_is_synced_again(self):
        from server import core, goals, mihoyo, planner
        old, new = self.roles()
        g = self.goal(materials=[self.mat(self.chip()[2], 10, 0)], account=core.account_key('zzz'),
                      sync_at=core.stamp())
        self.assertIsNotNone(planner.plan('zzz')['item'])
        mihoyo.select_account('zzz', new['uid'])
        self.assertIsNone(planner.plan('zzz')['item'])
        with mock.patch.object(core, 'now', return_value=core.now() + __import__('datetime').timedelta(minutes=20)):
            self.assertEqual([x['id'] for x in goals.due_for_sync(12)], [g['id']])
        with mock.patch.object(mihoyo, 'calculate', return_value=[]):  # its levels are the old role's
            synced = goals.sync(g['id'], observe=False)
        self.assertTrue(synced['calc_error'])

    def test_b08_stamina_belongs_to_its_role(self):
        from server import core, mihoyo, planner
        old, new = self.roles()
        core.add_sample('zzz', 180, 240, 'source_widget')
        self.assertEqual(planner.estimate('zzz')['value'], 180)
        mihoyo.select_account('zzz', new['uid'])
        self.assertIsNone(planner.estimate('zzz'))
        mihoyo.select_account('zzz', old['uid'])
        self.assertEqual(planner.estimate('zzz')['value'], 180)

    def test_b08_allowance_spends_only_the_role_it_was_granted_for(self):
        from server import core, mihoyo, planner, web
        old, new = self.roles()
        core.save_settings({'planning': {'disc': {'enabled': True, 'cap': 10, 'mission': 'Stage'}}})
        core.put('equip_used:zzz', 4)
        self.assertIsNone(planner.equipment('zzz').get('why'))
        mihoyo.select_account('zzz', new['uid'])
        eq = planner.equipment('zzz')
        self.assertFalse(eq['role_ok'])
        self.assertTrue(eq['why'])
        core.save_settings({'ui': {'lang': 'en'}})  # an unrelated save grants nothing
        self.assertFalse(planner.equipment('zzz')['role_ok'])
        core.save_settings({'planning': {'disc': {'account': None}}})  # nor can a request name the role
        self.assertFalse(planner.equipment('zzz')['role_ok'])
        web.Handler.route(None, '/api/equip/grant', {'game': 'zzz'})
        eq = planner.equipment('zzz')
        self.assertEqual((eq['role_ok'], eq['used'], eq.get('why')), (True, 0, None))  # a new role starts unused

    # ------------------------------------------------ B09–B12, B26: receipts
    def test_b09_failed_preparation_never_counts_old_logs(self):
        from server import mihoyo, planner, runner, scanners, tools
        tool = self.home / 'dummy.exe'
        tool.write_bytes(b'not executable')
        old_log = self.home / 'old.log'
        old_log.write_text('使用 "原粹树脂", 数量: 20\n' + tools.BGI_TERMINAL + '\n', encoding='utf-8')
        p = {'item': self.item(), 'phase': 'goal', 'reason': 'Test'}
        with mock.patch.object(mihoyo, 'refresh_notes'), mock.patch.object(planner, 'plan', return_value=p), \
                mock.patch.object(tools, 'game_exe', return_value=tool), mock.patch.object(tools, 'tool_exe', return_value=tool), \
                mock.patch.object(tools, 'running', return_value=False), mock.patch.object(tools, 'kill_path'), \
                mock.patch.object(tools, 'bgi_prepare', side_effect=ValueError('configuration failed')), \
                mock.patch.object(tools, 'log_files', return_value=[old_log]), mock.patch.object(tools, 'restore_all', return_value=[]), \
                mock.patch.object(tools, 'launch_game', side_effect=AssertionError('must not launch')), \
                mock.patch.object(scanners, 'due', return_value=False), mock.patch.object(runner.time, 'sleep'):
            r = runner._run_game('test-run', 'genshin')
        self.assertEqual((r['status'], r['completed']), ('FAILED', 0))

    def test_b10_b11_finished_run_is_not_success_with_a_restore_error_or_unknown_amount(self):
        from server import runner, tools
        r = runner._receipt(self.result(errors=['configuration restore failed']), 'genshin', None, tools.BGI_TERMINAL, None, False)
        self.assertEqual(r['status'], 'PARTIAL')
        text = '指令[ 一条龙 ] 执行成功\n指令[ 体力刷本 ] 执行成功\n'
        r = runner._receipt(self.result('zzz'), 'zzz', self.item('zzz'), text, {'completed': None, 'reason': 'missing'}, False)
        self.assertEqual(r['status'], 'PARTIAL')
        r = runner._receipt(self.result('zzz'), 'zzz', self.item('zzz'), text, {'completed': 2, 'battles': 1}, False)
        self.assertEqual(r['status'], 'SUCCESS')

    def test_b12_the_last_onedragon_outcome_counts(self):
        from server import tools
        self.assertEqual(tools.parse_zzz('指令[ 一条龙 ] 执行成功\n指令[ 一条龙 ] 执行失败\n')['one_dragon'], 'failed')
        self.assertEqual(tools.parse_zzz('指令[ 一条龙 ] 执行失败\n指令[ 一条龙 ] 执行成功\n')['one_dragon'], 'success')
        self.assertIsNone(tools.parse_zzz('no outcome')['one_dragon'])

    def test_b26_a_40_resin_claim_is_one_battle_and_two_rewards(self):
        from server import core, runner, tools
        g = self.goal(game='genshin')
        item = dict(self.item(), upper=2)
        r = self.result(phase='equipment', goal_id=g['id'])
        runner._receipt(r, 'genshin', item, '使用 "原粹树脂", 数量: 40\n' + tools.BGI_TERMINAL, None, False)
        self.assertEqual((r['completed'], core.get('equip_used:genshin'), core.goal(g['id'])['gear_runs']), (2, 2, 1))

    # ------------------------------------------------ B13: the head of the equipment queue
    def test_b13_unresolved_head_is_not_skipped(self):
        from server import core, planner
        core.save_settings({'planning': {'disc': {'enabled': True, 'cap': 10}}})
        rows = [{'goal_id': 'head', 'goal': 'Head', 'stage': None, 'set': 'Unknown', 'done': False, 'why': 'missing stage',
                 'owned_only': False},
                {'goal_id': 'tail', 'goal': 'Tail', 'stage': 'Known stage', 'set': 'Known', 'done': False, 'why': None,
                 'owned_only': False}]
        with mock.patch.object(planner, 'gear_queue', return_value=rows):
            eq = planner.equipment('zzz')
        self.assertIsNone(eq['goal_id'])
        self.assertIn('Head', eq['why'])

    # ------------------------------------------------ B01: the reason names the equipment block
    def test_b01_reason_says_why_a_requested_character_is_not_farmed(self):
        from server import planner
        rows = [{'goal_id': 'g', 'goal': 'G', 'stage': 'Stage', 'set': 'S', 'done': False, 'why': None, 'owned_only': False}]
        with mock.patch.object(planner, 'gear_queue', return_value=rows):
            p = planner.plan('zzz')
        self.assertIn(p['equipment']['why'], p['reason'])  # off by default, and a character asked for it

    # ------------------------------------------------ B14, B15: forecast
    def test_b14_forecast_keeps_the_recovery_remainder(self):
        from server import core, planner
        at = datetime(2026, 10, 20, 0, 7, tzinfo=core.CN)
        core.add_sample('genshin', 0, 200, 'source_widget', '2026-10-20T00:01:00+08:00')
        core.save_settings({'schedule': {'times': ['00:09', '00:17', '00:25'], 'games': ['genshin']}})
        with mock.patch.object(core, 'now', return_value=at):
            rows = planner.forecast(1)['rows']
            for row in rows:
                self.assertEqual(row['stamina'], planner.estimate('genshin', core.parse(row['at']))['value'])

    def test_b14_recovery_waits_at_the_cap_until_spent(self):
        from server import core, planner
        at = datetime(2026, 10, 20, 5, 0, tzinfo=core.CN)
        core.add_sample('genshin', 200, 200, 'source_widget', core.stamp(at))
        core.save_settings({'schedule': {'times': ['06:00', '06:10'], 'games': ['genshin']}})
        self.goal(game='genshin', materials=[], calc_at=None)
        with mock.patch.object(core, 'now', return_value=at), \
                mock.patch.object(planner, 'plan', side_effect=lambda g, slot, stamina, consumed: {
                    'item': {'key': 'k', 'goal': 'G', 'label': 'L', 'unit_label': '', 'upper': 1, 'expected': 1,
                             'goal_id': 'g', 'names': '', 'cost': 20}, 'reason': '', 'phase': 'goal'}):
            rows = planner.forecast(1)['rows']
        self.assertEqual((rows[0]['stamina'], rows[0]['left']), (200, 180))
        self.assertEqual(rows[1]['stamina'], 181)  # 10 minutes after spending: one point, not two

    def test_b15_one_slot_per_time(self):
        from server import core, planner
        core.save_settings({'schedule': {'times': ['05:00', '05:00'], 'games': ['zzz']}})
        self.assertEqual(core.settings()['schedule']['times'], ['05:00'])
        rows = planner.forecast(1)['rows']
        self.assertEqual(len(rows), len({(r['game'], r['at']) for r in rows}))

    # ------------------------------------------------ B16, B21, B25: settings
    def test_b16_b25_settings_that_cannot_work_are_refused(self):
        from server import core
        for patch in ({'schedule': {'enabled': True, 'times': []}}, {'schedule': {'enabled': True, 'games': []}},
                      {'planning': {'genshin_boss_yield': 0}}, {'planning': {'zzz_coffee_forecast': -80}},
                      {'planning': {'disc': {'cap': 1.5}}}, {'sync': {'goals_hours': float('nan')}},
                      {'execution': {'timeout_minutes': True}}, {'schedule': {'catchup_hours': 'four'}}):
            with self.assertRaises(ValueError, msg=patch):
                core.save_settings(patch)
        self.assertFalse(core.settings()['schedule']['enabled'])
        core.save_settings({'schedule': {'enabled': False, 'times': []}})  # a draft while off is fine

    def test_b21_a_refused_request_changes_nothing(self):
        from server import core, scheduler, web
        with mock.patch.object(scheduler, 'set_autostart', side_effect=ValueError('permission denied')):
            with self.assertRaises(ValueError):
                web.Handler.route(None, '/api/settings', {'settings': {'schedule': {'enabled': True, 'autostart': True}}})
        self.assertFalse(core.settings()['schedule']['enabled'])
        with self.assertRaises(ValueError):
            web.Handler.route(None, '/api/settings', {'settings': {'schedule': {'times': ['invalid']}},
                                                     'secrets': {'password': 'synthetic-test-value'}})
        self.assertFalse(core.secrets_store().get('password'))
        with self.assertRaises(ValueError):  # LAN without a password
            web.Handler.route(None, '/api/settings', {'settings': {'server': {'lan': True}}})
        web.Handler.route(None, '/api/settings', {'settings': {'server': {'lan': True}}, 'secrets': {'password': 'p'}})
        self.assertTrue(core.settings()['server']['lan'])
        with mock.patch.object(scheduler, 'set_autostart') as task, \
                mock.patch.object(core, 'save_settings', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                web.save_settings({'schedule': {'autostart': True}}, {})
        self.assertEqual([c.args for c in task.call_args_list], [(True,), (False,)])  # the logon task is put back

    # ------------------------------------------------ B17, B18: owned equipment
    def test_b17_same_second_edit_refreshes_the_arrangement(self):
        from server import core, goals, inventory
        from test_gear import full_gear
        at = datetime(2026, 10, 20, 1, 0, tzinfo=core.CN)
        with mock.patch.object(core, 'now', return_value=at):
            g = self.goal(gear=full_gear(), gear_target={'farm': True, 'score': 0})
            pieces = copy.deepcopy(g['gear']['discs'])
            for p in pieces:
                p.update(location=None, lock=False)
            inventory.save('zzz', pieces, 'Test')
            self.assertTrue(inventory.arrange('zzz')['goals'][g['id']]['done'])
            goals.update(g['id'], {'gear_target': {'farm': True, 'score': 100}})
            self.assertFalse(inventory.arrange('zzz')['goals'][g['id']]['done'])

    def test_b18_an_identical_piece_worn_by_another_character_is_not_available(self):
        from server import inventory
        from test_gear import full_gear
        g = self.goal(gear=full_gear())
        own = [dict(copy.deepcopy(d), location='Me', lock=False) for d in g['gear']['discs']]
        twin = dict(copy.deepcopy(g['gear']['discs'][0]), location='Other', lock=False)
        self.assertEqual(inventory.wearer(g, own + [twin]), 'Me')
        self.assertFalse(inventory.available_to(g, twin, worn_as='Me'))
        self.assertTrue(inventory.available_to(g, own[0], worn_as='Me'))
        self.assertFalse(inventory.available_to(g, twin))  # without knowing its own wearer name: only free pieces

    # ------------------------------------------------ B19, B20
    def test_b19_only_whole_images_are_cached(self):
        from server import assets, core
        k = 'zzz/character/1'
        core.put('asset_sources', {k: 'https://act-webstatic.mihoyo.com/test.png'})
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = 'https://act-webstatic.mihoyo.com/test.png'
        response.headers.get_content_type.return_value = 'image/png'
        response.read.return_value = b'\x89PNG'
        with mock.patch.object(assets.urllib.request, 'urlopen', return_value=response):
            with self.assertRaises(ValueError):
                assets._download(k)
        self.assertIsNone(assets.file(k))
        damaged = assets.root() / 'zzz/character/2.png'  # saved before this check existed
        damaged.parent.mkdir(parents=True, exist_ok=True)
        damaged.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 40)
        self.assertIsNone(assets.file('zzz/character/2'))
        self.assertNotIn('zzz/character/2', assets.cached())
        whole = (b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\x0dIHDR' + b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00'
                 + b'\x1f\x15\xc4\x89' + b'\x00\x00\x00\x00IEND\xaeB`\x82')
        damaged.write_bytes(whole)
        self.assertEqual(assets.file('zzz/character/2'), damaged)

    def test_b20_turning_a_channel_off_stops_its_queued_messages(self):
        from server import core, notify
        core.save_settings({'notify': {'channels': {'toast': {'enabled': True}}}})
        with core.db() as con:
            con.execute('INSERT INTO outbox(id,created,payload,attempts,next_at) VALUES (?,?,?,0,?)',
                        ('test', core.stamp(), json.dumps({'channel': 'toast', 'title': 'Test', 'text': 'Test'}), core.stamp()))
        core.save_settings({'notify': {'channels': {'toast': {'enabled': False}}}})
        with mock.patch.object(notify, 'send') as send:
            notify.drain()
            notify.drain()
        send.assert_not_called()
        row = notify.recent()[0]
        self.assertEqual((row['sent'], row['error']), (False, __import__('server.i18n', fromlist=['tr']).tr('channel_off')))

    # ------------------------------------------------ a weapon that was not read waits alone
    def test_unread_wengine_leaves_only_its_own_part_out(self):
        from server import mihoyo
        g = self.goal(current={'level': 50, 'special': 10}, target={'level': 60, 'special': 12, 'weapon': 60})
        rows = self.calculate(g, {'avatar_consume': [{'id': 1, 'name': 'Test', 'num': 5}], 'skill_consume': [],
                                  'user_owns_materials': {}})
        self.assertEqual(rows[0]['need'], 5)  # the level is calculated
        self.assertNotIn('weapon_info', self.body)
        self.assertEqual(mihoyo.weapon_wait(g), 'wengine_unread')
        g = self.goal(current={'level': 50, 'special': 10, 'weapon': 40}, weapon_id='14149',
                      target={'level': 60, 'special': 12, 'weapon': 60})
        self.calculate(g, self.raw())
        self.assertEqual((self.body['weapon_info']['weapon_init_level'], self.body['weapon_info']['weapon_level']), (40, 60))
        self.assertIsNone(mihoyo.weapon_wait(g))
        with self.assertRaises(ValueError):  # the W-Engine was asked for: an answer without its part is a format change
            self.calculate(g, {'avatar_consume': [], 'skill_consume': [], 'user_owns_materials': {}})
        self.assertIsNone(mihoyo.weapon_wait(self.goal(current={'level': 50}, target={'weapon': 0})))  # asks nothing

    def test_unread_weapon_leaves_genshin_level_and_talents_calculated(self):
        from genshin.client.components.calculator.calculator import Calculator
        from server import mihoyo
        sent = {}

        class Sent(Exception):
            pass

        async def request_calculator(endpoint, data=None, **kwargs):
            sent.update(data['items'][0])
            raise Sent  # only the request is checked
        fake = types.SimpleNamespace(request_calculator=request_calculator)
        fake.calculator = lambda: Calculator(fake)
        g = self.goal(game='genshin', character_id='10000089', current={'level': 80, 'skill': 8},
                      target={'level': 90, 'skill': 9, 'weapon': 90}, talent_groups={'skill': 8932})
        with mock.patch.object(mihoyo, 'accounts', return_value={'genshin': {'uid': '100000001'}}), \
                mock.patch.object(mihoyo, 'client', return_value=fake), self.assertRaises(Sent):
            mihoyo.calculate(g)
        self.assertNotIn('weapon', sent)
        self.assertEqual(sent['skill_list'], [{'id': 8932, 'level_current': 8, 'level_target': 9}])
        self.assertEqual(mihoyo.weapon_wait(g), 'weapon_unread')

    def test_genshin_weapon_without_its_level_is_not_read(self):
        from server import mihoyo
        row = {'id': 10000089, 'level_current': 80, 'skill_list': [], 'weapon': {'id': 11510, 'name': 'Sword'}}

        async def request_calculator(endpoint, data=None, **kwargs):
            return {'list': [row]}
        fake = types.SimpleNamespace(request_calculator=request_calculator)
        goal = {'game': 'genshin', 'character_id': '10000089'}
        with mock.patch.object(mihoyo, 'accounts', return_value={'genshin': {'uid': '100000001'}}), \
                mock.patch.object(mihoyo, 'client', return_value=fake), \
                mock.patch.object(mihoyo, '_ensure_fp', mock.AsyncMock()), \
                mock.patch.object(mihoyo, '_genshin_gear', mock.AsyncMock()):
            seen = mihoyo.observe(goal)
            self.assertEqual((seen['weapon_id'], seen['current'].get('weapon')), (None, None))  # never level 1
            row['weapon']['level_current'] = 70
            seen = mihoyo.observe(goal)
        self.assertEqual((seen['weapon_id'], seen['current']['weapon']), ('11510', 70))

    def test_unread_wengine_never_holds_back_level_and_skills(self):
        """A new goal for an agent without a W-Engine is calculated and farmed for its level and skills; the W-Engine
        waits for a reading, and the goal is not done while it waits."""
        from server import core, goals, mihoyo, notify, planner, web
        from server.i18n import tr
        chip = self.chip()[2]
        g = self.goal(current={}, target={'level': 60, 'special': 12, 'weapon': 60}, calc_at=None)
        reading = {'current': {'level': 60, 'special': 10}, 'weapon_id': None, 'weapon_name': ''}
        answer = {'avatar_consume': [], 'skill_consume': [{'id': int(chip[0]), 'name': chip[1]['name'], 'num': 10}],
                  'user_owns_materials': {chip[0]: 0}}

        async def request(*a, **k):
            self.body = k['body']
            return answer
        fake = types.SimpleNamespace(_request_upgrade_guide=request)
        event = mock.Mock()
        with mock.patch.object(mihoyo, 'observe', side_effect=lambda *a, **k: copy.deepcopy(reading)), \
                mock.patch.object(mihoyo, 'accounts', return_value={'zzz': {'uid': '10000002'}}), \
                mock.patch.object(mihoyo, 'client', return_value=fake), mock.patch.object(notify, 'event', event):
            synced = goals.sync(g['id'])
            self.assertIsNone(synced['calc_error'])
            self.assertEqual(synced['weapon_wait'], 'wengine_unread')
            self.assertNotIn('weapon_info', self.body)
            self.assertEqual(planner.plan('zzz')['item']['goal_id'], g['id'])  # its skill is farmed
            self.assertEqual(web.goal_view(core.goal(g['id']), planner.tool_context(), 0)['weapon_wait'], tr('wengine_unread'))
            answer['user_owns_materials'] = {chip[0]: 10}  # the skill materials are collected, the W-Engine still waits
            goals.sync(g['id'])
            event.assert_not_called()
            reading.update(weapon_id='14149', weapon_name='Test W-Engine')
            reading['current']['weapon'] = 60  # read at its target level: nothing more to farm
            answer['weapon_consume'] = []
            synced = goals.sync(g['id'])
        self.assertIsNone(synced['weapon_wait'])
        self.assertEqual(self.body['weapon_info']['weapon_id'], 14149)
        self.assertEqual([c.args[0] for c in event.call_args_list], ['goal_done'])

    # ------------------------------------------------ what stayed right
    def test_controls(self):
        from server import goals, planner, tools
        self.assertEqual(goals._levels('zzz', {'weapon': 0}), {'weapon': 0})
        self.assertIsNone(planner.estimate('zzz'))
        self.goal(enabled=False, materials=[self.mat(self.chip()[2], 10, 0)])
        self.assertIsNone(planner.plan('zzz')['item'])
        log = self.home / 'test.log'
        log.write_text('Old contents' * 200, encoding='utf-8')
        with mock.patch.object(tools, 'log_files', return_value=[log]):
            baseline = tools.log_baseline('genshin')
            log.write_text(tools.BGI_TERMINAL, encoding='utf-8')
            self.assertIn(tools.BGI_TERMINAL, tools.read_new('genshin', baseline))  # a rotated log is read whole


if __name__ == '__main__':
    unittest.main()
