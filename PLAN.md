# Game Companion Local — Architecture & Implementation Plan

> **Core Philosophy**: Transform cultivation and stamina management into a streamlined, standalone Windows local application inspired by the **SillyTavern** architecture: a single launch script starts a headless background daemon, operating silently with an accessible browser interface, retaining strictly core functions, and presented in the **Swiss Style (International Typographic Style)**.

---

## 1. System Vision & Architecture Paradigm

### 1.1 The "SillyTavern" Inspiration
Instead of a multi-machine setup (a remote relay server, external databases, cross-network synchronization, and scattered local runners), **Game Companion Local** consolidates all responsibilities into a single self-contained desktop application on Windows:
- **Single-Script Startup (`Start.bat` / `Start.ps1`)**: Sets up the virtual environment and its dependencies, starts the backend in the background without leaving a console window open, waits until it answers, explains any failure with a nonzero exit code, and opens the dashboard in the default browser.
- **Headless Background Daemon**: Runs in the background (started manually or by a single Windows Task Scheduler logon task) and evaluates schedule slots, stamina polling, goal sync and the notification outbox every 20 seconds.
- **Local Web Interface**: Standard browser access at `http://127.0.0.1:18800/` (the port is configurable) with loopback protection by default, and an optional LAN-access toggle secured with password authentication.
- **Clean Teardown (`Stop.ps1`)**: Stops only this installation's backend, identified by its PID file and process creation time; other programs on the same port are never touched.

---

## 2. The Four Core Pillars

The application is structured strictly around the four fundamental operational phases of cultivation and stamina automation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Game Companion Local Architecture                    │
└────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│  Pillar 1: Data & Material Engine    │       │  Pillar 2: Stamina Plan Compilation  │
│  - Miyoushe gap & stamina widgets    │ ────► │  - Single material per batch rule    │
│  - Offline item family tree pooling  │       │  - Live in-game stamina ground truth │
│  - SEELIE drop rates & domain days   │       │  - Quantitative goals before equip   │
│  - User-controlled goal parameters   │       │  - User queue priority stability     │
└──────────────────────────────────────┘       └──────────────────────────────────────┘
                                                                   │
                                                                   ▼
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│  Pillar 4: Receipt & State Sync      │       │  Pillar 3: Local Tool Orchestration  │
│  - Tool log & counter receipts       │ ◄──── │  - BetterGI / OneDragon integration  │
│  - Executed unit bookkeeping         │       │  - Plan to config injection          │
│  - Plan reconciliation & next queue  │       │  - Non-destructive Patch Journaling  │
│  - Single aggregated notification    │       │  - Windows COM audio muting interop  │
└──────────────────────────────────────┘       └──────────────────────────────────────┘
```

---

### Pillar 1: Data Acquisition & Material Computation
- **Miyoushe (米游社) & In-Game Roster Sync**:
  - QR login with the Miyoushe app (CN-server accounts). The app grant and the website cookies derived from it are DPAPI-encrypted and used for the official stamina widgets and the official Enhancement Progression Calculator.
  - Zero plaintext credential leakage: secrets are bound to the local Windows user profile.
- **Integrated Material Knowledge Base**:
  - Offline datasets (`server/datasets/genshin.json`, `server/datasets/zzz.json`) with characters, weapons, materials and domain weekdays (sources: genshin-db, Hakushin, SEELIE).
  - Material family pooling: tiers of one series (e.g. Teachings → Guide → Philosophies, or Basic → Advanced → Specialized chips) are pooled with the 3:1 crafting ratio.
  - Expected yields use SEELIE's published top-difficulty drop rates; they are planning estimates only and never count as inventory.
- **User-Defined Cultivation Goals**:
  - Explicit target milestones for character level, weapon level, individual skill ranks, and core enhancements.
  - Granular control: ability to pause, resume, reorder, or cancel individual items directly from the UI.

---

### Pillar 2: Stamina Plan Compilation & Decision Engine
The planning engine translates raw deficits into executable decisions using deterministic rules:
- **One Material per Batch**:
  - Focuses on a single quantitative bottleneck item until requirements are collected. Avoids splitting precious daily stamina across multiple domains.
- **Live In-Game Energy as Ground Truth**:
  - The automation tool reads the real stamina in game and stops when it runs out, so the issued count is an upper bound. Miyoushe's stamina widgets and the optional OneDragon live Battery Charge adapter only refine the estimate.
  - A missing reading is recorded as `UNKNOWN`, never guessed or defaulted to `0`.
- **Quantitative Priorities Precede Equipment Farming**:
  - Talent, ascension and weapon materials come before open-ended equipment farming (Artifacts / Drive Discs).
  - Once no goal material is farmable, the optional equipment continuation runs the configured Domain of Blessing / Area Patrol mission within a cumulative cap.
- **Absolute User Control Over Queues**:
  - Goal order and per-goal category order (level / talents / weapon) are set by the user on the dashboard. No algorithmic reshuffling or hidden overrides.
  - When nothing is farmable, stamina is kept and only free daily routines run (Mail, Serenitea Pot, Daily Commission Rewards; OneDragon dailies, Engagement and City Fund rewards).

---

### Pillar 3: Local Tool Orchestration & Instruction Translation
Translates high-level farming targets into native commands and configuration patches for local automation tools:
- **Local Tools (required, installed separately)**:
  - [BetterGI](https://github.com/babalae/better-genshin-impact) for Genshin and [ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) for ZZZ. Their folders are configured in settings; game paths are read from the tools' own configs.
- **Non-Destructive Configuration Patching**:
  - Before a run, the daemon writes a generated BetterGI One Dragon profile and patches the specific OneDragon / BetterGI config fields it needs.
  - **Patch Journaling**: The original value of every field it changes is saved to the SQLite journal *before* the file is written, so the journal survives a crash.
  - **Guaranteed Rollback**: Fields are restored after every batch (success, stop or error), and again at startup if the backend died mid-run.
- **Silent Early-Morning Operations**:
  - Scheduled morning slots mute the default playback device through PowerShell 7 CoreAudio COM interop and restore the previous mute state afterwards.

---

### Pillar 4: Receipt Collection & Plan State Reconciliation
- **Receipt Extraction**:
  - Genshin: counts 20 / 40 Original Resin claims in the BetterGI log written during the run. ZZZ: reads the per-row run counters of the generated OneDragon plan before restoring it.
  - Only units the tool actually completed are counted; anything not executed stays in the goal's allowance.
- **State Reconciliation**:
  - Executed units are added to the goal's stable list in SQLite. 60 s and 180 s after a run the goal is re-synced with the official calculator, which also picks up manual farming.
- **Aggregated Minimal Notifications**:
  - One consolidated summary per batch (optional quiet-on-success), plus failure, login-expired and goal-complete events.
  - Channels: Windows balloon toast, Telegram Bot API, a generic JSON relay, and a webhook, delivered through a retrying outbox.

---

## 3. Frontend Design

A calm, compact application for inspecting goals, understanding the next scheduled action and changing what affects it. From the International Typographic Style it keeps the grid, alignment and deliberate hierarchy, interpreted through these choices:

1. **Neutral surfaces with visible hierarchy**:
   - Light gray page, white panels, dark text, 1px gray borders and dark primary buttons; a matching dark theme, selectable as System / Light / Dark.
   - Color explains a state (with an icon and a label) or a material category (pale tint and a narrow edge); it is never decoration.
2. **Restrained typography**:
   - Local font stack (`Inter` when installed, `Segoe UI`, `Microsoft YaHei UI`, …); 20 / 16 / 14px at weights 400 / 700; tabular figures for counts that are compared.
3. **Summary, control, evidence**:
   - Each automatic choice shows what happens next, why, and where to change it; calculation details open on demand.
   - Recognizable game images (circular portraits, material icons) cached locally from official API responses, with text fallbacks.
3. **Bilingual Support with English as Base Language**:
   - English (`en`) serves as the core schema and default interface language (`<html lang="en">`).
   - Symmetrical, 1:1 mapped Chinese (`zh`) dictionary provides full native localization.
   - Instant header toggle (`EN / 中文`) with persistent `localStorage` preference memory.
   - Labels go through the frontend `t()` layer; backend-generated text (plan reasons, errors, run summaries) goes through `server/i18n.py` and follows the same language setting.

---

## 4. Implementation Status & Progress Tracker

| Component | Status | Verification & Deliverables |
| :--- | :---: | :--- |
| **Pillar 1: Data & Materials** | **Completed** | Offline datasets for Genshin & ZZZ, DPAPI credential vault, material tier pooling. |
| **Pillar 2: Stamina Planner** | **Completed** | Deterministic planner: single material focus, live stamina priority, quantitative first, explicit user queues. |
| **Pillar 3: Tool Orchestration** | **Completed** | BetterGI / OneDragon config injection, persisted patch journal with rollback, PS7 COM mute interop. |
| **Pillar 4: Receipt & State** | **Completed** | Log / counter receipts, SQLite execution tracking, single-message batch notification outbox. |
| **UI & Internationalization** | **Completed** | Swiss Style dashboard, English base language, symmetric EN/ZH switching for UI and backend text. |
| **Security & Privacy** | **Completed** | 100% anonymized codebase, DPAPI encrypted storage, `.gitignore` isolation, zero personal leaks. |

---

## 5. Future Iterations & Roadmap

- [ ] **Windows System Tray Minimizer**: Optional lightweight notification tray applet providing quick status glances and one-click manual batch execution.
- [ ] **Interactive Desktop Toast Actions**: Actionable Windows notification toasts to pause or skip items directly from incoming alerts.
- [ ] **Automated Game Patch Presets**: Automated scraping and dataset update routines for new character releases and new material domains.
- [ ] **Receipt Discrepancy Diagnostics**: Compare executed units with the official gap after re-sync and flag runs whose drops diverge from the expected rates.
- [ ] **Per-item Drop Receipts**: Record actual drops per run (today only executed units and stamina claims are recorded).
- [ ] **Equipment Cleanup (opt-in)**: OneDragon's Drive Disc dismantle and BetterGI's after-domain artifact salvage destroy items by rarity only; offer them only as explicit, per-run choices, never by default.
- [ ] **Packaged OneDragon Live Battery Charge Adapter**: Publish the optional OneDragon adapter as a reviewed patch with an install step.

---

## 6. Detailed Technical Specifications

For in-depth module breakdowns, SQLite schemas, REST API contracts, tool interop details, and AI developer invariants, refer to the technical specification:
👉 **[ARCHITECTURE.md](ARCHITECTURE.md)**

