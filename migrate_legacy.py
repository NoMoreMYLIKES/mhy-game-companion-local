"""Optional data migration: import goals and settings from a legacy state.sqlite.

Usage:
    python migrate_legacy.py --source <path-to-legacy-state.sqlite>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from server import core, goals


def migrate(source_db: Path) -> None:
    if not source_db.is_file():
        raise FileNotFoundError(f'Source database not found: {source_db}')

    con = sqlite3.connect(source_db)
    con.row_factory = sqlite3.Row

    # 1. Goals
    try:
        rows = con.execute('SELECT data FROM goals').fetchall()
    except sqlite3.OperationalError:
        rows = []

    imported_goals = 0
    for r in rows:
        old = json.loads(r[0])
        gid = old.get('id')
        game = old.get('game')
        name = old.get('name')
        if not (gid and game and name):
            continue

        # Legacy 'targets' becomes 'target'; categories use the default order
        targets = old.get('targets') or {}
        current = old.get('current') or {}
        category_order = ['level', 'talents', 'weapon']

        cid = old.get('character_key', '').split(':')[-1] or old.get('character_id') or gid

        new_goal = {
            'id': gid,
            'game': game,
            'character_id': str(cid),
            'name': name,
            'enabled': bool(old.get('enabled', True)),
            'position': int(old.get('priority', old.get('position', 1))),
            'created': old.get('created', core.stamp()),
            'current': current,
            'target': targets,
            'weapon_id': old.get('weapon_id'),
            'weapon_name': old.get('weapon_name', ''),
            'category_order': category_order,
            'paused': old.get('paused', []),
            'materials': [],
            'allowance': {},
            'sync_at': old.get('updated'),
        }
        core.save_goal(new_goal)
        imported_goals += 1

    print(f'[OK] Imported {imported_goals} goals.')

    # 2. Selected planning settings
    try:
        row = con.execute("SELECT value FROM kv WHERE key='planning_settings'").fetchone()
        if row:
            ps = json.loads(row[0])
            patch = {'planning': {}}
            if 'genshin_claim_mode' in ps:
                patch['planning']['genshin_claim_mode'] = ps['genshin_claim_mode']
            if 'genshin_boss_yield' in ps:
                patch['planning']['genshin_boss_yield'] = ps['genshin_boss_yield']
            core.save_settings(patch)
            print('[OK] Planning settings migrated.')
    except Exception as exc:
        print(f'[INFO] Skipped planning settings: {exc}')

    con.close()


def main():
    parser = argparse.ArgumentParser(description='Import goals from a legacy Game Companion database')
    parser.add_argument('--source', required=True, help='path to the legacy state.sqlite')
    args = parser.parse_args()
    migrate(Path(args.source))


if __name__ == '__main__':
    main()
