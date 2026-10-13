"""Backend message catalog: English is the base language, Chinese the translation.

Text is produced in the UI language selected at the time (``settings.ui.lang``),
so stored messages such as run summaries keep the language they were created in.
Game data (material, domain and task names) is not translated here: it comes from
the CN servers and the automation tools, and must match them exactly.
"""
from __future__ import annotations

LANGS = ('en', 'zh')

# key: (English, Chinese); placeholders use str.format names.
MESSAGES: dict[str, tuple[str, str]] = {
    # general
    'brand': ('Game Companion', '养成中枢'),
    'sep': (', ', '、'),
    'sep_strong': ('; ', '；'),
    'sentence': (' {text}.', '{text}。'),
    'game_line': ('{game}: {text}', '{game}：{text}'),
    'game_genshin': ('Genshin Impact', '原神'),
    'game_zzz': ('Zenless Zone Zero', '绝区零'),
    'stamina_genshin': ('Original Resin', '树脂'),
    'stamina_zzz': ('Battery Charge', '电量'),
    'unit_card': (' cards', '卡'),
    'unit_claim20': (' claims', '份'),
    'unit_boss': (' runs', '次'),
    'unit_zzz_boss': (' runs', '次'),
    'unit_disc': (' runs', '次'),
    'weekday_names': ('Mon,Tue,Wed,Thu,Fri,Sat,Sun', '一,二,三,四,五,六,日'),
    'every_day': ('Daily', '每天'),
    'on_days': ('{days}', '周{days}'),
    'unknown': ('unknown', '未知'),
    'not_configured': ('not configured', '未配置'),
    'tool_onedragon': ('OneDragon', '一条龙'),

    # settings validation
    'bad_times': ('Schedule times must use the HH:MM format', '执行时间格式应为 HH:MM'),
    'bad_port': ('Invalid port', '端口无效'),
    'bad_lan': ('LAN access must be true or false', '局域网访问只能为 true 或 false'),
    'bad_if_running': ('Invalid action for an already running game', '游戏已运行时的处理方式无效'),
    'bad_claim_mode': ('Invalid Genshin claim mode', '原神领奖方式无效'),
    'bad_timeout': ('The per-game timeout must be 10–480 minutes', '单游戏超时应在 10–480 分钟'),
    'bad_game': ('Invalid game selection', '游戏选择无效'),
    'bad_cap': ('A cumulative cap cannot be negative', '累计上限不能为负数'),
    'bad_lang': ('Invalid language', '语言无效'),
    'dpapi_failed': ('Windows credential encryption/decryption failed', 'Windows 凭据加密/解密失败'),

    # goals
    'out_of_range': ('{key} must be between {low} and {high}', '{key} 应在 {low}–{high}'),
    'invalid_game': ('Invalid game', '游戏无效'),
    'goal_exists': ('This character already has a goal.', '该角色已有培养目标。'),
    'goal_missing': ('Goal not found', '目标不存在'),
    'goal_done_title': ('{name}: all materials collected', '{name} 培养材料已齐'),
    'goal_done_body': ('You can level up in game now.', '可以在游戏内完成升级。'),

    # materials
    'note_enough': ('Enough', '已足够'),
    'note_no_route': ('No automatic route; obtain manually', '暂无自动路线，需手动获取'),
    'note_owned_unknown': ('Owned amount not read yet; scheduled after the next official sync',
                           '持有量未读取，等待官方同步后安排'),
    'note_domain': ('Official gap (after inventory and crafting) needs {claims} × 20 Original Resin reward claims '
                    'at SEELIE top-difficulty rates', '官方缺口（已扣库存与合成）按 SEELIE 最高难度期望折算 {claims} 份 20 树脂奖励'),
    'note_runs': ('{left} short; about {rate} per run makes {runs} runs', '缺 {left} 个，按每次约 {rate} 个估算 {runs} 次'),
    'note_series': ('Series short by {left} base-tier equivalents; SEELIE {rate} per card makes {cards} cards',
                    '整系列缺 {left} 基础档等价，按 SEELIE 每卡 {rate} 估算 {cards} 卡'),
    'note_exp': ('{left} × {name} short; SEELIE about {rate} EXP per card makes {cards} cards',
                 '缺 {left} 个{name}，按 SEELIE 每卡约 {rate} 经验估算 {cards} 卡'),
    'note_denny': ('{left} Dennies short; about {rate} per card makes {cards} cards', '缺 {left} 丁尼，按每卡约 {rate} 估算 {cards} 卡'),
    'note_no_rule': ('No conversion rule yet', '暂无换算规则'),
    'progress': ('{name}: need {need}, have {have}, short {left}', '{name} 需{need} 有{have} 缺{left}'),

    # planner
    'blk_done': ('Collected', '已收齐'),
    'blk_paused': ('Paused (resume on the Goals page)', '已暂停（培养页可恢复）'),
    'blk_closed': ('Not open today ({days})', '今天不开放（{days}）'),
    'blk_exhausted': ('This list is done; waiting for the official sync to correct inventory',
                      '本轮清单已执行完，等待官方同步校正库存'),
    'equip_artifact': ('Artifacts', '圣遗物'),
    'equip_disc': ('Drive Discs', '驱动盘'),
    'equip_off': ('{label} continuation is off (Settings → Farming rules)', '{label}接续未开启（设置 → 刷取规则）'),
    'equip_no_target': ('No {label} farming target selected (Settings → Farming rules)', '未选择{label}副本（设置 → 刷取规则）'),
    'equip_zero_cap': ('{label} cumulative cap is 0, so it is never farmed (Settings → Farming rules)',
                       '{label}累计上限为 0，不会自动刷（设置 → 刷取规则）'),
    'equip_cap_reached': ('{label} reached its cumulative cap of {cap}; raise the cap or reset usage in Settings',
                          '{label}已达累计上限 {cap}，可在设置提高上限或清零已用'),
    'equip_goal': ('{label} continuation', '{label}接续'),
    'equip_note': ('Cumulative cap {cap}, used {used}', '累计上限 {cap}，已用 {used}'),
    'source_forecast': ('Forecast', '预测'),
    'label_calc': ('Material calculation', '材料计算'),
    'calc_pending': ('Official material calculation not finished yet', '尚未完成官方材料计算'),
    'reason_idle': ('Nothing to farm; keeping {stamina}. Free daily tasks still run.',
                    '没有可执行的刷取项目，保留{stamina}；免费日常照常执行。'),
    'exp_unknown': ('stamina unknown, the in-game reading decides', '体力未知，由游戏实读决定'),
    'exp_known': ('about {value} {stamina} now, expect {expected}{unit}', '按当前约 {value} {stamina}预计 {expected}{unit}'),
    'lead_goal': ('Goal material: ', '定量材料：'),
    'lead_equip': ('No goal material to farm, continuing with: ', '当前无可执行定量材料，接续：'),
    'reason_plan': ('{lead}{goal} · {label} ({names}). Cap {upper}{unit} at {cost} {stamina} each; {exp}.',
                    '{lead}{goal} · {label}（{names}）。上限 {upper}{unit}（每{unit} {cost} {stamina}），{exp}。'),
    'daily_mail': ('Claim mail', '领取邮件'),
    'daily_teapot': ('Claim Serenitea Pot rewards', '领取尘歌壶奖励'),
    'daily_commission': ('Claim Daily Commission Rewards (Katheryne)', '领取每日委托奖励（凯瑟琳）'),
    'daily_onedragon': ('OneDragon native dailies (as enabled in OneDragon)', '一条龙原生日常（按一条龙中的启用项）'),
    'daily_zzz_rewards': ('Claim Engagement and New Eridu City Fund rewards after farming', '刷后领取活跃度与丽都城募奖励'),

    # runner
    'status_SUCCESS': ('Done', '完成'),
    'status_PARTIAL': ('Partial', '部分完成'),
    'status_FAILED': ('Failed', '失败'),
    'status_SKIPPED': ('Skipped', '跳过'),
    'status_STOPPED': ('Stopped', '已停止'),
    'slot_manual': ('manual', '手动'),
    'batch_title': ('Game Companion {slot} · {status}', '养成中枢 {slot} · {status}'),
    'select_game': ('Select at least one game.', '请选择至少一个游戏。'),
    'batch_running': ('A batch is already running.', '已有批次正在执行。'),
    'restore_pending': ('Tool configs from the last run are not restored yet: {errors}', '上次的工具配置尚未恢复：{errors}'),
    'stage_prepare': ('Preparing', '准备'),
    'stage_stopping': ('Stopping', '正在停止'),
    'stage_config': ('Writing tool config', '写入工具配置'),
    'stage_launch': ('Launching game', '启动游戏'),
    'stage_running': ('Automation running', '自动化运行中'),
    'stage_collect': ('Collecting results and restoring configs', '收集结果并恢复配置'),
    'mute_failed': ('Mute did not take effect: {error}', '静音未生效：{error}'),
    'run_exception': ('Run failed with an exception: {error}', '执行异常：{error}'),
    'tool_missing': ('{tool} not found: {path}', '未找到{tool}程序：{path}'),
    'skip_game_running': ('The game is already running (someone may be playing); skipped as configured',
                          '游戏正在运行（可能有人在玩），按设置跳过本次'),
    'zzz_no_patch': ('OneDragon live Battery Charge adapter not installed: whole card batches are issued and the '
                     'last one may be skipped if Battery Charge runs short', '一条龙实读电量适配缺失：按整份卡数执行，最后一份可能因电量不足跳过'),
    'kill_failed': ('Failed to end process: {error}', '结束进程失败：{error}'),
    'extra_resin': ('Log shows other resin spending: {items}', '日志出现其他树脂消耗：{items}'),
    'amount_unverified': ('Completed amount pending verification', '完成量待核验'),
    'source_onedragon': ('OneDragon live reading', '一条龙实读'),
    'user_stopped': ('stopped by user', '用户停止'),
    'timed_out': ('exceeded the per-game time limit; processes ended', '超过单游戏时限，已结束进程'),
    'no_terminal': ('the tool never logged its completion marker', '未看到工具的结束标记'),
    'qty_unverified': ('amount pending verification', '数量待核验'),
    'summary_item': ('{goal} · {label} {amount} (cap {upper})', '{goal} · {label} {amount}（上限 {upper}）'),
    'summary_idle': ('Nothing to farm; free daily tasks only', '无刷取项目，只做免费日常'),
    'recovered_configs': ('Restored tool configs left by an interrupted run', '已恢复上次中断时的工具配置'),
    'recovered_mute': ('Restored the volume state from before muting', '已恢复静音前的音量状态'),
    'run_interrupted_note': ('The backend exited during execution; this batch was interrupted',
                             '后台在执行中退出，本批中断'),
    'run_interrupted': ('The last batch was interrupted mid-run', '上次批次在执行中中断'),

    # Miyoushe (米游社, the CN-server counterpart of HoYoLAB)
    'err_login_expired': ('Miyoushe login has expired; scan the QR code again in Settings.',
                          '米游社登录已失效，请在设置中重新扫码。'),
    'err_captcha': ('Miyoushe requires a captcha ({code}); retrying later. Runs still use the in-game stamina.',
                    '米游社要求人机验证（{code}），稍后自动重试；执行仍按游戏内体力进行。'),
    'err_private': ('Miyoushe data is private; enable Real-Time Notes and character details in the Miyoushe app.',
                    '米游社数据未公开，请在米游社开启实时便笺/角色数据。'),
    'err_network': ('Miyoushe request timed out or the network is unavailable.', '连接米游社超时或网络不可用。'),
    'err_api': ('Miyoushe request failed: {name}', '米游社接口未成功：{name}'),
    'err_code': (' ({code})', '（{code}）'),
    'qr_scan': ('Scan with the Miyoushe app and confirm the login.', '请用米游社 App 扫码并确认登录。'),
    'qr_no_cookies': ('Scan succeeded but no login credentials were returned.', '扫码成功但未返回登录凭据。'),
    'qr_confirmed': ('Logged in; reading game accounts.', '登录成功，正在读取游戏账号。'),
    'qr_done': ('Logged in.', '登录成功。'),
    'qr_scanned': ('Scanned; confirm on your phone.', '已扫码，请在手机上确认。'),
    'qr_expired': ('QR code expired; generate a new one.', '二维码已过期，请重新生成。'),
    'account_not_listed': ('This account is not in the Miyoushe account list.', '该账号不在米游社账号列表中。'),
    'login_expired_title': ('Miyoushe login expired', '米游社登录失效'),
    'not_logged_in': ('Not logged in or no account selected', '未登录或未选择账号'),
    'backing_off': ('Backing off after errors', '退避中'),
    'bad_notes': ('Unexpected stamina format in Real-Time Notes', '便笺体力格式异常'),
    'source_notes': ('Miyoushe Real-Time Notes', '米游社实时便笺'),
    'notes_ok': ('Official stamina read', '已读取官方体力'),
    'login_first': ('Log in and select an account for this game first.', '请先登录并选择该游戏账号。'),
    'char_not_owned': ('The official API did not return this character (maybe not owned yet).',
                       '官方未返回此角色（可能尚未拥有）。'),
    'weapon_needed': ('A weapon target needs the weapon read or entered first.', '武器培养需要先读取或填写武器。'),
    'wengine_needed': ('A W-Engine target needs a W-Engine equipped and synced first.', '音擎培养需要先装备音擎并同步。'),
    'calc_format': ('The official calculator response format has changed.', '官方养成计算返回格式已变化。'),

    # notifications
    'relay_missing': ('Relay URL not set', '未填写中转地址'),
    'relay_unconfirmed': ('The relay did not confirm delivery', '中转服务未确认投递'),
    'tg_missing': ('Bot Token or Chat ID not set', '未填写 Bot Token 或 Chat ID'),
    'tg_rejected': ('Telegram rejected the message: {reason}', 'Telegram 拒绝：{reason}'),
    'webhook_missing': ('Webhook URL not set', '未填写 Webhook 地址'),
    'unknown_channel': ('Unknown notification channel', '未知通知渠道'),
    'pwsh_missing': ('PowerShell 7 not found', '未找到 PowerShell 7'),
    'test_title': ('Game Companion test notification', '养成中枢 测试通知'),
    'test_body': ('If you can see this message, this notification channel works.', '如果你看到这条消息，说明该通知渠道可用。'),

    # scheduler
    'slot_before_enable': ('Slot passed before the schedule was enabled', '启用前的时段'),
    'slot_missed': ('Missed by more than {hours} h (PC off or backend not running)', '错过超过 {hours} 小时（电脑未开或后台未运行）'),
    'slot_failed_title': ('Game Companion {slot} failed to start', '养成中枢 {slot} 未能开始'),
    'autostart_failed': ('Failed to create the logon autostart task (admin rights required): {detail}',
                         '创建登录自启任务失败（需要管理员权限）：{detail}'),
    'autostart_windows': ('Start with Windows needs Windows Task Scheduler. On Linux, run ./start.sh --service.',
                          '开机登录自启依赖 Windows 任务计划程序。Linux 上请运行 ./start.sh --service。'),
    'runs_need_windows': ('Runs need Windows: BetterGI, OneDragon and the games are Windows programs. '
                          'This host plans and reads Miyoushe data only.',
                          '执行需要 Windows：BetterGI、一条龙与游戏都是 Windows 程序。此主机只做规划与米游社数据读取。'),

    # tools
    'patch_bad_structure': ('{file} has an unexpected structure; cannot write {field}', '{file} 结构异常，无法写入 {field}'),
    'restore_failed': ('Failed to restore {file}: {error}', '{file} 恢复失败：{error}'),
    'bgi_template_missing': ('BetterGI One Dragon template config "{name}" not found; enter an existing config name in '
                             'Settings, or leave it empty to use the bundled template.',
                             '未找到 BetterGI 一条龙模板配置「{name}」，请在设置中填写已存在的配置名，或留空使用内置模板。'),
    'zzz_charge_missing': ('OneDragon has no "体力刷本" (Battery Charge plan) task; check the task list in OneDragon first.',
                           '一条龙未找到「体力刷本」任务，请先在一条龙中确认任务列表。'),
    'plan_unreadable': ('Plan counters unreadable: {error}', '清单计数无法读取：{error}'),
    'plan_missing': ('Plan counters missing; completed amount pending verification', '清单计数缺失，完成量待核验'),
    'game_missing': ('Game executable not found: {path} (Settings → Paths)', '未找到游戏程序：{path}（设置 → 路径）'),
    'mute_pwsh_missing': ('PowerShell 7 not found; cannot control mute.', '未找到 PowerShell 7，无法控制静音。'),
    'mute_script_failed': ('Mute script failed', '静音脚本失败'),

    # web
    'lan_off': ('LAN access is not enabled', '局域网访问未开启'),
    'lan_no_password': ('LAN access needs an access password set on this PC first', '局域网访问需要先在本机设置访问密码'),
    'password_required': ('Password required', '需要密码'),
    'bad_origin': ('Invalid request origin', '请求来源无效'),
    'lan_needs_password': ('Set an access password before enabling LAN access.', '开启局域网访问前请先设置访问密码。'),
    'unknown_api': ('Unknown API endpoint', '未知接口'),
    'starting': ('The backend is still starting; try again in a moment.', '后台仍在启动，请稍后再试。'),
    'shutdown_mismatch': ('This stop request does not match the running instance.', '停止请求与正在运行的实例不符。'),
    'shutdown_busy': ('A batch is running. Stop it on the dashboard first, or stop with -Force.',
                      '有批次正在执行。请先在控制台停止，或使用 -Force 停止。'),
}


def lang() -> str:
    from . import core
    value = core.settings().get('ui', {}).get('lang')
    return value if value in LANGS else 'en'


def tr(key: str, /, **params) -> str:
    """Message ``key`` in the current UI language, formatted with ``params``."""
    text = MESSAGES[key][LANGS.index(lang())]
    return text.format(**params) if params else text
