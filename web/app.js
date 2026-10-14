/* Game Companion Local — dashboard.
   Vanilla JavaScript, no build step. English is the base language; I18N.zh mirrors every key.
   Dynamic text is always escaped: t() escapes its arguments, esc() everything else.
   Polling refreshes the data every 5 s without losing drafts, focus, open details or busy buttons. */
'use strict';

// ----------------------------------------------------------- i18n dictionaries
const I18N = {
  en: {
    // Shell
    brand_title: 'Game Companion',
    brand_edition: 'Local',
    skip_link: 'Skip to content',
    nav_today: 'Today',
    nav_goals: 'Goals',
    nav_plan: 'Schedule',
    nav_runs: 'Runs',
    nav_settings: 'Settings',
    nav_label: 'Sections',
    lang_label: 'Language',
    theme_label: 'Theme',
    theme_system: 'System',
    theme_light: 'Light',
    theme_dark: 'Dark',
    connecting: 'Connecting to the backend…',
    connect_failed: 'Cannot reach the backend ({0}). Start it with Start.bat, then retry.',
    retry: 'Retry',
    req_failed: 'Request failed ({0})',
    working: 'Working…',
    saving: 'Saving…',
    syncing: 'Syncing…',
    starting: 'Starting…',
    saved_not_reloaded: 'Saved, but the latest data could not be loaded. Reload before changing it again.',

    // Dates and durations
    weekdays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    date_fmt: '{0} {1} {2}',
    today: 'Today',
    tomorrow: 'Tomorrow',
    just_now: 'just now',
    rel_in: 'in {0}',
    rel_ago: '{0} ago',
    dur_lt_min: 'under a minute',
    dur_m: '{0} min',
    dur_h: '{0} h',
    dur_hm: '{0} h {1} min',

    // Status strip
    strip_game_day: 'Game day {0}',
    strip_next_run: 'Next run at {0} ({1})',
    strip_schedule_off: 'Schedule off',
    strip_running: 'Running: {0}',
    strip_signed_out: 'Miyoushe not signed in',
    strip_not_admin: 'Not running as administrator',
    strip_plan_only: 'Plans only: runs need Windows',

    // Games and terms
    game_genshin: 'Genshin Impact',
    game_zzz: 'Zenless Zone Zero',
    unit_genshin: 'Original Resin',
    unit_zzz: 'Battery Charge',
    unknown: 'Unknown',
    none: 'None',

    // Today
    btn_run_both: 'Run both games',
    btn_run_now: 'Run now',
    btn_refresh: 'Refresh',
    account_line: '{0}, UID {1}',
    no_account: 'No game account selected',
    stamina_unknown_hint: 'No reading yet. Sign in to Miyoushe or refresh; during a run the tool still uses the real in-game value.',
    stamina_estimate: 'Estimated from {0}, read {1}',
    track_title: 'Next 48 hours',
    track_now: 'Now',
    track_cap: 'Cap {0}',
    track_aria: '{0} over the next 48 hours: {1} now, {2} planned batches. The Schedule page lists them.',
    track_dot: '{0}, {1}: {2} → {3} {4}',
    spend_line_at: 'Next batch at {0} uses ≈ {1}, leaving ≈ {2}.',
    spend_line: 'Next batch uses ≈ {0}, leaving ≈ {1}.',
    full_idle: 'Without runs, full in ≈ {0} ({1}).',
    full_now: 'Full: natural recovery is being wasted',
    notes_issue: 'Stamina refresh: {0}',
    btn_widget: 'Complete account connection',
    btn_widget_manage: 'Manage login',
    btn_widget_reconnect: 'Authorize again',
    btn_cancel_login: 'Cancel login',
    btn_widget_disconnect: 'Sign out of all games',
    widget_title: 'Miyoushe account connection',
    widget_hint: 'Scan once with Miyoushe for both games, including stamina, characters and cultivation data. Existing app authorization is reused automatically.',
    widget_connected: 'One login shared by all games and data sources',
    widget_disconnected: 'Complete the shared login to enable all data sources',
    widget_disconnected_done: 'Signed out of all games.',
    widget_status: 'Authorization status',
    btn_verify: 'Verify',
    btn_new_captcha: 'New captcha',
    dlg_verify_title: 'Miyoushe verification',
    verify_hint: 'Miyoushe wants a person to confirm this account before it shows the notes. Solve its captcha below; the notes are then read again.',
    verify_loading: 'Loading the captcha from Miyoushe…',
    verify_solve: 'Solve the captcha.',
    verify_checking: 'Sending the answer to Miyoushe…',
    verify_closed: 'The captcha was closed. Choose New captcha to try again.',
    verify_failed: 'The captcha did not load: {0}',
    verify_rejected: 'Not verified: {0}',
    next_batch: 'Next batch',
    next_batch_at: 'Next batch at {0}',
    phase_equipment: 'Equipment continuation',
    fact_cap: 'Cap {0}',
    fact_expect: 'Expect {0}',
    fact_spend: '≈ {0} {1}',
    for_goal: '{0}: {1}',
    btn_details: 'Details',
    btn_adjust: 'Adjust',
    detail_task: 'Task',
    detail_spend: 'Planned spend',
    detail_stop: 'Stops',
    detail_calc: 'Calculation',
    detail_reason: 'Reason',
    spend_detail: '{0} × {1} {2} ≈ {3} {2}',
    spend_unknown: 'Decided by the in-game stamina',
    stop_rule: 'When the in-game stamina runs out, or after {0}',
    nothing_title: 'Nothing to farm',
    keeping: 'Keeping {0}',
    waiting_title: 'Waiting ({0})',
    waiting_more: '+{0} more on the Goals page',
    dailies_title: 'Also in every batch',
    latest_run: 'Latest run',
    no_runs_yet: 'No runs yet.',
    view_all: 'View all',
    daily_only: 'Free dailies only',
    exc_signed_out: 'Miyoushe is not signed in, so stamina and material gaps cannot be read.',
    exc_sign_in: 'Sign in',
    exc_not_admin: 'The backend is not running as administrator, so runs cannot control the game window. Start it with Start.bat.',
    exc_plan_only: 'This host runs on Linux: it plans and reads Miyoushe data. Runs need BetterGI and OneDragon, which are Windows programs, so they start from the Windows copy.',
    exc_tool_genshin: 'BetterGI was not found, so Genshin Impact cannot run.',
    exc_tool_zzz: 'ZZZ OneDragon was not found, so Zenless Zone Zero cannot run.',
    exc_set_paths: 'Set paths',
    exc_goal_error: '{0}: {1}',
    exc_open: 'Open',

    // Running batch
    running_title: 'Batch running',
    running_game: '{0}, game {1} of {2}',
    stage_prepare: 'Prepare',
    stage_config: 'Configure tools',
    stage_launch: 'Launch game',
    stage_running: 'Automate',
    stage_collect: 'Collect and restore',
    stage_scan: 'Scan inventory',
    scan_title: 'Inventory scan',
    scan_help: 'Miyoushe shows only equipped pieces. A scan reads every artifact or Drive Disc you own, so equipment farming stops once pieces you own meet a character’s target, and the goal card lists what to equip. The app never equips, locks or dismantles anything.',
    scan_switch: 'Scan the inventory automatically',
    scan_sub: 'After every equipment run, and at least once a day otherwise, before the game closes',
    scan_yas: 'Genshin scanner (yas_artifact.exe, a maintained yas fork)',
    scan_zzz: 'ZZZ scanner (ZZZ-Scanner.Next.exe)',
    scan_last: 'Last scan {0}: {1} pieces',
    scan_never: 'Not scanned yet',
    scan_rules: 'Both scanners read the screen: the game must use the Simplified Chinese UI in a 1920×1080 window, and the mouse must not be touched during a scan (2–5 minutes per 1,000 pieces). Install the scanners yourself; the app opens the bag or the Drive Disc storage and runs them.',
    stage_stopping: 'Stopping…',
    btn_stop: 'Stop current run',

    // Goals
    goals_sub: 'Characters you are building. The order decides what is farmed first.',
    btn_add_goal: 'Add goal',
    goals_empty_title: 'No goals yet',
    goals_empty_desc: 'Add a character to start planning its materials.',
    queue_pos: 'Queue {0} of {1}',
    synced: 'Synced {0}',
    never_synced: 'Not synced yet',
    btn_sync: 'Sync',
    btn_move_up: 'Move up',
    btn_move_down: 'Move down',
    btn_target_settings: 'Target settings',
    btn_cancel_cultivation: 'Cancel cultivation',
    btn_resume_cultivation: 'Resume cultivation',
    btn_delete: 'Delete',
    confirm_cancel: 'Cancel cultivation for {0}? It stops being farmed; targets and progress are kept.',
    confirm_delete: 'Delete the goal for {0}? Its targets and progress are removed.',
    targets_char: 'Character targets',
    targets_weapon_genshin: 'Weapon targets',
    targets_weapon_zzz: 'W-Engine targets',
    col_field: 'Item',
    col_current: 'Current',
    col_target: 'Target',
    lbl_level: 'Level',
    lbl_weapon_level: 'Level',
    talent_normal_attack: 'Normal Attack',
    talent_skill: 'Elemental Skill',
    talent_burst: 'Elemental Burst',
    talent_basic: 'Basic Attack',
    talent_special: 'Special Attack',
    talent_dodge: 'Dodge',
    talent_chain: 'Chain Attack',
    talent_assist: 'Assist',
    talent_core: 'Core Skill',
    priority_label: 'Material priority',
    cat_level: 'Level',
    cat_talents: 'Talents / Skills',
    cat_weapon: 'Weapon / W-Engine',
    mats_title: 'Materials still needed',
    mats_none: 'Nothing left to collect.',
    completed_items: 'Completed items ({0})',
    need_more: 'Need {0} more',
    need_list: 'Need {0}',
    qty_unknown: 'Quantity unavailable',
    plan_units: '{0} / {1} done',
    open_days: 'Open {0}',
    status_collected: 'Collected',
    status_next: 'Next batch',
    status_queued: 'Queued',
    status_paused: 'Paused',
    status_waiting: 'Waiting',
    btn_pause: 'Pause',
    btn_resume: 'Resume',
    tier_material: 'Material',
    tier_need: 'Need',
    tier_have: 'Have',
    tier_short: 'Short',
    stable_list_help: 'Done counts only runs since the last official sync, so nothing is farmed twice.',
    canceled_title: 'Canceled cultivation ({0})',
    canceled_note: 'Canceled goals keep their targets and progress and are never farmed.',

    // Dialogs
    dlg_targets_title: 'Target settings for {0}',
    targets_help: 'Current levels come from the last sync. A target at or below the current level counts as reached.',
    btn_save_changes: 'Save changes',
    btn_discard: 'Discard changes',
    btn_close: 'Close',
    btn_add: 'Add',
    modal_add_title: 'Add a {0} goal',
    search_placeholder: 'Search characters',
    modal_loading: 'Loading characters…',
    modal_source_roster: 'Your characters, from Miyoushe.',
    modal_source_dataset: 'All characters from the offline list. Sign in to Miyoushe to see only yours.',
    no_match: 'No matching characters.',
    already_added: 'Already a goal',
    not_owned: 'Not owned',

    // Schedule
    plan_sub: 'Forecast for the next 3 days, simulated with the same rule as real runs. Past runs are on the Runs page.',
    plan_off_banner: 'The schedule is off, so nothing runs automatically. This is a preview.',
    btn_open_settings: 'Open settings',
    forecast: 'Forecast',
    day_head: '{0}, {1}',
    left_after: '≈ {0} left',
    plan_empty: 'No upcoming slots. Add schedule times in Settings.',

    // Runs
    trigger_schedule: 'Scheduled {0}',
    trigger_manual: 'Manual',
    run_status_SUCCESS: 'Success',
    run_status_PARTIAL: 'Partial',
    run_status_FAILED: 'Failed',
    run_status_SKIPPED: 'Skipped',
    run_status_STOPPED: 'Stopped',
    run_status_RUNNING: 'Running',
    run_done: 'Confirmed {0} of up to {1}',
    run_unverified: 'Amount pending verification',
    run_duration: 'Took {0}',
    runs_empty: 'No runs yet. Start one from Today.',
    no_games: 'No game ran',
    btn_more_runs: 'Show older runs',

    // Settings
    settings_sub: 'Changes are saved together. Secrets are encrypted with Windows DPAPI.',
    settings_sub_linux: 'Changes are saved together. Secrets are stored in files only this user can read.',
    set_account: 'Miyoushe account',
    set_env: 'Environment',
    set_schedule: 'Schedule',
    set_farming: 'Farming rules',
    set_dailies: 'Daily tasks',
    set_notify: 'Notifications',
    set_paths: 'Tools & paths',
    set_images: 'Game images',
    set_network: 'Network',
    unsaved: 'Unsaved changes',
    secret_saved: 'Saved. Leave empty to keep it.',
    btn_clear: 'Clear',
    acc_signed_in: 'Signed in',
    acc_desc: 'Scan once with Miyoushe for stamina, characters and cultivation data across both games. CN-server accounts only.',
    btn_qr: 'Show login QR code',
    btn_qr_new: 'New QR code',
    qr_alt: 'Miyoushe login QR code',
    btn_logout: 'Log out',
    confirm_logout: 'Log out of Miyoushe?',
    env_admin: 'Administrator rights',
    env_admin_ok: 'Running as administrator',
    env_admin_no: 'Not elevated',
    env_plan_only: 'BetterGI and OneDragon are Windows programs; these checks apply to the Windows copy.',
    env_bgi: 'BetterGI',
    env_bgi_template: 'BetterGI template',
    env_od: 'ZZZ OneDragon',
    env_adapter: 'Live Battery Charge adapter',
    env_adapter_help: 'Optional OneDragon patch that lets the last batch use the Battery Charge actually left. Without it, whole card batches are issued and the last one may be skipped.',
    env_game_genshin: 'Genshin Impact client',
    env_game_zzz: 'Zenless Zone Zero client',
    found: 'Found',
    missing: 'Not found',
    installed: 'Installed',
    not_installed: 'Not installed (optional)',
    bundled: 'Bundled template',
    sched_enable: 'Run on schedule',
    sched_enable_sub: 'Runs at the times below. A missed slot still runs within the catch-up limit.',
    autostart: 'Start with Windows',
    autostart_sub: 'One Task Scheduler logon task with highest privileges; no console window.',
    sched_plan_only: 'Runs need Windows; this host only plans.',
    autostart_linux: 'Windows only. On Linux, ./start.sh --service starts the backend with the machine.',
    sched_times: 'Times',
    sched_times_hint: 'HH:MM, comma-separated, China time (UTC+8)',
    sched_games: 'Games on schedule',
    catchup: 'Catch-up limit (hours)',
    catchup_hint: 'How late a missed slot may still run, for example after the PC was off',
    timeout: 'Per-game timeout (minutes)',
    if_running: 'If the game is already running',
    opt_restart: 'Restart it',
    opt_skip: 'Skip this run',
    genshin_claims: 'Genshin Domain rewards',
    opt_mode_double: 'Use 40 Original Resin for 2× rewards first',
    opt_mode_double_sub: 'Recommended. Leftover resin is used 20 at a time.',
    opt_mode_single: 'Use 20 Original Resin per claim',
    opt_mode_single_sub: 'One reward per 20 Original Resin.',
    boss_yield: 'Genshin boss drops per run',
    boss_yield_hint: 'Average at your World Level; converts the gap into boss runs',
    coffee_forecast: 'ZZZ coffee in the forecast (Battery Charge per day)',
    coffee_hint: 'Only affects the Schedule forecast',
    equip_title: 'Equipment continuation',
    equip_help: 'Artifacts and Drive Discs have no end, so they are farmed only when no goal material is left, up to the cumulative cap you set.',
    artifact_switch: 'Genshin: farm Artifacts',
    artifact_sub: 'Domain of Blessing, 20 Original Resin per claim',
    artifact_domain: 'Domain of Blessing',
    artifact_cap: 'Cumulative cap (claims)',
    disc_switch: 'ZZZ: farm Drive Discs',
    disc_sub: 'Area Patrol, 60 Battery Charge per run',
    disc_mission: 'Area Patrol mission',
    disc_cap: 'Cumulative cap (runs)',
    equip_used: 'Used {0} of {1}',
    equip_fixed_hint: 'Used only while no character’s equipment target steers farming',
    gear_wasted: 'Wasted upgrades: {0}',
    gear_status_owned: 'Owned pieces meet the target',
    gear_owned_title: 'With pieces you own: {0}',
    gear_owned_done: 'Equip these to meet the target',
    gear_owned_short: 'Still short with the best pieces you own; farming continues',
    inv_line: 'Inventory scanned {0}: {1} pieces, {2} spare',
    inv_spare_help: 'Spare: unequipped, unlocked pieces that score below 30 for every character that farms equipment. Dismantle them in the game if you like; the app never does.',
    gear_all_hit: 'Every upgrade counts',
    gear_totals: 'Counted rolls: {0}',
    gear_title: 'Drive Discs',
    btn_gear_target: 'Equipment target',
    gear_none_yet: 'Drive Discs not read yet. Sync this character to read them.',
    gear_status_met: 'Target met',
    gear_status_off: 'Not steering farming',
    gear_status_next: 'Next equipment run: {0}',
    gear_status_queued: 'Queued: {0}',
    gear_mains_ok: 'Main stats match',
    gear_mains_bad: 'Main stat mismatch',
    gear_slots_filled: '{0} of {1} slots filled',
    gear_src_custom: 'Your weights',
    gear_src_mine: 'Weights from your own picks on Miyoushe',
    gear_src_recommended: 'Weights from Miyoushe’s recommendation',
    gear_src_official: 'Weights from the build “{0}”',
    gear_src_none: 'No weights: set them in the equipment target',
    gear_read: 'Read {0}',
    gear_runs: '{0} runs farmed for this character',
    gear_weights_line: 'Counted substats: {0}',
    gear_no_weights: 'No substat counts yet: the build lists none and no weights are set.',
    gear_help: 'The score counts the substat rolls already on each disc (an S-rank roll counts 1, A and B rolls less) against the best a disc in that slot could hold, then averages the six slots; an empty slot counts 0. Equip better discs in the game; the score updates on the next sync.',
    gear_slot: 'Slot {0}',
    gear_slot_empty: 'Empty',
    gear_disc_score: 'Disc score',
    gear_level: 'Rank {0} · Lv. {1}',
    dlg_gear_title: 'Equipment target · {0}',
    gear_follow_build: 'Follow the build',
    gear_follow_weights: 'Use the build’s substats',
    gear_set_n: 'Set {0}',
    gear_set_none: 'None',
    gear_set_pieces: 'Pieces',
    gear_pieces: '{0} pieces',
    gear_farm_switch: 'Farm Drive Discs for this character',
    gear_farm_sub: 'Equipment continuation farms for the first unfinished character in goal order, until its target is met or the cap is reached.',
    gear_score_target: 'Score target (0–100)',
    gear_score_hint: 'Average of all slots. A random fully upgraded top-rarity piece scores about 35–40.',
    gear_stage: 'Area Patrol stage',
    gear_stage_auto: 'Automatic: the stage that drops the next set',
    gear_stage_hint: 'Choose one only if the automatic stage is wrong or unknown.',
    gear_sets_title: 'Sets',
    gear_mains_title: 'Main stats, slots 4–6',
    gear_weights_title: 'Substat weights',
    gear_weights_help: '1 counts a roll fully, 0 not at all. With the build’s substats, flat HP, ATK and DEF count by their share of the agent’s base stat.',
    toast_gear: 'Equipment target saved',
    prop_11103: 'HP',
    prop_11102: 'HP%',
    prop_12103: 'ATK',
    prop_12102: 'ATK%',
    prop_13103: 'DEF',
    prop_13102: 'DEF%',
    prop_20103: 'CRIT Rate',
    prop_21103: 'CRIT DMG',
    prop_23203: 'PEN',
    prop_23103: 'PEN Ratio',
    prop_31203: 'Anomaly Proficiency',
    prop_31402: 'Anomaly Mastery',
    prop_30502: 'Energy Regen',
    prop_12202: 'Impact',
    prop_31503: 'Physical DMG Bonus',
    prop_31603: 'Fire DMG Bonus',
    prop_31703: 'Ice DMG Bonus',
    prop_31803: 'Electric DMG Bonus',
    prop_31903: 'Ether DMG Bonus',
    prop_32303: 'Wind DMG Bonus',
    art_title: 'Artifacts',
    art_none_yet: 'Artifacts not read yet. Sync this character to read them.',
    art_help: 'The score counts each substat as its share of a maximum roll (a full-size roll counts 1, smaller rolls less) against the best an artifact in that slot could hold, then averages the five slots; an empty slot counts 0. Equip better artifacts in the game; the score updates on the next sync.',
    art_farm_switch: 'Farm Artifacts for this character',
    art_mains_title: 'Main stats: Sands, Goblet, Circlet',
    art_domain: 'Domain of Blessing',
    art_domain_auto: 'Automatic: the domain that drops the next set',
    art_domain_hint: 'Choose one only if the automatic domain is wrong or unknown.',
    art_level: '{0}★ · +{1}',
    art_slot_1: 'Flower of Life',
    art_slot_2: 'Plume of Death',
    art_slot_3: 'Sands of Eon',
    art_slot_4: 'Goblet of Eonothem',
    art_slot_5: 'Circlet of Logos',
    prop_2: 'HP',
    prop_3: 'HP%',
    prop_5: 'ATK',
    prop_6: 'ATK%',
    prop_8: 'DEF',
    prop_9: 'DEF%',
    prop_20: 'CRIT Rate',
    prop_22: 'CRIT DMG',
    prop_23: 'Energy Recharge',
    prop_26: 'Healing Bonus',
    prop_28: 'Elemental Mastery',
    prop_30: 'Physical DMG Bonus',
    prop_40: 'Pyro DMG Bonus',
    prop_41: 'Electro DMG Bonus',
    prop_42: 'Hydro DMG Bonus',
    prop_43: 'Dendro DMG Bonus',
    prop_44: 'Anemo DMG Bonus',
    prop_45: 'Geo DMG Bonus',
    prop_46: 'Cryo DMG Bonus',
    btn_reset: 'Reset',
    mute_morning: 'Mute audio during morning runs',
    mute_morning_sub: 'Scheduled slots before 12:00; the previous state is restored afterwards.',
    zzz_rewards: 'ZZZ: claim Engagement and New Eridu City Fund rewards',
    genshin_daily: 'Genshin: claim Daily Commission Rewards (Katheryne)',
    genshin_mail: 'Genshin: claim Mail',
    genshin_teapot: 'Genshin: claim Serenitea Pot rewards',
    lbl_path_bettergi: 'BetterGI folder',
    lbl_path_onedragon: 'ZZZ OneDragon folder',
    lbl_path_genshin_exe: 'Genshin Impact executable (optional)',
    lbl_path_zzz_exe: 'Zenless Zone Zero executable (optional)',
    lbl_bgi_template: 'BetterGI One Dragon template config (optional)',
    ph_from_tool: 'Empty: read from the tool config',
    ph_bundled_template: 'Empty: bundled morning template',
    paths_help: 'Folders of your local BetterGI and OneDragon installs. Game executables are read from the tools’ own configs unless set here.',
    template_help: 'Name of one of your BetterGI One Dragon configs to copy party and task settings from.',
    images_status: '{0} saved, {1} waiting, {2} failed',
    images_help: 'Portraits and material icons are saved here the first time the official API returns them. Pages never download images.',
    btn_images: 'Download missing images',
    lbl_port: 'Port',
    lan: 'Allow LAN access',
    lan_sub: 'Other devices on your network can open the dashboard with the password.',
    lbl_password: 'LAN password',
    network_help: 'Port and LAN changes take effect after the backend restarts.',
    notify_events: 'Events',
    ev_batch: 'Summary after each batch',
    ev_quiet: 'Skip the summary when a batch succeeds',
    ev_failure: 'Failures',
    ev_login: 'Miyoushe login expired',
    ev_goal_done: 'A goal’s materials are complete',
    notify_channels: 'Channels',
    ch_toast: 'Windows notification',
    windows_only: 'Windows only.',
    ch_telegram: 'Telegram bot',
    ch_webhook: 'Webhook',
    ch_relay: 'Relay service',
    lbl_tg_chat_id: 'Chat ID',
    lbl_tg_token: 'Bot token',
    lbl_webhook_url: 'Webhook URL',
    lbl_relay_url: 'Relay URL',
    btn_test: 'Send test',
    notify_recent: 'Recent notifications',
    notify_sent: 'Sent',
    notify_failed: 'Failed',
    notify_pending: 'Pending',
    notify_none: 'Nothing sent yet.',

    // Toasts
    toast_batch_started: 'Run started',
    toast_stop_sent: 'Stopping the current run…',
    toast_notes: 'Real-Time Notes refreshed',
    toast_verified: 'Verified; Real-Time Notes read again',
    toast_logged_out: 'Logged out',
    toast_goal_added: '{0} added',
    toast_goal_canceled: 'Cultivation canceled for {0}',
    toast_goal_resumed: 'Cultivation resumed for {0}',
    toast_goal_deleted: '{0} deleted',
    toast_synced: 'Synced with the official calculator',
    toast_paused: 'Item paused',
    toast_resumed: 'Item resumed',
    toast_order: 'Order updated',
    toast_targets: 'Targets saved; recalculating',
    toast_saved: 'Settings saved',
    toast_restart: 'Settings saved. Restart the backend to apply the port or LAN change.',
    toast_equip_reset: 'Counter reset',
    toast_save_first: 'Save your changes first',
    toast_test_sent: 'Test notification sent',
    toast_account: 'Account selected',
    toast_secret_cleared: 'Cleared',
    toast_images: 'Downloading missing images in the background',
    bad_times: 'Times must look like 05:00, 18:00',

    // Separators
    list_sep: ', ',
    clause_sep: '; '
  },

  zh: {
    // Shell
    brand_title: '养成中枢',
    brand_edition: '本地版',
    skip_link: '跳到主要内容',
    nav_today: '今日',
    nav_goals: '培养',
    nav_plan: '日程',
    nav_runs: '记录',
    nav_settings: '设置',
    nav_label: '页面导航',
    lang_label: '语言',
    theme_label: '主题',
    theme_system: '跟随系统',
    theme_light: '浅色',
    theme_dark: '深色',
    connecting: '正在连接后台…',
    connect_failed: '无法连接后台（{0}）。请通过 Start.bat 启动后重试。',
    retry: '重试',
    req_failed: '请求失败（{0}）',
    working: '处理中…',
    saving: '保存中…',
    syncing: '同步中…',
    starting: '正在启动…',
    saved_not_reloaded: '已保存，但无法加载最新数据。请刷新页面后再修改。',

    // Dates and durations
    weekdays: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    date_fmt: '{3}月{1}日 {0}',
    today: '今天',
    tomorrow: '明天',
    just_now: '刚刚',
    rel_in: '{0}后',
    rel_ago: '{0}前',
    dur_lt_min: '不到 1 分钟',
    dur_m: '{0} 分钟',
    dur_h: '{0} 小时',
    dur_hm: '{0} 小时 {1} 分钟',

    // Status strip
    strip_game_day: '游戏日 {0}',
    strip_next_run: '下次执行 {0}（{1}）',
    strip_schedule_off: '定时未开启',
    strip_running: '执行中：{0}',
    strip_signed_out: '米游社未登录',
    strip_not_admin: '未以管理员身份运行',
    strip_plan_only: '仅规划：执行需要 Windows',

    // Games and terms
    game_genshin: '原神',
    game_zzz: '绝区零',
    unit_genshin: '原粹树脂',
    unit_zzz: '电量',
    unknown: '未知',
    none: '无',

    // Today
    btn_run_both: '两款游戏依次执行',
    btn_run_now: '立即执行',
    btn_refresh: '刷新',
    account_line: '{0}，UID {1}',
    no_account: '未选择游戏账号',
    stamina_unknown_hint: '暂无读数。请登录米游社或刷新；执行时工具仍以游戏内实际数值为准。',
    stamina_estimate: '根据{1}的{0}估算',
    track_title: '未来 48 小时',
    track_now: '现在',
    track_cap: '上限 {0}',
    track_aria: '未来 48 小时的{0}：当前 {1}，计划 {2} 批。“日程”页列出了这些批次。',
    track_dot: '{0}，{1}：{2} → {3} {4}',
    spend_line_at: '下一批（{0}）约消耗 {1}，剩余约 {2}。',
    spend_line: '下一批约消耗 {0}，剩余约 {1}。',
    full_idle: '若不执行，约 {0}后回满（{1}）。',
    full_now: '已满：自然恢复正在溢出',
    notes_issue: '体力刷新：{0}',
    btn_widget: '完善账号连接',
    btn_widget_manage: '管理登录',
    btn_widget_reconnect: '重新授权',
    btn_cancel_login: '取消登录',
    btn_widget_disconnect: '退出所有游戏登录',
    widget_title: '米游社账号连接',
    widget_hint: '米游社扫码一次，原神与绝区零的体力、角色和培养数据共用登录。已有 App 授权会自动复用。',
    widget_connected: '各游戏及数据读取共用此登录',
    widget_disconnected: '完善统一登录后，启用全部数据读取通道',
    widget_disconnected_done: '已退出所有游戏登录。',
    widget_status: '授权状态',
    btn_verify: '验证',
    btn_new_captcha: '换一个验证码',
    dlg_verify_title: '米游社人机验证',
    verify_hint: '米游社需要先确认是本人在查看，才会返回便笺。请完成下方的验证码，完成后会重新读取便笺。',
    verify_loading: '正在从米游社加载验证码…',
    verify_solve: '请完成验证码。',
    verify_checking: '正在向米游社提交验证结果…',
    verify_closed: '验证码已关闭。点击“换一个验证码”重试。',
    verify_failed: '验证码未能加载：{0}',
    verify_rejected: '验证未通过：{0}',
    next_batch: '下一批',
    next_batch_at: '下一批 {0}',
    phase_equipment: '装备接续',
    fact_cap: '上限 {0}',
    fact_expect: '预计 {0}',
    fact_spend: '约 {0} {1}',
    for_goal: '{0}：{1}',
    btn_details: '详情',
    btn_adjust: '调整',
    detail_task: '任务',
    detail_spend: '计划消耗',
    detail_stop: '停止条件',
    detail_calc: '计算依据',
    detail_reason: '原因',
    spend_detail: '{0} × {1} {2} ≈ {3} {2}',
    spend_unknown: '以游戏内体力为准',
    stop_rule: '游戏内体力不足时，或完成 {0} 后',
    nothing_title: '暂无可刷项目',
    keeping: '保留{0}',
    waiting_title: '等待中（{0}）',
    waiting_more: '另有 {0} 项，见“培养”页',
    dailies_title: '每批还会执行',
    latest_run: '最近一次执行',
    no_runs_yet: '尚无执行记录。',
    view_all: '查看全部',
    daily_only: '仅免费日常',
    exc_signed_out: '米游社未登录，无法读取体力与材料缺口。',
    exc_sign_in: '去登录',
    exc_not_admin: '后台未以管理员身份运行，执行时无法控制游戏窗口。请通过 Start.bat 启动。',
    exc_plan_only: '此主机运行在 Linux 上，负责规划与读取米游社数据。执行需要 BetterGI 与一条龙这两个 Windows 程序，请在 Windows 端执行。',
    exc_tool_genshin: '未找到 BetterGI，原神无法执行。',
    exc_tool_zzz: '未找到绝区零一条龙，绝区零无法执行。',
    exc_set_paths: '设置路径',
    exc_goal_error: '{0}：{1}',
    exc_open: '查看',

    // Running batch
    running_title: '批次执行中',
    running_game: '{0}（第 {1}/{2} 个游戏）',
    stage_prepare: '准备',
    stage_config: '写入工具配置',
    stage_launch: '启动游戏',
    stage_running: '自动化运行',
    stage_collect: '收集结果并还原',
    stage_scan: '扫描背包',
    scan_title: '背包扫描',
    scan_help: '米游社只显示已装备的装备。扫描会读取你拥有的全部圣遗物或驱动盘：一旦已拥有的装备能达成角色目标，装备刷取即停止，培养卡片会列出需要换上的装备。本程序从不装备、上锁或分解任何装备。',
    scan_switch: '自动扫描背包',
    scan_sub: '每次装备刷取后、以及至少每天一次，在关闭游戏前进行',
    scan_yas: '原神扫描程序（yas_artifact.exe，维护中的 yas 分支）',
    scan_zzz: '绝区零扫描程序（ZZZ-Scanner.Next.exe）',
    scan_last: '上次扫描{0}：{1} 件',
    scan_never: '尚未扫描',
    scan_rules: '两个扫描程序都读取屏幕：游戏需使用简体中文界面、1920×1080 窗口，扫描期间不要操作鼠标（每 1,000 件约 2–5 分钟）。扫描程序需自行安装；本程序会打开背包或驱动盘仓库并运行它们。',
    stage_stopping: '正在停止…',
    btn_stop: '停止当前执行',

    // Goals
    goals_sub: '正在培养的角色。顺序决定先刷哪一项。',
    btn_add_goal: '添加目标',
    goals_empty_title: '还没有培养目标',
    goals_empty_desc: '添加角色后即可开始规划材料。',
    queue_pos: '队列第 {0}/{1} 位',
    synced: '{0}同步',
    never_synced: '尚未同步',
    btn_sync: '同步',
    btn_move_up: '上移',
    btn_move_down: '下移',
    btn_target_settings: '目标设置',
    btn_cancel_cultivation: '取消培养',
    btn_resume_cultivation: '恢复培养',
    btn_delete: '删除',
    confirm_cancel: '确定取消「{0}」的培养？该角色将不再被刷取，目标与进度会保留。',
    confirm_delete: '确定删除「{0}」的培养目标？目标与进度将被移除。',
    targets_char: '角色目标',
    targets_weapon_genshin: '武器目标',
    targets_weapon_zzz: '音擎目标',
    col_field: '项目',
    col_current: '当前',
    col_target: '目标',
    lbl_level: '等级',
    lbl_weapon_level: '等级',
    talent_normal_attack: '普通攻击',
    talent_skill: '元素战技',
    talent_burst: '元素爆发',
    talent_basic: '普通攻击',
    talent_special: '特殊技',
    talent_dodge: '闪避',
    talent_chain: '连携技',
    talent_assist: '支援技',
    talent_core: '核心技',
    priority_label: '材料优先级',
    cat_level: '等级',
    cat_talents: '天赋/技能',
    cat_weapon: '武器/音擎',
    mats_title: '仍需的材料',
    mats_none: '没有需要收集的材料。',
    completed_items: '已收齐的项目（{0}）',
    need_more: '还需 {0} 个',
    need_list: '还需 {0}',
    qty_unknown: '数量未知',
    plan_units: '已完成 {0} / {1}',
    open_days: '开放：{0}',
    status_collected: '已收齐',
    status_next: '下一批',
    status_queued: '排队中',
    status_paused: '已暂停',
    status_waiting: '等待',
    btn_pause: '暂停',
    btn_resume: '恢复',
    tier_material: '材料',
    tier_need: '需要',
    tier_have: '持有',
    tier_short: '缺少',
    stable_list_help: '“已完成”只统计上次官方同步后的执行，不会重复刷取。',
    canceled_title: '已取消的培养（{0}）',
    canceled_note: '已取消的目标保留目标与进度，不会被刷取。',

    // Dialogs
    dlg_targets_title: '{0}的目标设置',
    targets_help: '当前等级来自上次同步。目标不高于当前等级时视为已达成。',
    btn_save_changes: '保存更改',
    btn_discard: '放弃更改',
    btn_close: '关闭',
    btn_add: '添加',
    modal_add_title: '添加{0}培养目标',
    search_placeholder: '搜索角色',
    modal_loading: '正在读取角色…',
    modal_source_roster: '来自米游社的已拥有角色。',
    modal_source_dataset: '离线列表中的全部角色。登录米游社后仅显示已拥有的角色。',
    no_match: '没有匹配的角色。',
    already_added: '已是培养目标',
    not_owned: '未拥有',

    // Schedule
    plan_sub: '未来三天的预测，按与实际执行相同的规则模拟。已执行的批次见“记录”页。',
    plan_off_banner: '定时未开启，不会自动执行；以下仅为预览。',
    btn_open_settings: '前往设置',
    forecast: '预测',
    day_head: '{0} {1}',
    left_after: '剩余约 {0}',
    plan_empty: '暂无后续时段，请在设置中添加执行时间。',

    // Runs
    trigger_schedule: '定时 {0}',
    trigger_manual: '手动',
    run_status_SUCCESS: '成功',
    run_status_PARTIAL: '部分完成',
    run_status_FAILED: '失败',
    run_status_SKIPPED: '跳过',
    run_status_STOPPED: '已停止',
    run_status_RUNNING: '执行中',
    run_done: '确认完成 {0}，上限 {1}',
    run_unverified: '数量待核验',
    run_duration: '耗时 {0}',
    runs_empty: '暂无执行记录，可在“今日”页手动执行。',
    no_games: '未执行游戏',
    btn_more_runs: '显示更早的记录',

    // Settings
    settings_sub: '所有更改统一保存。敏感信息使用 Windows DPAPI 加密。',
    settings_sub_linux: '所有更改统一保存。敏感信息保存在仅当前用户可读的文件中。',
    set_account: '米游社账号',
    set_env: '运行环境',
    set_schedule: '定时',
    set_farming: '刷取规则',
    set_dailies: '日常任务',
    set_notify: '通知',
    set_paths: '工具与路径',
    set_images: '游戏图片',
    set_network: '网络',
    unsaved: '有未保存的更改',
    secret_saved: '已保存，留空则不修改',
    btn_clear: '清除',
    acc_signed_in: '已登录',
    acc_desc: '米游社扫码一次，原神与绝区零的体力、角色和培养数据共用登录。仅支持国服账号。',
    btn_qr: '显示登录二维码',
    btn_qr_new: '重新生成二维码',
    qr_alt: '米游社登录二维码',
    btn_logout: '退出登录',
    confirm_logout: '确定退出米游社登录？',
    env_admin: '管理员权限',
    env_admin_ok: '已以管理员身份运行',
    env_admin_no: '未提权',
    env_plan_only: 'BetterGI 与一条龙是 Windows 程序，以下检查仅适用于 Windows 端。',
    env_bgi: 'BetterGI',
    env_bgi_template: 'BetterGI 模板',
    env_od: '绝区零一条龙',
    env_adapter: '实读电量适配',
    env_adapter_help: '可选的一条龙补丁，让最后一批按实际剩余电量执行。未安装时按整份卡数下发，最后一份可能被跳过。',
    env_game_genshin: '原神客户端',
    env_game_zzz: '绝区零客户端',
    found: '已找到',
    missing: '未找到',
    installed: '已安装',
    not_installed: '未安装（可选）',
    bundled: '内置模板',
    sched_enable: '按时自动执行',
    sched_enable_sub: '在以下时间执行。错过的时段在补跑时限内仍会执行。',
    autostart: '开机登录自启',
    autostart_sub: '创建一个以最高权限运行的登录任务，无控制台窗口。',
    sched_plan_only: '执行需要 Windows，此主机只做规划。',
    autostart_linux: '仅限 Windows。Linux 上运行 ./start.sh --service 即可随系统启动。',
    sched_times: '执行时间',
    sched_times_hint: 'HH:MM，用逗号分隔，北京时间（UTC+8）',
    sched_games: '定时执行的游戏',
    catchup: '补跑时限（小时）',
    catchup_hint: '错过的时段（例如电脑未开机）最晚多久仍可补跑',
    timeout: '单游戏超时（分钟）',
    if_running: '游戏已在运行时',
    opt_restart: '重启游戏',
    opt_skip: '跳过本次',
    genshin_claims: '原神秘境领奖',
    opt_mode_double: '优先使用 40 原粹树脂领取双倍产出',
    opt_mode_double_sub: '推荐。剩余树脂按每次 20 使用。',
    opt_mode_single: '每次使用 20 原粹树脂',
    opt_mode_single_sub: '每 20 原粹树脂领取一次。',
    boss_yield: '原神首领每次平均掉落',
    boss_yield_hint: '按你的世界等级估计，用于把缺口换算为挑战次数',
    coffee_forecast: '绝区零咖啡（预测中每日增加的电量）',
    coffee_hint: '仅影响“日程”预测',
    equip_title: '装备接续',
    equip_help: '圣遗物与驱动盘没有终点，因此只在没有定量材料可刷时刷取，并且不超过你设定的累计上限。',
    artifact_switch: '原神：刷圣遗物',
    artifact_sub: '祝圣秘境，每次 20 原粹树脂',
    artifact_domain: '祝圣秘境',
    artifact_cap: '累计上限（次）',
    disc_switch: '绝区零：刷驱动盘',
    disc_sub: '区域巡防，每场 60 电量',
    disc_mission: '区域巡防关卡',
    disc_cap: '累计上限（场）',
    equip_used: '已用 {0} / {1}',
    equip_fixed_hint: '仅在没有角色的装备目标参与刷取时使用',
    gear_wasted: '未命中 {0} 次',
    gear_status_owned: '已有装备可达成目标',
    gear_owned_title: '使用已有装备：{0}',
    gear_owned_done: '换上这些即可达成目标',
    gear_owned_short: '换上已有的最佳装备后仍未达标，继续刷取',
    inv_line: '背包扫描于{0}：共 {1} 件，闲置 {2} 件',
    inv_spare_help: '闲置：未装备、未上锁，且对每个刷取装备的角色评分都低于 30 的装备。可在游戏中自行分解；本程序从不分解。',
    gear_all_hit: '满命中',
    gear_totals: '计入的强化次数：{0}',
    gear_title: '驱动盘',
    btn_gear_target: '装备目标',
    gear_none_yet: '尚未读取驱动盘。同步该角色即可读取。',
    gear_status_met: '已达成目标',
    gear_status_off: '未参与刷取',
    gear_status_next: '下次装备刷取：{0}',
    gear_status_queued: '排队中：{0}',
    gear_mains_ok: '主属性符合',
    gear_mains_bad: '主属性不符',
    gear_slots_filled: '已装备 {0} / {1}',
    gear_src_custom: '自定义权重',
    gear_src_mine: '权重来自你在米游社的自选属性',
    gear_src_recommended: '权重来自米游社推荐属性',
    gear_src_official: '权重来自方案「{0}」',
    gear_src_none: '没有权重：请在装备目标中设置',
    gear_read: '读取于{0}',
    gear_runs: '已为该角色刷取 {0} 次',
    gear_weights_line: '计入的副属性：{0}',
    gear_no_weights: '尚无计入的副属性：方案未列出，也没有设置权重。',
    gear_help: '评分统计每个驱动盘已有的副属性强化次数（S 级每次计 1，A、B 级按比例折算），与该位置理论最佳相比，再取六个位置的平均；空位计 0。请在游戏中换上更好的驱动盘，下次同步后评分更新。',
    gear_slot: '{0} 号位',
    gear_slot_empty: '空',
    gear_disc_score: '单盘评分',
    gear_level: '{0} 级 · Lv.{1}',
    dlg_gear_title: '装备目标 · {0}',
    gear_follow_build: '跟随方案',
    gear_follow_weights: '使用方案的副属性',
    gear_set_n: '套装 {0}',
    gear_set_none: '无',
    gear_set_pieces: '件数',
    gear_pieces: '{0} 件',
    gear_farm_switch: '为该角色刷驱动盘',
    gear_farm_sub: '装备接续按培养顺序，为第一个未达标的角色刷取，直到达成目标或达到累计上限。',
    gear_score_target: '评分目标（0–100）',
    gear_score_hint: '所有部位的平均分。随机强化满级的最高稀有度装备约 35–40 分。',
    gear_stage: '区域巡防关卡',
    gear_stage_auto: '自动：掉落下一个套装的关卡',
    gear_stage_hint: '仅在自动选择有误或未知时指定。',
    gear_sets_title: '套装',
    gear_mains_title: '主属性（4–6 号位）',
    gear_weights_title: '副属性权重',
    gear_weights_help: '1 表示每次强化全额计入，0 表示不计入。使用方案的副属性时，固定生命值、攻击力、防御力按其占代理人基础属性的比例计入。',
    toast_gear: '装备目标已保存',
    prop_11103: '生命值',
    prop_11102: '生命值%',
    prop_12103: '攻击力',
    prop_12102: '攻击力%',
    prop_13103: '防御力',
    prop_13102: '防御力%',
    prop_20103: '暴击率',
    prop_21103: '暴击伤害',
    prop_23203: '穿透值',
    prop_23103: '穿透率',
    prop_31203: '异常精通',
    prop_31402: '异常掌控',
    prop_30502: '能量自动回复',
    prop_12202: '冲击力',
    prop_31503: '物理伤害加成',
    prop_31603: '火属性伤害加成',
    prop_31703: '冰属性伤害加成',
    prop_31803: '电属性伤害加成',
    prop_31903: '以太伤害加成',
    prop_32303: '风属性伤害加成',
    art_title: '圣遗物',
    art_none_yet: '尚未读取圣遗物。同步该角色即可读取。',
    art_help: '评分把每条副属性折算为满档强化的份数（满档计 1，较小档位按比例），与该部位理论最佳相比，再取五个部位的平均；空位计 0。请在游戏中换上更好的圣遗物，下次同步后评分更新。',
    art_farm_switch: '为该角色刷圣遗物',
    art_mains_title: '主属性：时之沙、空之杯、理之冠',
    art_domain: '祝圣秘境',
    art_domain_auto: '自动：掉落下一个套装的秘境',
    art_domain_hint: '仅在自动选择有误或未知时指定。',
    art_level: '{0}★ · +{1}',
    art_slot_1: '生之花',
    art_slot_2: '死之羽',
    art_slot_3: '时之沙',
    art_slot_4: '空之杯',
    art_slot_5: '理之冠',
    prop_2: '生命值',
    prop_3: '生命值%',
    prop_5: '攻击力',
    prop_6: '攻击力%',
    prop_8: '防御力',
    prop_9: '防御力%',
    prop_20: '暴击率',
    prop_22: '暴击伤害',
    prop_23: '元素充能效率',
    prop_26: '治疗加成',
    prop_28: '元素精通',
    prop_30: '物理伤害加成',
    prop_40: '火元素伤害加成',
    prop_41: '雷元素伤害加成',
    prop_42: '水元素伤害加成',
    prop_43: '草元素伤害加成',
    prop_44: '风元素伤害加成',
    prop_45: '岩元素伤害加成',
    prop_46: '冰元素伤害加成',
    btn_reset: '清零',
    mute_morning: '早间批次静音',
    mute_morning_sub: '12:00 前的定时批次；结束后恢复原有状态。',
    zzz_rewards: '绝区零：领取活跃度与丽都城募奖励',
    genshin_daily: '原神：领取每日委托奖励（凯瑟琳）',
    genshin_mail: '原神：领取邮件',
    genshin_teapot: '原神：领取尘歌壶奖励',
    lbl_path_bettergi: 'BetterGI 目录',
    lbl_path_onedragon: '绝区零一条龙目录',
    lbl_path_genshin_exe: '原神程序路径（可选）',
    lbl_path_zzz_exe: '绝区零程序路径（可选）',
    lbl_bgi_template: 'BetterGI 一条龙模板配置（可选）',
    ph_from_tool: '留空：从工具配置读取',
    ph_bundled_template: '留空：使用内置早间模板',
    paths_help: '本机 BetterGI 与一条龙的安装目录。除非在此填写，游戏程序路径均从工具自身配置读取。',
    template_help: '填写你的某个 BetterGI 一条龙配置名称，以沿用其队伍与任务设置。',
    images_status: '已保存 {0}，待下载 {1}，失败 {2}',
    images_help: '角色头像与材料图标在官方接口首次返回时保存到本地；页面本身不会下载图片。',
    btn_images: '下载缺失的图片',
    lbl_port: '端口',
    lan: '允许局域网访问',
    lan_sub: '同一网络中的其他设备可凭密码打开控制台。',
    lbl_password: '局域网访问密码',
    network_help: '端口与局域网设置在后台重启后生效。',
    notify_events: '事件',
    ev_batch: '每批执行后发送摘要',
    ev_quiet: '批次成功时不发送摘要',
    ev_failure: '执行失败',
    ev_login: '米游社登录失效',
    ev_goal_done: '培养材料收齐',
    notify_channels: '渠道',
    ch_toast: 'Windows 通知',
    windows_only: '仅限 Windows。',
    ch_telegram: 'Telegram 机器人',
    ch_webhook: 'Webhook',
    ch_relay: '中转服务',
    lbl_tg_chat_id: 'Chat ID',
    lbl_tg_token: 'Bot Token',
    lbl_webhook_url: 'Webhook 地址',
    lbl_relay_url: '中转地址',
    btn_test: '发送测试',
    notify_recent: '最近的通知',
    notify_sent: '已发送',
    notify_failed: '发送失败',
    notify_pending: '待发送',
    notify_none: '尚未发送任何通知。',

    // Toasts
    toast_batch_started: '已开始执行',
    toast_stop_sent: '正在停止当前执行…',
    toast_notes: '实时便笺已刷新',
    toast_verified: '验证通过，已重新读取实时便笺',
    toast_logged_out: '已退出登录',
    toast_goal_added: '已添加{0}',
    toast_goal_canceled: '已取消{0}的培养',
    toast_goal_resumed: '已恢复{0}的培养',
    toast_goal_deleted: '已删除{0}',
    toast_synced: '已与官方养成计算器同步',
    toast_paused: '该项目已暂停',
    toast_resumed: '该项目已恢复',
    toast_order: '顺序已更新',
    toast_targets: '目标已保存，正在重新计算',
    toast_saved: '设置已保存',
    toast_restart: '设置已保存。端口或局域网设置需重启后台后生效。',
    toast_equip_reset: '计数已清零',
    toast_save_first: '请先保存更改',
    toast_test_sent: '测试通知已发送',
    toast_account: '已选择账号',
    toast_secret_cleared: '已清除',
    toast_images: '正在后台下载缺失的图片',
    bad_times: '执行时间格式应类似 05:00, 18:00',

    // Separators
    list_sep: '、',
    clause_sep: '；'
  }
};

// ----------------------------------------------------------- state
const store = {
  get(key, fallback) { try { return localStorage.getItem(key) ?? fallback; } catch (_) { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch (_) { /* private mode */ } }
};

let CURRENT_LANG = (() => { try { return localStorage.getItem('gcl_lang') || 'en'; } catch (_) { return 'en'; } })();
let THEME = store.get('gcl_theme', 'system');
let STATE = null;
let ASSETS = new Set();
let LAST_ERROR = null;
let CLOCK_SKEW = 0;
let REQ_SEQ = 0;
let APPLIED_SEQ = 0;
let ROUTE = { tab: 'today', arg: null };
let GOALS_GAME = store.get('gcl_goals_game', 'zzz');
let SETTINGS_DIRTY = false;
let SETTINGS_ERROR = '';
let MORE_RUNS = null;
let MODAL = null;
const OPEN = new Set();          // expanded detail rows (materials, schedule entries, next-batch details)
const PENDING = new Map();       // busy buttons that survive re-renders: selector -> label key

const GAMES = ['zzz', 'genshin'];
const TABS = [['today', 'home', 'nav_today'], ['goals', 'target', 'nav_goals'], ['plan', 'calendar', 'nav_plan'],
              ['runs', 'history', 'nav_runs'], ['settings', 'sliders', 'nav_settings']];
const RECOVERY_MINUTES = { genshin: 8, zzz: 6 };
const UNIT_ICON = { genshin: 'resin', zzz: 'battery' };
const STAGES = ['stage_prepare', 'stage_config', 'stage_launch', 'stage_running', 'stage_scan', 'stage_collect'];
const DAILY_ICON = { daily_mail: 'mail', daily_teapot: 'cup', daily_commission: 'clipboard',
                     daily_onedragon: 'list', daily_zzz_rewards: 'gift' };
const RUN_STATUS = { SUCCESS: ['good', 'check'], PARTIAL: ['warn', 'alert'], FAILED: ['bad', 'x'],
                     SKIPPED: ['muted', 'skip'], STOPPED: ['muted', 'stop'], RUNNING: ['info', 'pulse'] };
const BUSY_KEYS = ['action', 'id', 'key', 'game', 'games', 'dir', 'index', 'channel'];

// ----------------------------------------------------------- text helpers
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function esc(value) { return String(value ?? '').replace(/[&<>"']/g, c => ESC[c]); }
function lookup(key) {
  const dict = I18N[CURRENT_LANG] || I18N.en;
  if (dict[key] !== undefined) return dict[key];
  return I18N.en[key] !== undefined ? I18N.en[key] : key;
}
function format(text, args, escape) {
  return text.replace(/\{(\d+)\}/g, (match, i) => {
    const v = args[i];
    if (v === undefined || v === null) return match;
    return escape ? esc(v) : String(v);
  });
}
/** Translated text, safe for HTML: arguments are escaped. */
function t(key, ...args) { const s = lookup(key); return typeof s === 'string' ? format(s, args, true) : s; }
/** Translated plain text for textContent, title, confirm(). */
function tp(key, ...args) { const s = lookup(key); return typeof s === 'string' ? format(s, args, false) : s; }

const ICONS = {
  home: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/><path d="M12 8v4l3 2"/>',
  sliders: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
  play: '<path d="M7 4l13 8-13 8z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="1"/>',
  pause: '<path d="M9 5v14M15 5v14"/>',
  skip: '<path d="M5 5l10 7-10 7z"/><path d="M19 5v14"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  check: '<path d="M4 12l5 5L20 6"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  alert: '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  down: '<path d="M12 5v14M6 13l6 6 6-6"/>',
  left: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  right: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M6 12h12"/>',
  chevron: '<path d="M6 9l6 6 6-6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  monitor: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
  resin: '<path d="M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z"/>',
  battery: '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2M6 10v4M10 10v4"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
  gift: '<rect x="3" y="8" width="18" height="5" rx="1"/><path d="M5 13v8h14v-8M12 8v13M12 8c-2-4-6-4-6-1s6 1 6 1zM12 8c2-4 6-4 6-1s-6 1-6 1z"/>',
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 13l2 2 4-4"/>',
  cup: '<path d="M5 9h11v5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5z"/><path d="M16 11h2a2 2 0 0 1 0 4h-2M9 3v3M12 3v3"/>',
  list: '<path d="M9 6h12M9 12h12M9 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
  box: '<path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
  folder: '<path d="M3 6h7l2 2h9v11H3z"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  bell: '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  qr: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM17 17h4v4M20 14h1"/>',
  logout: '<path d="M15 4h4v16h-4"/><path d="M10 17l5-5-5-5M15 12H3"/>',
  send: '<path d="M4 12l16-8-6 16-2-7z"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13 7l4 4"/>',
  ban: '<circle cx="12" cy="12" r="9"/><path d="M6 6l12 12"/>'
};
function icon(name, cls = '') {
  if (name === 'pulse') return '<span class="pulse" aria-hidden="true"></span>';
  return `<svg class="ic${cls ? ' ' + cls : ''}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[name] || ''}</svg>`;
}
/** A button with an icon and a text label; the label becomes a processing text while busy. */
function button(action, ic, label, cls = '', attrs = '') {
  return `<button type="button" class="btn ${cls}" data-action="${action}" ${attrs}>${ic ? icon(ic) : ''}<span class="txt">${label}</span></button>`;
}
function iconButton(action, ic, label, attrs = '') {
  return `<button type="button" class="btn icon sm quiet" data-action="${action}" aria-label="${label}" title="${label}" ${attrs}>${icon(ic)}</button>`;
}
function badge(kind, ic, label) { return `<span class="badge ${kind}">${icon(ic)}<span>${label}</span></span>`; }
function help(html, ic = 'info') { return `<p class="help">${icon(ic)}<span>${html}</span></p>`; }
function alertBox(kind, ic, html, action = '') {
  return `<div class="alert ${kind}" role="${kind === 'bad' ? 'alert' : 'status'}">${icon(ic)}<div class="body"><span>${html}</span>${action}</div></div>`;
}
function linkButton(href, ic, label) { return `<a class="btn sm" href="${href}">${icon(ic)}<span>${label}</span></a>`; }
function runBadge(status) { const [kind, ic] = RUN_STATUS[status] || ['muted', 'minus']; return badge(kind, ic, t('run_status_' + status)); }
function unitTerm(game) { return `<span class="term">${icon(UNIT_ICON[game])}<span>${t('unit_' + game)}</span></span>`; }
function portrait(game, id, name, size = '') {
  const k = `${game}/character/${id}`;
  if (id && ASSETS.has(k)) return `<span class="portrait ${size}"><img src="/assets/${esc(k)}" alt="" loading="lazy"></span>`;
  return `<span class="portrait fallback ${size}" aria-hidden="true">${esc(String(name || '?').slice(0, 1))}</span>`;
}
function materialIcon(game, id, cls = 'mat-icon') {
  const k = `${game}/material/${id}`;
  return id && ASSETS.has(k) ? `<img class="${cls}" src="/assets/${esc(k)}" alt="" loading="lazy">` : '';
}

// ----------------------------------------------------------- time helpers (game clock is China time, UTC+8)
const pad = n => String(n).padStart(2, '0');
function num(v) { return typeof v === 'number' ? v.toLocaleString(CURRENT_LANG === 'zh' ? 'zh-CN' : 'en-US') : v; }
function nowMs() { return Date.now() + CLOCK_SKEW; }
function toMs(iso) { const v = Date.parse(iso); return Number.isNaN(v) ? null : v; }
function cnParts(ms) {
  const d = new Date(ms + 8 * 3600e3);
  return { y: d.getUTCFullYear(), m: d.getUTCMonth() + 1, d: d.getUTCDate(), h: d.getUTCHours(), mi: d.getUTCMinutes(), wd: (d.getUTCDay() + 6) % 7 };
}
function clockOf(ms) { const p = cnParts(ms); return `${pad(p.h)}:${pad(p.mi)}`; }
function clock(iso) { const v = toMs(iso); return v === null ? '–' : clockOf(v); }
function dayKeyOf(ms) { const p = cnParts(ms); return `${p.y}-${p.m}-${p.d}`; }
function dateOf(ms) { const p = cnParts(ms); return tp('date_fmt', lookup('weekdays')[p.wd], p.d, lookup('months')[p.m - 1], p.m); }
function dayLabel(ms) {
  const key = dayKeyOf(ms);
  if (key === dayKeyOf(nowMs())) return tp('today');
  if (key === dayKeyOf(nowMs() + 864e5)) return tp('tomorrow');
  return dateOf(ms);
}
function whenOf(ms) { return dayKeyOf(ms) === dayKeyOf(nowMs()) ? clockOf(ms) : `${dateOf(ms)} ${clockOf(ms)}`; }
function whenLabel(iso) { const v = toMs(iso); return v === null ? '–' : whenOf(v); }
function duration(minutes) {
  const m = Math.max(0, Math.round(minutes));
  if (m < 1) return tp('dur_lt_min');
  const h = Math.floor(m / 60), r = m % 60;
  if (!h) return tp('dur_m', r);
  return r ? tp('dur_hm', h, r) : tp('dur_h', h);
}
function relative(iso) {
  const v = toMs(iso);
  if (v === null) return '';
  const diff = (v - nowMs()) / 60000;
  if (Math.abs(diff) < 1) return tp('just_now');
  return diff > 0 ? tp('rel_in', duration(diff)) : tp('rel_ago', duration(-diff));
}
function gameDayLabel() {
  const [y, m, d] = String(STATE.game_date || '').split('-').map(Number);
  return y ? tp('date_fmt', lookup('weekdays')[STATE.weekday] || '', d, lookup('months')[m - 1], m) : '';
}

// ----------------------------------------------------------- API, toasts, busy buttons
async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'X-GC': '1' } };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) throw new Error((data && data.error) || tp('req_failed', res.status));
  return data;
}

function toast(message, kind = 'ok') {
  const box = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.setAttribute('role', kind === 'error' ? 'alert' : 'status');
  el.innerHTML = `${icon(kind === 'error' ? 'alert' : 'check')}<span></span>`;
  el.querySelector('span').textContent = message;
  box.appendChild(el);
  setTimeout(() => el.remove(), kind === 'error' ? 9000 : 4500);
}

function busySelector(el) {
  if (!el || !el.dataset || !el.dataset.action) return null;
  return BUSY_KEYS.filter(k => el.dataset[k] !== undefined).map(k => `[data-${k}="${CSS.escape(el.dataset[k])}"]`).join('');
}
function markBusy(el, labelKey) {
  if (el.getAttribute('aria-busy') === 'true') return;
  const txt = el.querySelector('.txt');
  el.style.minWidth = `${el.offsetWidth}px`;
  el.dataset.label = txt ? txt.textContent : '';
  el.setAttribute('aria-busy', 'true');
  el.disabled = true;
  el.insertAdjacentHTML('afterbegin', '<span class="spin" aria-hidden="true"></span>');
  if (txt) txt.textContent = tp(labelKey);
}
function unmarkBusy(el) {
  if (el.getAttribute('aria-busy') !== 'true') return;
  el.removeAttribute('aria-busy');
  el.disabled = false;
  el.querySelector('.spin')?.remove();
  const txt = el.querySelector('.txt');
  if (txt && el.dataset.label !== undefined) txt.textContent = el.dataset.label;
  el.style.minWidth = '';
}
/** Show a pending action on its button (also after re-renders); errors become toasts. */
async function busy(btn, fn, labelKey = 'working') {
  const sel = busySelector(btn);
  if (sel && PENDING.has(sel)) return;
  if (sel) PENDING.set(sel, labelKey);
  if (btn) markBusy(btn, labelKey);
  try {
    await fn();
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    if (sel) PENDING.delete(sel);
    (sel ? document.querySelectorAll(sel) : []).forEach(unmarkBusy);
    if (btn) unmarkBusy(btn);
  }
}
function reapplyBusy(root) {
  PENDING.forEach((labelKey, sel) => root.querySelectorAll(sel).forEach(el => markBusy(el, labelKey)));
}
/** Write, then load fresh state; feedback appears after the new state is drawn. */
async function commit(btn, request, message, labelKey, changed) {
  await busy(btn, async () => {
    await request();
    const ok = await refreshState(true);
    toast(ok ? message : tp('saved_not_reloaded'), ok ? 'ok' : 'error');
    if (ok && changed) flash(changed);
  }, labelKey);
}
/** Briefly mark the element a change landed on. */
function flash(selector) {
  const el = document.querySelector(selector);
  if (!el) return;
  el.classList.remove('flash');
  void el.offsetWidth;  // restart the animation
  el.classList.add('flash');
  el.addEventListener('animationend', () => el.classList.remove('flash'), { once: true });
}
const goalSel = id => `#goal-${CSS.escape(id)}`;

// ----------------------------------------------------------- state loading
async function refreshState(force = false) {
  const seq = ++REQ_SEQ;
  try {
    const next = await api('/api/state');
    if (seq < APPLIED_SEQ) return true;  // a newer response is already on screen
    APPLIED_SEQ = seq;
    CLOCK_SKEW = (toMs(next.now) ?? Date.now()) - Date.now();
    STATE = next;
    ASSETS = new Set(next.assets || []);
    LAST_ERROR = null;
    await syncBackendLang();
  } catch (err) {
    if (seq >= APPLIED_SEQ) LAST_ERROR = err.message;
    render();
    return false;
  }
  render(force);
  updateWidgetDialog();
  return true;
}

// Backend-generated text (plan reasons, errors, run summaries) follows the UI language.
async function syncBackendLang() {
  if (!STATE || (STATE.settings?.ui?.lang || 'en') === CURRENT_LANG) return;
  try {
    await api('/api/lang', 'POST', { lang: CURRENT_LANG });
    STATE = await api('/api/state');
    ASSETS = new Set(STATE.assets || []);
  } catch (_) { /* keep the current state */ }
}

// ----------------------------------------------------------- shell: tabs, language, theme, strip
function renderShell() {
  document.getElementById('brand-title').textContent = tp('brand_title');
  document.getElementById('brand-edition').textContent = tp('brand_edition');
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = tp(el.dataset.i18n); });
  document.title = `${tp('brand_title')} ${tp('brand_edition')}`;
  const tabs = document.getElementById('tabs');
  tabs.setAttribute('aria-label', tp('nav_label'));
  tabs.innerHTML = TABS.map(([id, ic, key]) =>
    `<a href="#/${id}" id="tab-${id}" data-tab="${id}"${id === ROUTE.tab ? ' aria-current="page"' : ''}>${icon(ic)}<span>${t(key)}</span></a>`).join('');
  document.querySelectorAll('#lang-switch [data-lang]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === CURRENT_LANG)));
  document.getElementById('lang-switch').setAttribute('aria-label', tp('lang_label'));
  renderThemeMenu();
}

function renderThemeMenu() {
  const options = [['system', 'monitor'], ['light', 'sun'], ['dark', 'moon']];
  const current = options.find(o => o[0] === THEME) || options[0];
  const menu = document.getElementById('theme-menu');
  const open = menu.open;
  menu.innerHTML = `
    <summary class="btn sm" aria-label="${t('theme_label')}: ${t('theme_' + current[0])}">${icon(current[1])}<span class="label">${t('theme_' + current[0])}</span>${icon('chevron', 'chev')}</summary>
    <div class="menu-list" role="menu" aria-label="${t('theme_label')}">
      ${options.map(([id, ic]) => `<button type="button" role="menuitemradio" aria-checked="${id === THEME}" data-action="theme" data-theme="${id}">${icon(ic)}<span>${t('theme_' + id)}</span>${icon('check', 'check')}</button>`).join('')}
    </div>`;
  menu.open = open;
}

function applyTheme(theme) {
  THEME = ['light', 'dark'].includes(theme) ? theme : 'system';
  if (THEME === 'system') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = THEME;
  store.set('gcl_theme', THEME);
  renderThemeMenu();
}

function setLanguage(lang) {
  CURRENT_LANG = I18N[lang] ? lang : 'en';
  store.set('gcl_lang', CURRENT_LANG);
  document.documentElement.lang = CURRENT_LANG === 'zh' ? 'zh-CN' : 'en';
  renderShell();
  document.getElementById('savebar').dataset.lang = '';
  render(true);
  if (STATE) refreshState();
}

function chip(ic, text, kind = '') { return `<span class="chip ${kind}">${icon(ic)}<span>${esc(text)}</span></span>`; }

function renderStrip() {
  const el = document.getElementById('status-strip');
  if (!STATE) {
    el.innerHTML = LAST_ERROR ? chip('alert', tp('connect_failed', LAST_ERROR), 'bad') : chip('clock', tp('connecting'));
    return;
  }
  const r = STATE.runner || {};
  const chips = [chip('calendar', tp('strip_game_day', gameDayLabel()))];
  if (r.running) chips.push(chip('pulse', tp('strip_running', r.stage || ''), 'info'));
  else if (STATE.automation === false) chips.push(chip('monitor', tp('strip_plan_only')));
  else if (STATE.settings?.schedule?.enabled && STATE.next_slot) chips.push(chip('clock', tp('strip_next_run', whenLabel(STATE.next_slot), relative(STATE.next_slot))));
  else chips.push(chip('pause', tp('strip_schedule_off')));
  if (!STATE.logged_in) chips.push(chip('user', tp('strip_signed_out'), 'warn'));
  if (!STATE.admin && STATE.automation !== false) chips.push(chip('shield', tp('strip_not_admin'), 'warn'));
  if (LAST_ERROR) chips.push(chip('alert', tp('connect_failed', LAST_ERROR), 'bad'));
  el.innerHTML = chips.join('');
}

// ----------------------------------------------------------- render orchestration
const VIEWS = { today: renderToday, goals: renderGoals, plan: renderPlan, runs: renderRuns, settings: renderSettings };

function render(force = false) {
  renderStrip();
  const el = document.getElementById(`view-${ROUTE.tab}`);
  if (!STATE) {
    el.innerHTML = LAST_ERROR
      ? alertBox('bad', 'alert', t('connect_failed', LAST_ERROR), button('retry', 'refresh', t('retry'), 'sm'))
      : '<div class="skeleton" aria-hidden="true"><div class="bar"></div><div class="bar"></div></div>';
    return;
  }
  keepState(el, () => VIEWS[ROUTE.tab](force));
  updateSavebar();
}

/** Re-render without losing open <details data-keep> panels, keyboard focus or busy buttons. */
function keepState(el, renderView) {
  const open = new Set([...el.querySelectorAll('details[data-keep][open]')].map(d => d.dataset.keep));
  const a = document.activeElement;
  const focus = a && el.contains(a) ? busySelector(a) : null;
  renderView();
  el.querySelectorAll('details[data-keep]').forEach(d => { if (open.has(d.dataset.keep)) d.open = true; });
  reapplyBusy(el);
  if (focus && !el.contains(document.activeElement)) el.querySelector(focus)?.focus({ preventScroll: true });
}

function pageHead(title, sub, actions = '') {
  return `<div class="page-head"><div><h1>${title}</h1>${sub ? `<p class="sub">${sub}</p>` : ''}</div>${actions ? `<div class="actions">${actions}</div>` : ''}</div>`;
}

function toggleButton(id) {
  const open = OPEN.has(id);
  return `<button type="button" class="btn sm quiet" data-action="toggle" data-key="${esc(id)}" aria-expanded="${open}">${icon('chevron', 'chev')}<span class="txt">${t('btn_details')}</span></button>`;
}

function detailPanel(id, html, cls = '') {
  return `<div class="${cls}" data-detail="${esc(id)}"${OPEN.has(id) ? '' : ' hidden'}>${html}</div>`;
}

function detailList(rows) {
  return `<dl class="details">${rows.filter(Boolean).map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
}

// ----------------------------------------------------------- 1. Today
function renderToday() {
  const el = document.getElementById('view-today');
  const r = STATE.runner || {};
  el.innerHTML = `
    ${pageHead(t('nav_today'), '', button('run', 'play', t('btn_run_both'), '', `data-games="zzz,genshin"${r.running || STATE.automation === false ? ' disabled' : ''}`))}
    ${exceptions()}
    ${r.running ? runningPanel(r) : ''}
    <div class="grid two">${GAMES.map(gameCard).join('')}</div>
    <div class="mt">${latestRunPanel()}</div>`;
}

function exceptions() {
  const list = [];
  const c = STATE.check || {};
  if (!STATE.logged_in) list.push(alertBox('warn', 'user', t('exc_signed_out'), linkButton('#/settings/set-account', 'user', t('exc_sign_in'))));
  const plansOnly = STATE.automation === false;
  if (plansOnly) list.push(alertBox('info', 'monitor', t('exc_plan_only')));
  else if (!STATE.admin) list.push(alertBox('warn', 'shield', t('exc_not_admin')));
  const scheduled = STATE.settings?.schedule?.games || [];
  GAMES.forEach(g => {
    const hasGoals = (STATE.goals?.[g] || []).some(x => x.enabled);
    if (!plansOnly && c[g] && !c[g].tool_ok && (hasGoals || scheduled.includes(g))) {
      list.push(alertBox('bad', 'alert', t('exc_tool_' + g), linkButton('#/settings/set-paths', 'folder', t('exc_set_paths'))));
    }
  });
  GAMES.forEach(g => (STATE.goals?.[g] || []).filter(x => x.enabled && (x.calc_error || x.observe_error)).forEach(x => {
    list.push(alertBox('bad', 'alert', t('exc_goal_error', x.name, x.calc_error || x.observe_error),
      linkButton(`#/goals/${encodeURIComponent(x.id)}`, 'target', t('exc_open'))));
  }));
  return list.length ? `<div class="alerts">${list.join('')}</div>` : '';
}

function runningPanel(r) {
  const key = r.stage_key || 'stage_prepare';
  const stages = STAGES.filter(k => k !== 'stage_scan' || r.scan);  // the scan step only when this game scans
  const current = stages.indexOf(key);
  const games = r.games || [];
  const stopping = key === 'stage_stopping';
  const steps = stages.map((k, i) => {
    const state = current < 0 ? '' : i < current ? 'done' : i === current ? 'current' : '';
    return `<li class="step ${state}">${state === 'done' ? icon('check') : `<span class="n">${i + 1}</span>`}<span>${t(k)}</span></li>`;
  }).join('');
  const game = r.game ? t('running_game', tp('game_' + r.game), games.indexOf(r.game) + 1, games.length) : '';
  return `
    <section class="panel running" aria-live="polite">
      <div class="head">${icon('pulse')}<b>${stopping ? t('stage_stopping') : t('running_title')}</b><span class="ink-2">${game}</span></div>
      <ol class="steps">${steps}</ol>
      ${button('stop', 'stop', t('btn_stop'), 'sm danger', stopping ? 'disabled' : '')}
    </section>`;
}

/** The next batch's numbers: the forecast row for the next scheduled slot, else the plan with today's stamina. */
function nextFacts(game) {
  const item = STATE.plans?.[game]?.item;
  if (!item) return null;
  if (STATE.settings?.schedule?.enabled && STATE.next_slot) {
    const r = (STATE.forecast?.rows || []).find(x => x.game === game && x.at === STATE.next_slot);
    if (r && r.task) return { at: r.at, expected: r.expected, spend: r.spend, left: r.left };
  }
  const st = STATE.stamina?.[game];
  const spend = item.expected != null ? item.expected * item.cost : null;
  return { at: null, expected: item.expected, spend, left: st && spend != null ? Math.max(0, st.value - spend) : null };
}

function gameCard(game) {
  const st = STATE.stamina?.[game];
  const plan = STATE.plans?.[game] || {};
  const item = plan.item;
  const acc = STATE.accounts?.[game];
  const health = STATE.health?.['notes-' + game];
  const running = STATE.runner?.running;
  const nf = nextFacts(game);
  return `
    <article class="panel game-card">
      <header class="panel-head">
        <div><h2>${t('game_' + game)}</h2><p class="ink-2">${acc ? t('account_line', acc.name || '–', acc.uid) : t('no_account')}</p></div>
        <div class="actions">
          ${button('refresh-notes', 'refresh', t('btn_refresh'), 'sm', `data-game="${game}"${STATE.logged_in && acc ? '' : ' disabled'}`)}
          ${button('run', 'play', t('btn_run_now'), 'sm primary', `data-games="${game}"${running || STATE.automation === false ? ' disabled' : ''}`)}
        </div>
      </header>
      ${staminaBlock(game, st, nf)}
      ${health && health.ok === false ? alertBox('warn', 'alert', t('notes_issue', health.reason || ''),
        acc ? button('widget', 'qr', t(STATE.qr?.unified ? 'btn_widget_reconnect' : 'btn_widget'), 'sm') +
          (health.captcha ? button('verify', 'shield', t('btn_verify'), 'sm', `data-game="${game}"`) : '') : '') : ''}
      ${item ? nextBlock(game, plan, item, nf) : idleBlock(game, plan)}
      ${waitingBlock(plan)}
      ${dailiesBlock(plan)}
    </article>`;
}

function staminaBlock(game, st, nf) {
  if (!st) return `<div class="stamina"><div class="figure"><span class="value">?</span>${unitTerm(game)}</div>${help(t('stamina_unknown_hint'))}</div>`;
  const fullMinutes = (st.cap - st.value) * RECOVERY_MINUTES[game];
  const facts = [
    nf && nf.spend > 0 ? [icon('target'), nf.at ? t('spend_line_at', whenLabel(nf.at), num(nf.spend), num(nf.left)) : t('spend_line', num(nf.spend), num(nf.left))] : null,
    st.value >= st.cap ? [icon('alert'), t('full_now')] : [icon('clock'), t('full_idle', duration(fullMinutes), whenOf(nowMs() + fullMinutes * 60000))],
    [icon('info'), t('stamina_estimate', st.source, relative(st.seen))]
  ].filter(Boolean);
  return `
    <div class="stamina">
      <div class="figure"><span class="value">${st.value}</span><span class="cap num">/ ${st.cap}</span>${unitTerm(game)}</div>
      ${staminaTrack(game, st)}
      <ul class="list facts-list">${facts.map(([ic, text]) => `<li>${ic}<span class="t">${text}</span></li>`).join('')}</ul>
    </div>`;
}

// ----------------------------------------------------------- 48-hour stamina track (recovery up to the cap, a drop per batch)
const TRACK_HOURS = 48;
const TRACKS = {};

function trackModel(game, st) {
  const now = nowMs(), span = TRACK_HOURS * 3600e3, end = now + span;
  const rate = RECOVERY_MINUTES[game] * 60000;
  const cap = st.cap;
  const pts = [[now, st.value]];
  const marks = [];
  let t0 = now, v = st.value;
  const advance = to => {
    if (v < cap) {
      const full = t0 + (cap - v) * rate;
      if (full < to) { pts.push([full, cap]); v = cap; } else v += (to - t0) / rate;
    }
    t0 = to;
    pts.push([t0, v]);
  };
  (STATE.forecast?.rows || []).filter(r => r.game === game && r.stamina != null)
    .map(r => [toMs(r.at), r]).filter(([at]) => at > now && at <= end)
    .forEach(([at, r]) => {
      advance(at);
      if (Math.abs(r.stamina - v) > 1.5) { v = r.stamina; pts.push([at, v]); }  // e.g. the daily ZZZ coffee
      if (r.spend > 0) {
        marks.push({ at, before: Math.round(v), after: Math.round(r.left), row: r });
        v = r.left;
        pts.push([at, v]);
      }
    });
  advance(end);
  return { now, span, cap, top: Math.max(cap, ...pts.map(p => p[1])) * 1.1, pts, marks };
}

function staminaTrack(game, st) {
  const m = trackModel(game, st);
  TRACKS[game] = m;
  const X = time => ((time - m.now) / m.span) * 100;
  const Y = val => (1 - val / m.top) * 100;
  const line = m.pts.map(([tt, vv], i) => `${i ? 'L' : 'M'}${(X(tt) * 10).toFixed(1)} ${Y(vv).toFixed(2)}`).join(' ');
  const unit = tp('unit_' + game);
  const ticks = [];
  const p = cnParts(m.now);
  for (let mid = Date.UTC(p.y, p.m - 1, p.d + 1) - 8 * 3600e3; mid < m.now + m.span; mid += 864e5) ticks.push(mid);
  const dots = m.marks.map(k => {
    const x = X(k.at);
    const side = x > 78 ? ' end' : x < 22 ? ' start' : '';
    const label = tp('track_dot', whenOf(k.at), k.row.task, k.before, k.after, unit);
    return `<button type="button" class="trk-dot${side}" style="left:${x.toFixed(2)}%;top:${Y(k.before).toFixed(2)}%" aria-label="${esc(label)}">
      <span class="trk-tip"><b>${num(k.before)} → ${num(k.after)}</b><span>${esc(whenOf(k.at))}</span><span>${esc(k.row.task)}</span></span></button>`;
  }).join('');
  return `
    <figure class="trk">
      <figcaption><span>${t('track_title')}</span><a href="#/plan">${t('nav_plan')}</a></figcaption>
      <div class="trk-plot" data-game="${game}">
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none" role="img" aria-label="${t('track_aria', unit, st.value, m.marks.length)}">
          ${ticks.map(tk => `<line class="trk-grid" x1="${(X(tk) * 10).toFixed(1)}" x2="${(X(tk) * 10).toFixed(1)}" y1="0" y2="100" vector-effect="non-scaling-stroke"/>`).join('')}
          <line class="trk-grid" x1="0" x2="1000" y1="${Y(m.cap).toFixed(2)}" y2="${Y(m.cap).toFixed(2)}" vector-effect="non-scaling-stroke"/>
          <path class="trk-area" d="${line} L1000 100 L0 100 Z"/>
          <path class="trk-line" d="${line}" vector-effect="non-scaling-stroke"/>
        </svg>
        <span class="trk-cap" style="top:${Y(m.cap).toFixed(2)}%">${t('track_cap', m.cap)}</span>
        <span class="trk-dot now" style="left:0%;top:${Y(st.value).toFixed(2)}%" aria-hidden="true"></span>
        ${dots}
      </div>
      <div class="trk-axis" aria-hidden="true"><span class="start">${t('track_now')}</span>${ticks.map(tk =>
        `<span style="left:${X(tk).toFixed(2)}%">${esc(lookup('weekdays')[cnParts(tk).wd])}</span>`).join('')}</div>
    </figure>`;
}

function trackValueAt(m, time) {
  for (let i = m.pts.length - 1; i > 0; i--) {
    const [t1, v1] = m.pts[i], [ta, va] = m.pts[i - 1];
    if (time >= ta && time <= t1) return t1 === ta ? v1 : va + (v1 - va) * (time - ta) / (t1 - ta);
  }
  return m.pts[0][1];
}

/** Crosshair: follows the pointer over a track, snapping to a batch when close. */
function trackPointer(e) {
  const plot = e.target.closest && e.target.closest('.trk-plot');
  document.querySelectorAll('.trk-plot .trk-x').forEach(el => { if (!plot || !plot.contains(el)) el.parentElement.querySelectorAll('.trk-x, .trk-read').forEach(n => n.remove()); });
  if (!plot || e.target.closest('.trk-dot')) { plot?.querySelectorAll('.trk-x, .trk-read').forEach(n => n.remove()); return; }
  const m = TRACKS[plot.dataset.game];
  if (!m) return;
  const rect = plot.getBoundingClientRect();
  const px = Math.min(rect.width, Math.max(0, e.clientX - rect.left));
  const mark = m.marks.find(k => Math.abs(((k.at - m.now) / m.span) * rect.width - px) < 14);
  const time = mark ? mark.at : Math.round((m.now + (px / rect.width) * m.span) / 600000) * 600000;
  let x = plot.querySelector('.trk-x'), read = plot.querySelector('.trk-read');
  if (!x) {
    x = document.createElement('span'); x.className = 'trk-x'; plot.appendChild(x);
    read = document.createElement('span'); read.className = 'trk-read'; plot.appendChild(read);
    read.append(document.createElement('b'), document.createElement('span'), document.createElement('span'));
  }
  const left = `${(((time - m.now) / m.span) * 100).toFixed(2)}%`;
  x.style.left = left;
  read.style.left = left;
  read.classList.toggle('end', px > rect.width * 0.8);
  read.classList.toggle('start', px < rect.width * 0.2);
  read.firstChild.textContent = mark ? `${num(mark.before)} → ${num(mark.after)}` : `≈ ${num(Math.round(trackValueAt(m, time)))}`;
  read.children[1].textContent = whenOf(time);
  read.children[2].textContent = mark ? mark.row.task : '';
}

function itemDetails(game, item, nf) {
  const unit = item.unit_label || '';
  const expected = nf ? nf.expected : item.expected;
  return detailList([
    [t('detail_task'), `${esc(item.label)} <span class="ink-2">${item.names ? t('for_goal', item.goal, item.names) : esc(item.goal)}</span>`],
    [t('detail_spend'), expected != null
      ? t('spend_detail', `${expected}${unit}`, item.cost, tp('unit_' + game), expected * item.cost) : t('spend_unknown')],
    [t('detail_stop'), t('stop_rule', `${item.upper}${unit}`)],
    item.note ? [t('detail_calc'), esc(item.note)] : null
  ]);
}

function nextBlock(game, plan, item, nf) {
  const when = nf.at ? t('next_batch_at', whenLabel(nf.at)) : t('next_batch');
  const goal = item.goal_id ? findGoal(item.goal_id) : null;
  const unit = item.unit_label || '';
  const spend = nf.spend;
  const detailId = `next-${game}`;
  const adjust = !goal   // equipment for a character is adjusted on its goal card, like its materials
    ? linkButton('#/settings/set-farming', 'edit', t('btn_adjust'))
    : linkButton(`#/goals/${encodeURIComponent(goal.id)}`, 'edit', t('btn_adjust'));
  return `
    <section class="sec next">
      <p class="label">${icon('target')}<span>${when}</span>${plan.phase === 'equipment' ? `<span>(${t('phase_equipment')})</span>` : ''}</p>
      <div class="who">
        ${goal ? portrait(game, goal.character_id, goal.name, 'md') : ''}
        <div><b>${esc(item.label)}</b><p class="ink-2">${item.names ? t('for_goal', item.goal, item.names) : esc(item.goal)}</p></div>
      </div>
      <p class="facts">
        <span>${t('fact_cap', `${item.upper}${unit}`)}</span>
        <span>${t('fact_expect', nf.expected != null ? `${nf.expected}${unit}` : tp('unknown'))}</span>
        ${spend != null ? `<span><b>${t('fact_spend', spend, tp('unit_' + game))}</b></span>` : ''}
      </p>
      <div class="next-foot">${toggleButton(detailId)}${adjust}</div>
      ${detailPanel(detailId, itemDetails(game, item, nf))}
    </section>`;
}

function idleBlock(game, plan) {
  return `
    <section class="sec next idle">
      <p class="label">${icon('pause')}<b>${t('nothing_title')}</b><span>(${t('keeping', tp('unit_' + game))})</span></p>
      <p class="ink-2">${esc(plan.reason || '')}</p>
      <div class="next-foot"><span></span>${linkButton('#/goals', 'edit', t('btn_adjust'))}</div>
    </section>`;
}

function waitingBlock(plan) {
  const list = plan.waiting || [];
  if (!list.length) return '';
  const rows = list.slice(0, 3).map(w => `<li>${icon('clock')}<span class="t">${esc(w.label)}<small>${t('for_goal', w.goal, w.why)}</small></span></li>`).join('');
  const more = list.length > 3 ? `<a href="#/goals">${t('waiting_more', list.length - 3)}</a>` : '';
  return `<section class="sec"><p class="section-title">${icon('clock')}<span>${t('waiting_title', list.length)}</span></p><ul class="list">${rows}</ul>${more}</section>`;
}

function dailiesBlock(plan) {
  const names = plan.daily || [];
  const keys = plan.daily_keys || [];
  const items = names.length
    ? names.map((name, i) => `<li>${icon(DAILY_ICON[keys[i]] || 'check')}<span class="t">${esc(name)}</span></li>`).join('')
    : `<li>${icon('minus')}<span class="t">${t('none')}</span></li>`;
  return `<section class="sec"><p class="section-title">${icon('gift')}<span>${t('dailies_title')}</span></p><ul class="list inline">${items}</ul></section>`;
}

function latestRunPanel() {
  const run = (STATE.runs || [])[0];
  return `
    <section class="panel">
      <header class="panel-head"><h2>${icon('history')}<span>${t('latest_run')}</span></h2><a href="#/runs">${t('view_all')}</a></header>
      ${run ? runBody(run) : `<p class="ink-2">${t('no_runs_yet')}</p>`}
    </section>`;
}

// ----------------------------------------------------------- 2. Goals
function renderGoals() {
  const el = document.getElementById('view-goals');
  if (!GAMES.includes(GOALS_GAME)) GOALS_GAME = 'zzz';
  const list = STATE.goals?.[GOALS_GAME] || [];
  const active = list.filter(g => g.enabled);
  const canceled = list.filter(g => !g.enabled);
  const nextKey = STATE.plans?.[GOALS_GAME]?.item?.key;
  const tabs = GAMES.map(g => {
    const count = (STATE.goals?.[g] || []).filter(x => x.enabled).length;
    return `<button type="button" role="tab" aria-selected="${g === GOALS_GAME}" data-action="goals-game" data-game="${g}"><span>${t('game_' + g)}</span><span class="count">${count}</span></button>`;
  }).join('');
  el.innerHTML = `
    ${pageHead(t('nav_goals'), t('goals_sub'), button('add-goal', 'plus', t('btn_add_goal'), 'primary'))}
    <div class="toolbar"><div class="seg" role="tablist" aria-label="${t('nav_goals')}">${tabs}</div>${help(t('stable_list_help'))}</div>
    ${inventoryLine(GOALS_GAME)}
    ${active.length ? active.map((g, i) => goalCard(g, i, active.length, nextKey)).join('') : `
      <div class="panel empty">${icon('target')}<h2>${t('goals_empty_title')}</h2><p>${t('goals_empty_desc')}</p>
        ${button('add-goal', 'plus', t('btn_add_goal'), 'primary')}</div>`}
    ${canceled.length ? canceledPanel(canceled) : ''}`;
}

function goalCard(g, idx, total, nextKey) {
  const id = esc(g.id);
  const errors = [g.calc_error, g.observe_error].filter(Boolean);
  const items = g.items || [];
  const pending = items.filter(it => !it.done);
  const done = items.filter(it => it.done);
  const next = items.find(it => it.key === nextKey);
  const plan = STATE.plans?.[g.game];
  return `
    <article class="goal" id="goal-${id}" data-goal="${id}">
      <header class="goal-id">
        ${portrait(g.game, g.character_id, g.name)}
        <div>
          <h2>${esc(g.name)}</h2>
          <p class="meta"><span>${t('queue_pos', idx + 1, total)}</span><span>${icon('refresh')}${g.sync_at ? t('synced', relative(g.sync_at)) : t('never_synced')}</span></p>
        </div>
        <div class="goal-actions">
          <span class="order">
            ${iconButton('move-goal', 'up', t('btn_move_up'), `data-id="${id}" data-dir="-1"${idx === 0 ? ' disabled' : ''}`)}
            ${iconButton('move-goal', 'down', t('btn_move_down'), `data-id="${id}" data-dir="1"${idx === total - 1 ? ' disabled' : ''}`)}
          </span>
          ${button('sync-goal', 'refresh', t('btn_sync'), 'sm', `data-id="${id}"`)}
          ${button('edit-targets', 'edit', t('btn_target_settings'), 'sm primary', `data-id="${id}"`)}
          ${button('cancel-goal', 'ban', t('btn_cancel_cultivation'), 'sm danger', `data-id="${id}"`)}
        </div>
      </header>
      ${errors.map(e => alertBox('bad', 'alert', esc(e))).join('')}
      ${next && plan?.item ? nextLine(g, next, plan.item) : ''}
      ${targetTables(g)}
      ${GEAR[g.game] ? gearSection(g) : ''}
      ${priorityRow(g)}
      <section>
        <div class="mats-head"><h3>${t('mats_title')}</h3></div>
        ${pending.length ? `<ul class="mats">${pending.map(it => materialRow(g, it, nextKey)).join('')}</ul>` : `<p class="ink-2">${t('mats_none')}</p>`}
        ${done.length ? `<details class="fold mt" data-keep="done-${id}"><summary>${icon('chevron', 'chev')}<span>${t('completed_items', done.length)}</span></summary>
          <div class="fold-body"><ul class="mats">${done.map(it => materialRow(g, it, nextKey)).join('')}</ul></div></details>` : ''}
      </section>
    </article>`;
}

function nextLine(g, item, planItem) {
  const nf = nextFacts(g.game);
  const spend = nf && nf.spend != null ? t('fact_spend', num(nf.spend), tp('unit_' + g.game)) : t('spend_unknown');
  const detailId = `goal-next-${g.id}`;
  return `
    <div>
      <p class="next-line">${icon('target')}<b>${nf && nf.at ? t('next_batch_at', whenLabel(nf.at)) : t('next_batch')}</b>
        <span>${esc(item.label)}</span><span>${spend}</span>${toggleButton(detailId)}</p>
      ${detailPanel(detailId, itemDetails(g.game, planItem, nf), 'mt')}
    </div>`;
}

const TARGET_FIELDS = {
  genshin: { char: [['level', 'lbl_level'], ['attack', 'talent_normal_attack'], ['skill', 'talent_skill'], ['burst', 'talent_burst']],
             weapon: [['weapon', 'lbl_weapon_level']] },
  zzz: { char: [['level', 'lbl_level'], ['attack', 'talent_basic'], ['special', 'talent_special'], ['dodge', 'talent_dodge'],
                ['chain', 'talent_chain'], ['assist', 'talent_assist'], ['core', 'talent_core']],
         weapon: [['weapon', 'lbl_weapon_level']] }
};
const TARGET_LIMITS = {
  genshin: { level: [1, 90], attack: [1, 10], skill: [1, 10], burst: [1, 10], weapon: [1, 90] },
  zzz: { level: [1, 60], attack: [1, 12], special: [1, 12], dodge: [1, 12], chain: [1, 12], assist: [1, 12], core: [0, 6], weapon: [0, 60] }
};

function targetTable(g, fields, editable) {
  const rows = fields.map(([k, label]) => {
    const cur = g.current?.[k];
    const tgt = g.target?.[k];
    const [min, max] = TARGET_LIMITS[g.game][k];
    const target = editable
      ? `<input type="number" name="${k}" min="${min}" max="${max}" step="1" inputmode="numeric" value="${esc(tgt ?? '')}" aria-label="${t(label)}: ${t('col_target')}">`
      : `<span class="${cur != null && tgt > cur ? 'up' : ''}">${tgt ?? '–'}</span>`;
    return `<tr><th scope="row">${t(label)}</th><td class="c">${cur ?? '–'}</td><td class="arrow" aria-hidden="true">→</td><td class="c">${target}</td></tr>`;
  }).join('');
  return `<table class="target-table"><thead><tr><th scope="col">${t('col_field')}</th><th scope="col" class="c">${t('col_current')}</th><th class="arrow"></th><th scope="col" class="c">${t('col_target')}</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function targetTables(g, editable = false) {
  const f = TARGET_FIELDS[g.game];
  return `
    <div class="targets">
      <section class="target-box"><h3>${t('targets_char')}</h3>${targetTable(g, f.char, editable)}</section>
      <section class="target-box"><h3>${t(g.game === 'genshin' ? 'targets_weapon_genshin' : 'targets_weapon_zzz')}${g.weapon_name ? `<span>${esc(g.weapon_name)}</span>` : ''}</h3>${targetTable(g, f.weapon, editable)}</section>
    </div>`;
}

// ----------------------------------------------------------- Equipment: Drive Discs (ZZZ), Artifacts (Genshin)
// Substats in weight-table order, main stats per configurable slot, and the per-game texts.
const GEAR = {
  zzz: { subs: [20103, 21103, 12102, 12103, 11102, 11103, 13102, 13103, 23203, 31203],
         mains: { 4: [11102, 12102, 13102, 20103, 21103, 31203],
                  5: [11102, 12102, 13102, 23103, 31503, 31603, 31703, 31803, 31903, 32303],
                  6: [11102, 12102, 13102, 30502, 31402, 12202] },
         kind: 'disc', unit: 'battery', title: 'gear_title', none: 'gear_none_yet', help: 'gear_help', farm: 'gear_farm_switch',
         mainsTitle: 'gear_mains_title', stage: 'gear_stage', stageAuto: 'gear_stage_auto', stageHint: 'gear_stage_hint',
         stages: () => STATE.catalog?.disc || [], sets: () => STATE.catalog?.disc_sets || [] },
  genshin: { subs: [20, 22, 6, 5, 3, 2, 9, 8, 23, 28],
             mains: { 3: [3, 6, 9, 23, 28], 4: [3, 6, 9, 28, 30, 40, 41, 42, 43, 44, 45, 46], 5: [3, 6, 9, 28, 20, 22, 26] },
             kind: 'artifact', unit: 'resin', title: 'art_title', none: 'art_none_yet', help: 'art_help', farm: 'art_farm_switch',
             mainsTitle: 'art_mains_title', stage: 'art_domain', stageAuto: 'art_domain_auto', stageHint: 'art_domain_hint',
             stages: () => STATE.catalog?.blessing || [], sets: () => STATE.catalog?.artifact_sets || [] }
};
/** Official property name in the UI language; the API's own (Chinese) name for ids this table lacks. */
function propName(id, fallback = '') { const k = 'prop_' + id; return lookup(k) !== k ? t(k) : esc(fallback || id); }
function slotName(game, slot) { return game === 'genshin' ? t('art_slot_' + slot) : t('gear_slot', slot); }
function setIcon(game, setId, cls = 'mat-icon') {
  const k = `${game}/${GEAR[game].kind}/${setId}`;
  return setId && ASSETS.has(k) ? `<img class="${cls}" src="/assets/${esc(k)}" alt="" loading="lazy">` : '';
}
function rollsText(r) { return r == null ? '' : `×${Number.isInteger(r) ? r : r.toFixed(1)}`; }
function gearQueueRow(g) { return (STATE.plans?.[g.game]?.equipment?.queue || []).find(r => r.goal_id === g.id); }

function gearStatus(g, ev) {
  const row = gearQueueRow(g);
  const eq = STATE.plans?.[g.game]?.equipment || {};
  if (ev && ev.done) return badge('good', 'check', t('gear_status_met'));
  if (g.gear_owned && g.gear_owned.done) return badge('good', 'check', t('gear_status_owned'));
  if (!ev?.target?.farm) return badge('muted', 'minus', t('gear_status_off'));
  if (row && row.why) return badge('warn', 'clock', esc(row.why));
  if (eq.goal_id === g.id && !eq.why) return badge('info', 'target', t('gear_status_next', esc(row.stage)));
  if (row && row.stage) return badge('muted', 'list', t('gear_status_queued', esc(row.stage)));
  return badge('warn', 'clock', esc(eq.why || ''));
}

function gearSection(g) {
  const ev = g.gear_eval;
  const id = esc(g.id);
  const cfg = GEAR[g.game];
  const head = `<div class="mats-head"><h3>${t(cfg.title)}</h3>${button('edit-gear', 'edit', t('btn_gear_target'), 'sm', `data-id="${id}"${ev ? '' : ' disabled'}`)}</div>`;
  if (!ev) return `<section class="gear">${head}<p class="ink-2">${g.gear_error ? esc(g.gear_error) : t(cfg.none)}</p></section>`;
  const tg = ev.target;
  const chips = [
    ...ev.sets.map(s => chip(s.ok ? 'check' : 'x', `${s.name} ${s.have}/${s.count}`, s.ok ? 'good' : 'warn')),
    ev.checks.main ? chip('check', tp('gear_mains_ok'), 'good') : chip('x', tp('gear_mains_bad'), 'warn'),
    ev.checks.filled ? '' : chip('x', tp('gear_slots_filled', ev.slots.filter(s => s.disc).length, ev.slots.length), 'warn'),
  ].join('');
  const src = ev.source === 'custom' ? t('gear_src_custom') : ev.source !== 'official' ? t('gear_src_none')
    : ev.plan?.name ? t('gear_src_official', esc(ev.plan.name)) : t(ev.plan?.mine ? 'gear_src_mine' : 'gear_src_recommended');
  const weighted = cfg.subs.filter(i => (ev.weights[i] || 0) > 0)
    .map(i => `${propName(i)} ${ev.weights[i]}`).join(tp('list_sep'));
  const detailId = `gear-${g.id}`;
  return `
    <section class="gear">
      ${head}
      <div class="gear-sum">
        <div class="gear-score"><span class="value">${ev.score ?? '–'}</span><span class="ink-2">/ ${tg.score}</span>${ev.score == null ? '' : miniMeter(ev.score, tg.score || 100)}</div>
        <div class="gear-checks">${chips}</div>
        <div class="gear-state">${gearStatus(g, ev)}</div>
      </div>
      ${ownedBlock(g)}
      <p class="meta ink-2"><span>${src}</span><span>${icon('refresh')}${t('gear_read', relative(ev.at))}</span>${g.gear_runs ? `<span>${t('gear_runs', num(g.gear_runs))}</span>` : ''}${toggleButton(detailId)}</p>
      ${detailPanel(detailId, `
        <ul class="discs">${ev.slots.map(s => discCard(g.game, s)).join('')}</ul>
        ${help(weighted ? t('gear_weights_line', weighted) : t('gear_no_weights'))}
        ${Object.keys(ev.totals || {}).length ? help(t('gear_totals', cfg.subs.filter(i => ev.totals[i] != null)
          .map(i => `${propName(i)} ${num(ev.totals[i])}`).join(tp('list_sep'))), 'list') : ''}
        ${help(t(cfg.help))}`, 'mt')}
    </section>`;
}

/** The best arrangement of pieces the character owns (with an inventory scan): what to equip, slot by slot. */
function ownedBlock(g) {
  const own = g.gear_owned;
  if (!own || (!own.changes.length && g.gear_eval?.done)) return '';
  const rows = own.changes.map(c => `
    <li>${setIcon(g.game, c.set_id)}<span><b>${slotName(g.game, c.slot)}</b> · ${esc(c.set)} · ${propName(c.main?.id, c.main?.name)}</span>
      <span class="num">${c.was == null ? '–' : num(Math.round(c.was * 10) / 10)} → <b>${num(c.score)}</b></span></li>`).join('');
  return `
    <div class="owned">
      <p>${icon(own.done ? 'check' : 'info')}<b>${t('gear_owned_title', num(own.score))}</b><span class="ink-2">${t(own.done ? 'gear_owned_done' : 'gear_owned_short')}</span></p>
      ${rows ? `<ul>${rows}</ul>` : ''}
    </div>`;
}

/** Last inventory scan of a game: when, how many pieces, and the spare ones (listed, never salvaged by the app). */
function inventoryLine(game) {
  const inv = STATE.inventory?.[game];
  if (!inv) return '';
  const sets = (inv.spare_sets || []).map(([name, n]) => `<li><span>${esc(name)}</span><span class="num">${num(n)}</span></li>`).join('');
  const id = `inv-${game}`;
  return `
    <div class="inv-line">
      <p>${icon('box')}<span>${t('inv_line', relative(inv.at), num(inv.count), num(inv.spare))}</span>${inv.spare ? toggleButton(id) : ''}</p>
      ${inv.spare ? detailPanel(id, `<ul class="spare">${sets}</ul>${help(t('inv_spare_help'))}`, 'mt') : ''}
    </div>`;
}

function discCard(game, s) {
  const d = s.disc;
  if (!d) return `<li class="disc empty"><b>${slotName(game, s.slot)}</b><span class="ink-2">${t('gear_slot_empty')}</span></li>`;
  const main = d.main ? `${propName(d.main.id, d.main.name)} <span class="num">${esc(d.main.value)}</span>` : '–';
  const subs = s.subs.map(x => `
    <li class="${x.weight > 0 ? 'eff' : ''}"><span>${propName(x.id, x.name)}</span><span class="num">${esc(x.value)}</span><span class="rolls num">${rollsText(x.rolls)}</span></li>`).join('');
  return `
    <li class="disc">
      <div class="disc-head">${setIcon(game, d.set_id)}<div><b>${slotName(game, s.slot)}</b><span>${esc(d.set)}</span></div>
        <span class="disc-score num" title="${t('gear_disc_score')}">${s.score ?? '–'}</span></div>
      <p class="disc-meta ink-2"><span>${t(game === 'genshin' ? 'art_level' : 'gear_level', esc(d.rarity), d.level)}</span>${s.wasted == null || !d.level ? ''
        : s.wasted ? `<span class="wasted">${t('gear_wasted', s.wasted)}</span>` : `<span class="all-hit">${icon('check')}${t('gear_all_hit')}</span>`}</p>
      <p class="disc-main${s.main_ok === false ? ' bad' : ''}">${s.main_ok === false ? icon('alert') : ''}${main}</p>
      <ul class="disc-subs">${subs}</ul>
    </li>`;
}

function priorityRow(g) {
  const order = g.category_order || ['level', 'talents', 'weapon'];
  const id = esc(g.id);
  return `
    <div class="priority">
      <span class="label">${icon('list')}<span>${t('priority_label')}</span></span>
      <ol>${order.map((c, i) => `
        <li><span class="n">${i + 1}</span><span>${t('cat_' + c)}</span>
          ${i > 0 ? iconButton('shift-cat', 'left', t('btn_move_up'), `data-id="${id}" data-index="${i}" data-dir="-1"`) : ''}
          ${i < order.length - 1 ? iconButton('shift-cat', 'right', t('btn_move_down'), `data-id="${id}" data-index="${i}" data-dir="1"`) : ''}
        </li>`).join('')}</ol>
    </div>`;
}

function needText(it) {
  const mats = it.materials || [];
  if (it.done) return t('status_collected');
  if (mats.some(m => m.remaining == null)) return t('qty_unknown');
  const short = mats.filter(m => m.remaining > 0);
  if (mats.length === 1) return t('need_more', num(short.length ? short[0].remaining : 0));
  const parts = short.slice(0, 2).map(m => `${num(m.remaining)} × ${m.name}`);
  if (short.length > 2) parts.push(`+${short.length - 2}`);
  return t('need_list', parts.join(tp('list_sep')));
}

function miniMeter(value, max) {
  const pct = max > 0 ? Math.min(100, (100 * value) / max) : 0;
  return `<span class="meter mini" aria-hidden="true">${pct > 0 ? `<span class="fill" style="width:${pct.toFixed(1)}%"></span>` : ''}</span>`;
}

function materialRow(g, it, nextKey) {
  const isNext = it.key === nextKey;
  let status;
  if (it.done) status = badge('good', 'check', t('status_collected'));
  else if (it.paused) status = badge('muted', 'pause', t('status_paused'));
  else if (isNext) status = badge('info', 'target', t('status_next'));
  else if (it.why) status = badge('warn', 'clock', t('status_waiting'));
  else status = badge('muted', 'minus', t('status_queued'));
  const mats = it.materials || [];
  const top = mats[mats.length - 1];
  const executed = it.executed || 0;
  const plan = it.units == null || it.done ? '<div></div>'
    : `<div class="mat-plan"><span>${t('plan_units', executed, `${it.units}${it.unit_label || ''}`)}</span>${miniMeter(executed, it.units)}</div>`;
  const detailId = `mat-${g.id}-${it.key}`;
  const action = it.done ? '' : button('pause-item', it.paused ? 'play' : 'pause', t(it.paused ? 'btn_resume' : 'btn_pause'), 'sm quiet',
    `data-id="${esc(g.id)}" data-key="${esc(it.key)}" data-pause="${it.paused ? '0' : '1'}"`);
  const tiers = mats.map(m => `
    <tr><td><span class="tier-name">${materialIcon(g.game, m.id, '')}${esc(m.name)}</span></td>
      <td class="n">${num(m.need) ?? '–'}</td><td class="n">${num(m.owned) ?? '–'}</td><td class="n">${m.remaining == null ? t('unknown') : num(m.remaining)}</td></tr>`).join('');
  return `
    <li class="mat${it.tint ? ' tint-' + esc(it.tint) : ''}" data-row="${esc(it.key)}">
      <div class="mat-row">
        <div class="mat-id">${top ? materialIcon(g.game, top.id) : ''}<div><b>${esc(it.label)}</b><span>${t('open_days', it.days)}</span></div></div>
        <div class="mat-need">${needText(it)}</div>
        ${plan}
        <div class="mat-state">${status}${!it.done && it.why ? `<p>${esc(it.why)}</p>` : ''}</div>
        <div class="mat-act">${action}${toggleButton(detailId)}</div>
      </div>
      ${detailPanel(detailId, `
        <table class="tier-table"><thead><tr><th>${t('tier_material')}</th><th class="n">${t('tier_need')}</th><th class="n">${t('tier_have')}</th><th class="n">${t('tier_short')}</th></tr></thead><tbody>${tiers}</tbody></table>
        ${it.note && it.note !== it.why ? help(esc(it.note)) : ''}`, 'mat-detail')}
    </li>`;
}

function canceledPanel(list) {
  return `
    <details class="panel fold mt" data-keep="canceled-${GOALS_GAME}">
      <summary>${icon('chevron', 'chev')}<b>${t('canceled_title', list.length)}</b></summary>
      <div class="fold-body canceled">
        ${help(t('canceled_note'))}
        <ul class="rows mt">${list.map(g => `
          <li>${portrait(g.game, g.character_id, g.name, 'md')}<span class="what">${esc(g.name)}</span>
            <span class="actions">
              ${button('resume-goal', 'play', t('btn_resume_cultivation'), 'sm', `data-id="${esc(g.id)}"`)}
              ${button('delete-goal', 'trash', t('btn_delete'), 'sm quiet danger', `data-id="${esc(g.id)}"`)}
            </span></li>`).join('')}</ul>
      </div>
    </details>`;
}

function findGoal(id) { return GAMES.flatMap(g => STATE.goals?.[g] || []).find(x => x.id === id); }

// ----------------------------------------------------------- dialogs (one static <dialog>, content per use)
function openDialog(html, wide = false) {
  const dialog = document.getElementById('modal');
  dialog.classList.toggle('wide', wide);
  dialog.innerHTML = html;
  reapplyBusy(dialog);
  if (!dialog.open) dialog.showModal();
}

function closeDialog() {
  const dialog = document.getElementById('modal');
  if (dialog.open) dialog.close();
}

function dialogShell(title, body, foot, form) {
  return `
    <form class="modal" data-form="${form}" method="dialog" novalidate>
      <header class="modal-head"><h2 id="modal-title">${title}</h2>
        <button type="button" class="btn sm quiet" data-action="modal-close">${icon('x')}<span class="txt">${t('btn_close')}</span></button></header>
      <div class="modal-body">${body}</div>
      <footer class="modal-foot">${foot}</footer>
    </form>`;
}

/** Miyoushe's captcha after a 1034. Geetest's script runs in a sandboxed frame with an opaque origin, so it
 *  can neither read this page nor call the API (POST needs the X-GC header, which a cross-origin page cannot
 *  send without CORS); only its answer is posted back, and the backend hands it to Miyoushe. */
async function openVerify(game) {
  MODAL = { kind: 'verify', game, frame: null };
  openDialog(dialogShell(t('dlg_verify_title'), `
      ${help(t('verify_hint'), 'shield')}
      <div class="captcha-box" id="captcha-box"></div>
      <p class="captcha-status ink-2" id="captcha-status" role="status">${t('verify_loading')}</p>`,
    button('widget', 'qr', t('btn_widget'), 'primary') +
    button('verify', 'refresh', t('btn_new_captcha'), 'sm', `data-game="${game}"`), 'verify'));
  const modal = MODAL;
  try {
    const challenge = await api('/api/verify/start', 'POST', { game });
    if (MODAL !== modal) return;  // closed or replaced meanwhile
    const frame = document.createElement('iframe');
    frame.className = 'captcha-frame';
    frame.title = t('dlg_verify_title');
    frame.setAttribute('sandbox', 'allow-scripts');
    modal.challenge = challenge;
    frame.srcdoc = captchaPage(challenge);
    modal.frame = frame;
    document.getElementById('captcha-box').replaceChildren(frame);
  } catch (err) {
    if (MODAL === modal) captchaStatus(tp('verify_failed', err.message));
  }
}

async function openWidget() {
  MODAL = { kind: 'widget' };
  openDialog(dialogShell(t('widget_title'), `<div id="widget-connect-body"></div>`, '', 'widget'));
  updateWidgetDialog();
  if (!STATE.qr?.unified && (!STATE.qr?.status || STATE.qr.status === 'idle')) {
    try {
      STATE.qr = await api('/api/login/start', 'POST', {});
      updateWidgetDialog();
    } catch (err) { toast(err.message, 'error'); }
  }
}

function updateWidgetDialog() {
  if (MODAL?.kind !== 'widget') return;
  const body = document.getElementById('widget-connect-body');
  if (!body) return;
  const qr = STATE.qr || {};
  const signature = JSON.stringify(qr) + CURRENT_LANG;
  if (MODAL.signature === signature) return;
  MODAL.signature = signature;
  const pending = ['creating', 'waiting', 'scanned', 'reading'].includes(qr.status);
  const img = ['waiting', 'scanned'].includes(qr.status) && qr.svg
    ? `<img alt="${t('qr_alt')}" src="data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(qr.svg)))}">` : '';
  body.innerHTML = `${help(t('widget_hint'), 'shield')}
    <p>${t(qr.unified ? 'widget_connected' : 'widget_disconnected')}</p>
    <div class="qr-box">${img}<p role="status" aria-label="${t('widget_status')}">${esc(qr.reason || '')}</p></div>
    <div class="actions">${!pending ? button('widget-start', 'qr', t(qr.unified ? 'btn_widget_reconnect' : 'btn_widget'), 'primary') : ''}
      ${STATE.logged_in ? button('logout', 'logout', t('btn_widget_disconnect'), 'sm') : pending ? button('cancel-login', 'x', t('btn_cancel_login'), 'sm') : ''}</div>`;
  reapplyBusy(body);
}

function captchaStatus(text) {
  const el = document.getElementById('captcha-status');
  if (el) el.textContent = text;
}

function captchaPage(c) {
  const config = JSON.stringify({
    gt: c.gt, challenge: c.challenge, new_captcha: c.new_captcha !== false, offline: false, product: 'bind',
    https: true, api_server: 'api.geetest.com', lang: CURRENT_LANG === 'zh' ? 'zh-cn' : 'en',
  }).replace(/</g, '\\u003c');
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<style>html, body { margin: 0; height: 100%; background: transparent; }</style>
<script src="https://static.geetest.com/static/js/gt.0.5.2.js"></script></head><body><script>
const send = (kind, result) => parent.postMessage({ gclCaptcha: kind, result }, '*');
if (typeof initGeetest !== 'function') send('error', 'static.geetest.com');
else initGeetest(${config}, c => {
  c.onReady(() => { send('ready'); c.verify(); });
  c.onSuccess(() => send('success', c.getValidate()));
  c.onError(e => send('error', String((e && (e.msg || e.error_code)) || '')));
  c.onClose(() => send('close'));
});
</script></body></html>`;
}

window.addEventListener('message', async event => {
  const modal = MODAL;
  if (modal?.kind !== 'verify' || !modal.frame || event.source !== modal.frame.contentWindow) return;
  const { gclCaptcha: kind, result } = event.data || {};
  if (kind === 'ready') captchaStatus(t('verify_solve'));
  else if (kind === 'close') captchaStatus(t('verify_closed'));
  else if (kind === 'error') captchaStatus(tp('verify_failed', String(result || '')));
  else if (kind === 'success' && result && typeof result === 'object') {
    captchaStatus(t('verify_checking'));
    try {
      const answer = { id: modal.challenge.id };
      ['geetest_challenge', 'geetest_validate', 'geetest_seccode'].forEach(k => { answer[k] = String(result[k] || ''); });
      const res = await api('/api/verify/finish', 'POST', { game: modal.game, answer });
      if (res && res.error) throw new Error(res.error);
      if (MODAL === modal) closeDialog();
      await refreshState(true);
      toast(tp('toast_verified'));
    } catch (err) {
      if (MODAL === modal) captchaStatus(tp('verify_rejected', err.message));
      await refreshState(true);
    }
  }
});

function openTargets(goal) {
  MODAL = { kind: 'targets', id: goal.id, error: '', dirty: false };
  renderTargetsDialog(goal);
}

function renderTargetsDialog(goal) {
  openDialog(dialogShell(t('dlg_targets_title', goal.name), `
      ${targetTables(goal, true)}
      ${help(t('targets_help'))}`,
    `${MODAL.error ? `<span class="err" role="alert">${icon('alert')}${esc(MODAL.error)}</span>` : ''}
      <button type="button" class="btn" data-action="targets-discard"${MODAL.dirty ? '' : ' hidden'}>${icon('x')}<span class="txt">${t('btn_discard')}</span></button>
      <button type="submit" class="btn primary" data-action="save-targets" data-id="${esc(goal.id)}">${icon('check')}<span class="txt">${t('btn_save_changes')}</span></button>`,
    'targets'), true);
}

function openGearTarget(goal) {
  MODAL = { kind: 'gear', id: goal.id, error: '', dirty: false };
  renderGearDialog(goal);
}

/** Sets this character could target: the build's, the equipped ones and every set a known stage drops. */
function gearSetOptions(game, ev) {
  const seen = new Map();
  const add = (id, name) => { if (id && !seen.has(String(id))) seen.set(String(id), name); };
  (ev.plan?.sets || []).forEach(s => add(s.id, s.name));
  ev.slots.forEach(s => s.disc && add(s.disc.set_id, s.disc.set));
  ev.target.sets.forEach(s => add(s.id, s.name));
  GEAR[game].sets().forEach(s => add(s.id, s.name));
  return [...seen].map(([id, name]) => ({ id, name }));
}

function renderGearDialog(goal) {
  const ev = goal.gear_eval;
  const own = goal.gear_target || {};
  const tg = ev.target;
  const follow = (key, sec) => `
    <label class="follow"><input type="checkbox" name="follow_${sec}" data-follow="${sec}" data-change="gear-follow"${own[key] == null ? ' checked' : ''}>
      <span>${t(sec === 'weights' ? 'gear_follow_weights' : 'gear_follow_build')}</span></label>`;
  const cfg = GEAR[goal.game];
  const options = gearSetOptions(goal.game, ev);
  const setRow = (i, s) => `
    <div class="set-row">
      <select name="set_${i}" aria-label="${t('gear_set_n', i + 1)}"><option value="">${t('gear_set_none')}</option>
        ${options.map(o => `<option value="${esc(o.id)}"${s && String(s.id) === o.id ? ' selected' : ''}>${esc(o.name)}</option>`).join('')}</select>
      <select name="count_${i}" aria-label="${t('gear_set_pieces')}">
        ${[4, 2].map(c => `<option value="${c}"${(s ? s.count : i ? 2 : 4) === c ? ' selected' : ''}>${t('gear_pieces', c)}</option>`).join('')}</select>
    </div>`;
  const mainGroup = slot => `
    <fieldset class="main-group"><legend>${slotName(goal.game, slot)}</legend>
      ${[...new Set([...cfg.mains[slot], ...(ev.build.main[slot] || [])])].map(i => `<label class="check"><input type="checkbox" name="main_${slot}" value="${i}"${(tg.main[slot] || []).includes(i) ? ' checked' : ''}><span>${propName(i, ev.plan?.names?.[i])}</span></label>`).join('')}
    </fieldset>`;
  const stages = cfg.stages();
  openDialog(dialogShell(t('dlg_gear_title', esc(goal.name)), `
      ${switchRow('farm', tg.farm, t(cfg.farm), t('gear_farm_sub'), cfg.unit, 'first')}
      <div class="fields wide">
        ${field(t('gear_score_target'), `<input type="number" name="score" min="0" max="100" step="1" value="${tg.score}">`, t('gear_score_hint'))}
        ${field(t(cfg.stage), `<select name="stage"><option value="">${t(cfg.stageAuto)}</option>
          ${stages.map(s => `<option value="${esc(s)}"${tg.stage === s ? ' selected' : ''}>${esc(s)}</option>`).join('')}</select>`, t(cfg.stageHint))}
      </div>
      <div class="sub-block"><h3>${t('gear_sets_title')}</h3>${follow('sets', 'sets')}
        <fieldset data-sec="sets"${own.sets == null ? ' disabled' : ''}>${[0, 1, 2].map(i => setRow(i, tg.sets[i])).join('')}</fieldset></div>
      <div class="sub-block"><h3>${t(cfg.mainsTitle)}</h3>${follow('main', 'main')}
        <fieldset data-sec="main" class="mains"${own.main == null ? ' disabled' : ''}>${Object.keys(cfg.mains).map(mainGroup).join('')}</fieldset></div>
      <div class="sub-block"><h3>${t('gear_weights_title')}</h3>${follow('weights', 'weights')}
        <fieldset data-sec="weights" class="fields weights"${own.weights == null ? ' disabled' : ''}>
          ${cfg.subs.map(i => field(propName(i), `<input type="number" name="w_${i}" min="0" max="1" step="0.01" value="${ev.weights[i] ?? 0}">`)).join('')}
        </fieldset>
        ${help(t('gear_weights_help'))}</div>`,
    `${MODAL.error ? `<span class="err" role="alert">${icon('alert')}${esc(MODAL.error)}</span>` : ''}
      <button type="submit" class="btn primary" data-action="save-gear" data-id="${esc(goal.id)}">${icon('check')}<span class="txt">${t('btn_save_changes')}</span></button>`,
    'gear'), true);
}

/** "Follow the build" on: show the build's values in the (disabled) section; off: start editing from them. */
function toggleFollow(box) {
  const goal = findGoal(MODAL.id);
  const ev = goal && goal.gear_eval;
  const sec = box.closest('form').querySelector(`fieldset[data-sec="${box.dataset.follow}"]`);
  if (!ev || !sec) return;
  sec.disabled = box.checked;
  if (!box.checked) return;
  if (box.dataset.follow === 'weights' && ev.official) GEAR[goal.game].subs.forEach(i => { sec.querySelector(`[name="w_${i}"]`).value = ev.official[i] ?? 0; });
  if (box.dataset.follow === 'main') sec.querySelectorAll('input').forEach(c => { c.checked = (ev.build.main[c.name.slice(5)] || []).includes(Number(c.value)); });
  if (box.dataset.follow === 'sets') [0, 1, 2].forEach(i => {
    const s = ev.build.sets[i];
    sec.querySelector(`[name="set_${i}"]`).value = s ? String(s.id) : '';
    sec.querySelector(`[name="count_${i}"]`).value = String(s ? s.count : i ? 2 : 4);
  });
}

async function submitGearTarget(form) {
  const goal = findGoal(MODAL.id);
  const fd = new FormData(form);   // disabled sections (following the build) are left out
  const target = { farm: fd.has('farm'), score: parseInt(fd.get('score'), 10), stage: fd.get('stage') || '' };
  if (!form.elements.follow_sets.checked) {
    const names = new Map(gearSetOptions(goal.game, goal.gear_eval).map(o => [o.id, o.name]));
    target.sets = [0, 1, 2].map(i => ({ id: fd.get('set_' + i), count: parseInt(fd.get('count_' + i), 10) }))
      .filter(s => s.id).map(s => ({ ...s, id: Number(s.id), name: names.get(s.id) || '' }));
  }
  const cfg = GEAR[goal.game];
  if (!form.elements.follow_main.checked) target.main = Object.fromEntries(Object.keys(cfg.mains).map(s => [s, fd.getAll('main_' + s).map(Number)]));
  if (!form.elements.follow_weights.checked) target.weights = Object.fromEntries(cfg.subs.map(i => [i, parseFloat(fd.get('w_' + i)) || 0]));
  const btn = form.querySelector('[data-action="save-gear"]');
  await busy(btn, async () => {
    try {
      await api('/api/goals/update', 'POST', { id: goal.id, patch: { gear_target: target } });
    } catch (err) {
      if (!MODAL || MODAL.kind !== 'gear') throw err;
      MODAL.error = err.message;
      const err_ = form.querySelector('.modal-foot .err');
      if (err_) err_.lastChild.textContent = err.message;
      else form.querySelector('.modal-foot').insertAdjacentHTML('afterbegin', `<span class="err" role="alert">${icon('alert')}<span>${esc(err.message)}</span></span>`);
      return;
    }
    if (MODAL && MODAL.kind === 'gear' && MODAL.id === goal.id) closeDialog();
    const ok = await refreshState(true);
    toast(ok ? tp('toast_gear') : tp('saved_not_reloaded'), ok ? 'ok' : 'error');
    if (ok) flash(`${goalSel(goal.id)} .gear`);
  }, 'saving');
}

async function openAddGoal() {
  const game = GOALS_GAME;
  MODAL = { kind: 'add', game, rows: null, source: 'roster', query: '', selected: null };
  renderAddDialog();
  try {
    MODAL.rows = (await api(`/api/roster?game=${game}`)).rows || [];
  } catch (_) {
    if (!MODAL || MODAL.kind !== 'add') return;
    MODAL.source = 'dataset';
    try { MODAL.rows = (await api(`/api/characters?game=${game}`)).rows || []; } catch (err) { MODAL.rows = []; toast(err.message, 'error'); }
  }
  if (MODAL && MODAL.kind === 'add' && MODAL.game === game) {
    renderAddDialog();
    document.getElementById('char-search')?.focus();
  }
}

function renderAddDialog() {
  const m = MODAL;
  openDialog(dialogShell(t('modal_add_title', tp('game_' + m.game)), m.rows === null ? `<p class="ink-2">${t('modal_loading')}</p>` : `
      ${help(t(m.source === 'roster' ? 'modal_source_roster' : 'modal_source_dataset'))}
      <label class="search">${icon('search')}<input type="search" id="char-search" placeholder="${t('search_placeholder')}" aria-label="${t('search_placeholder')}" value="${esc(m.query)}" autocomplete="off"></label>
      <ul class="char-list" id="char-list" role="listbox" aria-label="${t('search_placeholder')}">${charOptions()}</ul>`,
    `<button type="submit" class="btn primary" id="modal-add" data-action="add-goal-submit"${m.selected ? '' : ' disabled'}>${icon('plus')}<span class="txt">${t('btn_add')}</span></button>`,
    'add-goal'));
}

function charOptions() {
  const m = MODAL;
  const taken = new Set((STATE.goals?.[m.game] || []).map(g => String(g.character_id)));
  const q = m.query.trim().toLowerCase();
  const rows = (m.rows || []).filter(c => !q || String(c.name).toLowerCase().includes(q));
  if (!rows.length) return `<li><p class="ink-2" style="padding:12px">${t('no_match')}</p></li>`;
  return rows.map(c => {
    const id = String(c.id);
    const added = taken.has(id);
    const rarity = /^\d+$/.test(String(c.rarity ?? '')) ? `${c.rarity}★` : c.rarity;
    const facts = [c.element, rarity, c.level ? `Lv. ${c.level}` : ''].filter(Boolean).map(esc).join(esc(tp('list_sep')));
    const flag = added ? t('already_added') : c.owned === false ? t('not_owned') : '';
    return `<li><button type="button" class="char" role="option" data-action="pick-char" data-id="${esc(id)}" data-name="${esc(c.name)}"
        aria-selected="${m.selected?.id === id}"${added ? ' disabled' : ''}>
        ${portrait(m.game, id, c.name, 'md')}<span><b>${esc(c.name)}</b><span>${facts}</span></span><span class="ink-2">${flag}</span></button></li>`;
  }).join('');
}

// ----------------------------------------------------------- 3. Schedule
function renderPlan() {
  const el = document.getElementById('view-plan');
  const rows = STATE.forecast?.rows || [];
  const days = [];
  rows.forEach(r => {
    const at = toMs(r.at);
    const key = dayKeyOf(at);
    if (!days.length || days[days.length - 1].key !== key) days.push({ key, at, rows: [] });
    days[days.length - 1].rows.push(r);
  });
  el.innerHTML = `
    ${pageHead(t('nav_plan'), t('plan_sub'))}
    ${STATE.forecast?.schedule_enabled ? '' : `<div class="alerts">${alertBox('info', 'info', t('plan_off_banner'),
      linkButton('#/settings/set-schedule', 'sliders', t('btn_open_settings')))}</div>`}
    ${days.length ? days.map(day => `
      <section class="panel day">
        <div class="day-head"><h2>${dayLabel(day.at) === dateOf(day.at) ? esc(dateOf(day.at)) : t('day_head', dayLabel(day.at), dateOf(day.at))}</h2>${badge('muted', 'clock', t('forecast'))}</div>
        <ul class="entries">${day.rows.map(entry).join('')}</ul>
      </section>`).join('') : `<div class="panel empty">${icon('calendar')}<p>${t('plan_empty')}</p></div>`}`;
}

function entry(r) {
  const goal = r.goal_id ? findGoal(r.goal_id) : null;
  const detailId = `plan-${r.at}-${r.game}`;
  const unitName = tp('unit_' + r.game);
  const task = r.task
    ? `<div class="task">${goal ? portrait(r.game, goal.character_id, goal.name, 'sm') : ''}<div><b>${esc(r.task)}</b><span>${r.names ? t('for_goal', r.goal, r.names) : esc(r.goal)}</span>${r.phase === 'equipment' ? `<span>${t('phase_equipment')}</span>` : ''}</div></div>`
    : `<div class="task"><div><b>${t('daily_only')}</b></div></div>`;
  const spend = r.spend != null
    ? `<div class="spend"><b>${t('fact_spend', r.spend, unitName)}</b>${r.left != null ? `<span>${t('left_after', r.left)}</span>` : ''}</div>`
    : `<div class="spend"><span>${r.stamina == null ? t('spend_unknown') : t('left_after', r.left ?? r.stamina)}</span></div>`;
  const rowsDetail = r.task ? [
    [t('detail_task'), `${esc(r.task)} <span class="ink-2">${r.names ? t('for_goal', r.goal, r.names) : esc(r.goal)}</span>`],
    [t('detail_spend'), r.expected != null ? t('spend_detail', `${r.expected}${r.unit_label || ''}`, r.cost, unitName, r.spend ?? '?') : t('spend_unknown')],
    [t('detail_stop'), t('stop_rule', `${r.upper}${r.unit_label || ''}`)],
    [t('detail_calc'), esc(r.reason)]
  ] : [[t('detail_reason'), esc(r.reason)]];
  return `
    <li class="entry">
      <div class="entry-row">
        <span class="time">${clock(r.at)}</span>
        <span class="game">${t('game_' + r.game)}</span>
        ${task}
        ${spend}
        <span class="more-btn">${toggleButton(detailId)}</span>
      </div>
      ${detailPanel(detailId, detailList(rowsDetail))}
    </li>`;
}

// ----------------------------------------------------------- 4. Runs
function triggerLabel(run) { return run.source === 'schedule' ? t('trigger_schedule', run.slot) : t('trigger_manual'); }

function runGame(g) {
  const item = g.item;
  const unit = item?.unit_label || '';
  const amount = item
    ? (g.completed != null ? t('run_done', `${g.completed}${unit}`, `${item.upper}${unit}`) : t('run_unverified'))
    : '';
  return `
    <div class="run-game">
      <div class="top-line"><b>${t('game_' + g.game)}</b>${runBadge(g.status)}${amount ? `<span>${amount}</span>` : ''}</div>
      <p>${item ? `${esc(item.label)} <span class="ink-2">${esc(item.goal)}</span>` : esc(g.summary || '')}</p>
      ${(g.errors || []).map(e => `<p class="err">${icon('alert')}<span>${esc(e)}</span></p>`).join('')}
      ${(g.notes || []).map(n => `<p class="note">${icon('info')}<span>${esc(n)}</span></p>`).join('')}
    </div>`;
}

function runBody(run) {
  const start = toMs(run.started), end = toMs(run.ended);
  const games = run.games || [];
  return `
    <div class="run-head">${runBadge(run.status)}<span class="label">${icon(run.source === 'schedule' ? 'calendar' : 'play')}${triggerLabel(run)}</span>
      ${start && end ? `<span class="ink-2">${t('run_duration', duration((end - start) / 60000))}</span>` : ''}</div>
    ${games.length ? games.map(runGame).join('') : `<p class="ink-2">${t('no_games')}</p>`}
    ${(run.notes || []).map(n => help(esc(n))).join('')}`;
}

function renderRuns() {
  const el = document.getElementById('view-runs');
  const list = MORE_RUNS || STATE.runs || [];
  el.innerHTML = `
    ${pageHead(t('nav_runs'), '', button('refresh', 'refresh', t('btn_refresh')))}
    <section class="panel">
      ${list.length ? list.map(r => {
        const start = toMs(r.started);
        return `<article class="run"><div class="when"><b>${esc(clock(r.started))}</b><span>${esc(start ? dateOf(start) : '')}</span></div><div>${runBody(r)}</div></article>`;
      }).join('') : `<div class="empty">${icon('history')}<p>${t('runs_empty')}</p></div>`}
      ${!MORE_RUNS && list.length >= 20 ? `<div class="mt">${button('more-runs', 'history', t('btn_more_runs'), 'sm')}</div>` : ''}
    </section>`;
}

// ----------------------------------------------------------- 5. Settings
const SETTINGS_SECTIONS = [['set-account', 'user'], ['set-env', 'shield'], ['set-schedule', 'clock'], ['set-farming', 'target'],
                           ['set-dailies', 'gift'], ['set-notify', 'bell'], ['set-paths', 'folder'], ['set-images', 'image'],
                           ['set-network', 'globe']];

function renderSettings(force) {
  const el = document.getElementById('view-settings');
  const form = el.querySelector('#settings-form');
  if (form && (!force || SETTINGS_DIRTY) && force !== 'discard') {
    updateLive(el);
    return;
  }
  const s = STATE.settings;
  el.innerHTML = `
    ${pageHead(t('nav_settings'), t(STATE.automation === false ? 'settings_sub_linux' : 'settings_sub'))}
    <div class="settings">
      <nav class="settings-nav" aria-label="${t('nav_settings')}">${SETTINGS_SECTIONS.map(([id, ic]) =>
        `<button type="button" data-action="scroll-to" data-key="${id}">${icon(ic)}<span>${t(id.replace('-', '_'))}</span></button>`).join('')}</nav>
      <div class="settings-body">
        <section class="panel" id="set-account"><div data-live="account">${accountPanel()}</div></section>
        <section class="panel" id="set-env"><div data-live="env">${envPanel()}</div></section>
        <form id="settings-form" class="settings-form" novalidate autocomplete="off">
          ${schedulePanel(s)}${farmingPanel(s)}${dailiesPanel(s)}${notifyPanel(s)}${pathsPanel(s)}
          <section class="panel" id="set-images"><div data-live="images">${imagesPanel()}</div></section>
          ${networkPanel(s)}
        </form>
      </div>
    </div>`;
  SETTINGS_DIRTY = false;
  SETTINGS_ERROR = '';
  updateSavebar();
}

function updateLive(el) {
  el.querySelectorAll('[data-live]').forEach(box => {
    const a = document.activeElement;
    if (a && box.contains(a) && a.matches('select, input')) return;
    const kind = box.dataset.live;
    if (kind === 'account') box.innerHTML = accountPanel();
    else if (kind === 'env') box.innerHTML = envPanel();
    else if (kind === 'images') box.innerHTML = imagesPanel();
    else if (kind === 'notify-recent') box.innerHTML = notifyRecent();
    else if (kind.startsWith('equip-')) box.innerHTML = equipUsage(kind.slice(6));
  });
  reapplyBusy(el);
}

function panelHead(id, ic, extra = '') {
  return `<header class="panel-head"><h2>${icon(ic)}<span>${t(id.replace('-', '_'))}</span></h2>${extra}</header>`;
}

function accountPanel() {
  const qr = STATE.qr || {};
  if (STATE.logged_in) {
    const rows = GAMES.map(g => {
      const acc = STATE.accounts?.[g];
      const options = STATE.candidates?.[g] || [];
      const value = options.length > 1
        ? `<select data-change="select-account" data-game="${g}" aria-label="${t('game_' + g)}">${options.map(c =>
            `<option value="${esc(c.uid)}"${acc && String(acc.uid) === String(c.uid) ? ' selected' : ''}>${t('account_line', c.name, c.uid)}${c.server_name ? ` (${esc(c.server_name)})` : ''}</option>`).join('')}</select>`
        : acc ? `<span>${t('account_line', acc.name || '–', acc.uid)}</span>` : `<span class="ink-2">${t('no_account')}</span>`;
      return `<div class="kv-row"><span class="k">${t('game_' + g)}</span><span class="v">${value}</span></div>`;
    }).join('');
    return `${panelHead('set-account', 'user', button('logout', 'logout', t('btn_logout'), 'sm'))}
      <p style="margin-bottom:12px">${badge('good', 'check', t('acc_signed_in'))}</p><div class="kv">${rows}</div>
      <p>${t(STATE.qr?.unified ? 'widget_connected' : 'widget_disconnected')}</p>
      ${button('widget', 'qr', t(STATE.qr?.unified ? 'btn_widget_manage' : 'btn_widget'), 'sm')}`;
  }
  const waiting = ['waiting', 'scanned'].includes(qr.status) && qr.svg;
  const statusIcon = { error: 'alert', expired: 'clock', scanned: 'check', confirmed: 'check' }[qr.status] || 'qr';
  const img = waiting ? `<img alt="${t('qr_alt')}" src="data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(qr.svg)))}">` : '';
  const action = ['creating', 'waiting', 'scanned', 'reading'].includes(qr.status) ? '' : button('login', 'qr', t(['expired', 'error'].includes(qr.status) ? 'btn_qr_new' : 'btn_qr'), 'primary');
  return `${panelHead('set-account', 'user')}
    <p class="ink-2">${t('acc_desc')}</p>
    <div class="qr-box">${img}${qr.reason ? help(esc(qr.reason), statusIcon) : ''}${action}</div>`;
}

function envRow(label, ok, okText, badText, detail = '', kind = 'bad') {
  const state = ok ? badge('good', 'check', okText) : badge(kind, kind === 'muted' ? 'minus' : 'alert', badText);
  return `<div class="kv-row"><span class="k">${label}</span><span class="v">${state}${detail ? `<code>${esc(detail)}</code>` : ''}</span></div>`;
}

function envPanel() {
  const c = STATE.check || {};
  const bundled = !STATE.settings?.execution?.bgi_template;
  return `${panelHead('set-env', 'shield')}
    <div class="kv">
      ${STATE.automation === false ? help(t('env_plan_only'), 'monitor') : envRow(t('env_admin'), c.admin, t('env_admin_ok'), t('env_admin_no'), '', 'warn')}
      ${envRow(t('env_bgi'), c.genshin?.tool_ok, t('found'), t('missing'), c.genshin?.tool_exe)}
      ${envRow(t('env_bgi_template'), c.genshin?.template_ok, bundled ? t('bundled') : t('found'), t('missing'), bundled ? '' : STATE.settings?.execution?.bgi_template)}
      ${envRow(t('env_od'), c.zzz?.tool_ok, t('found'), t('missing'), c.zzz?.tool_exe)}
      ${envRow(t('env_adapter'), c.zzz?.patch_ok, t('installed'), t('not_installed'), '', 'muted')}
      ${envRow(t('env_game_genshin'), c.genshin?.game_ok, t('found'), t('missing'), c.genshin?.game_exe, 'warn')}
      ${envRow(t('env_game_zzz'), c.zzz?.game_ok, t('found'), t('missing'), c.zzz?.game_exe, 'warn')}
    </div>
    <div class="mt">${help(t('env_adapter_help'))}</div>`;
}

function switchRow(name, checked, label, sub = '', ic = '', cls = '', disabled = false) {
  return `
    <label class="switch-row ${cls}">
      <span class="switch-text">${ic ? icon(ic) : ''}<span><b>${label}</b>${sub ? `<span>${sub}</span>` : ''}</span></span>
      <input type="checkbox" class="switch" name="${name}"${checked ? ' checked' : ''}${disabled ? ' disabled' : ''}>
    </label>`;
}

function field(label, control, hint = '') {
  return `<label class="field"><span>${label}</span>${control}${hint ? `<span class="hint">${icon('info')}<span>${hint}</span></span>` : ''}</label>`;
}

function input(name, value, attrs = '') { return `<input name="${name}" value="${esc(value ?? '')}" ${attrs}>`; }

function schedulePanel(s) {
  const games = s.schedule.games || [];
  const plansOnly = STATE.automation === false;
  return `
    <section class="panel" id="set-schedule">
      ${panelHead('set-schedule', 'clock')}
      ${switchRow('schedule.enabled', s.schedule.enabled, t('sched_enable'), t(plansOnly ? 'sched_plan_only' : 'sched_enable_sub'), 'calendar', 'main first', plansOnly)}
      ${switchRow('schedule.autostart', s.schedule.autostart, t('autostart'), t(plansOnly ? 'autostart_linux' : 'autostart_sub'), 'monitor', '', plansOnly)}
      <div class="sub-block">
        <div class="fields">
          ${field(t('sched_times'), input('schedule.times', (s.schedule.times || []).join(', '), 'type="text" data-type="list" spellcheck="false"'), t('sched_times_hint'))}
          ${field(t('catchup'), input('schedule.catchup_hours', s.schedule.catchup_hours, 'type="number" min="0" max="24" step="0.5"'), t('catchup_hint'))}
          ${field(t('timeout'), input('execution.timeout_minutes', s.execution.timeout_minutes, 'type="number" min="10" max="480" step="5"'))}
          ${field(t('if_running'), `<select name="execution.if_game_running">
              <option value="restart"${s.execution.if_game_running === 'restart' ? ' selected' : ''}>${t('opt_restart')}</option>
              <option value="skip"${s.execution.if_game_running === 'skip' ? ' selected' : ''}>${t('opt_skip')}</option></select>`)}
        </div>
        <fieldset><legend>${t('sched_games')}</legend><div class="check-row">${GAMES.map(g =>
          `<label><input type="checkbox" name="schedule.games" data-type="set" value="${g}"${games.includes(g) ? ' checked' : ''}>${t('game_' + g)}</label>`).join('')}</div></fieldset>
      </div>
    </section>`;
}

function equipUsage(game) {
  const e = STATE.plans?.[game]?.equipment || {};
  return `<span class="usage">${icon('list')}<span>${t('equip_used', e.used ?? 0, e.cap ?? 0)}</span>
    ${button('equip-reset', 'refresh', t('btn_reset'), 'sm quiet', `data-game="${game}"${e.used ? '' : ' disabled'}`)}</span>`;
}

function scanStatus(game) {
  const inv = STATE.inventory?.[game];
  return inv ? t('scan_last', relative(inv.at), num(inv.count)) : t('scan_never');
}

function datalist(id, values) { return `<datalist id="${id}">${(values || []).map(v => `<option value="${esc(v)}">`).join('')}</datalist>`; }

function farmingPanel(s) {
  const p = s.planning;
  const choice = (value, title, sub) => `
    <label class="choice-card"><input type="radio" name="planning.genshin_claim_mode" value="${value}"${p.genshin_claim_mode === value ? ' checked' : ''}>
      <span class="body"><b>${icon('resin')}${title}</b><span>${sub}</span></span></label>`;
  return `
    <section class="panel" id="set-farming">
      ${panelHead('set-farming', 'target')}
      <fieldset><legend>${t('genshin_claims')}</legend><div class="choice">
        ${choice('double', t('opt_mode_double'), t('opt_mode_double_sub'))}${choice('single', t('opt_mode_single'), t('opt_mode_single_sub'))}
      </div></fieldset>
      <div class="fields mt">
        ${field(t('boss_yield'), input('planning.genshin_boss_yield', p.genshin_boss_yield, 'type="number" min="0.5" max="10" step="0.1"'), t('boss_yield_hint'))}
        ${field(t('coffee_forecast'), input('planning.zzz_coffee_forecast', p.zzz_coffee_forecast, 'type="number" min="0" max="300" step="10"'), t('coffee_hint'))}
      </div>
      <div class="sub-block">
        <h3>${icon('box')}<span>${t('equip_title')}</span></h3>
        ${help(t('equip_help'))}
        ${switchRow('planning.artifact.enabled', p.artifact.enabled, t('artifact_switch'), t('artifact_sub'), 'resin')}
        <div class="fields">
          ${field(t('artifact_domain'), input('planning.artifact.domain', p.artifact.domain, 'type="text" list="dl-blessing"') + datalist('dl-blessing', STATE.catalog?.blessing), t('equip_fixed_hint'))}
          ${field(t('artifact_cap'), input('planning.artifact.cap', p.artifact.cap, 'type="number" min="0" step="1"'))}
        </div>
        <div data-live="equip-genshin">${equipUsage('genshin')}</div>
        ${switchRow('planning.disc.enabled', p.disc.enabled, t('disc_switch'), t('disc_sub'), 'battery')}
        <div class="fields">
          ${field(t('disc_mission'), input('planning.disc.mission', p.disc.mission, 'type="text" list="dl-disc"') + datalist('dl-disc', STATE.catalog?.disc), t('equip_fixed_hint'))}
          ${field(t('disc_cap'), input('planning.disc.cap', p.disc.cap, 'type="number" min="0" step="1"'))}
        </div>
        <div data-live="equip-zzz">${equipUsage('zzz')}</div>
      </div>
      <div class="sub-block">
        <h3>${icon('search')}<span>${t('scan_title')}</span></h3>
        ${help(t('scan_help'))}
        ${switchRow('features.scan_inventory', s.features.scan_inventory, t('scan_switch'), t('scan_sub'), 'box')}
        <div class="fields wide">
          ${field(t('scan_yas'), input('paths.yas', s.paths.yas, 'type="text" spellcheck="false"'), scanStatus('genshin'))}
          ${field(t('scan_zzz'), input('paths.zzz_scanner', s.paths.zzz_scanner, 'type="text" spellcheck="false"'), scanStatus('zzz'))}
        </div>
        ${help(t('scan_rules'), 'alert')}
      </div>
    </section>`;
}

function dailiesPanel(s) {
  const f = s.features;
  return `
    <section class="panel" id="set-dailies">
      ${panelHead('set-dailies', 'gift')}
      ${switchRow('features.mute_morning', f.mute_morning, t('mute_morning'), t('mute_morning_sub'), 'bell', 'first')}
      ${switchRow('features.genshin_mail', f.genshin_mail, t('genshin_mail'), '', 'mail')}
      ${switchRow('features.genshin_daily_reward', f.genshin_daily_reward, t('genshin_daily'), '', 'clipboard')}
      ${switchRow('features.genshin_teapot', f.genshin_teapot, t('genshin_teapot'), '', 'cup')}
      ${switchRow('features.zzz_rewards', f.zzz_rewards, t('zzz_rewards'), '', 'gift')}
    </section>`;
}

function secretField(label, key) {
  const saved = STATE.settings?.secrets_set?.[key];
  const clear = saved ? button('clear-secret', 'x', t('btn_clear'), 'sm', `data-key="${key}"`) : '';
  return field(label, `<span class="with-action"><input name="secret.${key}" type="password" placeholder="${saved ? t('secret_saved') : ''}" autocomplete="new-password">${clear}</span>`);
}

function notifyRecent() {
  const list = (STATE.notifications || []).slice(0, 5);
  if (!list.length) return `<p class="ink-2">${t('notify_none')}</p>`;
  return `<ul class="rows">${list.map(n => `
    <li><span class="when"><b>${esc(clock(n.at))}</b><span>${esc(n.channel)}</span></span>
      <span class="what">${esc(n.title)}${n.error ? `<span>${esc(n.error)}</span>` : ''}</span>
      <span class="end">${n.sent ? badge('good', 'check', t('notify_sent')) : n.error ? badge('bad', 'x', t('notify_failed')) : badge('muted', 'clock', t('notify_pending'))}</span></li>`).join('')}</ul>`;
}

function notifyPanel(s) {
  const n = s.notify;
  const ch = n.channels;
  const test = channel => button('notify-test', 'send', t('btn_test'), 'sm', `data-channel="${channel}"`);
  const plansOnly = STATE.automation === false;  // balloon tips need Windows
  return `
    <section class="panel" id="set-notify">
      ${panelHead('set-notify', 'bell')}
      <p style="margin-bottom:8px"><b>${t('notify_events')}</b></p>
      ${switchRow('notify.events.batch', n.events.batch, t('ev_batch'), '', 'list', 'first')}
      ${switchRow('notify.quiet_success', n.quiet_success, t('ev_quiet'), '', 'check')}
      ${switchRow('notify.events.failure', n.events.failure, t('ev_failure'), '', 'alert')}
      ${switchRow('notify.events.login', n.events.login, t('ev_login'), '', 'user')}
      ${switchRow('notify.events.goal_done', n.events.goal_done, t('ev_goal_done'), '', 'target')}
      <div class="sub-block">
        <h3>${t('notify_channels')}</h3>
        ${switchRow('notify.channels.toast.enabled', ch.toast.enabled, t('ch_toast'), plansOnly ? t('windows_only') : '', 'monitor', 'first', plansOnly)}
        ${plansOnly ? '' : `<div class="actions">${test('toast')}</div>`}
        ${switchRow('notify.channels.telegram.enabled', ch.telegram.enabled, t('ch_telegram'), '', 'send')}
        <div class="fields">
          ${field(t('lbl_tg_chat_id'), input('notify.channels.telegram.chat_id', ch.telegram.chat_id, 'type="text" spellcheck="false"'))}
          ${secretField(t('lbl_tg_token'), 'telegram_token')}
        </div>
        <div class="actions">${test('telegram')}</div>
        ${switchRow('notify.channels.webhook.enabled', ch.webhook.enabled, t('ch_webhook'), '', 'globe')}
        <div class="fields wide">${secretField(t('lbl_webhook_url'), 'webhook_url')}</div>
        <div class="actions">${test('webhook')}</div>
        ${switchRow('notify.channels.relay.enabled', ch.relay.enabled, t('ch_relay'), '', 'globe')}
        <div class="fields wide">${secretField(t('lbl_relay_url'), 'relay_url')}</div>
        <div class="actions">${test('relay')}</div>
      </div>
      <div class="sub-block">
        <h3>${icon('history')}<span>${t('notify_recent')}</span></h3>
        <div data-live="notify-recent">${notifyRecent()}</div>
      </div>
    </section>`;
}

function pathsPanel(s) {
  return `
    <section class="panel" id="set-paths">
      ${panelHead('set-paths', 'folder')}
      ${help(t('paths_help'))}
      <div class="fields wide mt">
        ${field(t('lbl_path_bettergi'), input('paths.bettergi', s.paths.bettergi, 'type="text" spellcheck="false"'))}
        ${field(t('lbl_bgi_template'), input('execution.bgi_template', s.execution.bgi_template, `type="text" spellcheck="false" placeholder="${t('ph_bundled_template')}"`), t('template_help'))}
        ${field(t('lbl_path_onedragon'), input('paths.onedragon', s.paths.onedragon, 'type="text" spellcheck="false"'))}
        ${field(t('lbl_path_genshin_exe'), input('paths.genshin_exe', s.paths.genshin_exe, `type="text" spellcheck="false" placeholder="${t('ph_from_tool')}"`))}
        ${field(t('lbl_path_zzz_exe'), input('paths.zzz_exe', s.paths.zzz_exe, `type="text" spellcheck="false" placeholder="${t('ph_from_tool')}"`))}
      </div>
    </section>`;
}

function imagesPanel() {
  const a = STATE.assets_status || {};
  return `${panelHead('set-images', 'image', button('images-sync', 'image', t('btn_images'), 'sm', a.missing || a.failed ? '' : 'disabled'))}
    <p>${t('images_status', a.cached ?? 0, a.missing ?? 0, a.failed ?? 0)}</p>
    <div class="mt">${help(t('images_help'))}</div>`;
}

function networkPanel(s) {
  return `
    <section class="panel" id="set-network">
      ${panelHead('set-network', 'globe')}
      ${switchRow('server.lan', s.server.lan, t('lan'), t('lan_sub'), 'globe', 'first')}
      <div class="fields">
        ${field(t('lbl_port'), input('server.port', s.server.port, 'type="number" min="1" max="65535" step="1"'))}
        ${secretField(t('lbl_password'), 'password')}
      </div>
      <div class="mt">${help(t('network_help'))}</div>
    </section>`;
}

function setPath(obj, path, value) {
  const parts = path.split('.');
  let node = obj;
  parts.slice(0, -1).forEach(p => { node = node[p] = node[p] || {}; });
  node[parts[parts.length - 1]] = value;
}

function collectSettings(form) {
  const settings = {}, secrets = {}, sets = {};
  form.querySelectorAll('[name]').forEach(el => {
    const name = el.name;
    if (el.dataset.type === 'set') {
      sets[name] = sets[name] || [];
      if (el.checked) sets[name].push(el.value);
      return;
    }
    if (el.type === 'radio') {
      if (el.checked) setPath(settings, name, el.value);
      return;
    }
    let value;
    if (el.type === 'checkbox') value = el.checked;
    else if (el.type === 'number') value = el.value === '' ? null : Number(el.value);
    else if (el.dataset.type === 'list') value = el.value.split(/[,，;；\s]+/).map(x => x.trim()).filter(Boolean);
    else value = el.value.trim();
    if (name.startsWith('secret.')) {
      if (value) secrets[name.slice(7)] = value;
      return;
    }
    if (value !== null) setPath(settings, name, value);
  });
  Object.entries(sets).forEach(([name, values]) => setPath(settings, name, values));
  return { settings, secrets };
}

function updateSavebar() {
  const bar = document.getElementById('savebar');
  const show = ROUTE.tab === 'settings' && SETTINGS_DIRTY;
  bar.hidden = !show;
  document.body.classList.toggle('has-savebar', show);
  if (!show) return;
  const key = `${CURRENT_LANG}|${SETTINGS_ERROR}`;
  if (bar.dataset.lang === key) return;
  bar.dataset.lang = key;
  bar.innerHTML = `<span class="msg">${icon('info')}<span>${t('unsaved')}</span></span>
    ${SETTINGS_ERROR ? `<span class="err" role="alert">${icon('alert')}${esc(SETTINGS_ERROR)}</span>` : ''}
    ${button('settings-discard', 'x', t('btn_discard'))}
    ${button('settings-save', 'check', t('btn_save_changes'), 'primary')}`;
  reapplyBusy(bar);
}

// ----------------------------------------------------------- actions
function goalBy(btn) { return findGoal(btn.dataset.id); }

const ACTIONS = {
  retry: () => refreshState(),
  refresh: btn => busy(btn, () => refreshState(true)),
  theme: btn => { applyTheme(btn.dataset.theme); document.getElementById('theme-menu').open = false; },
  toggle: btn => {
    const id = btn.dataset.key;
    if (OPEN.has(id)) OPEN.delete(id); else OPEN.add(id);
    const panel = document.querySelector(`[data-detail="${CSS.escape(id)}"]`);
    if (panel) {
      panel.hidden = !OPEN.has(id);
      if (!panel.hidden) {
        panel.classList.add('reveal');
        panel.addEventListener('animationend', () => panel.classList.remove('reveal'), { once: true });
      }
    }
    btn.setAttribute('aria-expanded', String(OPEN.has(id)));
  },
  run: btn => commit(btn, () => api('/api/run', 'POST', { games: btn.dataset.games.split(',') }), tp('toast_batch_started'), 'starting'),
  stop: btn => commit(btn, () => api('/api/stop', 'POST', {}), tp('toast_stop_sent')),
  verify: btn => openVerify(btn.dataset.game),
  'refresh-notes': btn => commit(btn, async () => {
    const res = await api('/api/notes/refresh', 'POST', { game: btn.dataset.game });
    if (res && res.error) throw new Error(res.error);
  }, tp('toast_notes')),
  'goals-game': btn => { GOALS_GAME = btn.dataset.game; store.set('gcl_goals_game', GOALS_GAME); render(true); },
  'add-goal': () => openAddGoal(),
  'modal-close': () => closeDialog(),
  'pick-char': btn => {
    MODAL.selected = { id: btn.dataset.id, name: btn.dataset.name };
    document.querySelectorAll('#char-list .char').forEach(b => b.setAttribute('aria-selected', String(b === btn)));
    document.getElementById('modal-add').disabled = false;
  },
  'move-goal': btn => commit(btn, async () => {
    const goal = goalBy(btn);
    const list = (STATE.goals?.[goal.game] || []).filter(g => g.enabled);
    const i = list.findIndex(g => g.id === goal.id), j = i + Number(btn.dataset.dir);
    if (j < 0 || j >= list.length) return;
    [list[i], list[j]] = [list[j], list[i]];
    await api('/api/goals/order', 'POST', { game: goal.game, ids: list.map(g => g.id) });
  }, tp('toast_order'), undefined, goalSel(btn.dataset.id)),
  'sync-goal': btn => commit(btn, () => api('/api/goals/sync', 'POST', { id: btn.dataset.id, observe: true }), tp('toast_synced'), 'syncing', goalSel(btn.dataset.id)),
  'edit-targets': btn => { const goal = goalBy(btn); if (goal) openTargets(goal); },
  'edit-gear': btn => { const goal = goalBy(btn); if (goal && goal.gear_eval) openGearTarget(goal); },
  'targets-discard': () => { MODAL.dirty = false; MODAL.error = ''; renderTargetsDialog(findGoal(MODAL.id)); },
  'cancel-goal': btn => {
    const goal = goalBy(btn);
    if (!goal || !confirm(tp('confirm_cancel', goal.name))) return;
    commit(btn, () => api('/api/goals/update', 'POST', { id: goal.id, patch: { enabled: false } }), tp('toast_goal_canceled', goal.name));
  },
  'resume-goal': btn => {
    const goal = goalBy(btn);
    commit(btn, () => api('/api/goals/update', 'POST', { id: goal.id, patch: { enabled: true } }), tp('toast_goal_resumed', goal.name), undefined, goalSel(goal.id));
  },
  'delete-goal': btn => {
    const goal = goalBy(btn);
    if (!goal || !confirm(tp('confirm_delete', goal.name))) return;
    commit(btn, () => api('/api/goals/delete', 'POST', { id: goal.id }), tp('toast_goal_deleted', goal.name));
  },
  'pause-item': btn => commit(btn, async () => {
    const goal = goalBy(btn);
    const paused = new Set(goal.paused || []);
    if (btn.dataset.pause === '1') paused.add(btn.dataset.key); else paused.delete(btn.dataset.key);
    await api('/api/goals/update', 'POST', { id: goal.id, patch: { paused: [...paused] } });
  }, tp(btn.dataset.pause === '1' ? 'toast_paused' : 'toast_resumed'), undefined, `[data-row="${CSS.escape(btn.dataset.key)}"]`),
  'shift-cat': btn => commit(btn, async () => {
    const goal = goalBy(btn);
    const order = [...(goal.category_order || ['level', 'talents', 'weapon'])];
    const i = Number(btn.dataset.index), j = i + Number(btn.dataset.dir);
    [order[i], order[j]] = [order[j], order[i]];
    await api('/api/goals/update', 'POST', { id: goal.id, patch: { category_order: order } });
  }, tp('toast_order'), undefined, `${goalSel(btn.dataset.id)} .priority`),
  'more-runs': btn => busy(btn, async () => { MORE_RUNS = (await api('/api/runs?limit=200')).rows || []; render(true); }),
  'scroll-to': btn => document.getElementById(btn.dataset.key)?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
  widget: () => openWidget(),
  'widget-start': btn => busy(btn, async () => {
    STATE.qr = await api('/api/login/start', 'POST', {});
    updateWidgetDialog();
  }),
  login: btn => busy(btn, async () => {
    STATE.qr = await api('/api/login/start', 'POST', {});
    updateLive(document.getElementById('view-settings'));
    updateWidgetDialog();
  }),
  'cancel-login': btn => busy(btn, async () => {
    await api('/api/logout', 'POST', {});
    closeDialog();
    await refreshState(true);
  }),
  logout: btn => {
    if (!confirm(tp('confirm_logout'))) return;
    commit(btn, () => api('/api/logout', 'POST', {}), tp('toast_logged_out'));
  },
  'equip-reset': btn => commit(btn, () => api('/api/equip/reset', 'POST', { game: btn.dataset.game }), tp('toast_equip_reset')),
  'images-sync': btn => commit(btn, () => api('/api/assets/sync', 'POST', {}), tp('toast_images')),
  'notify-test': btn => {
    if (SETTINGS_DIRTY) { toast(tp('toast_save_first'), 'error'); return; }
    busy(btn, async () => { await api('/api/notify/test', 'POST', { channel: btn.dataset.channel }); toast(tp('toast_test_sent')); });
  },
  'clear-secret': btn => commit(btn, async () => {
    await api('/api/settings', 'POST', { settings: {}, secrets: { [btn.dataset.key]: '' } });
    if (!SETTINGS_DIRTY) setTimeout(() => renderSettings('discard'));
  }, tp('toast_secret_cleared')),
  'settings-discard': () => { SETTINGS_DIRTY = false; SETTINGS_ERROR = ''; renderSettings('discard'); },
  'settings-save': btn => busy(btn, async () => {
    const { settings, secrets } = collectSettings(document.getElementById('settings-form'));
    const times = settings.schedule?.times || [];
    try {
      if (!times.every(x => /^([01]\d|2[0-3]):[0-5]\d$/.test(x))) throw new Error(tp('bad_times'));
      const res = await api('/api/settings', 'POST', { settings, secrets });
      SETTINGS_DIRTY = false;
      SETTINGS_ERROR = '';
      const ok = await refreshState();
      renderSettings('discard');
      toast(ok ? tp(res && res.restart_needed ? 'toast_restart' : 'toast_saved') : tp('saved_not_reloaded'), ok ? 'ok' : 'error');
    } catch (err) {
      SETTINGS_ERROR = err.message;   // keep the draft; show the error next to Save
      updateSavebar();
    }
  }, 'saving')
};

const CHANGES = {
  'select-account': el => commit(null, () => api('/api/accounts/select', 'POST', { game: el.dataset.game, uid: el.value }), tp('toast_account')),
  'gear-follow': el => toggleFollow(el)
};

async function submitTargets(form) {
  const goal = findGoal(MODAL.id);
  const patch = { target: {} };
  for (const [k, v] of new FormData(form).entries()) if (v !== '') patch.target[k] = parseInt(v, 10);
  const btn = form.querySelector('[data-action="save-targets"]');
  await busy(btn, async () => {
    try {
      await api('/api/goals/update', 'POST', { id: goal.id, patch });
    } catch (err) {
      if (!MODAL || MODAL.kind !== 'targets') throw err;   // dialog closed meanwhile: report as a toast
      MODAL.error = err.message;                           // otherwise show it next to Save, keeping the draft
      redrawTargetsKeepingDraft(form);
      return;
    }
    if (MODAL && MODAL.kind === 'targets' && MODAL.id === goal.id) closeDialog();
    const ok = await refreshState(true);
    toast(ok ? tp('toast_targets') : tp('saved_not_reloaded'), ok ? 'ok' : 'error');
    if (ok) flash(`${goalSel(goal.id)} .targets`);
  }, 'saving');
}

/** Re-draw the dialog (to show an error) while keeping the values the user typed. */
function redrawTargetsKeepingDraft(form) {
  const values = Object.fromEntries(new FormData(form).entries());
  renderTargetsDialog(findGoal(MODAL.id));
  const fresh = document.querySelector('#modal form');
  Object.entries(values).forEach(([k, v]) => { const el = fresh.querySelector(`[name="${k}"]`); if (el) el.value = v; });
}

async function submitAddGoal(form) {
  const pick = MODAL && MODAL.selected;
  if (!pick) return;
  const game = MODAL.game;
  await commit(form.querySelector('[type=submit]'), async () => {
    await api('/api/goals/create', 'POST', { game, character_id: pick.id, name: pick.name });
    closeDialog();
  }, tp('toast_goal_added', pick.name), 'saving');
}

// ----------------------------------------------------------- routing and events
function parseRoute() {
  const [tab, arg] = location.hash.replace(/^#\/?/, '').split('/');
  return { tab: TABS.some(([id]) => id === tab) ? tab : 'today', arg: arg ? decodeURIComponent(arg) : null };
}

function showRoute() {
  const prev = ROUTE.tab;
  ROUTE = parseRoute();
  document.querySelectorAll('#tabs a').forEach(a => {
    if (a.dataset.tab === ROUTE.tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  document.querySelectorAll('main > section').forEach(s => { s.hidden = s.id !== `view-${ROUTE.tab}`; });
  if (ROUTE.tab !== 'runs') MORE_RUNS = null;
  if (ROUTE.tab === 'goals' && ROUTE.arg && STATE) {
    const goal = findGoal(ROUTE.arg);
    if (goal) GOALS_GAME = goal.game;
  }
  render(ROUTE.tab !== prev || Boolean(ROUTE.arg));
  if (ROUTE.arg) {
    const target = document.getElementById(ROUTE.tab === 'goals' ? `goal-${ROUTE.arg}` : ROUTE.arg);
    if (target) {
      target.scrollIntoView({ block: 'start' });
      if (target.classList.contains('goal')) { target.classList.add('flash'); setTimeout(() => target.classList.remove('flash'), 1600); }
    }
  } else if (ROUTE.tab !== prev) {
    window.scrollTo(0, 0);
  }
}

document.addEventListener('click', e => {
  const lang = e.target.closest('#lang-switch [data-lang]');
  if (lang) { setLanguage(lang.dataset.lang); return; }
  const btn = e.target.closest('[data-action]');
  if (btn && !btn.disabled && btn.type !== 'submit' && ACTIONS[btn.dataset.action]) {
    e.preventDefault();
    ACTIONS[btn.dataset.action](btn, e);
  }
  const menu = document.getElementById('theme-menu');
  if (menu.open && !menu.contains(e.target)) menu.open = false;
});

function markSettingsDirty() {
  if (!SETTINGS_DIRTY) { SETTINGS_DIRTY = true; updateSavebar(); }
}

document.addEventListener('change', e => {
  const el = e.target.closest('[data-change]');
  if (el && CHANGES[el.dataset.change]) CHANGES[el.dataset.change](el);
  if (e.target.closest('#settings-form')) markSettingsDirty();
});

document.addEventListener('input', e => {
  if (e.target.id === 'char-search' && MODAL) {
    MODAL.query = e.target.value;
    document.getElementById('char-list').innerHTML = charOptions();
    return;
  }
  const form = e.target.closest('form');
  if (!form) return;
  if (form.id === 'settings-form') markSettingsDirty();
  else if (form.dataset.form === 'gear' && MODAL) MODAL.dirty = true;
  else if (form.dataset.form === 'targets' && MODAL && !MODAL.dirty) {
    MODAL.dirty = true;
    form.querySelector('[data-action="targets-discard"]').hidden = false;
  }
});

document.addEventListener('submit', e => {
  const form = e.target;
  e.preventDefault();
  if (form.dataset.form === 'targets') submitTargets(form);
  else if (form.dataset.form === 'gear') submitGearTarget(form);
  else if (form.dataset.form === 'add-goal') submitAddGoal(form);
  else if (form.id === 'settings-form') ACTIONS['settings-save'](document.querySelector('[data-action="settings-save"]'));
});

document.addEventListener('pointermove', trackPointer);
document.addEventListener('pointerout', e => {
  const plot = e.target.closest && e.target.closest('.trk-plot');
  if (plot && !plot.contains(e.relatedTarget)) plot.querySelectorAll('.trk-x, .trk-read').forEach(n => n.remove());
});

document.addEventListener('keydown', e => {
  const menu = document.getElementById('theme-menu');
  if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); }
});

window.addEventListener('hashchange', showRoute);
window.addEventListener('beforeunload', e => {
  if (SETTINGS_DIRTY || (MODAL && MODAL.dirty)) { e.preventDefault(); e.returnValue = ''; }
});
document.getElementById('modal').addEventListener('close', () => { MODAL = null; });

// ----------------------------------------------------------- start
(function start() {
  applyTheme(THEME);
  document.documentElement.lang = CURRENT_LANG === 'zh' ? 'zh-CN' : 'en';
  ROUTE = parseRoute();
  renderShell();
  document.querySelectorAll('main > section').forEach(s => { s.hidden = s.id !== `view-${ROUTE.tab}`; });
  refreshState().then(() => { if (ROUTE.arg) showRoute(); });
  setInterval(() => { if (!document.hidden) refreshState(); }, 5000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshState(); });
})();
