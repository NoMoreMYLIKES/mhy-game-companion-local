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
- **Runs**: run now, or use the built-in schedule (off by default; 05:00 and 18:00) with catch-up after missed slots. Optionally start at Windows logon, and mute audio during morning runs.
- **Free dailies**: Genshin Mail, Serenitea Pot and Daily Commission Rewards; OneDragon dailies, Engagement and New Eridu City Fund rewards.
- **Notifications**: one summary per batch through Windows toast, Telegram, a webhook or a JSON relay.
- **Bilingual, light and dark**: English and Simplified Chinese (`EN / 中文` in the header); System, Light or Dark theme.
- **Game images**: character portraits and material icons are saved locally the first time the official API returns them; the dashboard never downloads images itself.
- **Privacy**: listens on `127.0.0.1` only by default, and LAN access requires a password. Credentials are encrypted with Windows DPAPI.

## Requirements

- Windows 10 / 11 (64-bit), [PowerShell 7](https://github.com/PowerShell/PowerShell), Python 3.10+
- Installed locally (not part of this repository):
  - Genshin Impact: [BetterGI](https://github.com/babalae/better-genshin-impact)
  - Zenless Zone Zero: [ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon), as an extracted release in a path without spaces
- A CN-server account, signed in by scanning a QR code with the Miyoushe app

## Quick Start

1. Double-click `Start.bat`. It asks for administrator rights, because automation needs them to control the game window. The first run creates `.venv` and installs the dependencies, then the dashboard opens at `http://127.0.0.1:18800/`.
2. In **Settings**:
   - Scan the login QR code.
   - Check **Tools & Paths**. A BetterGI One Dragon template is optional: leave it empty to use the bundled morning template.
   - Turn on the schedule if you want one.
3. In **Goals**, add characters and set their order.

To stop the backend, run `./Stop.ps1` in PowerShell 7.

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
- **执行**：可立即执行，或使用内置定时（默认关闭，05:00 与 18:00），错过时段可在限定时间内补跑；可选开机登录自启、早间批次自动静音。
- **免费日常**：原神领取邮件、尘歌壶奖励、每日委托奖励；绝区零一条龙日常、活跃度与丽都城募奖励。
- **通知**：每批一条摘要，可通过 Windows 气泡通知、Telegram、Webhook 或 JSON 中转服务发送。
- **双语与深浅色**：英文与简体中文（页面顶部 `EN / 中文` 切换）；主题可选跟随系统、浅色或深色。
- **游戏图片**：角色头像与材料图标在官方接口首次返回时保存到本地，控制台页面本身不会下载图片。
- **隐私**：默认只监听 `127.0.0.1`，局域网访问必须设置密码；凭据使用 Windows DPAPI 加密保存。

## 环境要求

- Windows 10 / 11（64 位）、[PowerShell 7](https://github.com/PowerShell/PowerShell)、Python 3.10+
- 需在本机自行安装（本仓库不包含）：
  - 原神：[BetterGI](https://github.com/babalae/better-genshin-impact)
  - 绝区零：[ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)（解压后的发行版，路径中不要有空格）
- 国服账号，使用米游社 App 扫码登录

## 快速开始

1. 双击 `Start.bat`。程序会请求管理员权限（自动化操作游戏窗口需要）。首次运行会创建 `.venv` 并安装依赖，随后自动打开控制台 `http://127.0.0.1:18800/`。
2. 在 **设置** 中：
   - 扫码登录。
   - 检查 **工具与路径**。BetterGI 一条龙模板配置为可选，留空即使用内置的早间模板。
   - 按需开启定时。
3. 在 **培养** 中添加角色并调整顺序。

停止后台：在 PowerShell 7 中执行 `./Stop.ps1`。

## 文档

- [PLAN.md](PLAN.md)：愿景、四大模块与路线图（英文）
- [ARCHITECTURE.md](ARCHITECTURE.md)：模块、数据模型、HTTP API、工具集成与贡献规范（英文）。可选的一条龙实读电量适配见 [第 6.2 节](ARCHITECTURE.md#62-zenlesszonezero-onedragon)。

## 免责声明

本项目为个人自动化与养成规划工具，与 HoYoverse / 米哈游及 BetterGI、一条龙的作者均无关联。游戏自动化可能违反相应游戏的服务条款，请自行承担使用风险。

</details>
