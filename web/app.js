/* Game Companion Local — Frontend Application
   Base Language: English (en)
   Bilingual Support: English (base) & Chinese (zh)
   Follows International Typographic Style (Swiss Style).
*/

// ----------------------------------------------------------- i18n Dictionaries
const I18N = {
  en: {
    // Brand & Header
    brand_title: 'Game Companion',
    brand_edition: 'Local',
    connecting: 'Connecting to backend…',
    connect_failed: 'Failed to connect backend: {0}',
    current_date: 'Date: <b>{0} ({1})</b>',
    weekdays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    batch_running: '<span class="warn">● Batch in progress [{0}] · {1}</span>',
    schedule_on: '<span>Schedule: <b>ON</b> (Next: {0})</span>',
    schedule_off: '<span>Schedule: <b>OFF</b></span>',
    hoyolab_unlogged: '<span class="warn">Miyoushe not logged in</span>',

    // Navigation Tabs
    tab_today: 'Today',
    tab_goals: 'Goals',
    tab_plan: 'Schedule',
    tab_runs: 'Runs',
    tab_settings: 'Settings',

    // Today View
    batch_banner_title: 'Automation Batch Running',
    batch_banner_sub: 'Slot: {0} · Stage: {1} · Game: {2}',
    btn_stop: 'Stop Execution',
    btn_refresh: 'Refresh',
    stamina_source: 'Source',
    stamina_read_time: 'Read Time',
    rule_note_prefix: 'Rule: Farm one material per batch until collected; adjust goals in',
    rule_note_link: 'Goals',
    retain_stamina: 'Keeping {0}; nothing to farm',
    routine_helpers: 'Routine Tasks: {0}',
    routine_none: 'None',
    manual_execution: 'Manual Execution',
    manual_execution_desc: 'Immediately start execution with current rules. The backend automatically injects configurations, launches games, farms, and restores configurations safely.',
    btn_run_zzz: 'Run ZZZ Now',
    btn_run_genshin: 'Run Genshin Now',
    btn_run_both: 'Run Both Sequentially',
    unit_resin: 'Original Resin',
    unit_battery: 'Battery Charge',
    game_genshin: 'Genshin Impact',
    game_zzz: 'Zenless Zone Zero',

    // Goals View
    btn_add_goal: '+ Add {0} Goal',
    no_active_goals: 'No active goals for {0}. Click above to add.',
    goal_meta: 'Target: Lv.{0} · Talents/Core · Weapon Lv.{1} {2}',
    btn_sync_gap: 'Sync Gap',
    btn_cancel_goal: 'Cancel Goal',
    btn_restore_goal: 'Restore Goal',
    cat_order_label: 'Material Priority Order:',
    cat_level: 'Level',
    cat_talents: 'Talents / Skills',
    cat_weapon: 'Weapon / W-Engine',
    talent_normal_attack: 'Normal Attack',
    talent_skill: 'Elemental Skill',
    talent_burst: 'Elemental Burst',
    talent_basic: 'Basic Attack',
    talent_special: 'Special Attack',
    talent_chain: 'Chain Attack',
    talent_dodge: 'Dodge',
    talent_assist: 'Assist',
    talent_core: 'Core Skill',
    th_item_days: 'Item & Open Days',
    th_demand: 'Demand',
    th_executed: 'Executed',
    th_status: 'Status',
    th_action: 'Action',
    status_done: 'Collected',
    status_next: 'Next Batch ({0})',
    status_queued: 'Queued ({0})',
    btn_pause: 'Pause',
    btn_resume: 'Resume',
    btn_up: 'Up',
    btn_down: 'Down',
    edit_targets_summary: 'Edit Target Level / Skill Values',
    btn_save_recalc: 'Save & Recalculate',
    cancelled_goals_header: 'Cancelled / Inactive Goals ({0})',
    cancelled_goals_note: '(Data & history preserved)',
    modal_add_title: 'Add {0} Cultivation Goal',
    lbl_select_char: 'Select Character',
    btn_confirm_add: 'Confirm Add',
    btn_cancel: 'Cancel',

    // Schedule View
    schedule_forecast_title: 'Schedule Forecast (Next 3 Days)',
    schedule_rule_desc: 'Same rules as execution: one material at a time in order, live in-game stamina first, stamina kept when nothing is left to farm',
    th_time_slot: 'Time Slot',
    th_game: 'Game',
    th_est_stamina: 'Est. Stamina',
    th_planned_item: 'Planned Item',
    th_est_spend: 'Est. Spend',
    th_rule_note: 'Rule Details',
    routine_only: 'Daily Routines Only',
    no_forecast_rows: 'No upcoming slots or games selected.',

    // Runs View
    runs_title: 'Run Records',
    btn_refresh_runs: 'Refresh Records',
    th_started: 'Started At',
    th_status_col: 'Status',
    th_slot_source: 'Slot / Source',
    th_receipt_summary: 'Execution & Receipt Summary',
    th_ended: 'Ended At',
    no_runs: 'No run history found.',
    no_games_executed: 'No games executed',

    // Settings View
    sec_account: 'Miyoushe Account',
    btn_logout: 'Log Out',
    confirm_logout: 'Log out of Miyoushe?',
    not_bound: 'Not bound',
    qr_desc: 'Scan the QR code with the Miyoushe (米游社) app to sync material gaps and Real-Time Notes. CN-server accounts only. Credentials are encrypted with Windows DPAPI and never stored in plain text.',
    btn_gen_qr: 'Generate Login QR',
    qr_prompt: 'Scan with the Miyoushe app',
    sec_tools: 'Local Tool Status',
    chk_admin: 'Admin Privileges',
    chk_admin_ok: 'Granted',
    chk_admin_warn: 'Not elevated (Dashboard viewable, game execution needs elevation)',
    chk_bgi: 'BetterGI',
    chk_zzz: 'ZZZ OneDragon',
    chk_live_patch: 'Live Battery Charge adapter (optional): {0}',
    chk_found: 'Found',
    chk_missing: 'Not found',
    chk_installed: 'Installed',
    chk_game_clients: 'Game Clients',
    chk_ready: 'Ready',
    chk_pending: 'Not configured',
    sec_config: 'Configuration & Rules',
    btn_save_all: 'Save All Settings',
    sec_timing: 'Schedule & Autostart',
    chk_sched_enable: 'Enable built-in schedule',
    chk_sched_enable_sub: 'Auto-run on slot time with catch-up prevention',
    chk_autostart: 'Start automatically on Windows logon',
    chk_autostart_sub: 'Runs silently with highest privileges via Task Scheduler',
    lbl_sched_times: 'Schedule Times (comma-separated)',
    lbl_sched_catchup: 'Missed Slot Catch-Up Limit (hours)',
    sec_farming_rules: 'Farming & Continuation',
    lbl_genshin_mode: 'Genshin Domain Reward Claims',
    opt_mode_double: 'Use 40 Original Resin for 2× rewards first (Recommended)',
    opt_mode_single: 'Use 20 Original Resin per claim',
    lbl_boss_yield: 'Genshin Boss: Avg. Drops per Run',
    chk_artifact: 'Genshin: Farm Artifacts once materials are done',
    chk_artifact_sub: 'Runs only when no goal material is left to farm',
    lbl_artifact_domain: 'Domain of Blessing (Artifacts)',
    lbl_artifact_cap: 'Artifact Cumulative Cap (claims)',
    chk_disc: 'ZZZ: Farm Drive Discs once materials are done',
    chk_disc_sub: 'Uses the live Battery Charge reading (60 per run)',
    lbl_disc_mission: 'Area Patrol Mission (Drive Discs)',
    lbl_disc_cap: 'Drive Disc Cumulative Cap (runs)',
    sec_features: 'Feature Toggles',
    chk_mute_morning: 'Mute audio during morning scheduled runs',
    chk_mute_morning_sub: 'Restores system volume and mute state after batch',
    chk_zzz_rewards: 'Claim ZZZ Engagement and New Eridu City Fund rewards after farming',
    chk_genshin_daily: 'Claim Genshin Daily Commission Rewards (Katheryne)',
    chk_genshin_mail: 'Claim Genshin Mail',
    chk_genshin_teapot: 'Claim Genshin Serenitea Pot rewards',
    sec_network: 'Network & LAN Access',
    lbl_port: 'Server Port',
    chk_lan: 'Allow LAN Access (SillyTavern style)',
    chk_lan_sub: 'Password required when enabled for safety',
    lbl_password: 'LAN Access Password (leave empty to keep current)',
    sec_notify: 'Notifications',
    chk_notify_batch: 'Send concise summary after each batch',
    chk_notify_toast: 'Windows Desktop Balloon Toast',
    chk_notify_relay: 'Relay service',
    lbl_relay_url: 'Relay URL',
    chk_notify_tg: 'Telegram Bot Direct',
    lbl_tg_chat_id: 'Chat ID',
    lbl_tg_token: 'Bot Token',
    sec_paths: 'Tools & Paths',
    lbl_path_bettergi: 'BetterGI folder',
    lbl_path_onedragon: 'ZZZ OneDragon folder',
    lbl_path_genshin_exe: 'Genshin Impact executable (optional)',
    lbl_path_zzz_exe: 'Zenless Zone Zero executable (optional)',
    lbl_bgi_template: 'BetterGI One Dragon template config (optional)',
    ph_from_tool: 'Empty: read from the tool config',
    ph_bundled_template: 'Empty: bundled template',

    // Toasts & Messages
    toast_batch_started: 'Batch started ({0})',
    toast_stop_sent: 'Stop request issued',
    toast_stamina_refreshed: 'Real-Time Notes refreshed',
    toast_logged_out: 'Logged out successfully',
    toast_goal_cancelled: 'Goal cancelled',
    toast_goal_restored: 'Goal restored',
    toast_goal_synced: 'Official gap synced',
    toast_item_paused: 'Item paused',
    toast_item_resumed: 'Item resumed',
    toast_order_updated: 'Order updated',
    toast_cat_order_updated: 'Category priority updated',
    toast_targets_updated: 'Target levels updated & recalculated',
    toast_settings_saved: 'Settings saved',
    toast_restart_needed: ' (Port or LAN mode changed; takes effect after restart)',
    toast_goal_added: 'Goal added: {0}',

    // Separators
    list_sep: ', ',
    clause_sep: '; ',
    game_summary: '<b>{0}</b>: {1}'
  },

  zh: {
    // Brand & Header
    brand_title: '养成中枢',
    brand_edition: '本地版',
    connecting: '正在连接后台…',
    connect_failed: '连接后台失败：{0}',
    current_date: '当前日期：<b>{0} ({1})</b>',
    weekdays: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    batch_running: '<span class="warn">● 正在执行批次 [{0}] · {1}</span>',
    schedule_on: '<span>定时调度：<b>开启</b> (下次：{0})</span>',
    schedule_off: '<span>定时调度：<b>未开启</b></span>',
    hoyolab_unlogged: '<span class="warn">米游社未登录</span>',

    // Navigation Tabs
    tab_today: '今日',
    tab_goals: '培养',
    tab_plan: '日程',
    tab_runs: '记录',
    tab_settings: '设置',

    // Today View
    batch_banner_title: '自动化批次执行中',
    batch_banner_sub: '时段：{0} · 阶段：{1} · 游戏：{2}',
    btn_stop: '停止执行',
    btn_refresh: '刷新体力',
    stamina_source: '读数信源',
    stamina_read_time: '读取时间',
    rule_note_prefix: '规则：定量收齐前每批只刷一种；在',
    rule_note_link: '培养',
    retain_stamina: '保留{0}，不执行耗体力刷取',
    routine_helpers: '日常辅助：{0}',
    routine_none: '无',
    manual_execution: '手动执行',
    manual_execution_desc: '按当前规则立即启动选定游戏的刷取。后台将自动接管工具、启动游戏、刷取并无损复原配置。',
    btn_run_zzz: '立即执行绝区零',
    btn_run_genshin: '立即执行原神',
    btn_run_both: '两游戏顺序执行',
    unit_resin: '树脂',
    unit_battery: '电量',
    game_genshin: '原神',
    game_zzz: '绝区零',

    // Goals View
    btn_add_goal: '+ 添加{0}目标',
    no_active_goals: '当前没有正在培养的角色。点击下方按钮添加目标。',
    goal_meta: '目标：等级 {0} · 技能/核心 · 武器 {1} {2}',
    btn_sync_gap: '同步官方缺口',
    btn_cancel_goal: '取消培养',
    btn_restore_goal: '恢复培养',
    cat_order_label: '材料优先顺序：',
    cat_level: '等级',
    cat_talents: '天赋/技能',
    cat_weapon: '武器/音擎',
    talent_normal_attack: '普通攻击',
    talent_skill: '元素战技',
    talent_burst: '元素爆发',
    talent_basic: '普通攻击',
    talent_special: '特殊技',
    talent_chain: '连携技',
    talent_dodge: '闪避',
    talent_assist: '支援技',
    talent_core: '核心技',
    th_item_days: '项目与开放日',
    th_demand: '总需求',
    th_executed: '已执行',
    th_status: '状态判定',
    th_action: '操作',
    status_done: '已收齐',
    status_next: '下批执行 ({0})',
    status_queued: '排队中 ({0})',
    btn_pause: '暂停',
    btn_resume: '恢复',
    btn_up: '上移',
    btn_down: '下移',
    edit_targets_summary: '修改目标等级 / 技能数值',
    btn_save_recalc: '保存并重新测算',
    cancelled_goals_header: '已取消/停用的目标 ({0})',
    cancelled_goals_note: '（数据与历史已保留）',
    modal_add_title: '添加{0}培养目标',
    lbl_select_char: '选择角色',
    btn_confirm_add: '确认添加',
    btn_cancel: '取消',

    // Schedule View
    schedule_forecast_title: '未来三天排程预测',
    schedule_rule_desc: '与执行同一规则：按顺序逐项收齐、以游戏内实读体力为准、无目标不耗体力',
    th_time_slot: '时段',
    th_game: '游戏',
    th_est_stamina: '预计体力',
    th_planned_item: '计划刷取项目',
    th_est_spend: '预计消耗',
    th_rule_note: '规则说明',
    routine_only: '免费日常',
    no_forecast_rows: '暂无未来时段或未选择游戏。',

    // Runs View
    runs_title: '运行记录',
    btn_refresh_runs: '刷新记录',
    th_started: '开始时间',
    th_status_col: '最终状态',
    th_slot_source: '时段/来源',
    th_receipt_summary: '执行结果与回执摘要',
    th_ended: '结束时间',
    no_runs: '暂无运行历史记录。',
    no_games_executed: '未执行游戏',

    // Settings View
    sec_account: '米游社账号',
    btn_logout: '退出登录',
    confirm_logout: '确定要退出米游社登录吗？',
    not_bound: '未绑定',
    qr_desc: '使用米游社 App 扫码登录，同步养成缺口与实时便笺（仅支持国服账号）。凭据经 Windows DPAPI 加密存储，不会明文保存。',
    btn_gen_qr: '生成登录二维码',
    qr_prompt: '请使用米游社 App 扫码',
    sec_tools: '本机工具检测',
    chk_admin: '管理员权限',
    chk_admin_ok: '已获取',
    chk_admin_warn: '未提权（后台仍可查看，执行游戏需提权）',
    chk_bgi: 'BetterGI',
    chk_zzz: '绝区零一条龙',
    chk_live_patch: '实读电量适配（可选）：{0}',
    chk_found: '已找到',
    chk_missing: '未找到',
    chk_installed: '正常',
    chk_game_clients: '游戏客户端',
    chk_ready: '正常',
    chk_pending: '待配置',
    sec_config: '功能与规则配置',
    btn_save_all: '保存所有配置',
    sec_timing: '定时与自启',
    chk_sched_enable: '开启内置定时调度',
    chk_sched_enable_sub: '到达时段自动执行，防重复补跑',
    chk_autostart: '开机登录自动启动本程序',
    chk_autostart_sub: '通过 Windows 计划任务以最高权限静默启动',
    lbl_sched_times: '定时时段 (逗号分隔)',
    lbl_sched_catchup: '开机错过补跑上限 (小时)',
    sec_farming_rules: '刷取与接续',
    lbl_genshin_mode: '原神秘境领奖方式',
    opt_mode_double: '优先使用 40 原粹树脂领取双倍产出（推荐）',
    opt_mode_single: '每次使用 20 原粹树脂',
    lbl_boss_yield: '原神 首领每次平均产出',
    chk_artifact: '原神：材料齐后自动接续圣遗物',
    chk_artifact_sub: '当前无可执行定量材料时刷取',
    lbl_artifact_domain: '祝圣秘境（圣遗物）',
    lbl_artifact_cap: '圣遗物累计上限 (份)',
    chk_disc: '绝区零：材料齐后自动接续驱动盘',
    chk_disc_sub: '按实读普通电量执行，每场 60 电量',
    lbl_disc_mission: '区域巡防关卡（驱动盘）',
    lbl_disc_cap: '驱动盘累计上限 (场)',
    sec_features: '功能开关',
    chk_mute_morning: '早间定时批次执行时静音',
    chk_mute_morning_sub: '结束后恢复原系统音量与静音状态',
    chk_zzz_rewards: '绝区零刷后领取活跃度与丽都城募奖励',
    chk_genshin_daily: '原神领取每日委托奖励（凯瑟琳）',
    chk_genshin_mail: '原神领取邮件',
    chk_genshin_teapot: '原神领取尘歌壶奖励',
    sec_network: '网络与局域网访问',
    lbl_port: '服务端口',
    chk_lan: '开放局域网访问 (SillyTavern 风格)',
    chk_lan_sub: '开启时必须配置访问密码以保障安全',
    lbl_password: '局域网访问密码 (留空保持现状)',
    sec_notify: '消息通知',
    chk_notify_batch: '每批执行结束发送聚合摘要 (精简通知)',
    chk_notify_toast: 'Windows 桌面气泡弹窗通知',
    chk_notify_relay: '中转服务通知',
    lbl_relay_url: '中转地址',
    chk_notify_tg: 'Telegram Bot 直连通知',
    lbl_tg_chat_id: 'Chat ID',
    lbl_tg_token: 'Bot Token',
    sec_paths: '工具与路径',
    lbl_path_bettergi: 'BetterGI 目录',
    lbl_path_onedragon: '绝区零一条龙目录',
    lbl_path_genshin_exe: '原神程序路径（可选）',
    lbl_path_zzz_exe: '绝区零程序路径（可选）',
    lbl_bgi_template: 'BetterGI 一条龙模板配置（可选）',
    ph_from_tool: '留空：从工具配置读取',
    ph_bundled_template: '留空：使用内置模板',

    // Toasts & Messages
    toast_batch_started: '批次已启动 ({0})',
    toast_stop_sent: '已下发停止请求',
    toast_stamina_refreshed: '实时便笺已刷新',
    toast_logged_out: '已退出登录',
    toast_goal_cancelled: '已取消培养',
    toast_goal_restored: '已恢复培养',
    toast_goal_synced: '已同步官方缺口与持有量',
    toast_item_paused: '该项目已暂停',
    toast_item_resumed: '该项目已恢复',
    toast_order_updated: '顺序已更新',
    toast_cat_order_updated: '分类优先级已更新',
    toast_targets_updated: '目标等级已更新并重新测算',
    toast_settings_saved: '配置已保存',
    toast_restart_needed: '（端口或局域网模式变更，重启后台后生效）',
    toast_goal_added: '已添加目标：{0}',

    // Separators
    list_sep: '、',
    clause_sep: '；',
    game_summary: '<b>{0}</b>：{1}'
  }
};

let CURRENT_LANG = localStorage.getItem('gcl_lang') || 'en';
let STATE = null;
let ACTIVE_TAB = 'today';
let POLL_TIMER = null;

// ----------------------------------------------------------- i18n Helpers
function t(key, ...args) {
  const dict = I18N[CURRENT_LANG] || I18N.en;
  let text = dict[key] !== undefined ? dict[key] : (I18N.en[key] !== undefined ? I18N.en[key] : key);
  if (typeof text === 'string') {
    args.forEach((val, i) => {
      text = text.replace(new RegExp(`\\{${i}\\}`, 'g'), val);
    });
  }
  return text;
}

function setLanguage(lang) {
  if (!I18N[lang]) lang = 'en';
  CURRENT_LANG = lang;
  localStorage.setItem('gcl_lang', lang);
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

  const btnEn = document.getElementById('btn-lang-en');
  const btnZh = document.getElementById('btn-lang-zh');
  if (btnEn) btnEn.className = lang === 'en' ? 'active' : '';
  if (btnZh) btnZh.className = lang === 'zh' ? 'active' : '';

  // Update static UI elements
  const brandTitle = document.getElementById('brand-title');
  if (brandTitle) brandTitle.textContent = t('brand_title');
  const brandEdition = document.getElementById('brand-edition');
  if (brandEdition) brandEdition.textContent = t('brand_edition');

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.dataset.i18n;
    if (k) el.textContent = t(k);
  });

  render();
  if (STATE) refreshState();
}

// Backend-generated text (plan reasons, errors, run summaries) follows the UI language.
async function syncBackendLang() {
  if (!STATE || (STATE.settings?.ui?.lang || 'en') === CURRENT_LANG) return;
  try {
    await api('/api/lang', 'POST', { lang: CURRENT_LANG });
    STATE = await api('/api/state');
  } catch (_) {}
}

// ----------------------------------------------------------- API
async function api(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'X-GC': '1' }
  };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    let err = 'Request failed (' + res.status + ')';
    try {
      const data = await res.json();
      if (data && data.error) err = data.error;
    } catch (_) {}
    throw new Error(err);
  }
  return await res.json();
}

function showToast(msg, isOk = true) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = 'toast' + (isOk ? ' ok' : '');
  el.hidden = false;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.hidden = true; }, 4000);
}

// ----------------------------------------------------------- Lifecycle & Polling
async function refreshState() {
  try {
    STATE = await api('/api/state');
    await syncBackendLang();
    render();
  } catch (err) {
    const sl = document.getElementById('status-line');
    if (sl) sl.innerHTML = `<span class="warn">${t('connect_failed', err.message)}</span>`;
  }
}

function startPolling() {
  refreshState();
  if (POLL_TIMER) clearInterval(POLL_TIMER);
  POLL_TIMER = setInterval(refreshState, 5000);
}

// ----------------------------------------------------------- Tab Switch
function switchTab(name) {
  ACTIVE_TAB = name;
  document.querySelectorAll('nav button').forEach(b => {
    b.setAttribute('aria-selected', b.dataset.tab === name ? 'true' : 'false');
  });
  document.querySelectorAll('main > section').forEach(s => {
    s.hidden = s.id !== `view-${name}`;
  });
  render();
}

// ----------------------------------------------------------- Main Render
function render() {
  if (!STATE) return;

  // Header status line
  const runner = STATE.runner || {};
  const sl = document.getElementById('status-line');
  if (sl) {
    const wkName = (I18N[CURRENT_LANG]?.weekdays || I18N.en.weekdays)[STATE.weekday] || '';
    let html = `<span>${t('current_date', STATE.game_date, wkName)}</span>`;
    if (runner.running) {
      html += t('batch_running', runner.slot || 'manual', runner.stage || 'running');
    } else if (STATE.settings?.schedule?.enabled) {
      html += t('schedule_on', STATE.next_slot || '...');
    } else {
      html += t('schedule_off');
    }
    if (!STATE.logged_in) {
      html += t('hoyolab_unlogged');
    }
    sl.innerHTML = html;
  }

  // Active view render
  if (ACTIVE_TAB === 'today') renderToday();
  else if (ACTIVE_TAB === 'goals') renderGoals();
  else if (ACTIVE_TAB === 'plan') renderPlan();
  else if (ACTIVE_TAB === 'runs') renderRuns();
  else if (ACTIVE_TAB === 'settings') renderSettings();
}

// ----------------------------------------------------------- 1. Today View
function renderToday() {
  const el = document.getElementById('view-today');
  if (!el || !STATE) return;

  const runner = STATE.runner || {};
  const isRunning = runner.running;

  let banner = '';
  if (isRunning) {
    banner = `
      <div class="banner red">
        <div>
          <b>${t('batch_banner_title')}</b>
          <div class="small">${t('batch_banner_sub', runner.slot || 'manual', runner.stage || 'busy', runner.game || 'orchestrating')}</div>
        </div>
        <button class="btn danger" onclick="handleStop(this)">${t('btn_stop')}</button>
      </div>`;
  }

  const makeCard = (game, labelKey, unitKey) => {
    const st = STATE.stamina?.[game];
    const plan = STATE.plans?.[game] || {};
    const item = plan.item;
    const valueStr = st ? `${st.value}` : '?';
    const capStr = st ? `/ ${st.cap}` : '';
    const unitName = t(unitKey);
    const gameLabel = t(labelKey);

    let actionDesc = '';
    if (item) {
      actionDesc = `
        <div class="next">
          <div class="what">${item.goal} · ${item.label}</div>
          <div class="why">${plan.reason}</div>
          <div class="where">${t('rule_note_prefix')} <a onclick="switchTab('goals')">${t('rule_note_link')}</a></div>
        </div>`;
    } else {
      actionDesc = `
        <div class="next none">
          <div class="what">${t('retain_stamina', unitName)}</div>
          <div class="why">${plan.reason || t('no_active_goals')}</div>
          <div class="where">${t('rule_note_prefix')} <a onclick="switchTab('goals')">${t('rule_note_link')}</a></div>
        </div>`;
    }

    const dailyText = (plan.daily && plan.daily.length) ? plan.daily.join(t('list_sep')) : t('routine_none');

    return `
      <div class="col-6 block">
        <div class="head">
          <h2>${gameLabel}</h2>
          <button class="btn quiet small" onclick="handleRefreshNotes('${game}', this)">${t('btn_refresh')}</button>
        </div>
        <div class="figure">
          <span class="big num">${valueStr}</span>
          <span class="cap num">${capStr} ${unitName}</span>
        </div>
        <div class="kv" style="margin-top:10px;">
          <dt>${t('stamina_source')}</dt><dd>${st?.source || '-'}</dd>
          <dt>${t('stamina_read_time')}</dt><dd>${st?.seen ? st.seen.split('T')[1].slice(0, 8) : '-'}</dd>
        </div>
        ${actionDesc}
        <div class="small muted" style="margin-top:12px;">${t('routine_helpers', dailyText)}</div>
      </div>`;
  };

  el.innerHTML = `
    ${banner}
    <div class="grid">
      ${makeCard('zzz', 'game_zzz', 'unit_battery')}
      ${makeCard('genshin', 'game_genshin', 'unit_resin')}
    </div>
    <div class="block" style="margin-top:40px;">
      <div class="head">
        <h3>${t('manual_execution')}</h3>
      </div>
      <p class="small muted" style="margin-bottom:16px;">${t('manual_execution_desc')}</p>
      <div class="actions">
        <button class="btn" ${isRunning ? 'disabled' : ''} onclick="handleRunBatch(['zzz'], this)">${t('btn_run_zzz')}</button>
        <button class="btn" ${isRunning ? 'disabled' : ''} onclick="handleRunBatch(['genshin'], this)">${t('btn_run_genshin')}</button>
        <button class="btn secondary" ${isRunning ? 'disabled' : ''} onclick="handleRunBatch(['zzz', 'genshin'], this)">${t('btn_run_both')}</button>
      </div>
    </div>`;
}

// ----------------------------------------------------------- 2. Goals View
function renderGoals() {
  const el = document.getElementById('view-goals');
  if (!el || !STATE) return;

  const renderGameGoals = (game, labelKey) => {
    const list = STATE.goals?.[game] || [];
    const active = list.filter(g => g.enabled);
    const disabled = list.filter(g => !g.enabled);
    const gameLabel = t(labelKey);

    let activeHtml = '';
    if (!active.length) {
      activeHtml = `<div class="empty">${t('no_active_goals', gameLabel)}</div>`;
    } else {
      activeHtml = active.map((g, idx) => {
        const items = g.items || [];
        const isCurrentFirst = idx === 0;

        const itemsRows = items.map(it => {
          let statusText = '';
          if (it.done) statusText = `<span class="muted">${t('status_done')}</span>`;
          else if (it.why) statusText = `<span class="muted">${it.why}</span>`;
          else if (isCurrentFirst) statusText = `<b class="red">${t('status_next', it.available + (it.unit_label || ''))}</b>`;
          else statusText = `<span>${t('status_queued', it.available + (it.unit_label || ''))}</span>`;

          const pauseBtn = it.paused
            ? `<button class="btn quiet small" onclick="handleTogglePauseItem('${g.id}', '${it.key}', false, this)">${t('btn_resume')}</button>`
            : `<button class="btn quiet small" onclick="handleTogglePauseItem('${g.id}', '${it.key}', true, this)">${t('btn_pause')}</button>`;

          return `
            <tr>
              <td><b>${it.label}</b><div class="small muted">${it.names} · ${it.days}</div></td>
              <td class="r num">${it.units !== null ? it.units + (it.unit_label || '') : '?'}</td>
              <td class="r num">${it.executed || 0}${it.unit_label || ''}</td>
              <td>${statusText}</td>
              <td class="r">${it.done ? '' : pauseBtn}</td>
            </tr>`;
        }).join('');

        const catsOrder = (g.category_order || ['level', 'talents', 'weapon']).map((c, i) => {
          const catLabel = t('cat_' + c);
          return `
            <span class="chip">
              ${catLabel}
              ${i > 0 ? `<button title="${t('btn_up')}" onclick="handleShiftCat('${g.id}', ${i}, -1)">←</button>` : ''}
              ${i < 2 ? `<button title="${t('btn_down')}" onclick="handleShiftCat('${g.id}', ${i}, 1)">→</button>` : ''}
            </span>`;
        }).join('');

        return `
          <div class="goal">
            <div class="goal-head">
              <div class="goal-pos num">#${g.position}</div>
              <div>
                <div class="goal-name">${g.name}</div>
                <div class="goal-meta">
                  ${t('goal_meta', g.target?.level || '-', g.target?.weapon || '-', g.weapon_name ? `(${g.weapon_name})` : '')}
                </div>
              </div>
              <div class="actions">
                ${idx > 0 ? `<button class="btn quiet small" onclick="handleMoveGoal('${game}', ${idx}, -1)">${t('btn_up')}</button>` : ''}
                ${idx < active.length - 1 ? `<button class="btn quiet small" onclick="handleMoveGoal('${game}', ${idx}, 1)">${t('btn_down')}</button>` : ''}
                <button class="btn quiet small" onclick="handleSyncGoal('${g.id}', this)">${t('btn_sync_gap')}</button>
                <button class="btn quiet small danger" onclick="handleToggleGoalEnabled('${g.id}', false, this)">${t('btn_cancel_goal')}</button>
              </div>
            </div>
            <div class="goal-body">
              <div class="order-cats">
                <span class="muted small">${t('cat_order_label')}</span>
                ${catsOrder}
              </div>
              <div class="scroll">
                <table>
                  <thead>
                    <tr>
                      <th>${t('th_item_days')}</th>
                      <th class="r">${t('th_demand')}</th>
                      <th class="r">${t('th_executed')}</th>
                      <th>${t('th_status')}</th>
                      <th class="r">${t('th_action')}</th>
                    </tr>
                  </thead>
                  <tbody>${itemsRows || '<tr><td colspan="5" class="empty">...</td></tr>'}</tbody>
                </table>
              </div>
              <details class="edit">
                <summary>${t('edit_targets_summary')}</summary>
                <div class="edit-box">
                  <form onsubmit="handleUpdateGoalTargets(event, '${g.id}')">
                    <div class="fields">
                      <label class="field">${t('cat_level')}<input type="number" name="level" value="${g.target?.level || 90}"></label>
                      <label class="field">${t('cat_weapon')}<input type="number" name="weapon" value="${g.target?.weapon || 90}"></label>
                      ${game === 'genshin' ? `
                        <label class="field">${t('talent_normal_attack')}<input type="number" name="attack" value="${g.target?.attack || 1}"></label>
                        <label class="field">${t('talent_skill')}<input type="number" name="skill" value="${g.target?.skill || 9}"></label>
                        <label class="field">${t('talent_burst')}<input type="number" name="burst" value="${g.target?.burst || 9}"></label>
                      ` : `
                        <label class="field">${t('talent_basic')}<input type="number" name="attack" value="${g.target?.attack || 12}"></label>
                        <label class="field">${t('talent_special')}<input type="number" name="special" value="${g.target?.special || 12}"></label>
                        <label class="field">${t('talent_chain')}<input type="number" name="chain" value="${g.target?.chain || 12}"></label>
                        <label class="field">${t('talent_dodge')}<input type="number" name="dodge" value="${g.target?.dodge || 9}"></label>
                        <label class="field">${t('talent_assist')}<input type="number" name="assist" value="${g.target?.assist || 9}"></label>
                        <label class="field">${t('talent_core')}<input type="number" name="core" value="${g.target?.core || 6}"></label>
                      `}
                    </div>
                    <div style="margin-top:12px;">
                      <button type="submit" class="btn small">${t('btn_save_recalc')}</button>
                    </div>
                  </form>
                </div>
              </details>
            </div>
          </div>`;
      }).join('');
    }

    let disabledHtml = '';
    if (disabled.length) {
      disabledHtml = `
        <div class="cancelled">
          <h4>${t('cancelled_goals_header', disabled.length)}</h4>
          <ul class="plain">
            ${disabled.map(g => `
              <li>
                <span><b>${g.name}</b> <small class="muted">${t('cancelled_goals_note')}</small></span>
                <button class="btn secondary small" onclick="handleToggleGoalEnabled('${g.id}', true, this)">${t('btn_restore_goal')}</button>
              </li>
            `).join('')}
          </ul>
        </div>`;
    }

    return `
      <div class="col-6 block">
        <div class="head">
          <h2>${gameLabel}</h2>
          <button class="btn secondary small" onclick="openAddGoalModal('${game}')">${t('btn_add_goal', gameLabel)}</button>
        </div>
        ${activeHtml}
        ${disabledHtml}
      </div>`;
  };

  el.innerHTML = `
    <div class="grid">
      ${renderGameGoals('zzz', 'game_zzz')}
      ${renderGameGoals('genshin', 'game_genshin')}
    </div>
    <div id="add-goal-modal" class="edit-box" style="display:none; margin-top:30px;"></div>`;
}

// ----------------------------------------------------------- 3. Plan / Schedule View
function renderPlan() {
  const el = document.getElementById('view-plan');
  if (!el || !STATE) return;

  const fc = STATE.forecast || {};
  const rows = fc.rows || [];

  let tableRows = '';
  if (!rows.length) {
    tableRows = `<tr><td colspan="6" class="empty">${t('no_forecast_rows')}</td></tr>`;
  } else {
    tableRows = rows.map(r => {
      const gName = r.game === 'genshin' ? t('game_genshin') : t('game_zzz');
      const timeStr = r.at ? r.at.replace('T', ' ').slice(5, 16) : '-';
      return `
        <tr>
          <td><b>${timeStr}</b></td>
          <td>${gName}</td>
          <td class="num">${r.stamina !== null ? r.stamina : '?'}</td>
          <td><b>${r.label || t('routine_only')}</b></td>
          <td class="num">${r.expected !== null ? r.expected + (r.unit_label || '') : '-'}</td>
          <td class="small muted">${r.reason}</td>
        </tr>`;
    }).join('');
  }

  el.innerHTML = `
    <div class="block">
      <div class="head">
        <h2>${t('schedule_forecast_title')}</h2>
        <span class="small muted">${t('schedule_rule_desc')}</span>
      </div>
      <div class="scroll">
        <table>
          <thead>
            <tr>
              <th>${t('th_time_slot')}</th>
              <th>${t('th_game')}</th>
              <th>${t('th_est_stamina')}</th>
              <th>${t('th_planned_item')}</th>
              <th>${t('th_est_spend')}</th>
              <th>${t('th_rule_note')}</th>
            </tr>
          </thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div>
    </div>`;
}

// ----------------------------------------------------------- 4. Runs View
function renderRuns() {
  const el = document.getElementById('view-runs');
  if (!el || !STATE) return;

  const list = STATE.runs || [];
  let tableRows = '';
  if (!list.length) {
    tableRows = `<tr><td colspan="5" class="empty">${t('no_runs')}</td></tr>`;
  } else {
    tableRows = list.map(r => {
      const timeStr = r.started ? r.started.replace('T', ' ').slice(5, 19) : '-';
      const gamesSummaries = (r.games || []).map(g => {
        const gName = g.game === 'genshin' ? t('game_genshin') : t('game_zzz');
        const err = (g.errors && g.errors.length) ? `<div class="small red">${g.errors.join(t('clause_sep'))}</div>` : '';
        return `<div>${t('game_summary', gName, g.summary || g.status)}${err}</div>`;
      }).join('');

      return `
        <tr>
          <td class="num"><b>${timeStr}</b></td>
          <td><span class="badge ${r.status}">${r.status}</span></td>
          <td>${r.slot || 'manual'} (${r.source || 'manual'})</td>
          <td>${gamesSummaries || `<span class="muted">${t('no_games_executed')}</span>`}</td>
          <td class="small muted num">${r.ended ? r.ended.split('T')[1].slice(0, 8) : '-'}</td>
        </tr>`;
    }).join('');
  }

  el.innerHTML = `
    <div class="block">
      <div class="head">
        <h2>${t('runs_title')}</h2>
        <button class="btn quiet small" onclick="refreshState()">${t('btn_refresh_runs')}</button>
      </div>
      <div class="scroll">
        <table>
          <thead>
            <tr>
              <th>${t('th_started')}</th>
              <th>${t('th_status_col')}</th>
              <th>${t('th_slot_source')}</th>
              <th>${t('th_receipt_summary')}</th>
              <th>${t('th_ended')}</th>
            </tr>
          </thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div>
    </div>`;
}

// ----------------------------------------------------------- 5. Settings View
function renderSettings() {
  const el = document.getElementById('view-settings');
  if (!el || !STATE) return;

  const s = STATE.settings || {};
  const chk = STATE.check || {};
  const qr = STATE.qr || {};

  el.innerHTML = `
    <div class="grid">
      <!-- HoYoLAB Login -->
      <div class="col-6 block">
        <div class="head">
          <h2>${t('sec_account')}</h2>
          ${STATE.logged_in ? `<button class="btn quiet danger small" onclick="handleLogout()">${t('btn_logout')}</button>` : ''}
        </div>
        <div id="login-panel">
          ${STATE.logged_in ? `
            <div class="kv">
              <dt>${t('game_zzz')}</dt><dd>${STATE.accounts?.zzz?.name || t('not_bound')} (${STATE.accounts?.zzz?.uid || '-'})</dd>
              <dt>${t('game_genshin')}</dt><dd>${STATE.accounts?.genshin?.name || t('not_bound')} (${STATE.accounts?.genshin?.uid || '-'})</dd>
            </div>
          ` : `
            <p class="small muted" style="margin-bottom:12px;">${t('qr_desc')}</p>
            <div class="actions">
              <button class="btn" onclick="handleStartLogin(this)">${t('btn_gen_qr')}</button>
            </div>
            ${qr.status === 'waiting' && qr.svg ? `
              <div style="margin-top:16px;">
                <div class="qr">${qr.svg}</div>
                <div class="small muted" style="margin-top:8px;">${qr.reason || t('qr_prompt')}</div>
              </div>
            ` : ''}
          `}
        </div>
      </div>

      <!-- Tools Check -->
      <div class="col-6 block">
        <div class="head">
          <h2>${t('sec_tools')}</h2>
        </div>
        <ul class="plain">
          <li>
            <span class="tag">${t('chk_admin')}</span>
            <span>${chk.admin ? `<b>${t('chk_admin_ok')}</b>` : `<span class="warn">${t('chk_admin_warn')}</span>`}</span>
          </li>
          <li>
            <span class="tag">${t('chk_bgi')}</span>
            <span>${chk.genshin?.tool_ok ? t('chk_found') : `<span class="warn">${t('chk_missing')} ${chk.genshin?.tool_exe || 'BetterGI.exe'}</span>`}</span>
          </li>
          <li>
            <span class="tag">${t('chk_zzz')}</span>
            <span>${chk.zzz?.tool_ok ? t('chk_found') : `<span class="warn">${t('chk_missing')} ${chk.zzz?.tool_exe || 'OneDragon-Launcher.exe'}</span>`} · ${t('chk_live_patch', chk.zzz?.patch_ok ? `<b>${t('chk_installed')}</b>` : `<span class="warn">${t('chk_missing')}</span>`)}</span>
          </li>
          <li>
            <span class="tag">${t('chk_game_clients')}</span>
            <span>${t('game_genshin')}: ${chk.genshin?.game_ok ? t('chk_ready') : t('chk_pending')} · ${t('game_zzz')}: ${chk.zzz?.game_ok ? t('chk_ready') : t('chk_pending')}</span>
          </li>
        </ul>
      </div>

      <!-- Settings Form -->
      <div class="col-12 block" style="margin-top:30px;">
        <form onsubmit="handleSaveSettings(event)">
          <div class="head">
            <h2>${t('sec_config')}</h2>
            <button type="submit" class="btn">${t('btn_save_all')}</button>
          </div>

          <div class="grid">
            <div class="col-6">
              <h3>${t('sec_timing')}</h3>
              <div class="rule"></div>
              <label class="check">
                <input type="checkbox" name="schedule_enabled" ${s.schedule?.enabled ? 'checked' : ''}>
                <span>${t('chk_sched_enable')}<small>${t('chk_sched_enable_sub')}</small></span>
              </label>
              <label class="check">
                <input type="checkbox" name="schedule_autostart" ${s.schedule?.autostart ? 'checked' : ''}>
                <span>${t('chk_autostart')}<small>${t('chk_autostart_sub')}</small></span>
              </label>
              <div class="fields" style="margin-top:10px;">
                <label class="field">${t('lbl_sched_times')}<input type="text" name="schedule_times" value="${(s.schedule?.times || []).join(', ')}"></label>
                <label class="field">${t('lbl_sched_catchup')}<input type="number" name="schedule_catchup" value="${s.schedule?.catchup_hours || 4}"></label>
              </div>

              <h3 style="margin-top:24px;">${t('sec_farming_rules')}</h3>
              <div class="rule"></div>
              <div class="fields wide">
                <label class="field">${t('lbl_genshin_mode')}
                  <select name="genshin_claim_mode">
                    <option value="double" ${s.planning?.genshin_claim_mode === 'double' ? 'selected' : ''}>${t('opt_mode_double')}</option>
                    <option value="single" ${s.planning?.genshin_claim_mode === 'single' ? 'selected' : ''}>${t('opt_mode_single')}</option>
                  </select>
                </label>
                <label class="field">${t('lbl_boss_yield')}<input type="number" step="0.1" name="genshin_boss_yield" value="${s.planning?.genshin_boss_yield || 2.4}"></label>
              </div>
              <label class="check" style="margin-top:12px;">
                <input type="checkbox" name="artifact_enabled" ${s.planning?.artifact?.enabled ? 'checked' : ''}>
                <span>${t('chk_artifact')}<small>${t('chk_artifact_sub')}</small></span>
              </label>
              <div class="fields">
                <label class="field">${t('lbl_artifact_domain')}<input type="text" name="artifact_domain" value="${s.planning?.artifact?.domain || ''}"></label>
                <label class="field">${t('lbl_artifact_cap')}<input type="number" name="artifact_cap" value="${s.planning?.artifact?.cap || 0}"></label>
              </div>
              <label class="check" style="margin-top:12px;">
                <input type="checkbox" name="disc_enabled" ${s.planning?.disc?.enabled ? 'checked' : ''}>
                <span>${t('chk_disc')}<small>${t('chk_disc_sub')}</small></span>
              </label>
              <div class="fields">
                <label class="field">${t('lbl_disc_mission')}<input type="text" name="disc_mission" value="${s.planning?.disc?.mission || ''}"></label>
                <label class="field">${t('lbl_disc_cap')}<input type="number" name="disc_cap" value="${s.planning?.disc?.cap || 0}"></label>
              </div>

              <h3 style="margin-top:24px;">${t('sec_paths')}</h3>
              <div class="rule"></div>
              <div class="fields wide">
                <label class="field">${t('lbl_path_bettergi')}<input type="text" name="path_bettergi" value="${s.paths?.bettergi || ''}"></label>
                <label class="field">${t('lbl_bgi_template')}<input type="text" name="bgi_template" value="${s.execution?.bgi_template || ''}" placeholder="${t('ph_bundled_template')}"></label>
                <label class="field">${t('lbl_path_onedragon')}<input type="text" name="path_onedragon" value="${s.paths?.onedragon || ''}"></label>
                <label class="field">${t('lbl_path_genshin_exe')}<input type="text" name="path_genshin_exe" value="${s.paths?.genshin_exe || ''}" placeholder="${t('ph_from_tool')}"></label>
                <label class="field">${t('lbl_path_zzz_exe')}<input type="text" name="path_zzz_exe" value="${s.paths?.zzz_exe || ''}" placeholder="${t('ph_from_tool')}"></label>
              </div>
            </div>

            <div class="col-6">
              <h3>${t('sec_features')}</h3>
              <div class="rule"></div>
              <label class="check">
                <input type="checkbox" name="mute_morning" ${s.features?.mute_morning ? 'checked' : ''}>
                <span>${t('chk_mute_morning')}<small>${t('chk_mute_morning_sub')}</small></span>
              </label>
              <label class="check">
                <input type="checkbox" name="zzz_rewards" ${s.features?.zzz_rewards ? 'checked' : ''}>
                <span>${t('chk_zzz_rewards')}</span>
              </label>
              <label class="check">
                <input type="checkbox" name="genshin_daily_reward" ${s.features?.genshin_daily_reward ? 'checked' : ''}>
                <span>${t('chk_genshin_daily')}</span>
              </label>
              <label class="check">
                <input type="checkbox" name="genshin_mail" ${s.features?.genshin_mail ? 'checked' : ''}>
                <span>${t('chk_genshin_mail')}</span>
              </label>
              <label class="check">
                <input type="checkbox" name="genshin_teapot" ${s.features?.genshin_teapot ? 'checked' : ''}>
                <span>${t('chk_genshin_teapot')}</span>
              </label>

              <h3 style="margin-top:24px;">${t('sec_network')}</h3>
              <div class="rule"></div>
              <div class="fields">
                <label class="field">${t('lbl_port')}<input type="number" name="server_port" value="${s.server?.port || 18800}"></label>
              </div>
              <label class="check" style="margin-top:8px;">
                <input type="checkbox" name="server_lan" ${s.server?.lan ? 'checked' : ''}>
                <span>${t('chk_lan')}<small>${t('chk_lan_sub')}</small></span>
              </label>
              <div class="fields" style="margin-top:8px;">
                <label class="field">${t('lbl_password')}<input type="password" name="secret_password" placeholder="${s.secrets_set?.password ? '••••••••' : '-'}"></label>
              </div>

              <h3 style="margin-top:24px;">${t('sec_notify')}</h3>
              <div class="rule"></div>
              <label class="check">
                <input type="checkbox" name="notify_batch" ${s.notify?.events?.batch ? 'checked' : ''}>
                <span>${t('chk_notify_batch')}</span>
              </label>
              <label class="check">
                <input type="checkbox" name="notify_toast" ${s.notify?.channels?.toast?.enabled ? 'checked' : ''}>
                <span>${t('chk_notify_toast')}</span>
              </label>
              <label class="check">
                <input type="checkbox" name="notify_relay" ${s.notify?.channels?.relay?.enabled ? 'checked' : ''}>
                <span>${t('chk_notify_relay')}</span>
              </label>
              <label class="field" style="margin-top:6px;">${t('lbl_relay_url')}<input type="url" name="secret_relay_url" placeholder="${s.secrets_set?.relay_url ? '••••••••' : 'https://...'}"></label>
              <label class="check" style="margin-top:8px;">
                <input type="checkbox" name="notify_telegram" ${s.notify?.channels?.telegram?.enabled ? 'checked' : ''}>
                <span>${t('chk_notify_tg')}</span>
              </label>
              <div class="fields">
                <label class="field">${t('lbl_tg_chat_id')}<input type="text" name="tg_chat_id" value="${s.notify?.channels?.telegram?.chat_id || ''}"></label>
                <label class="field">${t('lbl_tg_token')}<input type="password" name="secret_telegram_token" placeholder="${s.secrets_set?.telegram_token ? '••••••••' : '-'}"></label>
              </div>
            </div>
          </div>
          <div class="sticky-save">
            <button type="submit" class="btn">${t('btn_save_all')}</button>
          </div>
        </form>
      </div>
    </div>`;
}

// ----------------------------------------------------------- Actions Handlers
async function withBusy(btn, fn) {
  if (!btn) return await fn();
  const oldText = btn.innerHTML;
  btn.disabled = true;
  btn.setAttribute('aria-busy', 'true');
  btn.innerHTML = `<span class="spin" aria-hidden="true"></span> ${oldText}`;
  try {
    await fn();
  } catch (err) {
    showToast(err.message, false);
  } finally {
    btn.disabled = false;
    btn.removeAttribute('aria-busy');
    btn.innerHTML = oldText;
  }
}

async function handleRunBatch(games, btn) {
  await withBusy(btn, async () => {
    const res = await api('/api/run', 'POST', { games });
    showToast(t('toast_batch_started', res.run_id));
    await refreshState();
  });
}

async function handleStop(btn) {
  await withBusy(btn, async () => {
    await api('/api/stop', 'POST', {});
    showToast(t('toast_stop_sent'));
    await refreshState();
  });
}

async function handleRefreshNotes(game, btn) {
  await withBusy(btn, async () => {
    await api('/api/notes/refresh', 'POST', { game });
    showToast(t('toast_stamina_refreshed'));
    await refreshState();
  });
}

async function handleStartLogin(btn) {
  await withBusy(btn, async () => {
    const res = await api('/api/login/start', 'POST', {});
    STATE.qr = res;
    render();
  });
}

async function handleLogout() {
  if (!confirm(t('confirm_logout'))) return;
  await api('/api/logout', 'POST', {});
  showToast(t('toast_logged_out'));
  await refreshState();
}

async function handleToggleGoalEnabled(id, enabled, btn) {
  await withBusy(btn, async () => {
    await api('/api/goals/update', 'POST', { id, patch: { enabled } });
    showToast(enabled ? t('toast_goal_restored') : t('toast_goal_cancelled'));
    await refreshState();
  });
}

async function handleSyncGoal(id, btn) {
  await withBusy(btn, async () => {
    await api('/api/goals/sync', 'POST', { id, observe: true });
    showToast(t('toast_goal_synced'));
    await refreshState();
  });
}

async function handleTogglePauseItem(goalId, itemKey, pause, btn) {
  await withBusy(btn, async () => {
    const g = [...(STATE.goals.zzz || []), ...(STATE.goals.genshin || [])].find(x => x.id === goalId);
    if (!g) return;
    const paused = new Set(g.paused || []);
    if (pause) paused.add(itemKey);
    else paused.delete(itemKey);
    await api('/api/goals/update', 'POST', { id: goalId, patch: { paused: Array.from(paused) } });
    showToast(pause ? t('toast_item_paused') : t('toast_item_resumed'));
    await refreshState();
  });
}

async function handleMoveGoal(game, index, delta) {
  const list = (STATE.goals?.[game] || []).filter(g => g.enabled);
  const target = index + delta;
  if (target < 0 || target >= list.length) return;
  const temp = list[index];
  list[index] = list[target];
  list[target] = temp;
  const ids = list.map(g => g.id);
  await api('/api/goals/order', 'POST', { game, ids });
  showToast(t('toast_order_updated'));
  await refreshState();
}

async function handleShiftCat(goalId, index, delta) {
  const g = [...(STATE.goals.zzz || []), ...(STATE.goals.genshin || [])].find(x => x.id === goalId);
  if (!g) return;
  const order = [...(g.category_order || ['level', 'talents', 'weapon'])];
  const target = index + delta;
  if (target < 0 || target >= order.length) return;
  const temp = order[index];
  order[index] = order[target];
  order[target] = temp;
  await api('/api/goals/update', 'POST', { id: goalId, patch: { category_order: order } });
  showToast(t('toast_cat_order_updated'));
  await refreshState();
}

async function handleUpdateGoalTargets(e, id) {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  const patch = { target: {} };
  for (let [k, v] of data.entries()) {
    if (v !== '') patch.target[k] = parseInt(v, 10);
  }
  await api('/api/goals/update', 'POST', { id, patch });
  showToast(t('toast_targets_updated'));
  await refreshState();
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const form = e.target;
  const f = new FormData(form);

  const times = (f.get('schedule_times') || '05:00, 18:00').split(',').map(s => s.trim()).filter(Boolean);
  const settingsPatch = {
    server: {
      port: parseInt(f.get('server_port') || '18800', 10),
      lan: f.get('server_lan') === 'on'
    },
    schedule: {
      enabled: f.get('schedule_enabled') === 'on',
      autostart: f.get('schedule_autostart') === 'on',
      times: times,
      catchup_hours: parseInt(f.get('schedule_catchup') || '4', 10)
    },
    planning: {
      genshin_claim_mode: f.get('genshin_claim_mode'),
      genshin_boss_yield: parseFloat(f.get('genshin_boss_yield') || '2.4'),
      artifact: {
        enabled: f.get('artifact_enabled') === 'on',
        domain: f.get('artifact_domain')?.trim() || '',
        cap: parseInt(f.get('artifact_cap') || '0', 10)
      },
      disc: {
        enabled: f.get('disc_enabled') === 'on',
        mission: f.get('disc_mission')?.trim() || '',
        cap: parseInt(f.get('disc_cap') || '0', 10)
      }
    },
    paths: {
      bettergi: f.get('path_bettergi')?.trim() || '',
      onedragon: f.get('path_onedragon')?.trim() || '',
      genshin_exe: f.get('path_genshin_exe')?.trim() || '',
      zzz_exe: f.get('path_zzz_exe')?.trim() || ''
    },
    execution: {
      bgi_template: f.get('bgi_template')?.trim() || ''
    },
    features: {
      mute_morning: f.get('mute_morning') === 'on',
      zzz_rewards: f.get('zzz_rewards') === 'on',
      genshin_daily_reward: f.get('genshin_daily_reward') === 'on',
      genshin_mail: f.get('genshin_mail') === 'on',
      genshin_teapot: f.get('genshin_teapot') === 'on'
    },
    notify: {
      events: { batch: f.get('notify_batch') === 'on' },
      channels: {
        toast: { enabled: f.get('notify_toast') === 'on' },
        relay: { enabled: f.get('notify_relay') === 'on' },
        telegram: {
          enabled: f.get('notify_telegram') === 'on',
          chat_id: f.get('tg_chat_id')?.trim() || ''
        }
      }
    }
  };

  const secretsPatch = {};
  if (f.get('secret_password')) secretsPatch.password = f.get('secret_password');
  if (f.get('secret_relay_url')) secretsPatch.relay_url = f.get('secret_relay_url');
  if (f.get('secret_telegram_token')) secretsPatch.telegram_token = f.get('secret_telegram_token');

  try {
    const res = await api('/api/settings', 'POST', { settings: settingsPatch, secrets: secretsPatch });
    showToast(t('toast_settings_saved') + (res.restart_needed ? t('toast_restart_needed') : ''));
    await refreshState();
  } catch (err) {
    showToast(err.message, false);
  }
}

async function openAddGoalModal(game) {
  const modal = document.getElementById('add-goal-modal');
  if (!modal) return;
  modal.style.display = 'block';
  modal.innerHTML = '<div class="small muted">...</div>';

  try {
    let chars = [];
    try {
      const r = await api(`/api/roster?game=${game}`);
      chars = r.rows || [];
    } catch (_) {
      const r = await api(`/api/characters?game=${game}`);
      chars = r.rows || [];
    }

    const options = chars.map(c => `<option value="${c.id}">${c.name} (${c.element || ''})</option>`).join('');
    const gameLabel = game === 'genshin' ? t('game_genshin') : t('game_zzz');

    modal.innerHTML = `
      <h3>${t('modal_add_title', gameLabel)}</h3>
      <form onsubmit="handleCreateGoal(event, '${game}')" style="margin-top:12px;">
        <div class="fields wide">
          <label class="field">${t('lbl_select_char')}
            <select name="character" id="select-char">${options}</select>
          </label>
        </div>
        <div class="actions" style="margin-top:16px;">
          <button type="submit" class="btn small">${t('btn_confirm_add')}</button>
          <button type="button" class="btn secondary small" onclick="document.getElementById('add-goal-modal').style.display='none'">${t('btn_cancel')}</button>
        </div>
      </form>`;
  } catch (err) {
    modal.innerHTML = `<span class="warn">${err.message}</span>`;
  }
}

async function handleCreateGoal(e, game) {
  e.preventDefault();
  const sel = document.getElementById('select-char');
  if (!sel) return;
  const cid = sel.value;
  const name = sel.options[sel.selectedIndex].text.split(' ')[0];

  try {
    await api('/api/goals/create', 'POST', { game, character_id: cid, name });
    showToast(t('toast_goal_added', name));
    document.getElementById('add-goal-modal').style.display = 'none';
    await refreshState();
  } catch (err) {
    showToast(err.message, false);
  }
}

// ----------------------------------------------------------- Initial Setup
window.addEventListener('DOMContentLoaded', () => {
  // Bind tab switches
  document.querySelectorAll('nav button').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Bind language buttons
  const btnEn = document.getElementById('btn-lang-en');
  const btnZh = document.getElementById('btn-lang-zh');
  if (btnEn) btnEn.addEventListener('click', () => setLanguage('en'));
  if (btnZh) btnZh.addEventListener('click', () => setLanguage('zh'));

  // Initialize language (default base: en)
  setLanguage(CURRENT_LANG);

  startPolling();
});
