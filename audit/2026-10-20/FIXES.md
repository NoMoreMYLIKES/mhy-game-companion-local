# Fixes for the 2026-10-20 logic audit

All 26 items of `REPORT.zh-CN.md` are fixed on top of `87e59e6`. Each one has a regression test in
`tests/test_logic.py` (named `test_bNN_…`), part of the normal `unittest discover` run. `reproduce.py` now
passes 36/36. The UI and HTTP cases of `ui_cases.js` / `http_cases.js` pass against `serve_fixture.py`.

`reproduce.py` and `serve_fixture.py` needed one fixture change: `mihoyo.observe` takes `force=` since `87e59e6`
(after the audited `80a1c7b`), so their stand-ins now accept it. Before that change, the stand-ins raised
`TypeError` before doing their edit, so four sync cases could not pass on any code.

| Item | Fix | Where |
| :--- | :--- | :--- |
| B01 | The card shows "Not farmed now" plus the reason and a Settings link when the continuation is blocked. The plan's reason names the block whenever a character asked for equipment, even while the continuation is off. Nothing is switched on for the user. | `planner.plan`, `app.js gearStatus/gearBlock` |
| B02 | A calculator row's amount is `num` or `cnt` (non-negative, whole). A missing or contradictory amount is a format error, never 0. | `mihoyo._quantity` |
| B03 | The account's stock is handed out once, in goal order, to enabled goals of the selected role. Genshin only reports gaps, so a later goal's share is UNKNOWN when the stock is known only as "each goal alone is covered". | `materials.stock/ledger`, `planner.items_by_goal` |
| B04 | Need-0 tiers stay in the ZZZ series pool, and the adapter keeps a series' other tiers that the answer reports. Tiers it does not report stay uncounted. | `materials._series`, `mihoyo.calculate` |
| B05 | A sync merges into the record as it is when the answers arrive. Cancel, delete and the user's edits win. A calculation for changed inputs is dropped. | `goals.sync` |
| B06 | Changing targets, levels or the weapon marks the calculation stale. A stale goal is not farmed until it is recalculated. | `goals.update`, `planner.calc_block` |
| B07 | The calculator is never asked with an unknown current level. W-Engine level 0 stays valid. | `mihoyo.calculate` |
| B08 | Stamina readings, goal data, inventory scans and the equipment cap carry their game role. Replies for a role that is no longer selected are dropped. Goals of another role re-sync within 15 min. A cap waits for an explicit "Allow for this role". | `core.account_key`, `goals.sync`, `planner`, `/api/equip/grant` |
| B09 | The log baseline is taken before configuring, and logs are read only after this batch started its tool. | `runner._run_game` |
| B10 | A finished run that has a run error (for example a restore failure) is PARTIAL. BetterGI `[ERR]` lines become a note. | `runner._receipt` |
| B11 | An unknown completed amount is PARTIAL. | `runner._receipt` |
| B12 | A OneDragon command's outcome is its last success/failure line. | `tools.parse_zzz` |
| B13 | The first unfinished character decides. While it has no stage, the queue waits and shows why. | `planner.equipment` |
| B14 | The forecast counts recovery from the reading and keeps the remainder between slots. At the cap, recovery waits until stamina is spent. | `planner.forecast` |
| B15 | Times are saved deduplicated and sorted. Slots are one per distinct time. | `core.prepare_settings`, `planner.slot_times` |
| B16 | Turning the schedule on needs at least one time and one game. | `core.prepare_settings` |
| B17 | The arrangement cache keys on a goals version bumped by every goal write, not on whole-second stamps. | `core.goals_version`, `inventory.arrange` |
| B18 | Pieces are matched by wearer name, not by identical stats. Another character's piece is never available. | `inventory.wearer/available_to` |
| B19 | Only whole images are saved (header with a picture size, plus the end marker). A damaged cached file counts as missing. | `assets.complete/file/cached` |
| B20 | A queued message whose channel was turned off is closed as not sent. | `notify.drain` |
| B21 | Settings are all or nothing: the whole request is validated, then the logon task is changed, then files are stored. The task is put back if storing fails. | `web.save_settings` |
| B22 | A sync never writes the target. Only the calculator request uses max(target, current). | `goals.sync`, `mihoyo.calculate` |
| B23 | An open target dialog updates its current levels and read time on every refresh, and keeps what the user typed. | `app.js updateTargetsDialog` |
| B24 | The Sync toast names failed reads (levels, equipment, materials). The card's "synced" time is the last successful reading. | `app.js syncGoal` |
| B25 | Numeric settings are checked for type, finiteness and range (boss yield ≥ 0.5, coffee 0–300, caps, intervals, window size). | `core.validate_settings` |
| B26 | Equipment battles (a 40-resin claim is one) are counted apart from reward units. The cap still counts units. | `runner._receipt` |

Not verified here: real game runs and receipts, in-game OCR, real notification delivery, and the live
official response shapes. The ZZZ calculator's amount field was confirmed neither by a live capture nor by
public sources, which is why both `num` and `cnt` are accepted and anything else is refused.
