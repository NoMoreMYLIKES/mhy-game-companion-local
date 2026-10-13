"""Inventory scans: the scanners' output formats, when a scan runs, and where it sits in a batch."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ScanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix='gcl_scan_')
        os.environ['GCL_HOME'] = cls.temp_dir

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_good_from_yas(self):
        from server import scanners
        data = {'format': 'GOOD', 'version': 1, 'source': 'yas', 'artifacts': [
            {'setKey': 'ViridescentVenerer', 'slotKey': 'circlet', 'level': 20, 'rarity': 5, 'mainStatKey': 'critRate_',
             'location': 'Kazuha', 'lock': True,
             'substats': [{'key': 'critDMG_', 'value': 19.4}, {'key': 'atk', 'value': 19}, {'key': 'eleMas', 'value': 40}]},
            {'setKey': 'SomeFutureSet', 'slotKey': 'flower', 'level': 0, 'rarity': 5, 'mainStatKey': 'hp',
             'location': '', 'lock': False, 'substats': []},
            {'setKey': 'GladiatorsFinale', 'slotKey': 'unknown', 'mainStatKey': 'hp'}]}
        pieces = scanners.from_good(data)
        self.assertEqual(len(pieces), 2)  # an unknown slot is skipped
        p = pieces[0]
        self.assertEqual((p['slot'], p['set_id'], p['set'], p['main']['id'], p['location'], p['lock']),
                         (5, 15002, '翠绿之影', 20, 'Kazuha', True))
        self.assertEqual([(s['id'], s['number'], s['percent']) for s in p['subs']], [(22, 19.4, True), (5, 19.0, False), (28, 40.0, False)])
        self.assertEqual((pieces[1]['set_id'], pieces[1]['set'], pieces[1]['location']), (0, 'SomeFutureSet', None))
        with self.assertRaises(ValueError):
            scanners.from_good({'format': 'Mona'})

    def test_zzz_scanner_export(self):
        from server import scanners
        records = [{'序号': 1, '名称': '啄木鸟电音', '槽位': 5, '品质': 'S', '等级': 15, '最大等级': 15,
                    '主属性': {'攻击力': '30%'},
                    '副属性': [{'暴击率': '7.2%'}, {'攻击力': 38.0}, {'穿透值': 9.0}, {'暴击伤害': '4.8%'}]},
                   {'序号': 2, '名称': '极地重金属', '槽位': 1, '品质': 'A', '等级': 12, '最大等级': 12,
                    '主属性': {'生命值': 1468.0}, '副属性': [{'暴击率': '3.2%'}]}]
        pieces = scanners.from_zzz_scanner(records)
        p = pieces[0]
        self.assertEqual((p['slot'], p['set_id'], p['main']['id'], p['location'], p['lock']), (5, 31000, 12102, None, None))
        self.assertEqual([(s['id'], s['level']) for s in p['subs']], [(20103, 3), (12103, 2), (23203, 1), (21103, 1)])
        a = pieces[1]
        self.assertEqual((a['set_id'], a['main']['id'], a['subs'][0]['level']), (32500, 11103, 2))  # 3.2% = two A-rank rolls

    def test_unlocated_scan_keeps_other_goals_pieces_and_lists_no_spare(self):
        from server import core, inventory, scanners
        worn = {'slot': 1, 'level': 15, 'rarity': 'S', 'set_id': 31000, 'set': '啄木鸟电音', 'icon': '',
                'main': {'id': 11103}, 'subs': [{'id': 20103, 'number': 9.6, 'percent': True, 'level': 4}]}
        mine = {'id': 'm', 'game': 'zzz', 'character_id': '1', 'name': 'M', 'enabled': True, 'position': 1,
                'gear': {'discs': [], 'base': {}, 'plan': {'subs': [20103], 'main': {}, 'sets': []}},
                'gear_target': {'farm': True, 'score': 10}}
        other = {'id': 'o', 'game': 'zzz', 'character_id': '2', 'name': 'O', 'enabled': True, 'position': 2,
                 'gear': {'discs': [worn], 'base': {}, 'plan': None}}
        for g in (mine, other):
            core.save_goal(g)
        spare = dict(worn, subs=[{'id': 31203, 'number': 9.0, 'percent': False, 'level': 1}])
        inventory.save('zzz', [dict(worn, location=None, lock=None), dict(spare, location=None, lock=None)], 'test', located=False)
        result = inventory.arrange('zzz')
        self.assertNotEqual(result['goals']['m']['picks'].get('1'), '0')  # O wears piece 0
        self.assertEqual(result['spare'], [])
        for g in (mine, other):
            core.delete_goal(g['id'])
        core.delete('inventory_at:zzz')

    def test_scan_schedule(self):
        from server import core, scanners
        exe = Path(self.temp_dir) / 'yas_artifact.exe'
        exe.write_text('')
        core.save_settings({'paths': {'yas': str(exe)}, 'features': {'scan_inventory': False}})
        self.assertFalse(scanners.due('genshin', 'equipment'))           # switched off
        core.save_settings({'features': {'scan_inventory': True}})
        self.assertTrue(scanners.due('genshin', 'goal'))                 # never scanned
        core.put('inventory_at:genshin', core.stamp())
        self.assertFalse(scanners.due('genshin', 'goal'))                # scanned today
        self.assertTrue(scanners.due('genshin', 'equipment'))            # after equipment farming, always
        self.assertFalse(scanners.due('zzz', 'equipment'))               # no ZZZ scanner set
        core.delete('inventory_at:genshin')
        core.save_settings({'features': {'scan_inventory': False}})

    def test_batch_scans_before_closing_the_game(self):
        """ZZZ: OneDragon runs without -c, the scan runs while the game is open, then the game is closed."""
        from server import planner, runner, scanners, tools
        from server.i18n import tr
        calls = []
        item = {'key': 'equip:zzz', 'goal_id': None, 'goal': 'Drive Discs', 'label': 'Stage', 'names': '', 'unit': 'disc',
                'unit_label': ' runs', 'upper': 2, 'expected': 1}
        proc = mock.Mock(pid=1)
        proc.poll.return_value = 0
        exe = mock.Mock(is_file=lambda: True)
        with mock.patch.object(planner, 'plan', return_value={'phase': 'equipment', 'item': item, 'reason': ''}), \
                mock.patch.object(scanners, 'due', return_value=True), \
                mock.patch.object(scanners, 'run', side_effect=lambda *a: calls.append('scan') or {'count': 7}), \
                mock.patch('server.mihoyo.refresh_notes'), \
                mock.patch.multiple(tools, game_exe=lambda g: 'game.exe', tool_exe=lambda g: exe, zzz_prepare=lambda r, i: ['p'],
                                    zzz_patch_ok=lambda: True, log_baseline=lambda g: {}, launch_game=lambda g: None,
                                    zzz_root=lambda: '.', read_new=lambda g, b: '', zzz_receipt=lambda ids: {'completed': 1},
                                    restore_all=lambda: [], parse_zzz=lambda t: {'one_dragon': 'success', 'charge': 'success',
                                                                                 'last_energy': None, 'errors': []}), \
                mock.patch.object(tools, 'running', side_effect=lambda p: p == 'game.exe' and 'closed' not in calls), \
                mock.patch.object(tools, 'kill_path', side_effect=lambda p: calls.append('close game' if p == 'game.exe' else 'close tool')), \
                mock.patch.object(tools, 'start', side_effect=lambda path, args, **kw: calls.append(args) or proc), \
                mock.patch.object(runner, '_sleep', return_value=False), mock.patch('time.sleep'):
            result = runner._run_game('run', 'zzz')
        launch = next(c for c in calls if isinstance(c, list))
        self.assertEqual(launch, ['-o'])  # no -c: the game stays open for the scan
        order = [c for c in calls if c in ('scan', 'close game')]
        self.assertEqual(order[-2:], ['scan', 'close game'])
        self.assertIn(tr('scan_done', count=7), result['notes'])


if __name__ == '__main__':
    unittest.main()
