# Technical Architecture & Developer Specification

This document describes how **Game Companion Local** is built: modules, stored data, the execution pipeline, the HTTP API, tool integration, failure handling and the rules contributors (human or AI) must follow. It reflects the code in this repository; when the two disagree, the code wins and this file should be fixed.

---

## 1. System Map & Module Responsibilities

A headless Python backend (`server/`), a static Swiss Style frontend (`web/`), a PowerShell 7 audio helper (`tools/`) and tests (`tests/`):

```
mhy-game-companion-local/
├── Start.bat / Start.ps1       # .venv and packages, elevation, start through server.launcher, browser
├── Stop.ps1                    # Stop this installation's verified backend through server.launcher
├── start.sh / stop.sh          # Linux: the same through server.launcher, optionally as a systemd user service
├── requirements.txt            # genshin, qrcode, PyYAML
├── migrate_legacy.py           # Optional import of goals/settings from a legacy state.sqlite
├── PLAN.md                     # Vision, the four pillars, roadmap
├── ARCHITECTURE.md             # This file
├── server/
│   ├── __main__.py             # Entry point: check settings, bind, PID file, health, recover, scheduler
│   ├── launcher.py             # start / stop / status with the backend's own settings; explains failures
│   ├── procinfo.py             # Process identity (creation time, image) and the owner of a port
│   ├── core.py                 # Paths, time (UTC+8, 04:00 reset), SQLite, settings, DPAPI secrets
│   ├── i18n.py                 # Backend message catalog (English base, Chinese translation)
│   ├── auth.py                 # One app QR grant, CN cookie derivation and shared login
│   ├── widget.py               # Genshin and ZZZ official stamina widgets
│   ├── mihoyo.py               # Accounts, source health, legacy verification and calculators
│   ├── goals.py                # Goal CRUD, ordering, official sync, executed-unit allowance
│   ├── gear.py                 # Drive Discs / Artifacts: read, score, equipment targets, next set to farm
│   ├── materials.py            # Datasets, farming routes, units and expected-yield conversion
│   ├── planner.py              # The single planning rule: preview, forecast and execution
│   ├── runner.py               # Batch pipeline: plan → configure → launch → receipt → restore
│   ├── tools.py                # BetterGI / OneDragon configs, patch journal, processes, logs, audio
│   ├── scheduler.py            # 20 s loop: slots with catch-up, notes polling, goal sync, outbox
│   ├── notify.py               # Notification outbox and channels
│   ├── assets.py               # Local cache of portraits / material icons / disc and artifact set icons from official API responses
│   ├── web.py                  # ThreadingHTTPServer: static UI + JSON API + cached images, loopback/LAN guard
│   ├── templates/              # bettergi_morning.json (neutral BetterGI One Dragon template)
│   └── datasets/               # genshin.json, zzz.json (offline game data); zzz_disc_stages.json, genshin_artifact_domains.json (where each set drops)
├── tools/audio.ps1             # CoreAudio COM: get / mute / set the default playback device
├── web/                        # index.html, style.css, app.js (SPA with en/zh dictionaries)
└── tests/                      # test_smoke.py (imports, planner, i18n, anonymization), test_launcher.py
```

| Module | Role | Depends on | Writes |
| :--- | :--- | :--- | :--- |
| `core` | Foundation | `sqlite3`, Windows `crypt32` | `data/app.db`, `data/settings.json`, `data/*.dpapi.json` |
| `i18n` | `tr(key, **params)` in the current UI language | `core.settings()` | – |
| `mihoyo` | Official data through `genshin.py` (CN region, `zh-cn`) | `core` | secrets, `accounts`, `health:*`, stamina samples |
| `goals` | Goals and their stable lists | `mihoyo`, `materials`, `gear` | `goals` table |
| `gear` | Drive Disc / Artifact scores, equipment targets and the next set (pure functions over the goal document) | – | – |
| `materials` | Material rows → farmable *items* with a unit count | datasets, tool catalogs | – |
| `planner` | Which item a batch would farm, and why | `goals`, `materials`, stamina samples | – |
| `runner` | One batch at a time | `planner`, `tools`, `goals`, `notify` | `runs` table, `current_run`, `mute_journal` |
| `tools` | Everything that touches BetterGI / OneDragon / processes | tool folders | tool configs, `patch_journal` |
| `scheduler` | Background loop and the logon task | everything above | `slot_done:*` |
| `notify` | Outbox delivery with retries | channel endpoints | `outbox` table |
| `assets` | Saves each image once, the first time an official API response names it | `core` | `data/assets/`, `asset_sources`, `asset_failed` |
| `web` | HTTP API and static files | everything above | – |

---

## 2. Storage & Data Models

All runtime data lives in `data/` (or `%GCL_HOME%`), which is git-ignored.

| File | Content |
| :--- | :--- |
| `app.db` | SQLite database (below) |
| `settings.json` | Non-secret settings; only the values the user changed (merged over `core.DEFAULTS`) |
| `mihoyo.dpapi.json` | DPAPI-encrypted Miyoushe cookies |
| `settings-secrets.dpapi.json` | DPAPI-encrypted LAN password hash, relay URL, Telegram token, webhook URL |
| `server.pid` | `{app, pid, host, port, version, started, image, exe, instance, launch, token, created}`, written once the port is bound. `created` (process creation time) lets Stop tell the backend from a process that reused its PID; `token` authorizes `POST /api/shutdown` |
| `instance.json` | `{id, path, created}`: opaque id of this runtime folder at this location (a copied folder gets a new id). `/api/health` reports it so the launcher can tell installations apart |
| `startup-error.json` | `{kind, message, code, …}` when startup fails (`settings`, `exception`, `bind`); the launcher reads it to explain the failure |
| `logs/startup.log` | Output of the backend process started by the launcher (tracebacks from before logging starts) |
| `logs/app.log` | Rotating application log (2 MB × 3) |
| `assets/<game>/<kind>/<id>.<ext>` | Cached character portraits and material icons (stable game IDs) |

### 2.1 SQLite schema (`core.SCHEMA`)

Rows hold JSON documents; the schema stays small and the document shapes evolve in code.

```sql
CREATE TABLE IF NOT EXISTS kv      (key TEXT PRIMARY KEY, value TEXT NOT NULL);           -- JSON values
CREATE TABLE IF NOT EXISTS goals   (id TEXT PRIMARY KEY, data TEXT NOT NULL);             -- goal document
CREATE TABLE IF NOT EXISTS runs    (id TEXT PRIMARY KEY, started TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY AUTOINCREMENT, game TEXT, at TEXT,
                                    current INTEGER, cap INTEGER, source TEXT);           -- stamina readings (last 2000)
CREATE TABLE IF NOT EXISTS outbox  (id TEXT PRIMARY KEY, created TEXT, payload TEXT, attempts INTEGER DEFAULT 0,
                                    next_at TEXT, sent_at TEXT, error TEXT);              -- notifications (14 days)
```

**Goal document** (`goals.data`):

```json
{
  "id": "hex", "game": "genshin | zzz", "character_id": "10000089", "name": "…",
  "enabled": true, "position": 1, "created": "…", "updated": "…",
  "current": {"level": 80, "attack": 6, "skill": 8, "burst": 8, "weapon": 70},
  "target":  {"level": 90, "attack": 1, "skill": 9, "burst": 9, "weapon": 90},
  "weapon_id": "…", "weapon_name": "…",
  "category_order": ["level", "talents", "weapon"],
  "paused": ["<item key>"],
  "materials": [{"id": "104321", "name": "…", "need": 9, "owned": null, "remaining": 3,
                 "category": "talents", "categories": ["talents"], "domain": "…", "weekdays": [0, 3, 6], "monster": "…"}],
  "allowance": {"<item key>": {"calc_at": "…", "units": 7, "done": 2}},
  "calc_at": "…", "calc_error": null, "sync_at": "…", "observe_at": "…", "observe_error": null,
  "gear": {"at": "…", "base": {"2": 938}, "discs": [{"slot": 1, "level": 15, "rarity": "S", "set_id": 31000, "set": "…",
           "main": {"id": 11103, "value": "2200", …}, "subs": [{"id": 20103, "value": "7.2%", "number": 7.2, "percent": true, "level": 3, "valid": true}]}],
           "plan": {"name": "…", "sets": [{"id": 31000, "name": "…"}], "main": {"4": [20103]}, "subs": [20103, 21103], "names": {"20103": "…"}}},
  "gear_target": {"farm": true, "score": 50, "sets": [{"id": 31000, "count": 4}], "main": {"4": [21103]}, "weights": {"20103": 1, …}, "stage": ""},
  "gear_runs": 12, "gear_error": null
}
```

`gear` is what the last observation read: the equipped pieces (`discs`, for either game), base HP/ATK/DEF and the build: for ZZZ the plan the account follows in Miyoushe's upgrade guide; for Genshin the character detail's `recommend_relic_property` (the account's own picks when it has any, else Miyoushe's recommendation; no sets). A substat's `level` is its roll count (ZZZ `level`; Genshin `times` + 1). `gear_target` holds only what the user changed: `sets`, `main` and `weights` left out follow the build, `stage` empty picks the stage automatically. `gear_runs` counts equipment runs farmed for this character.

`materials` are the official calculator rows (`remaining = null` means UNKNOWN). `allowance` is the **stable list**: the unit count issued at the last calculation and how many were executed since, so a run is never repeated while the official inventory catches up.

**Run document** (`runs.data`):

```json
{
  "id": "20261012-050012-a1b2c3", "started": "…", "ended": "…",
  "slot": "05:00 | manual", "source": "schedule | manual",
  "status": "SUCCESS | PARTIAL | FAILED | SKIPPED | STOPPED", "notes": ["…"],
  "games": [{
    "game": "genshin", "status": "SUCCESS", "phase": "goal | equipment | null",
    "reason": "plan reason", "item": {"key": "…", "goal": "…", "label": "…", "names": "…",
                                      "unit_label": "…", "upper": 7, "expected": 6},
    "goal_id": "…", "completed": 6, "started_tool": true,
    "log": {"claims20": 0, "claims40": 3, "resin": 120, "extra": [], "terminal": true, "insufficient": false, "errors": []},
    "errors": [], "notes": [], "summary": "…", "started": "…", "ended": "…"
  }]
}
```

**KV keys**: `patch_journal`, `mute_journal`, `current_run`, `device` (Miyoushe device id/fingerprint), `accounts`, `account_candidates`, `health:<notes-genshin|notes-zzz|calc|detail>` (`detail`: the Genshin character detail that carries artifacts), `slot_done:<YYYY-MM-DD@HH:MM>`, `equip_used:<game>`, `asset_sources` (image URL per asset key), `asset_failed` (last failed download per key).

Stamina samples store their source as a message key (`source_notes`, `source_onedragon`) and are translated when shown.

### 2.2 Secrets (DPAPI)

Secrets are encrypted with `CryptProtectData` (`CRYPTPROTECT_UI_FORBIDDEN`), bound to the Windows user, and never returned by the API (`/api/state` only exposes `secrets_set` booleans). The LAN password is stored as a PBKDF2-SHA256 hash. Linux has no DPAPI: there the step is a pass-through, the secret files are written readable by their owner only (0600) and the runtime folder is set to 0700 at startup; nothing else protects them.

---

## 3. Planning Rule (`planner.plan`)

One rule serves the dashboard preview, the 3-day forecast and execution. Per game, per batch, exactly one item:

1. Enabled goals in user order → the goal's category order → the first item that is not collected, has an automatic route, is not paused, has a known unit count, is open today (Genshin domain weekdays, 04:00 reset) and still has allowance left.
2. Otherwise the optional equipment continuation (Genshin Domain of Blessing / ZZZ Area Patrol mission) while its cumulative cap has room. When any enabled goal of that game has `farm` on in its equipment target, the first such character (goal order) whose equipment does not meet the target decides where: its next set (the first unmet target set, else the 4-piece set) and the place that drops it: the ZZZ Area Patrol stage (the installed OneDragon's compendium, else `zzz_disc_stages.json`) or the Genshin Domain of Blessing (`genshin_artifact_domains.json`, named as BetterGI names it). When every such character is finished, nothing is farmed; the stage or domain in Settings is used only while no character steers farming.
3. Otherwise nothing: stamina is kept and only free daily tasks run.

**Equipment score** (`gear`): each substat counts its value in top-rarity rolls (A and B discs roll smaller steps; Genshin rolls are 70–100 % of a maximum roll, so each counts its share of one) times its weight; a piece scores that against the best a piece with its main stat could hold (four different weighted substats plus five upgrades of the best one), from 0 to 100; the set score is the mean over all slots (six discs, five artifacts), an empty slot counting 0. Each piece also reports its wasted upgrades (upgrades into substats that do not count), and the set its counted rolls per substat. Weights default to 1 for the substats the followed build recommends, with flat HP/ATK/DEF worth their share of the agent's base stat; the user can set all ten. Builds name stat families, not variants (Miyoushe may send flat ATK for "ATK"): a recommended family gives its % stat 1 and its flat stat the base-stat share, and a main-stat pick becomes the variant the slot can carry (flat ATK on slot 5 → ATK%); the main-stat check compares families. A target is met when all six slots are filled, the target sets and slot 4–6 main stats match and the score reaches the target. Unknown (unreadable substats, no weights) is never met.

Unit conversion (`materials`): Genshin talent / weapon domains count **20 Original Resin reward claims** from the official net gap with SEELIE top-difficulty rates (a 40-resin double claim counts as 2); Genshin bosses count runs from `planning.genshin_boss_yield`; ZZZ Combat Simulation counts **cards** (20 Battery Charge each), pooling a material series with the 3:1 ratio; ZZZ Expert Challenge counts runs. The issued count is an upper bound: the tools stop when the real in-game stamina runs out.

---

## 4. Execution Pipeline (`runner`)

```
[scheduler slot or POST /api/run]
  start_batch: one batch at a time (LOCK + STATE); restore any leftover patch journal first
  └─ worker thread _batch:
       morning scheduled slot (< 12:00) and features.mute_morning → audio mute, save mute_journal
       for game in (zzz, genshin):
         refresh Real-Time Notes (best effort) → planner.plan(game)
         equipment batch for a character → re-read its discs (goals.sync, observe) and plan again
         tool missing → FAILED;  game already running → skip or restart (execution.if_game_running)
         write tool config (journaled) → launch game → launch tool hidden
         wait: tool exit | execution.timeout_minutes | stop request | BetterGI end-of-run log line + 30 s
         finally: kill tool and game, read new log text / plan counters, restore journal
         receipt → completed units → allowance (goal) or equip_used (+ the character's gear_runs) (equipment)
       finally: unmute, final status, notification, delete current_run
  after: re-sync a material goal at +60 s and +180 s; refresh Real-Time Notes at +60 s
```

Status per game: `STOPPED` (user stop), `FAILED` (timeout, or errors without the tool's success marker), `PARTIAL` (no success marker), `SKIPPED`, else `SUCCESS`. The batch takes the worst game status.

---

## 5. HTTP API (`web.py`)

Loopback only by default. With `server.lan` enabled the server binds `0.0.0.0` and non-loopback clients need HTTP Basic auth with the LAN password. Every `POST` must carry `X-GC: 1` (a custom header, so cross-site forms cannot post). Errors return `{"error": "<message in the UI language>"}` with 400/403/500, and 503 while the backend is still starting (only `/api/health`, `/api/shutdown` and static files answer then).

| Endpoint | Method | Body / Query | Result |
| :--- | :--- | :--- | :--- |
| `/api/health` | GET | – | `{ok, app, version, pid, instance, launch, created, ready, busy}`; answers as soon as the port is bound, with `ready: false` until recovery and the scheduler have started |
| `/api/state` | GET | – | Everything the dashboard renders (below) |
| `/api/roster` | GET | `?game=` | Characters from Miyoushe (needs login) |
| `/api/characters` | GET | `?game=` | Characters from the offline dataset (UI fallback) |
| `/api/runs` | GET | `?limit=50` | Run documents |
| `/assets/<game>/<kind>/<id>` | GET | – | A cached image (`kind` is `character`, `material`, `disc` (ZZZ set by suit id) or `artifact` (Genshin set by set id)); 404 when not saved |
| `/api/login/start` | POST | `{}` | QR state (`status`, `svg`, `reason`) |
| `/api/widget/start` | POST | `{}` | Compatibility alias for the shared login flow; no separate widget grant |
| `/api/logout` | POST | `{}` | Clears cookies and accounts |
| `/api/accounts/select` | POST | `{game, uid}` | Picks one of several game accounts |
| `/api/goals/create` | POST | `{game, character_id, name, target?, current?}` | Goal |
| `/api/goals/update` | POST | `{id, patch}` | `enabled`, `name`, `target`, `current`, `weapon_id`, `category_order`, `paused`, `gear_target` (validated by `gear.clean_target`, `null` follows the build again) |
| `/api/goals/delete` | POST | `{id}` | – |
| `/api/goals/order` | POST | `{game, ids}` | – |
| `/api/goals/sync` | POST | `{id, observe}` | Goal after official sync |
| `/api/notes/refresh` | POST | `{game}` | `{current, cap}` or `{error}` |
| `/api/verify/start` | POST | `{game}` | `{gt, challenge, new_captcha}`: a Miyoushe captcha for this account (after a 1034) |
| `/api/verify/finish` | POST | `{game, answer}` | The solved captcha (`geetest_challenge`, `geetest_validate`, `geetest_seccode`) goes to Miyoushe; then `{current, cap}` or `{error}` as for a notes refresh |
| `/api/run` | POST | `{games}` | `{run_id}` |
| `/api/stop` | POST | `{}` | – |
| `/api/settings` | POST | `{settings, secrets}` | `{ok, restart_needed}`; toggles the logon task when `schedule.autostart` changes |
| `/api/lang` | POST | `{lang: "en" \| "zh"}` | Language for backend-generated text |
| `/api/notify/test` | POST | `{channel}` | Sends a test message |
| `/api/equip/reset` | POST | `{game}` | Resets the equipment cap counter |
| `/api/assets/sync` | POST | `{}` | Retries every known image that is not saved yet; returns the cache status |
| `/api/shutdown` | POST | `{token, force?}` | `{ok}`; `token` comes from `server.pid`. Refused while a batch runs unless `force`, which stops the batch, waits up to 5 minutes for its configs to be restored, then exits |

`/api/state` keys: `version, now, game_date, weekday, admin, logged_in, accounts, candidates, qr, runner, next_slot, plans, stamina, goals, forecast, runs, health, settings, check, notifications, catalog, assets, assets_status`. Goal items carry `materials` (per-material need / owned / remaining) and `tint` (`exp`, `family`, `core` or null); goals carry `gear_eval` (`gear.evaluate`: per-slot scores and wasted upgrades, set and main-stat checks, `done`, `next_set`, the weights in force, counted rolls, the build defaults); `catalog.disc_sets` / `catalog.artifact_sets` list every set a known stage or domain drops; forecast rows carry `goal`, `task`, `spend` and `left` (stamina after the batch). `stamina.<game>` is `{value, cap, source, seen}` or `null` (UNKNOWN); `plans.<game>` is `{item, reason, waiting, equipment, daily, daily_keys, phase, …}` (`equipment.mode` is `character` or `fixed`; `equipment.queue` lists the characters that steer farming and why each waits); `runner` carries `stage` (translated) and `stage_key` (stable, for the UI stepper).

---

## 6. Tool Integration

Both tools are **required local installs** and are not part of this repository:

- **BetterGI** (Genshin): <https://github.com/babalae/better-genshin-impact> — folder in `paths.bettergi`.
- **ZenlessZoneZero-OneDragon** (ZZZ): <https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon> (docs: <https://one-dragon.com/>) — folder of an extracted release in `paths.onedragon` (auto-detected in `Downloads` if empty). Upstream asks for an English-only path without spaces, e.g. `D:\ZZZ-OD`.

Game executables are read from the tools' own configs unless `paths.genshin_exe` / `paths.zzz_exe` are set. Every field the app changes in a tool config is journaled first (`tools.patch_fields`) and restored by `tools.restore_all()`.

### 6.1 BetterGI

- **Profile**: `User/OneDragon/<execution.bgi_profile>.json` (default `GameCompanion`; file name and `Name` match, as BetterGI identifies configs by `Name`) is regenerated before each run from a template: the BetterGI One Dragon config named in `execution.bgi_template`, or, when that is empty, the bundled neutral morning template `server/templates/bettergi_morning.json`. The bundled template uses the legacy format (`TaskEnabledList` keyed by task name), which every BetterGI version reads; user templates in the 0.63+ format (`TaskDefinitions` + `TaskOrder`) are kept in that format.
- **Tasks**: exactly one resin task is enabled (`自动秘境` Domain or `自动首领讨伐` Boss) and moved first; the free tasks (`领取邮件` Mail, `领取尘歌壶奖励` Serenitea Pot, `领取每日奖励` Daily Commission Rewards) follow the feature toggles and run last; `合成树脂`, `自动地脉花` and `自动幽境危战` stay off. Domain: `DomainName`, `SundayEverySelectedValue`; Boss: `AutoBossName`, `AutoBossSpecifyRunCount`, `AutoBossRunCount`.
- **Resin control** (journaled, `User/config.json`, camelCase keys): `autoDomainConfig.specifyResinUse`, `originalResin40UseCount`, `originalResin20UseCount`, the other resin counts 0, `rewardRecognitionEnabled`. BetterGI spends 40-resin claims before 20-resin claims.
- **Launch**: `BetterGI.exe startOneDragon <profile>`. BetterGI must not already be running (a second instance only forwards its arguments), so the runner ends any running BetterGI first.
- **Receipt**: new text in `log/better-genshin-impactYYYYMMDD*.log` since the run started; claims are parsed from `使用 "原粹树脂", 数量: 20|40` lines, other resin use is reported, and `一条龙和配置组任务结束` (logged only when the run completes normally) marks the end.

### 6.2 ZenlessZoneZero-OneDragon

- **Configs** (instance `01`, journaled): `config/01/one_dragon/_group.yml` (enables `charge_plan`; with the rewards feature, moves `engagement_reward` and `city_fund` right after it), `config/01/one_dragon/charge_plan.yml` (a generated `plan_list`: Combat Simulation rows of up to 5 cards, or one row per Expert Challenge / Area Patrol run, `restore_charge: 不使用`, no loop), `config/env.yml` (`auto_update_code: false` for the duration of the batch).
- **Launch**: `OneDragon-Launcher.exe -o -c` (Installer / Full packages) or `OneDragon-RuntimeLauncher.exe -o -c` (WithRuntime packages) from the OneDragon folder: `-o` runs One Dragon, `-c` closes the game after a completed run.
- **Receipt**: the `run_times` counter of each generated plan row (read before restoring); log lines in `.log/log.txt*` (`指令[ 一条龙 ] 执行成功`, `指令[ 体力刷本 ] 执行成功`, `剩余电量`) give the success markers and the last Battery Charge reading.
- **Battery Charge**: upstream OneDragon reads Battery Charge before every plan row; with `skip_plan: true` (set by this app) a row it cannot afford is skipped. It never shortens a row, so a 5-card Combat Simulation row needs 100 Battery Charge.
- **Optional live Battery Charge adapter**: a local patch to OneDragon's `src/zzz_od/application/charge_plan/charge_plan_app.py`, detected by its markers (`game-companion collection adapter v2`, `game-companion live energy v1`). It lets the last batch use the Battery Charge actually left instead of being skipped, and reports where it stopped (`companion_energy_stop`); the `companion_*` keys this app writes are only read by the adapter. It is not distributed with this repository, and the app works without it.

### 6.3 Audio

`tools/audio.ps1 -Action get|mute|set` (PowerShell 7 only) controls the default playback device through `IAudioEndpointVolume` and prints JSON. The previous state is kept in `mute_journal` until restored.

---

## 7. Failure Handling

| Failure | Detection | Response |
| :--- | :--- | :--- |
| Backend dies mid-run | `current_run` / `patch_journal` / `mute_journal` left in KV | `runner.recover()` at startup restores configs and mute state and closes the run as `FAILED` |
| Config restore fails | exception per file | Entry stays in the journal; retried before the next batch, which refuses to start while it fails |
| Tool or game hangs | `execution.timeout_minutes` | Processes are killed (`taskkill /T /F`), configs restored, game marked `FAILED` |
| User stop | `/api/stop` | Waits are interrupted; same cleanup; `STOPPED` |
| Missing stamina reading | Notes / logs unavailable | Stamina is UNKNOWN (`null`), never 0; the tool still decides with the in-game value |
| Miyoushe login expired | retcode -100 / 10001 / -10001 | Error shown in the UI, one `login` notification, source backs off |
| Captcha / network / API errors | retcode or exception type | Per-source backoff: 15 min doubling up to 6 h (`mihoyo.record`) |
| Missed slot | Backend not running at slot time | Runs late within `schedule.catchup_hours`, otherwise marked skipped |
| Notification delivery fails | Channel raises | Outbox retry with exponential delay, up to 6 attempts |
| Mute fails | `audio.ps1` error | Note on the run; the batch continues |
| Startup fails (port in use, exception, invalid settings) | Backend exit code and `startup-error.json` | `server.launcher` explains it and exits nonzero (7.1) |

**Shared account login.** `server/auth.py` creates and polls one Passport app QR grant with client type 3. It requires an explicit stoken v2, account ID and mid, then calls the CN `getLTokenBySToken` and `getCookieAccountInfoBySToken` endpoints to derive website cookies ([CN Passport implementation reference](https://github.com/BTMuli/TeyvatGuide/blob/master/src/request/passportReq.ts)). The cookie-token response must confirm the grant owner; the LToken response may omit its UID. Role discovery must succeed before the old login is replaced. App and website credentials, discovered roles and the current selections are atomically saved together in `mihoyo.dpapi.json`; stoken is never added to ordinary SDK requests. Only public QR progress and a `unified` flag are returned to the UI. Logout cancels pending authorization and clears both games' credentials. Requests recheck login and selected role before saving results.

**Official stamina widgets.** Both games share that app grant. Genshin uses `game_record/app/genshin/aapi/widget/v2`; ZZZ uses `event/game_record_zzz/api/zzz/widget` ([ZZZ implementation reference](https://github.com/ZZZure/ZZZeroUID/blob/master/ZZZeroUID/utils/api/request.py)). Requests use the saved device identity, record API X4 DS and client type 5. ZZZ reads `energy.progress.current/max`. An explicitly returned role must match the selection. Widgets may ignore role parameters, so a response without role identifiers requires a fresh role lookup with exactly one matching role for that game. Ambiguous or absent data never becomes a zero sample. Each widget has its own source health and backoff; the dashboard displays the active source's state. Old captcha dialogs cannot replace an active widget source.

Existing separate widget grants are accepted only while their old account binding matches. **Complete account connection** derives shared credentials from that grant without another scan, and retires the separate secret after success. Website-only installs need one app scan. There is one login management UI, with no per-game authorization or disconnect. Login completion and successful reads are reported separately; upstream revocation or API restrictions can still require action.

**Legacy verification.** Website-only installs retain manual Geetest verification. Creation and submission reuse the same client cookie jar, bind to a short-lived server session ID, and consume answers once. Only the server-issued access proof is encrypted and reused for later reads. Account or role changes invalidate proofs. Refusals report only the code, never raw API responses, and direct the user toward shared login instead of repeatedly asking for new captchas. Geetest runs in an opaque-origin sandboxed frame and is completed by the user.

Offline tests cover one-scan login, grant validation, token derivation, cancellation, migration, role attribution, missing data, source backoff and verification reuse. Live checks with an existing grant confirmed both stamina widgets and both character data sources using derived website cookies. These checks do not establish indefinite authorization or long-term API availability. UI layout checks use synthetic account and QR responses separately from live credential checks.


### 7.1 Starting and stopping

`Start.ps1` and `Stop.ps1` are thin wrappers around `python -m server.launcher`, which reads the same runtime folder (`GCL_HOME`, default `data/`) and `settings.json` as the backend, so a custom port or folder applies to every command.

**Start** (`Start.ps1`; `Start.bat` for a double-click):

1. Creates `.venv` with Python 3.10+ (the `py` launcher, then `PATH`, then the usual install folders) and installs `requirements.txt` when its SHA-256 differs from `.venv/gcl-requirements.sha256` or a package is missing (`launcher check-deps`). Every step checks the native exit code.
2. `-Port N` saves the port in `settings.json` first.
3. If this installation already answers, it only opens the dashboard: no administrator prompt.
4. Otherwise it restarts itself as administrator in a hidden window. That window runs `launcher start` and reports its output and exit code back through a temporary file; the original window shows them and opens the browser as the signed-in user. `-NonElevated` skips this step.
5. `launcher start` refuses a port that answers for another program or installation, naming the owner when Windows reports it. It starts `pythonw -m server` detached, with its output in `logs/startup.log`, and waits until `/api/health` reports this runtime folder's instance id, this launch's token and `ready: true`. It returns as soon as the backend exits, with the reason from `startup-error.json`, and stops a backend that is not ready within `-Timeout` seconds (default 60).

**Stop** (`Stop.ps1 [-Force]`) stops only the process in this runtime folder's `server.pid`, after checking its creation time so that a reused PID is never stopped: first with `POST /api/shutdown` and the token from the PID file, then by ending the process. A running batch is not interrupted unless `-Force` is given. Other programs that use the port are never touched. An out-of-date PID file is removed; one whose process cannot be verified is kept and reported.

| Exit code | `Start.ps1` / `Start.bat` / `start.sh` | `Stop.ps1` / `stop.sh` |
| :--- | :--- | :--- |
| 0 | Ready, or already running | Stopped, or not running |
| 3 | `settings.json` cannot be used | – |
| 4 | The port is used by another program or installation | – |
| 5 | The backend exited while starting | – |
| 6 | Not ready in time (it was stopped) | – |
| 7 | – | A batch is running (use `-Force`) |
| 8 | – | The backend could not be stopped |
| 10 | Python 3.10+ not found (`Start.bat`: PowerShell 7 not found) | – |
| 11 | `.venv` cannot be created or does not run | – |
| 12 | The Python packages cannot be installed | – |
| 13 | Administrator rights were not granted (Windows) | – |
| 14 | The administrator window reported no result (Windows) | – |
| 15 | `start.sh --service`: the systemd service cannot be installed or started | – |

**Linux** (`start.sh`, `stop.sh`) uses the same launcher without elevation. `start.sh` creates `.venv` (through `uv` when the system Python has no `venv` module), installs the packages the same way, takes `--port`, `--timeout` and `--open` (no browser by default: a headless host may only have a text browser) and returns the same exit codes. `--service` writes the systemd user unit `game-companion-local.service`, which runs `python -m server` in the foreground with the current `GCL_HOME` and `Restart=on-failure` except for exit codes 2 and 3, then starts the backend through it; with lingering on, it starts with the machine. `stop.sh [--force]` is `launcher stop`, so a service backend stops cleanly and stays stopped. The backend leaves on `SIGTERM` the way it does on `POST /api/shutdown`, so `systemctl --user stop` also restores tool settings. A Linux host plans and reads Miyoushe data only: `tools.automation()` is false there, so runs, schedule slots and the logon task are refused with a message, and the dashboard says so instead of offering them.

After a failure `Start.bat` waits for a key when it was opened by double-click; set `GCL_NO_PAUSE=1` to never wait. The backend itself (`python -m server`) exits with 1 (startup exception), 2 (cannot listen on the address) or 3 (invalid settings) and records the reason in `startup-error.json` and `logs/app.log`. The logon task starts it that way, with `GCL_HOME` set when the runtime folder is not the default.

---

## 8. Frontend

`web/` is plain HTML, CSS and JavaScript served by the backend; there is no build step and no external request (no web fonts, no CDN images).

- **Visual system**: neutral surfaces (light gray page, white panels, dark text, 1px gray borders, dark primary buttons), light / dark / system themes as separate token sets, text at 20 / 16 / 14px with weights 400 / 700, 6px control and 8px group radii. Color only explains a state (always with an icon and a label) or a material category (pale tint plus a narrow edge: experience, convertible family, ZZZ core-skill material).
- **Information order**: summary first (what runs next, planned spend, status), then the control that changes it (Target settings, pause, order, Adjust links), then evidence behind a Details disclosure (per-tier quantities, conversion, the planner's reasoning).
- **Stamina track**: Today draws the next 48 hours per game from the forecast: natural recovery up to the cap, a drop at each planned batch (and the ZZZ coffee as a jump). A crosshair reads any time; batch markers open the same details on hover and keyboard focus. The Schedule page is its text equivalent, and the summary under it uses the same forecast numbers.
- **Images**: circular character portraits, material icons and Drive Disc set icons come only from `/assets/…` and only when `/api/state.assets` lists them; otherwise a text fallback is drawn, so a missing image never causes a request.
- **Refresh without loss**: `/api/state` is polled every 5 s. Re-renders keep open details, keyboard focus and busy buttons; dialogs and the settings form are not redrawn while they hold a draft; a late older response is discarded; after a write the confirmation appears only once the fresh state is drawn, and "saved but not reloaded" is reported separately.

## 9. Internationalization

- English is the base language; Simplified Chinese is the translation.
- Frontend: `I18N.en` / `I18N.zh` in `web/app.js` must have identical keys (tested). The choice is kept in `localStorage` and sent to the backend with `POST /api/lang`.
- Backend: `server/i18n.py` maps each key to `(English, Chinese)` with identical `str.format` placeholders (tested). Text is produced in the language active at the time, so stored run summaries keep their original language.
- Game data is not translated: material, domain and mission names come from the CN servers and the tools' Chinese catalogs, and tool identifiers (task names, log lines, config values) must stay exactly as the tools write them. They are commented in English where they appear.
- Use the official in-game English terms (Original Resin, Battery Charge, Domain of Blessing, Area Patrol, Combat Simulation, Expert Challenge, Miyoushe for 米游社) and the official Chinese terms.

---

## 10. Extension Guides

### Adding a backend message
1. Add `'key': ('English text {name}', '中文 {name}')` to `server/i18n.py`.
2. Use `tr('key', name=value)`; run the tests (they check placeholders and unknown keys).

### Adding a notification channel
1. Add the channel to `notify.CHANNELS` and `core.DEFAULTS['notify']['channels']`.
2. Implement delivery in `notify.send()` (raise `ValueError(tr(...))` with a readable reason on failure); secrets go in `core.SECRET_FIELDS`.
3. Add the settings controls and their `I18N.en` / `I18N.zh` keys in `web/app.js`.

### Adding an API endpoint
1. Read-only: add a path to `Handler.do_GET`. Mutations: add it to `Handler.route` (POST, `X-GC` and LAN checks already apply).
2. Raise `ValueError` for user errors; it becomes a 400 with the message.

### Updating datasets
`server/datasets/*.json` are generated snapshots (see each file's `source`, `source_url` and `at`). Regenerate them from those sources rather than editing by hand; material ids and Chinese names must match the official calculator. `genshin_artifact_domains.json` lists the 22 Domains of Blessing with the 5-star sets each drops, built from genshin-db (ChineseSimplified domains at their highest tier, and artifacts for set ids), keeping the domains BetterGI's `tp.json` lists under the same names. `zzz_disc_stages.json` lists the 15 Area Patrol stages and the two sets each drops, built from OneDragon's `compendium_data.yml` (`mission_type_name_display`) with suit ids from Enka's `store/zzz/equipments.json`; it is only the fallback for hosts without OneDragon.

---

## 11. Invariants for Contributors and AI Agents

1. **No personal data in the repository**: no real names, UIDs, account names, usernames, home-folder paths, host or tailnet names, IP addresses or e-mail addresses. Put terms you want guarded in the git-ignored `tests/pii_denylist.txt`; the smoke test also scans for generic patterns.
2. **Never treat an unread stamina value as 0**: UNKNOWN is `None` end to end.
3. **Never change a tool config outside the patch journal**: journal first, then write; always restore.
4. **English base language**: comments, logs and new strings in English; every UI string in both `I18N.en` and `I18N.zh`, every backend message in `server/i18n.py`.
5. **PowerShell 7 only** (`C:\Program Files\PowerShell\7\pwsh.exe`), never Windows PowerShell 5.1.
6. **Runtime data stays local**: never commit `data/`.
7. **Runs need Windows**: code that starts or stops tools, games or Windows services checks `tools.automation()` first; a Linux host plans and reads data only.
8. **Only the characters the user selected are requested in detail**: equipment comes with the goal's own sync. ZZZ discs ride in the upgrade-guide answer already read for levels; Genshin artifacts need Miyoushe's character detail, requested with that goal's character id only (never the whole roster), not again within 60 s of the last read, and backed off like the other sources after a failure or captcha (`health:detail`). A failed equipment read never stops the level read.
9. **No request without a user action or a scheduled job**: opening a page never calls the official API or downloads images; images are saved once from responses the app already requested. ZZZ portraits are the one derived address: the upgrade guide returns no `role_square_url`, so `mihoyo.zzz_portrait` uses the official square avatar (`act-webstatic.mihoyo.com/game_record/zzzv2/role_square_avatar/role_square_avatar_<id>.png`) of an agent id such a response named.

---

## 12. Verification

```powershell
python -m unittest tests.test_smoke tests.test_launcher tests.test_gear tests.test_auth tests.test_widget   # imports, launcher, gear, shared login and widgets; use an isolated GCL_HOME before imports
python -m server                                          # run in the foreground
python -m server.launcher status                          # address, runtime folder and PID, as Start and Stop see them
Invoke-RestMethod http://127.0.0.1:18800/api/health
```
