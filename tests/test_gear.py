"""Drive Disc evaluation: rolls, scores, targets, and the per-character equipment continuation."""
import asyncio
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def prop(pid, value, name=''):
    return {'id': pid, 'name': name, 'value': value, 'number': float(value.rstrip('%')),
            'percent': value.endswith('%'), 'level': None, 'valid': None}


def disc(slot, set_id, main, subs, rarity='S', level=15):
    return {'slot': slot, 'level': level, 'rarity': rarity, 'set_id': set_id, 'set': f'Set {set_id}', 'icon': '',
            'main': prop(*main), 'subs': [prop(*s) for s in subs]}


# Legal discs (no substat repeats the main stat), with S-rank rolls noted per substat.
SUBS = {
    1: [(20103, '9.6%'), (21103, '9.6%'), (12102, '6%'), (23203, '9')],     # 4, 2, 2, 1
    2: [(20103, '9.6%'), (21103, '9.6%'), (12102, '6%'), (23203, '9')],     # flat ATK main
    3: [(20103, '9.6%'), (21103, '9.6%'), (12102, '6%'), (23203, '9')],
    4: [(21103, '14.4%'), (12102, '9%'), (12103, '38'), (23203, '9')],      # 3, 3, 2, 1 under a CRIT Rate main
    5: [(20103, '7.2%'), (21103, '9.6%'), (12103, '38'), (23203, '18')],    # 3, 2, 2, 2 under an ATK% main
    6: [(20103, '7.2%'), (21103, '9.6%'), (12103, '38'), (23203, '18')],
}
MAIN = {1: (11103, '2200'), 2: (12103, '316'), 3: (13103, '184'), 4: (20103, '24%'), 5: (12102, '30%'), 6: (12102, '30%')}
BUILD = {'name': 'Build', 'mine': False, 'set_kind': 1,
         'sets': [{'id': 31000, 'name': 'Set 31000', 'icon': '', 'count': 0}, {'id': 32000, 'name': 'Set 32000', 'icon': '', 'count': 0}],
         'main': {'4': [20103, 21103], '5': [12102], '6': [12102]}, 'subs': [20103, 21103, 12102]}


def full_gear(sets=(31000, 31000, 31000, 31000, 32000, 32000)):
    return {'at': '2026-10-13T08:00:00+08:00', 'base': {'hp': 8000, 'atk': 900, 'def': 600}, 'plan': BUILD,
            'discs': [disc(slot, sets[slot - 1], MAIN[slot], SUBS[slot]) for slot in range(1, 7)]}


class GearTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix='gcl_gear_')
        os.environ['GCL_HOME'] = cls.temp_dir
        from server import core  # an earlier test module may have imported it already: GCL_HOME alone would not reach it
        cls.data = mock.patch.object(core, 'DATA', Path(cls.temp_dir))
        cls.data.start()

    @classmethod
    def tearDownClass(cls):
        cls.data.stop()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_score_counts_rolls_against_the_best_disc(self):
        from server import gear
        goal = {'game': 'zzz', 'gear': full_gear()}
        w, source = gear.weights(goal)
        self.assertEqual(source, 'official')
        self.assertEqual(w[12103], 0.7)  # 19 / (3% of base ATK 900) of an ATK% roll
        self.assertEqual(w[23203], 0.0)
        ev = gear.evaluate(goal)
        # slot 1: 4 + 2 + 2 counted rolls of a best 1 + 1 + 1 + 0.7 + 5 × 1 = 8.7
        # slot 2: flat ATK is the main stat, so the best is 1 + 1 + 1 + 5 = 8
        # slot 4: CRIT Rate main; 3 + 3 + 2 × 0.7 of 1 + 1 + 0.7 + 5 = 7.7
        # slot 5: ATK% main; 3 + 2 + 2 × 0.7 of 7.7
        self.assertEqual([s['score'] for s in ev['slots']], [92.0, 100.0, 92.0, 96.1, 83.1, 83.1])
        self.assertAlmostEqual(ev['score'], 91.05, delta=0.06)

    def test_builds_name_stat_families(self):
        """Miyoushe sent flat ATK (12103) as the slot 5 and 6 pick and as a substat; it means ATK in general."""
        from server import gear
        g = full_gear()
        g['plan'] = {**BUILD, 'main': {'4': [31203], '5': [12103], '6': [12103]}, 'subs': [12103, 31203]}
        goal = {'game': 'zzz', 'gear': g}
        self.assertEqual(gear.build_defaults(goal)['main'], {'4': [31203], '5': [12102], '6': [12102]})
        w, _ = gear.weights(goal)
        self.assertEqual((w[12102], w[12103], w[31203], w[20103]), (1.0, 0.7, 1.0, 0.0))  # flat ATK by base ATK 900
        ev = gear.evaluate(goal)
        self.assertEqual([s['main_ok'] for s in ev['slots'][3:]], [False, True, True])  # CRIT Rate on slot 4 is off-build

    def test_lower_rarity_rolls_count_as_fractions(self):
        from server import gear
        self.assertAlmostEqual(gear.rolls(prop(20103, '1.6%'), 'zzz'), 2 / 3)
        self.assertIsNone(gear.rolls(prop(20103, '2.4'), 'zzz'))  # a percent stat without % is not trusted

    def test_unreadable_or_impossible_disc_leaves_the_score_unknown(self):
        from server import gear
        goal = {'game': 'zzz', 'gear': full_gear()}
        goal['gear']['discs'][0]['subs'][0] = prop(20103, '2.4')            # CRIT Rate without %
        goal['gear']['discs'][1]['subs'][0] = prop(12103, '19')            # repeats the flat ATK main stat
        ev = gear.evaluate(goal)
        self.assertEqual([s['score'] for s in ev['slots'][:2]], [None, None])
        self.assertIsNone(ev['score'])
        self.assertIsNone(ev['done'])  # unknown is not finished

    def test_targets_sets_mains_and_next_set(self):
        from server import gear
        goal = {'game': 'zzz', 'gear': full_gear(sets=(31000, 31000, 31000, 32000, 32000, 33000)), 'gear_target': {'farm': True, 'score': 10}}
        ev = gear.evaluate(goal)
        self.assertEqual([(s['id'], s['have'], s['ok']) for s in ev['sets']], [(31000, 3, False), (32000, 2, True)])
        self.assertEqual(ev['next_set']['id'], 31000)
        self.assertFalse(ev['done'])
        goal['gear'] = full_gear()
        ev = gear.evaluate(goal)
        self.assertTrue(all(ev['checks'].values()))
        self.assertTrue(ev['done'])
        self.assertEqual(ev['next_set']['id'], 31000)  # all sets met: the 4-piece set stays first
        goal['gear_target']['main'] = {'4': [21103], '5': [12102], '6': [12102]}
        ev = gear.evaluate(goal)
        self.assertEqual([s['main_ok'] for s in ev['slots']], [None, None, None, False, True, True])
        self.assertFalse(ev['done'])

    def test_empty_slot_counts_zero_and_is_not_filled(self):
        from server import gear
        g = full_gear()
        g['discs'] = g['discs'][:5]
        ev = gear.evaluate({'game': 'zzz', 'gear': g})
        self.assertFalse(ev['checks']['filled'])
        self.assertEqual(ev['slots'][5]['score'], None)
        self.assertLess(ev['score'], 80)

    def test_clean_target_rejects_impossible_targets(self):
        from server import gear
        ok = gear.clean_target({'farm': True, 'score': 60, 'sets': [{'id': 1, 'count': 4}, {'id': 2, 'count': 2}],
                                'main': {'4': [20103], '5': [], '6': [12102]}}, 'zzz')
        self.assertEqual(ok['sets'][0], {'id': 1, 'name': '', 'count': 4})
        for bad in ({'sets': [{'id': 1, 'count': 4}, {'id': 2, 'count': 4}]},
                    {'sets': [{'id': 1, 'count': 3}]},
                    {'main': {'4': [23103]}},
                    {'score': 101},
                    {'weights': {'20103': 1}},
                    {'weights': {str(i): 0 for i in gear.RULES['zzz']['step']}}):
            with self.assertRaises(ValueError, msg=bad):
                gear.clean_target(bad, 'zzz')
        with self.assertRaises(ValueError):
            gear.clean_target({'farm': True}, 'hsr')
        with self.assertRaises(ValueError):  # five artifact slots: 4 + 2 pieces cannot fit
            gear.clean_target({'sets': [{'id': 1, 'count': 4}, {'id': 2, 'count': 2}]}, 'genshin')

    def test_observe_normalizes_the_upgrade_guide(self):
        from server import gear
        p = lambda pid, value, name='': SimpleNamespace(type=pid, value=value, name=name, level=1, valid=True)
        suit = SimpleNamespace(id=31000, name='Set A', icon='https://act-webstatic.mihoyo.com/x.png')
        guide = SimpleNamespace(
            discs=[SimpleNamespace(position=1, level=15, rarity='S', set_effect=suit, icon='',
                                   main_properties=[p(11103, '2200')], properties=[p(20103, '4.8%')])],
            avatar=SimpleNamespace(properties=[p(2, '900'), p(5, '5%')]),
            plan=SimpleNamespace(name='Build', detail=SimpleNamespace(discs=SimpleNamespace(
                sets=[suit], set_kind=1, slot_4_main_stats=[p(20103, '')], slot_5_main_stats=[], slot_6_main_stats=[],
                sub_stats=[p(20103, ''), p(21103, '')]))),
            from_my_plan=True)
        seen = gear.observe_zzz(guide)
        self.assertEqual(seen['discs'][0]['subs'][0]['number'], 4.8)
        self.assertEqual(seen['base'], {'atk': 900.0})
        self.assertEqual(seen['plan']['subs'], [20103, 21103])
        self.assertEqual(seen['plan']['main']['4'], [20103])
        self.assertEqual(gear.icons(seen), {'zzz/disc/31000': 'https://act-webstatic.mihoyo.com/x.png'})

    def test_equipment_continuation_follows_the_first_unfinished_character(self):
        from server import core, materials, planner
        core.save_settings({'planning': {'disc': {'enabled': True, 'mission': 'Fixed stage', 'cap': 10}}})
        done = {'id': 'a', 'game': 'zzz', 'character_id': '1', 'name': 'Done', 'enabled': True, 'position': 1,
                'gear': full_gear(), 'gear_target': {'farm': True, 'score': 10}}
        todo = {'id': 'b', 'game': 'zzz', 'character_id': '2', 'name': 'Todo', 'enabled': True, 'position': 2,
                'gear': full_gear(sets=(32000,) * 6), 'gear_target': {'farm': True, 'score': 10}}
        off = {'id': 'c', 'game': 'zzz', 'character_id': '3', 'name': 'Off', 'enabled': True, 'position': 3,
               'gear': full_gear(sets=(32000,) * 6)}
        for goal in (done, todo, off):
            core.save_goal(goal)
        stages = [{'name': 'Stage A', 'sets': [{'id': None, 'name': 'Set 31000'}, {'id': 33000, 'name': 'Set 33000'}]}]
        with mock.patch.object(materials, 'zzz_disc_stages', return_value=stages):
            eq = planner.equipment('zzz')
            self.assertEqual((eq['mode'], eq['goal_id'], eq['name'], eq['set']), ('character', 'b', 'Stage A', 'Set 31000'))
            self.assertEqual([r['goal_id'] for r in eq['queue']], ['a', 'b'])  # 'Off' does not steer farming
            item = planner.plan('zzz')['item']
            self.assertEqual((item['goal_id'], item['route']['mission_type']), ('b', 'Stage A'))
            # every target met: nothing is farmed, the fixed stage is not used either
            todo['gear'] = done['gear']
            core.save_goal(todo)
            eq = planner.equipment('zzz')
            self.assertIsNone(eq['goal_id'])
            self.assertTrue(eq['why'])
        for goal in (done, todo, off):
            core.delete_goal(goal['id'])
        eq = planner.equipment('zzz')
        self.assertEqual((eq['mode'], eq['name']), ('fixed', 'Fixed stage'))


    def test_equipment_runs_are_credited_to_the_character_and_the_cap(self):
        from server import core, runner
        core.save_goal({'id': 'r', 'game': 'zzz', 'character_id': '9', 'name': 'R', 'enabled': True})
        core.put('equip_used:zzz', 5)
        item = {'key': 'equip:zzz', 'goal': 'Drive Discs for R', 'label': 'Stage', 'unit_label': ' runs', 'upper': 10, 'unit': 'disc'}
        result = {'game': 'zzz', 'status': 'FAILED', 'phase': 'equipment', 'goal_id': 'r', 'completed': None,
                  'errors': [], 'notes': []}
        with mock.patch('server.tools.parse_zzz', return_value={'one_dragon': 'success', 'charge': 'success',
                                                                'last_energy': 10, 'errors': []}):
            runner._receipt(result, 'zzz', item, '', {'completed': 3, 'battles': 3, 'energy_stop': None}, False)
            self.assertEqual((core.get('equip_used:zzz'), core.goal('r')['gear_runs']), (8, 3))
            unverified = {**result, 'completed': None, 'notes': []}
            runner._receipt(unverified, 'zzz', item, '', {'completed': None, 'reason': 'missing'}, False)
        self.assertEqual((core.get('equip_used:zzz'), core.goal('r')['gear_runs']), (8, 3))  # unknown counts nothing
        core.delete_goal('r')

    def test_genshin_artifacts_from_the_character_detail(self):
        from server import core, gear, materials, planner
        sub = lambda pid, value, times: {'property_type': pid, 'value': value, 'times': times}
        flower = {'id': 1, 'name': 'Flower', 'icon': 'https://act-webstatic.mihoyo.com/flower.png', 'pos': 1, 'rarity': 5, 'level': 20,
                  'set': {'id': 15031, 'name': '逐影猎人'}, 'main_property': sub(2, '4780', 0),
                  'sub_property_list': [sub(20, '7.8%', 1), sub(22, '21.0%', 2), sub(3, '9.9%', 1), sub(23, '5.8%', 0)]}
        raw = {'list': [{'base': {'id': 10000089}, 'relics': [flower],
                         'base_properties': [{'property_type': 2000, 'base': '15,307'}, {'property_type': 2001, 'base': '674'}],
                         'recommend_relic_property': {'recommend_properties': {
                             'sand_main_property_list': [3, 23], 'goblet_main_property_list': [3, 42],
                             'circlet_main_property_list': [20, 22], 'sub_property_list': [20, 22, 3, 23]},
                             'custom_properties': None}}],
               'property_map': {'20': {'property_type': 20, 'name': '暴击率'}}}
        seen = gear.observe_genshin(raw, 10000089)
        self.assertEqual(seen['base'], {'hp': 15307.0, 'atk': 674.0})
        self.assertEqual([s['level'] for s in seen['discs'][0]['subs']], [2, 3, 2, 1])  # times + 1
        self.assertEqual(seen['plan']['main'], {'3': [3, 23], '4': [3, 42], '5': [20, 22]})
        self.assertEqual(gear.icons(seen, 'genshin'), {'genshin/artifact/15031': flower['icon']})
        goal = {'id': 'gi', 'game': 'genshin', 'character_id': '10000089', 'name': 'Furina', 'enabled': True, 'position': 1,
                'gear': {**seen, 'at': core.stamp()}, 'gear_target': {'farm': True, 'score': 60, 'sets': [{'id': 15031, 'count': 4}]}}
        ev = gear.evaluate(goal)
        w = {int(k): v for k, v in ev['weights'].items()}
        self.assertEqual((w[20], w[3], w[2], w[5]), (1.0, 1.0, 0.33, 0.0))  # flat HP: 298.75 / (5.83% of 15,307)
        # each roll counts its share of a maximum roll; the HP main stat leaves CR, CD, HP%, ER as the best four
        got = 7.8 / 3.89 + 21.0 / 7.77 + 9.9 / 5.83 + 5.8 / 6.48
        self.assertAlmostEqual(ev['slots'][0]['score'], round(100 * got / 9, 1), delta=0.05)
        self.assertEqual(ev['slots'][0]['wasted'], 0)
        self.assertEqual(ev['totals']['22'], 3)
        self.assertFalse(ev['checks']['filled'])
        self.assertEqual(materials.stage_for_set({'id': 15031, 'name': ''}, materials.gear_stages('genshin')), '罪祸的终末')
        core.save_settings({'planning': {'artifact': {'enabled': True, 'domain': '', 'cap': 20}}})
        core.save_goal(goal)
        eq = planner.equipment('genshin')
        self.assertEqual((eq['mode'], eq['goal_id'], eq['name']), ('character', 'gi', '罪祸的终末'))
        item = planner.plan('genshin')['item']
        self.assertEqual((item['route'], item['claims']), ({'kind': 'domain', 'name': '罪祸的终末', 'domain_type': 'BlessDomain'},
                                                           {'o40': 10, 'o20': 0}))
        core.delete_goal('gi')
        with self.assertRaises(ValueError):
            gear.observe_genshin(raw, 10000002)  # never another character's data

    def test_inventory_arrangement_in_goal_order(self):
        """Owned pieces: the best arrangement per farming character, never another character's pieces."""
        import copy
        from server import core, inventory, materials, planner
        core.save_settings({'planning': {'disc': {'enabled': True, 'mission': '', 'cap': 10}}})
        worn = full_gear(sets=(31000, 31000, 31000, 32000, 32000, 33000))  # 3 + 2: the 4-piece set is short
        a = {'id': 'ia', 'game': 'zzz', 'character_id': '1', 'name': 'A', 'enabled': True, 'position': 1,
             'gear': worn, 'gear_target': {'farm': True, 'score': 10}}
        b = {'id': 'ib', 'game': 'zzz', 'character_id': '2', 'name': 'B', 'enabled': True, 'position': 2,
             'gear': full_gear(sets=(33000,) * 6), 'gear_target': {'farm': True, 'score': 10}}
        for goal in (a, b):
            core.save_goal(goal)
        pieces = [dict(copy.deepcopy(d), location='A') for d in worn['discs']]   # what A wears
        pieces += [dict(copy.deepcopy(d), location='B') for d in b['gear']['discs']]  # and B (a scan lists every piece)
        better6 = disc(6, 31000, MAIN[6], SUBS[6])                               # a slot 6 piece of A's 4-piece set, in the bag
        pieces.append(dict(better6, location=None))
        stolen = disc(5, 31000, MAIN[5], [(20103, '14.4%'), (21103, '14.4%'), (12102, '9%')])  # better, but worn by C
        pieces.append(dict(stolen, location='C'))
        junk = disc(2, 33000, MAIN[2], [(11103, '112'), (13103, '15'), (31203, '9')])
        pieces += [dict(junk, location=None), dict(copy.deepcopy(junk), location=None, lock=True)]
        inventory.save('zzz', pieces, 'test')
        result = inventory.arrange('zzz')
        owned = result['goals']['ia']
        self.assertTrue(owned['done'])                                   # 4 + 2 with the bag piece on slot 6
        self.assertEqual([c['slot'] for c in owned['changes']], [6])     # equip only that one
        self.assertNotEqual(owned['picks']['5'], str(len(worn['discs']) * 2 + 1))  # C's piece is never taken
        self.assertNotIn(owned['picks']['6'], result['goals']['ib']['picks'].values())
        self.assertEqual(result['spare'], [str(len(pieces) - 2)])        # the unlocked junk; the locked copy stays
        with mock.patch.object(materials, 'zzz_disc_stages', return_value=[]):
            row = next(r for r in planner.gear_queue('zzz') if r['goal_id'] == 'ia')
        self.assertTrue(row['done'])
        self.assertEqual(row['why'], __import__('server.i18n', fromlist=['tr']).tr('gear_owned_meets'))
        for goal in (a, b):
            core.delete_goal(goal['id'])
        core.delete('inventory_at:zzz')

    def test_arrangement_prefers_set_counts_over_score(self):
        from server import inventory
        goal = {'id': 'x', 'game': 'zzz', 'gear': full_gear(sets=(33000,) * 6),
                'gear_target': {'farm': True, 'score': 0, 'sets': [{'id': 31000, 'count': 4}]}}
        pool = []
        for slot in range(1, 7):
            strong = disc(slot, 33000, MAIN[slot], SUBS[slot])                      # high score, wrong set
            weak = disc(slot, 31000, MAIN[slot], [(11103, '112'), (13103, '15')])   # right set, low score
            pool += [dict(strong, uid=f's{slot}'), dict(weak, uid=f'w{slot}')]
        found = inventory.best(goal, pool)
        self.assertEqual(sum(1 for uid in found['picks'].values() if uid.startswith('w')), 4)  # exactly the 4 needed
        self.assertTrue(found['checks']['sets'])

    def test_area_patrol_stages_and_set_lookup(self):
        from server import materials
        stages = materials.zzz_disc_stages('')  # no OneDragon here: the bundled snapshot
        self.assertEqual(len(stages), 15)
        self.assertEqual(materials.stage_for_set({'id': 31000, 'name': ''}, stages), '高塔与巨炮')
        self.assertEqual(materials.stage_for_set({'id': None, 'name': '雪兔梦游仙境 '}, stages), '伏龙与战车')
        self.assertIsNone(materials.stage_for_set({'id': 1, 'name': 'Unknown'}, stages))
        self.assertEqual(len(materials.gear_sets('zzz', '')), 30)

    def logged_in_home(self):
        """A temporary runtime folder holding a shared login with one Genshin role."""
        from server import core
        home = Path(tempfile.mkdtemp(prefix='gcl_gear_read_'))
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        patcher = mock.patch.object(core, 'DATA', home)
        patcher.start()
        self.addCleanup(patcher.stop)
        core.save_secret('mihoyo', {'cookies': {'ltuid': '1'}, 'generation': 'test',
                                    'app': {'aid': '1', 'mid': 'test-mid', 'stoken': 'v2_test', 'identity': {}},
                                    'accounts': {'genshin': {'uid': '100000001', 'server': 'cn_gf01'}}})

    def test_artifact_captcha_backs_off_until_the_user_syncs(self):
        """A captcha on the artifact read pauses scheduled reads; Sync on the goal tries again at once."""
        import genshin
        from server import mihoyo
        self.logged_in_home()
        detail = mock.AsyncMock(side_effect=genshin.GenshinException({'retcode': 1034, 'message': ''}))
        client = SimpleNamespace(get_genshin_detailed_characters=detail)
        goal = {'game': 'genshin', 'character_id': '10000089'}
        for force, reads in ((False, 1), (False, 1), (True, 2)):
            result = {}
            asyncio.run(mihoyo._genshin_gear(client, goal, result, force))
            self.assertIn('1034', result['gear_error'])
            self.assertEqual(detail.await_count, reads)
        self.assertEqual(mihoyo.health('detail')['failures'], 2)

    def test_sync_without_a_login_asks_for_one(self):
        from server import core, mihoyo
        from server.i18n import tr
        self.logged_in_home()
        core.save_secret('mihoyo', {'cookies': {'ltuid': '1'}})  # an old website-only login: no accounts
        with mock.patch.object(mihoyo, 'client', side_effect=AssertionError('no request without a login')), \
                self.assertRaises(ValueError) as caught:
            mihoyo.observe({'game': 'genshin', 'character_id': '10000089'})
        self.assertEqual(str(caught.exception), tr('login_first'))


if __name__ == '__main__':
    unittest.main()
