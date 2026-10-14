# Game Companion Local

Stamina planning and farming automation for *Genshin Impact* and *Zenless Zone Zero* on a single Windows PC.
原神 / 绝区零 本地养成规划与体力自动化（养成中枢 · 本地版）。

<details open>
<summary><b>English</b></summary>

## Overview

Game Companion Local turns cultivation goals into daily farming runs. It reads your material gaps and stamina from Miyoushe (米游社). It decides which single material each batch should farm and why. Then it drives [BetterGI](https://github.com/babalae/better-genshin-impact) and [ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) to do the run, and restores their settings afterwards.

## Design

Standalone, single-machine architecture inspired by SillyTavern. A launch script starts the backend quietly in the background with no console window left open. Everything is controlled from a web dashboard built in the International Typographic Style (Swiss Style).

The planner follows four rules:

- **One material per batch** until it is collected.
- **Goal materials first**. Artifacts and Drive Discs are farmed only when nothing else is left, and only up to a cap you set.
- **In-game stamina decides**. A value that could not be read is *unknown*, never 0.
- **Tool settings are always restored**. Every change to a BetterGI or OneDragon config is recorded first and put back after the run, even after a crash.

## Features

- **Goals**: targets per character (level, talents / skills, weapon or W-Engine). Material gaps come from the official Enhancement Progression Calculator, and you set the order.
- **Plan and forecast**: the dashboard shows what the next batch will farm and why, with a 48-hour stamina chart per game. A 3-day forecast uses the same rule.
- **Drive Discs and Artifacts**: the equipped gear of each goal's character is read at its sync (only the characters you added) and scored against the build Miyoushe recommends for it, or your own picks there: every substat roll that counts, against the best a piece could hold, with wasted upgrades shown. Give a character an equipment target (score, sets, main stats, adjustable substat weights) and Drive Disc or Artifact farming goes to the first unfinished character, on the Area Patrol stage or Domain of Blessing that drops the set it still needs, until the target is met or your cap is reached.
- **Runs**: run now, or use the built-in schedule (off by default; 05:00 and 18:00) with catch-up after missed slots. Optionally start at Windows logon, and mute audio during morning runs.
- **Free dailies**: Genshin Mail, Serenitea Pot and Daily Commission Rewards; OneDragon dailies, Engagement and New Eridu City Fund rewards.
- **Notifications**: one summary per batch through Windows toast, Telegram, a webhook or a JSON relay.
- **Captcha**: when Miyoushe asks for human verification (1034), **Verify** on the dashboard shows its captcha; once you solve it, the notes are read again.
- **One shared login**: scan once with Miyoushe to connect both games. The app derives the credentials for character and cultivation data, and reads resin and battery through the official widgets. Manage or renew this login under Settings → Account; signing out clears it for both games. Existing widget authorization can be upgraded without another scan.
- **Bilingual, light and dark**: English and Simplified Chinese (`EN / 中文` in the header); System, Light or Dark theme.
- **Game images**: character portraits, material icons and Drive Disc / Artifact set icons are saved locally the first time the official API returns them; the dashboard never downloads images itself.
- **Privacy**: listens on `127.0.0.1` only by default, and LAN access requires a password. Credentials are encrypted with Windows DPAPI (on Linux: files only your user can read).

## Requirements

- Windows 10 / 11 (64-bit), [PowerShell 7](https://github.com/PowerShell/PowerShell), Python 3.10+
- Installed locally (not part of this repository):
  - Genshin Impact: [BetterGI](https://github.com/babalae/better-genshin-impact)
  - Zenless Zone Zero: [ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon), as an extracted release in a path without spaces
- A CN-server account, signed in by scanning a QR code with the Miyoushe app
- Optional: a Linux machine (Python 3.10+, bash; systemd to keep it running) to host the dashboard, planning and Miyoushe data. Runs still need the Windows PC; see [Linux](#linux) below.

## Quick Start

1. Double-click `Start.bat`. It asks for administrator rights, because automation needs them to control the game window. The first run creates `.venv` and installs the dependencies, then the dashboard opens at `http://127.0.0.1:18800/`.
2. In **Settings**:
   - Scan the login QR code once for both games and all data sources.
   - Check **Tools & Paths**. A BetterGI One Dragon template is optional: leave it empty to use the bundled morning template.
   - Turn on the schedule if you want one.
3. In **Goals**, add characters and set their order.

To stop the backend, run `./Stop.ps1` in PowerShell 7. It stops only this installation's backend and refuses while a batch runs; `./Stop.ps1 -Force` stops the batch first and restores the tool settings.

If the backend cannot start, the window says why and stays open. A common cause is another program using port 18800: `Start.bat -Port 18810` uses another port and saves it for this installation. Exit codes and details are in [ARCHITECTURE.md section 7.1](ARCHITECTURE.md#71-starting-and-stopping).

### Linux

The backend also runs on Linux, for example on a home server or a VPS, to plan and read Miyoushe data around the clock. Runs need Windows: BetterGI, OneDragon and the games are Windows programs, so the dashboard there offers no Run buttons.

- `./start.sh` sets up `.venv` and starts the backend in the background at `http://127.0.0.1:18800/`. `./start.sh --port 18810` uses another port.
- `./start.sh --service` runs it as a systemd user service that restarts after a crash. After `sudo loginctl enable-linger $USER` it also starts with the machine.
- `./stop.sh` stops it.

It listens on `127.0.0.1` only. From another computer, open it through an SSH tunnel (`ssh -N -L 18800:127.0.0.1:18800 you@server`, then `http://127.0.0.1:18800/`). Linux has no DPAPI, so credentials are stored in files only your user can read.

Legacy website-only sessions can encounter verification refusals such as 10306 or -1. Choose **Complete account connection** in Settings to use the shared app login and official stamina widgets for both games. Existing app authorization is reused. Login and each data source have separate success states: authorization does not guarantee that every official API is available, and an expired or revoked login may need renewal.

## Documentation

- [PLAN.md](PLAN.md): vision, the four pillars and the roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md): modules, data model, HTTP API, tool integration, and rules for contributors. The optional OneDragon live Battery Charge adapter is described in [section 6.2](ARCHITECTURE.md#62-zenlesszonezero-onedragon).

## Disclaimer

This is a personal automation and planning project. It is not affiliated with HoYoverse / miHoYo or with the authors of BetterGI or OneDragon. Automating games may conflict with their Terms of Service; use it at your own risk.

</details>

<details>
<summary><b>简体中文</b></summary>

## 简介

养成中枢 · 本地版把养成目标变成每天的刷取批次：从米游社读取材料缺口与体力，决定每批只刷哪一种材料并说明原因，然后驱动 [BetterGI](https://github.com/babalae/better-genshin-impact) 与 [绝区零一条龙（ZenlessZoneZero-OneDragon）](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) 完成刷取，结束后恢复它们的原有配置。

## 设计

参考 SillyTavern 的单机架构：启动脚本在后台静默运行服务，不留控制台窗口；所有操作都在采用国际主义排版风格（Swiss Style）的网页控制台中完成。

规划遵循四条原则：

- **每批只刷一种材料**，收齐后再换下一种。
- **定量材料优先**：只有没有其他可刷材料时，才在你设定的累计上限内接续刷圣遗物或驱动盘。
- **以游戏内体力为准**：未读到的数值记为“未知”，绝不当作 0。
- **工具配置必定还原**：对 BetterGI / 一条龙配置的每处修改都先记录、运行后还原，即使后台异常退出也会在下次启动时恢复。

## 功能

- **养成目标**：按角色设定等级、天赋/技能、武器/音擎目标；材料缺口来自官方养成计算器；顺序由你决定。
- **计划与预测**：控制台显示下一批刷什么、为什么，并为每款游戏绘制未来 48 小时的体力曲线；未来三天的预测使用同一规则。
- **驱动盘与圣遗物**：同步培养目标时读取该角色已装备的驱动盘或圣遗物（只读取你添加的角色），按米游社为其推荐的属性（或你在米游社的自选属性）评分：统计每次计入的副属性强化，与理论最佳相比，并标出未命中的强化。为角色设定装备目标（评分、套装、主属性、可调整的副属性权重）后，刷取会按顺序交给第一个未达标的角色，自动选择掉落其所缺套装的区域巡防关卡或祝圣秘境，直到达成目标或达到你设定的上限。
- **执行**：可立即执行，或使用内置定时（默认关闭，05:00 与 18:00），错过时段可在限定时间内补跑；可选开机登录自启、早间批次自动静音。
- **免费日常**：原神领取邮件、尘歌壶奖励、每日委托奖励；绝区零一条龙日常、活跃度与丽都城募奖励。
- **通知**：每批一条摘要，可通过 Windows 气泡通知、Telegram、Webhook 或 JSON 中转服务发送。
- **人机验证**：米游社要求人机验证（1034）时，在控制台点击 **验证** 即可显示其验证码；完成后会重新读取便笺。
- **一次扫码，全项目共用**：米游社扫码一次即可连接原神和绝区零，自动取得角色与培养数据所需凭据，树脂和电量使用官方小组件读取。在“设置 → 账号与连接”统一管理或更新登录，退出后两个游戏同时退出。已有小组件授权可直接升级，无需再扫码。
- **双语与深浅色**：英文与简体中文（页面顶部 `EN / 中文` 切换）；主题可选跟随系统、浅色或深色。
- **游戏图片**：角色头像、材料图标与驱动盘、圣遗物套装图标在官方接口首次返回时保存到本地，控制台页面本身不会下载图片。
- **隐私**：默认只监听 `127.0.0.1`，局域网访问必须设置密码；凭据使用 Windows DPAPI 加密保存（Linux 上为仅当前用户可读的文件）。

## 环境要求

- Windows 10 / 11（64 位）、[PowerShell 7](https://github.com/PowerShell/PowerShell)、Python 3.10+
- 需在本机自行安装（本仓库不包含）：
  - 原神：[BetterGI](https://github.com/babalae/better-genshin-impact)
  - 绝区零：[ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)（解压后的发行版，路径中不要有空格）
- 国服账号，使用米游社 App 扫码登录
- 可选：一台 Linux 机器（Python 3.10+、bash；常驻运行需 systemd），用于承载控制台、规划与米游社数据。执行仍需 Windows 电脑，见下方 Linux 一节。

## 快速开始

1. 双击 `Start.bat`。程序会请求管理员权限（自动化操作游戏窗口需要）。首次运行会创建 `.venv` 并安装依赖，随后自动打开控制台 `http://127.0.0.1:18800/`。
2. 在 **设置** 中：
   - 扫码登录。
   - 检查 **工具与路径**。BetterGI 一条龙模板配置为可选，留空即使用内置的早间模板。
   - 按需开启定时。
3. 在 **培养** 中添加角色并调整顺序。

停止后台：在 PowerShell 7 中执行 `./Stop.ps1`。它只停止本安装的后台，有批次正在执行时会拒绝；`./Stop.ps1 -Force` 会先停止批次并还原工具配置。

如果后台无法启动，窗口会说明原因并保持打开。常见原因是端口 18800 被其他程序占用：执行 `Start.bat -Port 18810` 即改用其他端口，并为本安装保存。退出码与细节见 [ARCHITECTURE.md 第 7.1 节](ARCHITECTURE.md#71-starting-and-stopping)（英文）。

### Linux

后台也可以运行在 Linux 上（例如家用服务器或 VPS），全天进行规划并读取米游社数据。执行需要 Windows：BetterGI、一条龙与游戏都是 Windows 程序，因此 Linux 上的控制台不提供执行按钮。

- `./start.sh` 会创建 `.venv` 并在后台启动服务，地址为 `http://127.0.0.1:18800/`；`./start.sh --port 18810` 改用其他端口。
- `./start.sh --service` 以 systemd 用户服务运行，异常退出后会自动重启；执行一次 `sudo loginctl enable-linger $USER` 后还会随系统启动。
- `./stop.sh` 停止服务。

服务只监听 `127.0.0.1`。从其他电脑访问时请使用 SSH 隧道（`ssh -N -L 18800:127.0.0.1:18800 用户名@服务器`，然后打开 `http://127.0.0.1:18800/`）。Linux 没有 DPAPI，凭据保存在仅当前用户可读的文件中。

旧版仅网页登录的会话可能遇到 10306、-1 等验证拒绝。请在设置中选择 **完善账号连接**，统一使用 App 授权和两个游戏的官方体力小组件；已有 App 授权会自动复用。登录和各数据源分别报告状态：授权成功不代表所有官方接口始终可用，授权过期或被撤销后仍可能需要重新登录。

## 文档

- [PLAN.md](PLAN.md)：愿景、四大模块与路线图（英文）
- [ARCHITECTURE.md](ARCHITECTURE.md)：模块、数据模型、HTTP API、工具集成与贡献规范（英文）。可选的一条龙实读电量适配见 [第 6.2 节](ARCHITECTURE.md#62-zenlesszonezero-onedragon)。

## 免责声明

本项目为个人自动化与养成规划工具，与 HoYoverse / 米哈游及 BetterGI、一条龙的作者均无关联。游戏自动化可能违反相应游戏的服务条款，请自行承担使用风险。

</details>
