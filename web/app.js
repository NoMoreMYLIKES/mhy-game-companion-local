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
    look_label: 'Appearance',
    theme_label: 'Theme',
    theme_timetable: 'Timetable',
    theme_zzz: 'Proxy',
    mode_label: 'Mode',
    mode_system: 'System',
    mode_light: 'Light',
    mode_dark: 'Dark',
    connecting: 'Connecting to the backend…',
    connect_failed: 'Cannot reach the backend ({0}). Start it with Start.bat, then retry.',
    retry: 'Retry',
    req_failed: 'The app’s local service hit an error. Try again; if it keeps failing, see the log file listed in Settings\u00a0›\u00a0Environment. (HTTP {0})',   // the menu path stays on one line
    btn_dismiss: 'Dismiss',
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
    strip_game_day: 'Game day {0} · resets 04:00',
    strip_next_run: 'Next run at {0} ({1})',
    strip_schedule_off: 'Schedule off',
    strip_running: 'Running: {0}',
    strip_running_game: 'Running: {0} · {1} (step {2} of {3})',
    strip_signed_out: 'Miyoushe not signed in',
    strip_login_expired: 'Miyoushe login expired',
    strip_not_admin: 'Not running as administrator',
    strip_plan_only: 'Plans only: runs need Windows',

    // Games and terms
    game_genshin: 'Genshin Impact',
    game_zzz: 'Zenless Zone Zero',
    game_short_genshin: 'GI',
    game_short_zzz: 'ZZZ',
    el_pyro: 'Pyro',
    el_hydro: 'Hydro',
    el_anemo: 'Anemo',
    el_electro: 'Electro',
    el_dendro: 'Dendro',
    el_cryo: 'Cryo',
    el_geo: 'Geo',
    el_physical: 'Physical',
    el_fire: 'Fire',
    el_ice: 'Ice',
    el_electric: 'Electric',
    el_ether: 'Ether',
    el_wind: 'Wind',
    rank_letter: '{0}-rank',
    unit_genshin: 'Original Resin',
    unit_zzz: 'Battery Charge',
    unknown: 'Unknown',
    none: 'None',

    // Today
    btn_run_both: 'Run both games',
    btn_run_now: 'Run now',
    btn_refresh: 'Refresh',
    btn_reread: 'Re-read {0}',
    confirm_run: 'Start now?\n\n{0}\n\nUntil the batch ends, the game and its automation tool use this PC’s mouse and keyboard.',
    confirm_run_item: '{0}: {1} for {2} (≈ {3} {4})',
    confirm_run_open: '{0}: {1} for {2} (the in-game stamina decides)',
    confirm_run_idle: '{0}: free dailies only',
    run_needs_windows: 'Runs need Windows: start them from the Windows copy.',
    run_why_windows: 'Runs need Windows',
    run_why_busy: 'A batch is running',
    account_line: '{0}, UID {1}',
    no_account: 'No game account selected',
    not_signed_in: 'Not signed in',
    stamina_unknown_hint: 'No reading yet. Sign in to Miyoushe or refresh; during a run the tool still uses the real in-game value.',
    stamina_signed_out_hint: 'Sign in to Miyoushe to read it; during a run the tool still uses the real in-game value.',
    tile_next_spend: 'Next run −{0}',
    full_now_genshin: 'Full: natural recovery is being wasted',
    full_now_zzz: 'Full: further recovery goes to Stored Battery, more slowly',
    tile_full: 'Full',
    tile_unread: 'Not read',
    st_full_at: 'Full at',
    st_full_in: 'In ≈ {0} if nothing runs',
    st_read: 'Read',
    notes_issue: '{0} could not be read: {1}',
    col_runs: 'Upcoming runs',
    col_runs_ran: 'Last and upcoming runs',
    col_goals: 'Goals',
    tag_next: 'Next',
    departed: 'Ran {0}',
    tt_manual: 'Manual',
    dailies_line: 'Also in every batch: {0}',
    goals_progress: '{0}% collected · {1} of {2} items done',
    goals_items: '{0} of {1} items done',
    goal_all_done: 'Materials ready: level up in game',
    goal_error: 'Could not be read',
    goals_none: 'No goals for this game yet.',
    goals_more: '+{0} more on the Goals page',
    btn_login_manage: 'Manage login',
    btn_login_again: 'Authorize again',
    btn_login_cancel: 'Cancel login',
    login_title: 'Miyoushe login',
    login_shared: 'One login shared by all games and data sources',
    login_status: 'Login status',
    next_batch: 'Next batch',
    next_batch_at: 'Next batch at {0}',
    phase_equipment: 'Equipment continuation',
    fact_spend: '≈ {0} {1}',
    for_goal: '{0}: {1}',
    btn_details: 'Details',
    btn_adjust_goal: 'Adjust goal',
    btn_farming_settings: 'Farming settings',
    btn_open_goals: 'Open goals',
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
    latest_run: 'Latest run',
    no_runs_yet: 'No runs yet.',
    view_all: 'View all',
    daily_only: 'Free dailies only',
    exc_signed_out: 'Miyoushe is not signed in, so stamina and material gaps cannot be read.',
    exc_sign_in: 'Sign in',
    exc_login_expired: 'Miyoushe login has expired, so {0} and material gaps cannot be read.',
    exc_login_expired_calc: 'Miyoushe login has expired, so material gaps cannot be read.',
    tile_login_expired: 'Not read: the Miyoushe login has expired.',
    exc_not_admin: 'The backend is not running as administrator, so runs cannot control the game window. Start it with Start.bat.',
    exc_tool_genshin: 'BetterGI was not found, so Genshin Impact cannot run.',
    exc_tool_zzz: 'ZZZ OneDragon was not found, so Zenless Zone Zero cannot run.',
    exc_set_paths: 'Set paths',
    exc_goal_error: '{0} could not be read from Miyoushe, so plans use the last data read. ({1})',
    exc_open: 'Open goal',
    btn_sync_again: 'Sync again',
    left_coffee: '≈ {0} left (incl. +{1} coffee)',
    full_before: 'Full at {0}, ≈ {1} before this\u00a0run',

    // Running batch
    running_title: 'Batch running',
    running_game: '{0}, game {1} of {2}',
    stage_prepare: 'Prepare',
    stage_config: 'Set up tools',
    stage_launch: 'Launch game',
    stage_running: 'Automate',
    stage_collect: 'Read results, restore tools',
    stage_scan: 'Scan inventory',
    scan_title: 'Inventory scan',
    scan_help: 'Miyoushe shows only equipped pieces. A scan reads every artifact or Drive Disc you own, so equipment farming stops once pieces you own meet a character’s target, and the goal card lists what to equip. The app never equips, locks or dismantles anything; your tools can if you turn that on (see Daily tasks › What your tools can also do).',
    scan_switch: 'Scan the inventory automatically',
    scan_sub: 'After every equipment run, and at least once a day otherwise, before the game closes',
    scan_yas: 'Artifact scanner (yas_artifact.exe)',
    scan_zzz: 'Drive Disc scanner (ZZZ-Scanner.Next.exe)',
    scan_rules_title: 'Scanner requirements',
    scan_last_zzz: 'Last scan {0}: {1} discs',
    scan_last_genshin: 'Last scan {0}: {1} artifacts',
    scan_never: 'Not scanned yet',
    scan_rules: 'Both scanners read the screen: the game must use the Simplified Chinese UI in a 1920×1080 window, and the mouse must not be touched during a scan (2–5 minutes per 1,000 pieces). Install the scanners yourself; the app opens the bag or the Drive Disc storage and runs them.',
    stage_stopping: 'Stopping…',
    btn_stop: 'Stop current run',
    running_hands_off: 'Hands off the mouse and keyboard until the batch ends.',

    // Goals
    goals_sub: 'Characters you are building. The order decides what is farmed first.',
    btn_add_goal: 'Add goal',
    goals_empty_title: 'No goals yet',
    goals_empty_desc: 'Add a character to start planning its materials.',
    queue_pos: 'Queue {0} of {1}',
    synced: 'Levels synced {0}',
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
    cat_talents_genshin: 'Talents',
    cat_talents_zzz: 'Skills',
    cat_weapon_genshin: 'Weapon',
    cat_weapon_zzz: 'W-Engine',
    btn_change: 'Change',
    mat_from: 'From {0}',
    mat_exp: 'EXP',
    mat_family: 'Tiered',
    mat_core: 'Core skill',
    mats_title: 'Materials still needed',
    mats_none: 'All materials collected: level up in game.',
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
    status_manual: 'By hand',
    btn_pause: 'Pause',
    btn_resume: 'Resume',
    tier_material: 'Material',
    tier_need: 'Need',
    tier_have: 'Have',
    tier_short: 'Short',
    stable_list_help: 'Progress = Miyoushe’s count at the last sync + what runs farmed since.',
    canceled_title: 'Canceled cultivation ({0})',
    canceled_note: 'Canceled goals keep their targets and progress and are never farmed.',

    // Dialogs
    dlg_targets_title: 'Target settings for {0}',
    targets_help: 'Current levels come from the last sync. A target at or below the current level counts as reached.',
    btn_save_changes: 'Save changes',
    btn_discard: 'Discard changes',
    btn_close: 'Close',
    btn_add: 'Add',
    btn_pick_first: 'Pick a character',
    btn_max: 'Set all to max',
    modal_add_title: 'Add a {0} goal',
    search_placeholder: 'Search characters',
    modal_loading: 'Loading characters…',
    modal_source_roster: 'Your characters, from Miyoushe.',
    modal_source_dataset: 'All characters from the offline list. Sign in to Miyoushe to see only yours.',
    modal_source_offline: 'All characters from the offline list: your own could not be read from Miyoushe.',
    no_match: 'No matching characters.',
    already_added: 'Already a goal',
    not_owned: 'Not owned',

    // Schedule
    plan_sub: 'Forecast for the next 3 days, simulated with the same rule as real runs. Past runs are on the Runs page.',
    plan_off_banner: 'The schedule is off, so nothing runs automatically. This is a preview.',
    reason_same: 'Same reason as above.',
    idle_fix: 'To spend it anyway, add a goal or set up Equipment continuation in Farming rules.',
    day_before_reset: 'game day {0} until 04:00',
    btn_open_settings: 'Open settings',
    day_head: '{0}, {1}',
    left_after: '≈ {0} left',
    plan_empty_title: 'Nothing scheduled',
    plan_empty: 'Add run times in Settings, and the next three days are forecast here.',

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
    run_unverified: 'Counted at the next sync',
    run_duration: 'Took {0}',
    runs_empty_title: 'No runs yet',
    runs_empty: 'Batches started on Today or by the schedule are listed here with their results.',
    btn_open_today: 'Open Today',
    no_games: 'No game ran',
    btn_more_runs: 'Show older runs',

    // Settings
    settings_sub: 'Changes are saved together, with the bar that appears at the bottom.',
    secret_hint: 'Encrypted with Windows DPAPI.',
    secret_hint_linux: 'Stored in a file only this user can read.',
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
    env_admin_hint: 'Runs may fail to control the game window. Start the app with Start.bat (in the app folder), or turn on Start with Windows (it runs elevated).',
    env_plan_only: 'BetterGI and OneDragon are Windows programs; these checks apply to the Windows copy.',
    env_bgi: 'BetterGI',
    env_bgi_template: 'BetterGI template',
    env_od: 'ZZZ OneDragon',
    env_adapter: 'Live Battery Charge adapter',
    env_adapter_help: 'Optional OneDragon patch that lets the last batch use the Battery Charge actually left. Without it, whole card batches are issued and the last one may be skipped.',
    env_game_genshin: 'Genshin Impact client',
    env_game_zzz: 'Zenless Zone Zero client',
    env_data_dir: 'Data folder',
    env_data_dir_hint: 'Your settings, goals, run history and Miyoushe login are kept here.',
    env_log: 'Log file',
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
    opt_restart: 'Close the game and run',
    opt_skip: 'Skip this slot',
    if_running_hint: 'Closing the game loses its unsaved progress.',
    genshin_claims: 'Genshin Domain rewards',
    opt_mode_double: 'Use 40 Original Resin for 2× rewards first',
    opt_mode_double_sub: 'Recommended. Leftover resin is used 20 at a time.',
    opt_mode_single: 'Use 20 Original Resin per claim',
    opt_mode_single_sub: 'One reward per 20 Original Resin.',
    boss_yield: 'Genshin boss drops per run',
    boss_yield_hint: 'Average at your World Level; converts the gap into boss runs',
    coffee_forecast: 'ZZZ coffee in the forecast (Battery Charge per day)',
    coffee_hint: 'Used in forecasts (Today and Schedule); runs read the real Battery Charge',
    equip_title: 'Equipment continuation',
    equip_help: 'Artifacts and Drive Discs have no end, so they are farmed only when no goal material is left, up to the cumulative cap you set.',
    artifact_switch: 'Genshin: farm Artifacts',
    artifact_sub: 'Domain of Blessing, 20 Original Resin per claim',
    artifact_domain: 'Domain of Blessing',
    artifact_cap: 'Budget until reset (claims)',
    disc_switch: 'ZZZ: farm Drive Discs',
    disc_sub: 'Area Patrol, 60 Battery Charge per run',
    disc_mission: 'Area Patrol mission',
    disc_cap: 'Budget until reset (runs)',
    equip_used: 'Used {0} of {1}',
    equip_role_other: 'This budget was granted for another game role, so it spends nothing for the selected one.',
    btn_equip_grant: 'Allow for this role',
    equip_fixed_hint: 'Used only while no character’s equipment target steers farming',
    equip_none: 'None: only characters’ targets steer',
    stages_needed: 'Drops a set your goals need',
    stages_other: 'Other',
    gear_wasted: 'Upgrades on uncounted substats: {0}',
    gear_status_owned: 'Owned pieces meet the target',
    gear_owned_title: 'With pieces you own: score {0}',
    gear_owned_done: 'Equip these to meet the target',
    gear_owned_short: 'Still short with the best pieces you own; farming continues',
    inv_line_zzz: 'Drive Disc storage scanned {0}: {1} discs, {2} spare',
    inv_line_genshin: 'Artifact bag scanned {0}: {1} artifacts, {2} spare',
    inv_spare_help: 'Spare: unequipped, unlocked pieces that score below 30 for every character that farms equipment. Dismantle them in the game if you like; the app never does.',
    gear_all_hit: 'Every upgrade counts',
    gear_totals: 'Counted rolls: {0}',
    gear_title: 'Drive Discs',
    btn_gear_target: 'Equipment target',
    gear_none_yet: 'Drive Discs not read yet. Sync this character to read them.',
    gear_status_met: 'Target met',
    gear_verdict_met: 'Target met',
    gear_verdict_below: 'Target not met · {0} of {1} conditions met',
    gear_glance_met: '{0}: target met',
    gear_glance_equip: '{0}: equip {1} from storage to meet the target',
    gear_status_off: 'Not steering farming',
    gear_status_next: 'Next equipment run: {0}',
    gear_status_queued: 'Queued: {0}',
    gear_status_blocked: 'Not farmed now',
    gear_sets_line: 'Sets: {0}',
    gear_mains_ok: 'Main stats match',
    gear_mains_bad: 'Main stat mismatch',
    gear_slots_filled: '{0} of {1} slots filled',
    gear_src_custom: 'Your weights',
    gear_src_mine: 'Weights from your own picks on Miyoushe',
    gear_src_recommended: 'Weights from Miyoushe’s recommendation',
    gear_src_official: 'Weights from the build “{0}”',
    gear_src_none: 'No weights: set them in the equipment target',
    gear_read_zzz: 'Equipped discs read {0}',
    gear_read_genshin: 'Equipped artifacts read {0}',
    gear_runs: '{0} runs farmed for this character',
    gear_weights_line: 'Counted substats: {0}',
    gear_no_weights: 'No substat counts yet: the build lists none and no weights are set.',
    gear_help: 'The score counts the substat rolls already on each disc (an S-rank roll counts 1, A and B rolls less) against the best a disc in that slot could hold, then averages the six slots; an empty slot counts 0. Equip better discs in the game; the score updates on the next sync.',
    gear_slot: 'Slot {0}',
    gear_slot_empty: 'Empty',
    gear_disc_score: 'Disc score',
    gear_rank: 'Rank {0}',
    gear_lv: 'Lv. {0}',
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
    art_rank: '{0}★',
    art_lv: '+{0}',
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
    genshin_daily_sub: 'Without doing commissions, every 30 Original Resin spent turns stored Encounter Points into one commission reward, up to 4 a day (120 resin for all 4).',
    genshin_teapot_sub: 'Collects realm currency and companionship EXP from the Serenitea Pot.',
    tools_more_title: 'What your tools can also do',
    tools_zzz_intro: 'Each batch runs your OneDragon run list (一条龙), so whatever you turn on there runs too, for example:',
    tools_zzz_list: ['Notorious Hunt: 3 free reward claims a week; pick the boss your goals need in OneDragon',
                     'Lost Void weekly bounty, Ridu Weekly, redeem codes, the scratch card and the video store',
                     'Coffee: the forecast counts it ({0})',
                     'Long runs (Lost Void, Withered Domain, Shiyu Defense) count toward the per-game timeout ({1}); limit them in OneDragon'],
    tools_genshin_intro: 'Batches run only the domain or boss this app picks, plus the claims above. BetterGI can also run these; start them from BetterGI, and the resin they spend is not there for the next batch:',
    tools_genshin_list: ['Ley Line Outcrops: Mora and EXP books', 'Craft Condensed Resin: stores resin, up to 5', 'Stygian Onslaught: artifacts',
                         'Map-tracking routes from its script repository: local specialties and ores'],
    tools_more_risk: 'Two tool options dismantle equipment, and they also run inside this app’s batches when turned on in the tool: OneDragon’s Drive Disc dismantle (in its run list; A-rank and lower by default) and BetterGI’s quick artifact salvage after domains. This app never turns either on; keep them off to keep your pieces.',
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
    toast_logged_out: 'Logged out',
    toast_goal_added: '{0} added',
    toast_goal_canceled: 'Cultivation canceled for {0}',
    toast_goal_resumed: 'Cultivation resumed for {0}',
    toast_goal_deleted: '{0} deleted',
    toast_synced: 'Synced with the official calculator',
    toast_sync_failed: 'Sync incomplete: {0}',
    toast_paused: 'Item paused',
    toast_resumed: 'Item resumed',
    toast_order: 'Order updated',
    toast_targets: 'Targets saved; recalculating',
    toast_saved: 'Settings saved',
    toast_restart: 'Settings saved. Restart the backend to apply the port or LAN change.',
    toast_equip_reset: 'Counter reset',
    toast_equip_granted: 'Budget allowed for the selected role',
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
    look_label: '外观',
    theme_label: '主题',
    theme_timetable: '时刻表',
    theme_zzz: '绳匠',
    mode_label: '明暗',
    mode_system: '跟随系统',
    mode_light: '浅色',
    mode_dark: '深色',
    connecting: '正在连接后台…',
    connect_failed: '无法连接后台（{0}）。请通过 Start.bat 启动后重试。',
    retry: '重试',
    req_failed: '本地服务出错。请重试；如持续失败，请查看 设\u2060置\u00a0›\u00a0运\u2060行\u2060环\u2060境 中列出的日志文件。（HTTP {0}）',
    btn_dismiss: '关闭',
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
    rel_in: '{0}\u2060后',   // a word joiner keeps 后 / 前 on the line of their duration
    rel_ago: '{0}\u2060前',
    dur_lt_min: '不到\u00a01\u00a0分\u2060钟',
    dur_m: '{0}\u00a0分\u2060钟',   // no-break spaces and word joiners keep a duration on one line
    dur_h: '{0}\u00a0小\u2060时',
    dur_hm: '{0}\u00a0小\u2060时\u00a0{1}\u00a0分\u2060钟',

    // Status strip
    strip_game_day: '游戏日 {0} · 04:00 刷新',
    strip_next_run: '下次执行 {0}（{1}）',
    strip_schedule_off: '定时未开启',
    strip_running: '执行中：{0}',
    strip_running_game: '执行中：{0} · {1}（第 {2}/{3} 步）',
    strip_signed_out: '米游社未登录',
    strip_login_expired: '米游社登录已过期',
    strip_not_admin: '未以管理员身份运行',
    strip_plan_only: '仅规划：执行需要 Windows',

    // Games and terms
    game_genshin: '原神',
    game_zzz: '绝区零',
    game_short_genshin: '原神',
    game_short_zzz: '绝区零',
    el_pyro: '火',
    el_hydro: '水',
    el_anemo: '风',
    el_electro: '雷',
    el_dendro: '草',
    el_cryo: '冰',
    el_geo: '岩',
    el_physical: '物理',
    el_fire: '火',
    el_ice: '冰',
    el_electric: '电',
    el_ether: '以太',
    el_wind: '风',
    rank_letter: '{0}级',
    unit_genshin: '原粹树脂',
    unit_zzz: '电量',
    unknown: '未知',
    none: '无',

    // Today
    btn_run_both: '两款游戏依次执行',
    btn_run_now: '立即执行',
    btn_refresh: '刷新',
    btn_reread: '重新读取{0}',
    confirm_run: '现在开始执行？\n\n{0}\n\n批次结束前，游戏和自动化工具会占用这台电脑的鼠标和键盘。',
    confirm_run_item: '{0}：为{2}刷{1}（约 {3} {4}）',
    confirm_run_open: '{0}：为{2}刷{1}（以游戏内体力为准）',
    confirm_run_idle: '{0}：仅免费日常',
    run_needs_windows: '执行需要 Windows，请在 Windows 端执行。',
    run_why_windows: '执行需要 Windows',
    run_why_busy: '正在执行批次',
    account_line: '{0}，UID {1}',
    no_account: '未选择游戏账号',
    not_signed_in: '未登录',
    stamina_unknown_hint: '暂无读数。请登录米游社或刷新；执行时工具仍以游戏内实际数值为准。',
    stamina_signed_out_hint: '登录米游社后即可读取；执行时工具仍以游戏内实际数值为准。',
    tile_next_spend: '下一批 −{0}',
    full_now_genshin: '已满：自然恢复正在溢出',
    full_now_zzz: '已满：之后的回复转入储蓄电量，速度较慢',
    tile_full: '已满',
    tile_unread: '未读取',
    st_full_at: '回满',
    st_full_in: '若不执行，约 {0}\u2060后',
    st_read: '读取',
    notes_issue: '无法读取{0}：{1}',
    col_runs: '接下来的执行',
    col_runs_ran: '最近与接下来的执行',
    col_goals: '培养目标',
    tag_next: '下一批',
    departed: '已执行 {0}',
    tt_manual: '手动',
    dailies_line: '每批还会执行：{0}',
    goals_progress: '已收集 {0}% · 完成 {1}/{2} 项',
    goals_items: '完成 {0}/{1} 项',
    goal_all_done: '材料已齐，请进游戏升级',
    goal_error: '读取失败',
    goals_none: '此游戏还没有培养目标。',
    goals_more: '另有 {0} 个，见“培养”页',
    btn_login_manage: '管理登录',
    btn_login_again: '重新授权',
    btn_login_cancel: '取消登录',
    login_title: '米游社登录',
    login_shared: '各游戏及数据读取共用此登录',
    login_status: '登录状态',
    next_batch: '下一批',
    next_batch_at: '下一批 {0}',
    phase_equipment: '装备接续',
    fact_spend: '约 {0} {1}',
    for_goal: '{0}：{1}',
    btn_details: '详情',
    btn_adjust_goal: '调整目标',
    btn_farming_settings: '刷取设置',
    btn_open_goals: '查看培养',
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
    latest_run: '最近一次执行',
    no_runs_yet: '尚无执行记录。',
    view_all: '查看全部',
    daily_only: '仅免费日常',
    exc_signed_out: '米游社未登录，无法读取体力与材料缺口。',
    exc_sign_in: '去登录',
    exc_login_expired: '米游社登录已过期，无法读取{0}与材料缺口。',
    exc_login_expired_calc: '米游社登录已过期，无法读取材料缺口。',
    tile_login_expired: '未读取：米游社登录已过期。',
    exc_not_admin: '后台未以管理员身份运行，执行时无法控制游戏窗口。请通过 Start.bat 启动。',
    exc_tool_genshin: '未找到 BetterGI，原神无法执行。',
    exc_tool_zzz: '未找到绝区零一条龙，绝区零无法执行。',
    exc_set_paths: '设置路径',
    exc_goal_error: '无法从米游社读取{0}，规划沿用上次读取的数据。（{1}）',
    exc_open: '查看目标',
    btn_sync_again: '重新同步',
    left_coffee: '剩余约 {0}（含咖啡 +{1}）',
    full_before: '{0} 已满，比本次执行早约 {1}',

    // Running batch
    running_title: '批次执行中',
    running_game: '{0}（第 {1}/{2} 个游戏）',
    stage_prepare: '准备',
    stage_config: '写入工具配置',
    stage_launch: '启动游戏',
    stage_running: '自动化运行',
    stage_collect: '读取结果并还原工具',
    stage_scan: '扫描背包',
    scan_title: '背包扫描',
    scan_help: '米游社只显示已装备的装备。扫描会读取你拥有的全部圣遗物或驱动盘：一旦已拥有的装备能达成角色目标，装备刷取即停止，培养卡片会列出需要换上的装备。本程序从不装备、上锁或分解任何装备；但工具开启相应选项后会分解装备，见 日常任务 › 工具还能做什么。',
    scan_switch: '自动扫描背包',
    scan_sub: '每次装备刷取后、以及至少每天一次，在关闭游戏前进行',
    scan_yas: '圣遗物扫描程序（yas_artifact.exe）',
    scan_zzz: '驱动盘扫描程序（ZZZ-Scanner.Next.exe）',
    scan_rules_title: '扫描要求',
    scan_last_zzz: '上次扫描 {0}：{1} 个驱动盘',
    scan_last_genshin: '上次扫描 {0}：{1} 件圣遗物',
    scan_never: '尚未扫描',
    scan_rules: '两个扫描程序都读取屏幕：游戏需使用简体中文界面、1920×1080 窗口，扫描期间不要操作鼠标（每 1,000 件约 2–5 分钟）。扫描程序需自行安装；本程序会打开背包或驱动盘仓库并运行它们。',
    stage_stopping: '正在停止…',
    btn_stop: '停止当前执行',
    running_hands_off: '批次结束前请勿操作鼠标和键盘。',

    // Goals
    goals_sub: '正在培养的角色。顺序决定先刷哪一项。',
    btn_add_goal: '添加目标',
    goals_empty_title: '还没有培养目标',
    goals_empty_desc: '添加角色后即可开始规划材料。',
    queue_pos: '队列第 {0}/{1} 位',
    synced: '培养数据 {0}同步',
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
    cat_talents_genshin: '天赋',
    cat_talents_zzz: '技能',
    cat_weapon_genshin: '武器',
    cat_weapon_zzz: '音擎',
    btn_change: '修改',
    mat_from: '来源：{0}',
    mat_exp: '经验',
    mat_family: '多阶',
    mat_core: '核心技',
    mats_title: '仍需的材料',
    mats_none: '材料已齐，请进游戏升级。',
    completed_items: '已收齐的项目（{0}）',
    need_more: '还需 {0}',
    need_list: '还需 {0}',
    qty_unknown: '数量未知',
    plan_units: '已完成 {0} / {1}',
    open_days: '开放：{0}',
    status_collected: '已收齐',
    status_next: '下一批',
    status_queued: '排队中',
    status_paused: '已暂停',
    status_waiting: '等待',
    status_manual: '需手动',
    btn_pause: '暂停',
    btn_resume: '恢复',
    tier_material: '材料',
    tier_need: '需要',
    tier_have: '持有',
    tier_short: '缺少',
    stable_list_help: '进度 = 上次同步时米游社的数量 + 之后执行刷到的数量。',
    canceled_title: '已取消的培养（{0}）',
    canceled_note: '已取消的目标保留目标与进度，不会被刷取。',

    // Dialogs
    dlg_targets_title: '{0}的目标设置',
    targets_help: '当前等级来自上次同步。目标不高于当前等级时视为已达成。',
    btn_save_changes: '保存更改',
    btn_discard: '放弃更改',
    btn_close: '关闭',
    btn_add: '添加',
    btn_pick_first: '请先选择角色',
    btn_max: '全部设为最高',
    modal_add_title: '添加{0}培养目标',
    search_placeholder: '搜索角色',
    modal_loading: '正在读取角色…',
    modal_source_roster: '来自米游社的已拥有角色。',
    modal_source_dataset: '离线列表中的全部角色。登录米游社后仅显示已拥有的角色。',
    modal_source_offline: '离线列表中的全部角色：未能从米游社读取你拥有的角色。',
    no_match: '没有匹配的角色。',
    already_added: '已是培养目标',
    not_owned: '未拥有',

    // Schedule
    plan_sub: '未来三天的预测，按与实际执行相同的规则模拟。已执行的批次见“记录”页。',
    plan_off_banner: '定时未开启，不会自动执行；以下仅为预览。',
    reason_same: '原因同上。',
    idle_fix: '如仍想消耗，可添加培养目标，或在刷取规则中设置装备接续。',
    day_before_reset: '04:00 前仍为游戏日 {0}',
    btn_open_settings: '前往设置',
    day_head: '{0} {1}',
    left_after: '剩余约 {0}',
    plan_empty_title: '暂无排程',
    plan_empty: '在设置中添加执行时间后，这里会预测未来三天的执行。',

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
    run_unverified: '下次同步时确认',
    run_duration: '耗时 {0}',
    runs_empty_title: '尚无执行记录',
    runs_empty: '在“今日”页启动或按定时执行的批次及其结果会列在这里。',
    btn_open_today: '前往今日',
    no_games: '未执行游戏',
    btn_more_runs: '显示更早的记录',

    // Settings
    settings_sub: '更改通过底部出现的保存栏统一保存。',
    secret_hint: '使用 Windows DPAPI 加密保存。',
    secret_hint_linux: '保存在仅当前用户可读的文件中。',
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
    env_admin_no: '未以管理员身份运行',
    env_admin_hint: '执行时可能无法操作游戏窗口。请通过程序目录中的 Start.bat 启动，或开启「开机登录自启」（以最高权限运行）。',
    env_plan_only: 'BetterGI 与一条龙是 Windows 程序，以下检查仅适用于 Windows 端。',
    env_bgi: 'BetterGI',
    env_bgi_template: 'BetterGI 模板',
    env_od: '绝区零一条龙',
    env_adapter: '实读电量适配',
    env_adapter_help: '可选的一条龙补丁，让最后一批按实际剩余电量执行。未安装时按计划的整批卡数下发，最后一批可能因电量不足被跳过。',
    env_game_genshin: '原神客户端',
    env_game_zzz: '绝区零客户端',
    env_data_dir: '程序数据目录',
    env_data_dir_hint: '设置、培养目标、执行记录与米游社登录信息都保存在这里。',
    env_log: '日志文件',
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
    opt_restart: '关闭游戏后执行',
    opt_skip: '跳过本次',
    if_running_hint: '关闭游戏会丢失游戏中未保存的进度。',
    genshin_claims: '原神秘境领奖',
    opt_mode_double: '优先使用 40 原粹树脂领取双倍产出',
    opt_mode_double_sub: '推荐。剩余树脂按每次 20 使用。',
    opt_mode_single: '每次使用 20 原粹树脂',
    opt_mode_single_sub: '每 20 原粹树脂领取一次。',
    boss_yield: '原神首领每次平均掉落',
    boss_yield_hint: '按你的世界等级估计，用于把缺口换算为挑战次数',
    coffee_forecast: '绝区零咖啡（预测中每日增加的电量）',
    coffee_hint: '用于预测（今日与日程）；执行时以实际电量为准',
    equip_title: '装备接续',
    equip_help: '圣遗物与驱动盘没有终点，因此只在目标材料都刷完后刷取，并且不超过你设定的累计上限。',
    artifact_switch: '原神：刷圣遗物',
    artifact_sub: '祝圣秘境，每次 20 原粹树脂',
    artifact_domain: '祝圣秘境',
    artifact_cap: '累计预算（次，清零前）',
    disc_switch: '绝区零：刷驱动盘',
    disc_sub: '区域巡防，每场 60 电量',
    disc_mission: '区域巡防关卡',
    disc_cap: '累计预算（场，清零前）',
    equip_used: '已用 {0} / {1}',
    equip_role_other: '此累计预算是为另一个游戏角色授权的，当前所选角色不会消耗它。',
    btn_equip_grant: '为当前角色授权',
    equip_fixed_hint: '仅在没有角色的装备目标参与刷取时使用',
    equip_none: '无：仅按角色的装备目标',
    stages_needed: '掉落培养目标所需的套装',
    stages_other: '其他',
    gear_wasted: '落在不计分副属性的强化：{0} 次',
    gear_status_owned: '已有装备可达成目标',
    gear_owned_title: '使用已有装备：评分 {0}',
    gear_owned_done: '换上这些即可达成目标',
    gear_owned_short: '换上已有的最佳装备后仍未达标，继续刷取',
    inv_line_zzz: '驱动盘仓库扫描于 {0}：共 {1} 个，闲置 {2} 个',
    inv_line_genshin: '圣遗物背包扫描于 {0}：共 {1} 件，闲置 {2} 件',
    inv_spare_help: '闲置：未装备、未上锁，且对每个刷取装备的角色评分都低于 30 的装备。可在游戏中自行分解；本程序从不分解。',
    gear_all_hit: '满命中',
    gear_totals: '计入的强化次数：{0}',
    gear_title: '驱动盘',
    btn_gear_target: '装备目标',
    gear_none_yet: '尚未读取驱动盘。同步该角色即可读取。',
    gear_status_met: '已达成目标',
    gear_verdict_met: '已达成目标',
    gear_verdict_below: '未达成目标 · 满足 {0}/{1} 项',
    gear_glance_met: '{0}：已达成目标',
    gear_glance_equip: '{0}：换上仓库中 {1} 件即可达标',
    gear_status_off: '未参与刷取',
    gear_status_next: '下次装备刷取：{0}',
    gear_status_queued: '排队中：{0}',
    gear_status_blocked: '暂不刷取',
    gear_sets_line: '套装：{0}',
    gear_mains_ok: '主属性符合',
    gear_mains_bad: '主属性不符',
    gear_slots_filled: '已装备 {0} / {1}',
    gear_src_custom: '自定义权重',
    gear_src_mine: '权重来自你在米游社的自选属性',
    gear_src_recommended: '权重来自米游社推荐属性',
    gear_src_official: '权重来自方案「{0}」',
    gear_src_none: '没有权重：请在装备目标中设置',
    gear_read_zzz: '已装备驱动盘读取于 {0}',
    gear_read_genshin: '已装备圣遗物读取于 {0}',
    gear_runs: '已为该角色刷取 {0} 次',
    gear_weights_line: '计入的副属性：{0}',
    gear_no_weights: '尚无计入的副属性：方案未列出，也没有设置权重。',
    gear_help: '评分统计每个驱动盘已有的副属性强化次数（S 级每次计 1，A、B 级按比例折算），与该位置理论最佳相比，再取六个位置的平均；空位计 0。请在游戏中换上更好的驱动盘，下次同步后评分更新。',
    gear_slot: '{0} 号位',
    gear_slot_empty: '空',
    gear_disc_score: '单盘评分',
    gear_rank: '{0} 级',
    gear_lv: 'Lv.{0}',
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
    art_rank: '{0}★',
    art_lv: '+{0}',
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
    genshin_daily_sub: '不做委托时，每消耗 30 原粹树脂，可用长效历练点换 1 次委托奖励，每天最多 4 次（4 次共需 120 树脂）。',
    genshin_teapot_sub: '领取尘歌壶的洞天宝钱与好感经验。',
    tools_more_title: '工具还能做什么',
    tools_zzz_intro: '每批都会运行你在一条龙「一条龙」页勾选的全部项目，例如：',
    tools_zzz_list: ['恶名狩猎：每周 3 次免费奖励；请在一条龙中选择培养目标所需的首领',
                     '迷失之地每周悬赏、丽都周纪、兑换码、刮刮卡与录像店营业',
                     '咖啡店：预测中已计入（{0}）',
                     '耗时较长的项目（迷失之地、枯萎之都、式舆防卫战）计入单游戏超时（{1}）；可在一条龙中限制次数'],
    tools_genshin_intro: '批次只执行本程序选定的秘境或首领，以及上方的领取项目。BetterGI 还可以执行以下项目；请在 BetterGI 中执行，它们消耗的树脂下一批就用不上了：',
    tools_genshin_list: ['地脉花：摩拉与经验书', '合成浓缩树脂：存树脂，最多 5 个', '幽境危战：圣遗物', '脚本仓库的地图追踪路线：地方特产与矿物'],
    tools_more_risk: '有两个工具选项会分解装备，若在工具中开启，本程序的批次也会执行：一条龙列表中的「驱动盘拆解」（默认分解 A 级及以下）与 BetterGI 秘境后的「快速分解圣遗物」。本程序从不开启它们；如需保留装备，请保持关闭。',
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
    ev_login: '米游社登录已过期',
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
    toast_logged_out: '已退出登录',
    toast_goal_added: '已添加{0}',
    toast_goal_canceled: '已取消{0}的培养',
    toast_goal_resumed: '已恢复{0}的培养',
    toast_goal_deleted: '已删除{0}',
    toast_synced: '已与官方养成计算器同步',
    toast_sync_failed: '同步未完成：{0}',
    toast_paused: '该项目已暂停',
    toast_resumed: '该项目已恢复',
    toast_order: '顺序已更新',
    toast_targets: '目标已保存，正在重新计算',
    toast_saved: '设置已保存',
    toast_restart: '设置已保存。端口或局域网设置需重启后台后生效。',
    toast_equip_reset: '计数已清零',
    toast_equip_granted: '已为当前角色授权累计预算',
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

// This page's language: its own choice, else the one last chosen with the switch on any page (settings.ui.lang,
// adopted from the first state; English until then). A new tab, address or device never resets the choice.
let CURRENT_LANG = (() => { try { return localStorage.getItem('gcl_lang') || null; } catch (_) { return null; } })();
let THEME = store.get('gcl_theme', 'timetable');   // the look, one of THEMES
let MODE = store.get('gcl_mode', 'system');        // color mode: system, light or dark
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
// Looks the user can pick. A theme is CSS only: style.css draws the default (timetable), themes/<id>.css restyles the
// same markup under :root[data-theme="<id>"] and may use its hooks (data-view on <body>, data-game on game sections).
// No logic depends on the theme.
const THEMES = ['timetable', 'zzz'];
const MODES = [['system', 'monitor'], ['light', 'sun'], ['dark', 'moon']];
const TABS = [['today', 'home', 'nav_today'], ['goals', 'target', 'nav_goals'], ['plan', 'calendar', 'nav_plan'],
              ['runs', 'history', 'nav_runs'], ['settings', 'sliders', 'nav_settings']];
const RECOVERY_MINUTES = { genshin: 8, zzz: 6 };
const STAGES = ['stage_prepare', 'stage_config', 'stage_launch', 'stage_running', 'stage_scan', 'stage_collect'];
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
  hand: '<path d="M8 13V5.5a1.5 1.5 0 0 1 3 0V12M11 11V4.5a1.5 1.5 0 0 1 3 0V12M14 11.5V6a1.5 1.5 0 0 1 3 0v7c0 4-2.5 7-6 7-2.5 0-4-1-5.5-3L3.4 13.6a1.5 1.5 0 0 1 2.3-1.9L8 14"/>',
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
function badge(kind, ic, label, state = '') {
  return `<span class="badge ${kind}"${state ? ` data-state="${state}"` : ''}>${icon(ic)}<span>${label}</span></span>`;
}
function help(html, ic = 'info') { return `<p class="help">${icon(ic)}<span>${html}</span></p>`; }
function alertBox(kind, ic, html, action = '') {
  return `<div class="alert ${kind}" role="${kind === 'bad' ? 'alert' : 'status'}">${icon(ic)}<div class="body"><span>${html}</span>${action}</div></div>`;
}
function linkButton(href, ic, label) { return `<a class="btn sm" href="${href}">${icon(ic)}<span>${label}</span></a>`; }
function runBadge(status) {
  const [kind, ic] = RUN_STATUS[status] || ['muted', 'minus'];
  return badge(kind, ic, t('run_status_' + status), String(status).toLowerCase());
}
function portrait(game, id, name, size = '') {
  const k = `${game}/character/${id}`;
  if (id && ASSETS.has(k)) return `<span class="portrait ${size}"><img src="/assets/${esc(k)}" alt="" loading="lazy"></span>`;
  const initial = String(name || '').match(/[\p{L}\p{N}]/u)?.[0] || '?';  // 「11号」 → 1, not 「
  return `<span class="portrait fallback ${size}" aria-hidden="true">${esc(initial)}</span>`;
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
  if (CURRENT_LANG) opts.headers['X-Lang'] = CURRENT_LANG;  // server-written text in this page's language
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

/** A toast: what it is about (the action, when known) and when, then the message. Confirmations leave by themselves
 *  after 5 s (not while hovered or focused); errors stay until dismissed. */
function toast(message, kind = 'ok', subject = '') {
  const box = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.setAttribute('role', kind === 'error' ? 'alert' : 'status');
  const time = `<time>${clockOf(nowMs())}</time>`;  // with an action, the time joins it on a head row; else it ends the one row
  el.innerHTML = `${icon(kind === 'error' ? 'alert' : 'check')}<div class="toast-body">${subject ? `<p class="toast-head"><b></b>${time}</p>` : ''}<span></span></div>
    ${subject ? '' : time}<button type="button" class="toast-close" aria-label="${t('btn_dismiss')}" title="${t('btn_dismiss')}">${icon('x')}</button>`;
  if (subject) el.querySelector('.toast-head b').textContent = subject;
  el.querySelector('.toast-body > span').textContent = message;
  el.querySelector('.toast-close').addEventListener('click', () => el.remove());
  box.appendChild(el);
  if (kind === 'error') return;
  const leave = () => { if (el.matches(':hover, :focus-within')) setTimeout(leave, 1000); else el.remove(); };
  setTimeout(leave, 5000);
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
    toast(err.message, 'error', btn ? btn.dataset.label || btn.getAttribute('aria-label') || '' : '');  // names the action that failed
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
/** Sync one goal. The answer can be 200 with some official reads failed: the toast names those instead of
 *  claiming a full sync. */
async function syncGoal(btn) {
  const id = btn.dataset.id;
  await busy(btn, async () => {
    const goal = await api('/api/goals/sync', 'POST', { id, observe: true });
    const ok = await refreshState(true);
    const failed = goal?.id ? [...new Set([goal.observe_error, goal.gear_error, goal.calc_error].filter(Boolean))] : [];
    if (!ok) toast(tp('saved_not_reloaded'), 'error');
    else if (failed.length) toast(tp('toast_sync_failed', failed.join(tp('list_sep'))), 'error');
    else {
      toast(tp('toast_synced'), 'ok');
      flash(goalSel(id));
    }
  }, 'syncing');
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
    if (!CURRENT_LANG) adoptLang(next.settings?.ui?.lang);
  } catch (err) {
    if (seq >= APPLIED_SEQ) LAST_ERROR = err.message;
    render();
    return false;
  }
  render(force);
  updateLoginDialog();
  updateTargetsDialog();
  return true;
}

/** A page without its own choice takes the saved one; its first state was already written in it. */
function adoptLang(lang) {
  CURRENT_LANG = I18N[lang] ? lang : 'en';
  document.documentElement.lang = CURRENT_LANG === 'zh' ? 'zh-CN' : 'en';
  renderShell();
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
  renderLookMenu();
}

/** The Appearance menu: the theme (a swatch drawn by CSS) and the color mode. */
function renderLookMenu() {
  const menu = document.getElementById('look-menu');
  const open = menu.open;
  const mode = MODES.find(m => m[0] === MODE) || MODES[0];
  const item = (action, id, checked, mark, label) =>
    `<button type="button" role="menuitemradio" aria-checked="${checked}" data-action="${action}" data-key="${id}">${mark}<span>${label}</span>${icon('check', 'check')}</button>`;
  menu.innerHTML = `
    <summary class="btn sm" aria-label="${t('look_label')}: ${t('theme_' + THEME)}, ${t('mode_' + MODE)}">${icon(mode[1])}<span class="label">${t('theme_' + THEME)}</span>${icon('chevron', 'chev')}</summary>
    <div class="menu-list" role="menu" aria-label="${t('look_label')}">
      <div role="group" aria-labelledby="look-themes"><p class="menu-head" id="look-themes">${t('theme_label')}</p>
        ${THEMES.map(id => item('theme', id, id === THEME, `<span class="swatch" data-swatch="${id}" aria-hidden="true"></span>`, t('theme_' + id))).join('')}</div>
      <div role="group" aria-labelledby="look-modes"><p class="menu-head" id="look-modes">${t('mode_label')}</p>
        ${MODES.map(([id, ic]) => item('mode', id, id === MODE, icon(ic), t('mode_' + id))).join('')}</div>
    </div>`;
  menu.open = open;
}

function applyTheme(theme) {
  THEME = THEMES.includes(theme) ? theme : THEMES[0];
  document.documentElement.dataset.theme = THEME;
  store.set('gcl_theme', THEME);
  renderLookMenu();
}

function applyMode(mode) {
  MODE = MODES.some(([id]) => id === mode) ? mode : 'system';
  if (MODE === 'system') delete document.documentElement.dataset.mode;
  else document.documentElement.dataset.mode = MODE;
  store.set('gcl_mode', MODE);
  renderLookMenu();
}

function setLanguage(lang) {
  CURRENT_LANG = I18N[lang] ? lang : 'en';
  store.set('gcl_lang', CURRENT_LANG);
  document.documentElement.lang = CURRENT_LANG === 'zh' ? 'zh-CN' : 'en';
  renderShell();
  document.getElementById('savebar').dataset.lang = '';
  render(true);
  // Saved for background text (run summaries, notifications) and for pages without a choice of their own.
  api('/api/lang', 'POST', { lang: CURRENT_LANG }).catch(err => toast(err.message, 'error'));
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
  if (r.running) {
    const { stages, current } = runSteps(r);
    chips.push(chip('pulse', r.game && current >= 0
      ? tp('strip_running_game', tp('game_' + r.game), tp(stages[current]), current + 1, stages.length)
      : tp('strip_running', r.stage || ''), 'info'));
  } else if (STATE.automation === false) chips.push(chip('monitor', tp('strip_plan_only')));
  else if (STATE.settings?.schedule?.enabled && STATE.next_slot) chips.push(chip('clock', tp('strip_next_run', whenLabel(STATE.next_slot), relative(STATE.next_slot)), 'next'));
  else chips.push(chip('pause', tp('strip_schedule_off')));
  GAMES.forEach(g => {
    const st = STATE.stamina?.[g];
    if (st) chips.push(chip(g === 'zzz' ? 'battery' : 'resin', `${tp('game_short_' + g)} ${st.value}/${st.cap}`, 'stamina'));
  });
  if (!STATE.logged_in) chips.push(chip('user', tp('strip_signed_out'), 'warn'));
  else if (STATE.login_expired) chips.push(chip('user', tp('strip_login_expired'), 'warn'));
  if (!STATE.admin && STATE.automation !== false) chips.push(chip('shield', tp('strip_not_admin'), 'warn'));
  if (LAST_ERROR) chips.push(chip('alert', tp('connect_failed', LAST_ERROR), 'bad'));
  el.innerHTML = chips.join('');
  el.style.setProperty('--p', slotProgress().toFixed(3));
  const stamina = GAMES.map(g => [g, STATE.stamina?.[g]]).filter(([, st]) => st)
    .map(([g, st]) => `${tp('game_short_' + g)} ${st.value}/${st.cap}`);
  document.title = [...stamina, `${tp('brand_title')} ${tp('brand_edition')}`].join(' · ');
}

/** How far the wait from the previous scheduled time to the next run has come (0–1); 0 without a schedule. */
function slotProgress() {
  const next = toMs(STATE.next_slot), now = nowMs();
  const times = STATE.settings?.schedule?.enabled ? STATE.settings.schedule.times || [] : [];
  if (next == null || !times.length) return 0;
  const p = cnParts(now);
  const midnight = Date.UTC(p.y, p.m - 1, p.d) - 8 * 3600e3;  // today 00:00 China time
  let prev = next - 864e5;
  [0, -864e5].forEach(day => times.forEach(x => {
    const [h, m] = x.split(':').map(Number);
    const at = midnight + day + (h * 60 + m) * 60e3;
    if (at <= now && at > prev) prev = at;
  }));
  return Math.min(1, Math.max(0, (now - prev) / (next - prev)));
}

/** The steps of a running batch (the scan step only when this game scans) and the index of the current one. */
function runSteps(r) {
  const stages = STAGES.filter(k => k !== 'stage_scan' || r.scan);
  return { stages, current: stages.indexOf(r.stage_key || 'stage_prepare') };
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

function toggleButton(id, labelKey = 'btn_details') {
  const open = OPEN.has(id);
  return `<button type="button" class="btn sm quiet" data-action="toggle" data-key="${esc(id)}" aria-expanded="${open}">${icon('chevron', 'chev')}<span class="txt">${t(labelKey)}</span></button>`;
}

/** An empty view as a sheet: what is missing on its title strip, then how to fill it. */
function emptySheet(ic, title, text, action = '') {
  return `<section class="panel empty"><header class="panel-head"><h2>${icon(ic)}<span>${title}</span></h2></header>
    <div class="empty-body"><p>${text}</p>${action}</div></section>`;
}

function detailPanel(id, html, cls = '') {
  return `<div class="${cls}" data-detail="${esc(id)}"${OPEN.has(id) ? '' : ' hidden'}>${html}</div>`;
}

function detailList(rows) {
  return `<dl class="details">${rows.filter(Boolean).map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
}

// ----------------------------------------------------------- 1. Today
// One band per game on the same grid (stamina, the next runs, the goals), so both games read across the same columns.
function renderToday() {
  const el = document.getElementById('view-today');
  const r = STATE.runner || {};
  el.innerHTML = `
    ${pageHead(t('nav_today'), '', runButton('zzz,genshin', t('btn_run_both'), ''))}
    ${exceptions()}
    ${r.running ? runningPanel(r) : ''}
    ${GAMES.map(gameBand).join('')}
    ${latestRunPanel()}`;
}

/** A Run button; while it cannot run (Linux host, a batch running) it is disabled and says why beside it. */
function runButton(games, label, cls) {
  const why = STATE.automation === false ? 'run_why_windows' : STATE.runner?.running ? 'run_why_busy' : '';
  return `${why ? `<span class="run-why">${t(why)}</span>` : ''}${button('run', 'play', label, cls, `data-games="${games}"${why ? ' disabled' : ''}`)}`;
}

function exceptions() {
  const list = [];
  const c = STATE.check || {};
  if (!STATE.logged_in) list.push(alertBox('warn', 'user', t('exc_signed_out'), linkButton('#/settings/set-account', 'user', t('exc_sign_in'))));
  else if (STATE.login_expired) {
    // name what the login actually blocks: the stamina read through Miyoushe, and the material gaps
    const units = GAMES.filter(g => STATE.health?.['stamina-' + g]?.expired).map(g => tp('unit_' + g));
    const text = units.length ? t('exc_login_expired', units.join(tp('list_sep'))) : t('exc_login_expired_calc');
    list.push(alertBox('warn', 'user', text, button('login-dialog', 'qr', t('btn_login_manage'), 'sm')));
  }
  const plansOnly = STATE.automation === false;  // said by the status strip and the disabled Run buttons
  if (!plansOnly && !STATE.admin) list.push(alertBox('warn', 'shield', t('exc_not_admin')));
  const scheduled = STATE.settings?.schedule?.games || [];
  GAMES.forEach(g => {
    const hasGoals = (STATE.goals?.[g] || []).some(x => x.enabled);
    if (!plansOnly && c[g] && !c[g].tool_ok && (hasGoals || scheduled.includes(g))) {
      list.push(alertBox('bad', 'alert', t('exc_tool_' + g), linkButton('#/settings/set-paths', 'folder', t('exc_set_paths'))));
    }
  });
  GAMES.forEach(g => (STATE.goals?.[g] || []).filter(x => x.enabled && (x.calc_error || x.observe_error)).forEach(x => {
    list.push(alertBox('bad', 'alert', t('exc_goal_error', x.name, x.calc_error || x.observe_error),
      `<span class="actions">${button('sync-goal', 'refresh', t('btn_sync_again'), 'sm', `data-id="${esc(x.id)}"`)}
        ${linkButton(`#/goals/${encodeURIComponent(x.id)}`, 'target', t('exc_open'))}</span>`));
  }));
  return list.length ? `<div class="alerts">${list.join('')}</div>` : '';
}

function runningPanel(r) {
  const { stages, current } = runSteps(r);
  const games = r.games || [];
  const stopping = r.stage_key === 'stage_stopping';
  const steps = stages.map((k, i) => {
    const state = current < 0 ? '' : i < current ? 'done' : i === current ? 'current' : '';
    return `<li class="step ${state}">${state === 'done' ? icon('check') : `<span class="n">${i + 1}</span>`}<span>${t(k)}</span></li>`;
  }).join('');
  const game = r.game ? t('running_game', tp('game_' + r.game), games.indexOf(r.game) + 1, games.length) : '';
  return `
    <section class="panel running" aria-live="polite">
      <div class="head">${icon('pulse')}<b>${stopping ? t('stage_stopping') : t('running_title')}</b><span class="ink-2">${game}</span></div>
      <ol class="steps" style="--n:${stages.length}">${steps}</ol>
      ${button('stop', 'stop', t('btn_stop'), 'sm danger', stopping ? 'disabled' : '')}
      <p class="hands-off">${icon('info')}<span>${t('running_hands_off')}</span></p>
    </section>`;
}

/** The next batch's numbers: the forecast row for the next scheduled slot, else the plan with today's stamina. */
function nextFacts(game) {
  const item = STATE.plans?.[game]?.item;
  if (!item) return null;
  if (STATE.settings?.schedule?.enabled && STATE.next_slot) {
    const r = (STATE.forecast?.rows || []).find(x => x.game === game && x.at === STATE.next_slot);
    if (r && r.task) return { at: r.at, expected: r.expected, spend: r.spend, left: r.left, coffee: r.coffee };
  }
  const st = STATE.stamina?.[game];
  const spend = item.expected != null ? item.expected * item.cost : null;
  return { at: null, expected: item.expected, spend, left: st && spend != null ? Math.max(0, st.value - spend) : null };
}

function gameBand(game) {
  const acc = STATE.accounts?.[game];
  return `
    <section class="band" data-game="${game}" aria-labelledby="band-${game}">
      <header class="band-head">
        <div class="band-title"><h2 id="band-${game}">${t('game_' + game)}</h2><span class="ink-2">${acc ? t('account_line', acc.name || '–', acc.uid) : t(STATE.logged_in ? 'no_account' : 'not_signed_in')}</span></div>
        <div class="actions">
          ${button('refresh-notes', 'refresh', t('btn_reread', tp('unit_' + game)), 'sm', `data-game="${game}"${STATE.logged_in && acc ? '' : ' disabled'}`)}
          ${runButton(game, t('btn_run_now'), 'sm primary')}
        </div>
      </header>
      <div class="band-grid">
        <div class="col col-stamina">${staminaCol(game)}</div>
        <div class="col col-runs">${runsCol(game)}</div>
        <div class="col col-goals">${goalsCol(game)}</div>
      </div>
    </section>`;
}

/** The stamina figure on its tile, with the tile's state (ok, full, unknown) and, for themes that draw a gauge,
 *  --value, --max and --spend (what the next batch spends of it). */
function staminaCol(game) {
  const st = STATE.stamina?.[game];
  const acc = STATE.accounts?.[game];
  const health = STATE.health?.['stamina-' + game];
  const failed = health && health.ok === false;
  const issue = !failed ? '' : health.expired ? help(t('tile_login_expired'), 'alert')
    : alertBox('warn', 'alert', t('notes_issue', tp('unit_' + game), health.reason || ''), acc ? button('login-dialog', 'qr', t('btn_login_manage'), 'sm') : '');
  const head = `<div class="col-head"><h3>${t('unit_' + game)}</h3></div>`;
  if (!st) {
    return `${head}<div class="tile" data-state="unknown"><p class="figure"><span class="value">?</span><span class="tile-state">${t('tile_unread')}</span></p>
      <span class="meter stamina-meter" aria-hidden="true"></span></div>${failed ? issue : help(t(STATE.logged_in ? 'stamina_unknown_hint' : 'stamina_signed_out_hint'))}`;
  }
  const minutes = (st.cap - st.value) * RECOVERY_MINUTES[game];
  const full = st.value >= st.cap;
  const spend = Math.min(st.value, nextFacts(game)?.spend ?? 0);
  return `
    ${head}
    <div class="tile" data-state="${full ? 'full' : 'ok'}" style="--value:${st.value};--max:${st.cap};--spend:${spend}">
      <p class="figure"><span class="value">${num(st.value)}</span><span class="cap">/${num(st.cap)}</span>${full ? `<span class="tile-state">${t('tile_full')}</span>` : ''}</p>
      <span class="meter stamina-meter" aria-hidden="true"><span class="fill" style="width:${Math.min(100, (100 * st.value) / st.cap).toFixed(1)}%"></span></span>
      ${spend ? `<p class="tile-note">${t('tile_next_spend', num(spend))}</p>` : ''}
    </div>
    ${full ? `<p class="st-full">${icon('alert')}<span>${t('full_now_' + game)}</span></p>` : ''}
    <dl class="st-facts">
      ${full ? '' : `<div><dt>${t('st_full_at')}</dt><dd><b>${esc(whenOf(nowMs() + minutes * 60000))}</b><span>${t('st_full_in', duration(minutes))}</span></dd></div>`}
      <div class="st-read"><dt>${t('st_read')}</dt><dd><b>${esc(relative(st.seen))}</b><span>${esc(st.source)}</span></dd></div>
    </dl>
    ${issue}`;
}

/** The next scheduled runs as timetable rows; without a schedule for this game, what Run now would farm. */
function runsCol(game) {
  const plan = STATE.plans?.[game] || {};
  const sched = STATE.settings?.schedule || {};
  const rows = sched.enabled && (sched.games || []).includes(game)
    ? (STATE.forecast?.rows || []).filter(r => r.game === game && toMs(r.at) > nowMs()).slice(0, 3) : [];
  const ran = departedRow(game);
  const list = ran + (rows.length ? rows.map((r, i) => ttRow(r, i === 0)).join('') : plan.item ? manualRow(game, plan) : '');
  return `
    <div class="col-head"><h3>${t(ran ? 'col_runs_ran' : 'col_runs')}</h3><a href="#/plan">${t('nav_plan')}</a></div>
    ${plan.item ? '' : idleNote(game, plan)}
    ${list ? `<ol class="tt">${list}</ol>` : ''}
    <p class="tt-daily">${icon('gift')}<span>${t('dailies_line', (plan.daily || []).join(tp('list_sep')) || tp('none'))}</span></p>`;
}

/** This game's part of the latest batch, kept on the board for the rest of its game day (it resets at 04:00). */
function departedRow(game) {
  const run = (STATE.runs || []).find(x => (x.games || []).some(g => g.game === game));
  const start = run && toMs(run.started);
  const gameDay = ms => dayKeyOf(ms - 4 * 3600e3);
  if (!start || run.status === 'RUNNING' || gameDay(start) !== gameDay(nowMs())) return '';
  const g = run.games.find(x => x.game === game);
  const what = g.item ? `${esc(g.item.label)} <span class="ink-2">${esc(g.item.goal)}</span>` : esc(g.summary || '');
  return `
    <li class="tt-row departed">
      ${ttTime(run.started)}
      <div class="tt-what"><p class="tt-task">${runBadge(g.status)}<a class="ink-2" href="#/runs">${t('departed', runSpan(run))}</a></p><p>${what}</p></div>
    </li>`;
}

/** A run's time with its weekday, so rows read the same before and after midnight. */
function ttTime(at) {
  const ms = toMs(at);
  return `<span class="tt-time">${clockOf(ms)}<small>${esc(lookup('weekdays')[cnParts(ms).wd])}</small></span>`;
}

/** What stays after a run; the forecast's coffee is named when it is part of the figure. */
function leftText(r) {
  if (r.left == null) return '';
  return r.coffee ? t('left_coffee', num(r.left), num(r.coffee)) : t('left_after', num(r.left));
}

function ttSpend(spend, left) {
  return `<span class="tt-spend">${spend == null ? '<b>?</b>' : `<b>−${num(spend)}</b>`}${left ? `<span>${left}</span>` : ''}</span>`;
}

/** Natural recovery hit the cap before this run (the forecast knows when). */
function fullBefore(r) {
  if (!r.full_at) return '';
  const lead = duration((toMs(r.at) - toMs(r.full_at)) / 60000);
  const fix = r.task ? '#/settings/set-schedule' : '#/settings/set-farming';  // a run time helps only when there is something to farm
  return `<p class="tt-full">${icon('clock')}<a href="${fix}">${t('full_before', clock(r.full_at), lead)}</a></p>`;
}

function ttRow(r, first) {
  const next = first && r.task;
  const id = `today-${r.game}-${r.at}`;
  if (!r.task) {
    return `<li class="tt-row idle">${ttTime(r.at)}<div class="tt-what"><p class="ink-2">${t('daily_only')}</p>${fullBefore(r)}</div>
      <span class="tt-spend"><span>${leftText(r)}</span></span></li>`;
  }
  return `
    <li class="tt-row${next ? ' next' : ''}">
      ${ttTime(r.at)}
      <div class="tt-what">
        <p class="tt-task"><b>${esc(r.task)}</b>${next ? `<span class="tag">${t('tag_next')}</span>` : ''}</p>
        <p class="ink-2">${r.names ? t('for_goal', r.goal, r.names) : esc(r.goal)}${r.phase === 'equipment' ? ` (${t('phase_equipment')})` : ''}</p>
        ${fullBefore(r)}
        ${next ? `<div class="tt-acts">${toggleButton(id)}${adjustLink(r.goal_id)}</div>` : ''}
      </div>
      ${ttSpend(r.spend, leftText(r))}
      ${next ? detailPanel(id, detailList(forecastDetails(r)), 'tt-detail') : ''}
    </li>`;
}

function manualRow(game, plan) {
  const item = plan.item;
  const nf = nextFacts(game);
  const id = `today-${game}-manual`;
  return `
    <li class="tt-row next">
      <span class="tt-time"><small>${t('tt_manual')}</small></span>
      <div class="tt-what">
        <p class="tt-task"><b>${esc(item.label)}</b><span class="tag">${t('tag_next')}</span></p>
        <p class="ink-2">${item.names ? t('for_goal', item.goal, item.names) : esc(item.goal)}${plan.phase === 'equipment' ? ` (${t('phase_equipment')})` : ''}</p>
        <div class="tt-acts">${toggleButton(id)}${adjustLink(item.goal_id)}</div>
      </div>
      ${ttSpend(nf && nf.spend, nf ? leftText(nf) : '')}
      ${detailPanel(id, itemDetails(game, item, nf), 'tt-detail')}
    </li>`;
}

function idleNote(game, plan) {
  return `
    <div class="tt-idle">
      <p><b>${t('nothing_title')}</b> <span class="ink-2">(${t('keeping', tp('unit_' + game))})</span></p>
      ${plan.reason ? `<p class="ink-2">${esc(plan.reason)}</p>` : ''}
      <div class="tt-acts">${linkButton(`#/goals/${game}`, 'target', t('btn_open_goals'))}</div>
    </div>`;
}

/** Equipment for a character is adjusted on its goal card, like its materials; the fixed fallback in Settings. */
function adjustLink(goalId) {
  const goal = goalId ? findGoal(goalId) : null;
  return goal ? linkButton(`#/goals/${encodeURIComponent(goal.id)}`, 'edit', t('btn_adjust_goal'))
    : linkButton('#/settings/set-farming', 'sliders', t('btn_farming_settings'));
}

function forecastDetails(r) {
  const unitName = tp('unit_' + r.game);
  return r.task ? [
    [t('detail_task'), `${esc(r.task)} <span class="ink-2">${r.names ? t('for_goal', r.goal, r.names) : esc(r.goal)}</span>`],
    [t('detail_spend'), r.expected != null ? t('spend_detail', `${r.expected}${r.unit_label || ''}`, r.cost, unitName, r.spend ?? '?') : t('spend_unknown')],
    [t('detail_stop'), t('stop_rule', `${r.upper}${r.unit_label || ''}`)],
    [t('detail_calc'), esc(r.reason)]
  ] : [[t('detail_reason'), esc(r.reason)]];
}

/** The active goals in queue order: how much each has collected, and what it farms next or waits for. */
function goalsCol(game) {
  const list = (STATE.goals?.[game] || []).filter(g => g.enabled);
  const plan = STATE.plans?.[game] || {};
  const head = `<div class="col-head"><h3>${t('col_goals')}</h3><a href="#/goals/${game}">${t('view_all')}</a></div>`;
  if (!list.length) {
    return `${head}<p class="gl-empty ink-2">${t('goals_none')}</p>
      <div class="tt-acts">${button('add-goal', 'plus', t('btn_add_goal'), 'sm', `data-game="${game}"`)}</div>`;
  }
  const more = list.length > 4 ? `<p class="gl-more"><a href="#/goals/${game}">${t('goals_more', list.length - 4)}</a></p>` : '';
  return `${head}<ol class="gl">${list.slice(0, 4).map(g => goalRow(g, plan)).join('')}</ol>${more}`;
}

/** Share of an item already covered: 1 when collected, else the mean covered share of its known material
 *  quantities (the official shortfall already counts conversion); null when no quantity is known. */
function itemFraction(it) {
  if (it.done) return 1;
  const known = (it.materials || []).filter(m => m.need > 0 && m.remaining != null);
  if (!known.length) return null;
  return known.reduce((sum, m) => sum + Math.min(1, Math.max(0, 1 - m.remaining / m.need)), 0) / known.length;
}

function goalRow(g, plan) {
  const items = g.items || [];
  const fractions = items.map(itemFraction);
  const known = fractions.filter(f => f != null);
  const done = items.filter(it => it.done).length;
  const label = known.length
    ? t('goals_progress', Math.floor(100 * known.reduce((a, b) => a + b, 0) / known.length), done, items.length)
    : t('goals_items', done, items.length);
  const parts = items.map((it, i) => {
    const f = fractions[i], title = esc(`${it.label}: ${needText(it, true)}`);
    return f == null ? `<span class="part unknown" title="${title}"></span>`
      : `<span class="part${f >= 1 ? ' done' : ''}" title="${title}"><span style="width:${(100 * f).toFixed(1)}%"></span></span>`;
  }).join('');
  const ev = g.gear_eval, own = g.gear_owned, gearTitle = tp(GEAR[g.game].title);
  const gearText = !ev?.target?.farm ? '' : ev.done ? t('gear_glance_met', gearTitle)
    : own?.done ? t('gear_glance_equip', gearTitle, own.changes.length)
    : `${esc(gearTitle)} <span class="num">${ev.score ?? '–'} / ${ev.target.score}</span>`;
  const gear = gearText ? `<p class="gl-gear">${ev.done ? icon('check') : own?.done ? icon('box') : ''}<span>${gearText}</span></p>` : '';
  return `
    <li class="gl-row">
      ${portrait(g.game, g.character_id, g.name, 'md')}
      <div class="gl-main">
        <p class="gl-name"><a href="#/goals/${encodeURIComponent(g.id)}">${esc(g.name)}</a>${items.length ? `<span class="ink-2">${label}</span>` : ''}</p>
        ${items.length ? `<span class="parts" role="img" aria-label="${label}">${parts}</span>` : ''}
        <p class="gl-status">${goalStatus(g, plan)}</p>
        ${gear}
      </div>
    </li>`;
}

function goalStatus(g, plan) {
  if (g.calc_error || g.observe_error) return `<span class="bad">${icon('alert')}${t('goal_error')}</span>`;
  if (plan.item && plan.item.goal_id === g.id) {
    return `<span class="tag">${t('tag_next')}</span><span>${esc(plan.item.label)}${plan.phase === 'equipment' ? ` (${t('phase_equipment')})` : ''}</span>`;
  }
  const open = (g.items || []).find(it => !it.done);
  if (!open) return `<span class="good">${icon('check')}${t('goal_all_done')}</span>${g.weapon_wait ? `<span class="ink-2">${esc(g.weapon_wait)}</span>` : ''}`;
  return `<span class="ink-2">${t('for_goal', open.label, open.paused ? tp('status_paused') : open.why || tp('status_queued'))}</span>`;
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

function latestRunPanel() {
  const run = (STATE.runs || [])[0];
  const quiet = run && !(run.notes || []).length && (run.games || []).every(g => !(g.errors || []).length && !(g.notes || []).length);
  if (quiet && GAMES.some(game => departedRow(game))) return '';  // today's batch stands on the game sheets and has nothing more to say
  return `
    <section class="band latest">
      <header class="band-head"><div class="band-title"><h2>${t('latest_run')}</h2>${run ? `<span class="ink-2 num">${esc(runSpan(run, true))}</span>` : ''}</div><a href="#/runs">${t('view_all')}</a></header>
      <div class="band-body">${run ? runBody(run) : `<p class="ink-2">${t('no_runs_yet')}</p>`}</div>
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
    ${pageHead(t('nav_goals'), t('goals_sub'), active.length ? button('add-goal', 'plus', t('btn_add_goal'), 'primary') : '')}
    <div class="toolbar"><div class="seg" role="tablist" aria-label="${t('nav_goals')}">${tabs}</div>${help(t('stable_list_help'))}</div>
    ${inventoryLine(GOALS_GAME)}
    ${active.length ? active.map((g, i) => goalCard(g, i, active.length, nextKey)).join('')
      : emptySheet('target', t('goals_empty_title'), t('goals_empty_desc'), button('add-goal', 'plus', t('btn_add_goal'), 'primary'))}
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
    <article class="goal" id="goal-${id}" data-goal="${id}" data-game="${g.game}">
      <header class="goal-id">
        ${portrait(g.game, g.character_id, g.name)}
        <div>
          <h2>${esc(g.name)}${agentTags(g)}</h2>
          <p class="meta"><span class="queue">${t('queue_pos', idx + 1, total)}${orderControl('move-goal', `data-id="${id}"`, idx, total)}</span>
            <span>${icon('refresh')}${g.observe_at ? t('synced', relative(g.observe_at)) : t('never_synced')}</span></p>
        </div>
        <div class="goal-actions">
          ${button('sync-goal', 'refresh', t('btn_sync'), 'sm', `data-id="${id}"`)}
          ${button('edit-targets', 'edit', t('btn_target_settings'), 'sm primary', `data-id="${id}"`)}
          ${button('cancel-goal', 'ban', t('btn_cancel_cultivation'), 'sm quiet danger', `data-id="${id}"`)}
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
        ${g.weapon_wait ? `<div class="mt">${help(esc(g.weapon_wait), 'clock')}</div>` : ''}
        ${done.length ? `<details class="fold mt" data-keep="done-${id}"><summary>${icon('chevron', 'chev')}<span>${t('completed_items', done.length)}</span></summary>
          <div class="fold-body"><ul class="mats">${done.map(it => materialRow(g, it, nextKey)).join('')}</ul></div></details>` : ''}
      </section>
    </article>`;
}

/** A character's rank and element in words (the offline dataset's values). */
function agentTags(c, game = c.game) {
  const rarity = /^\d+$/.test(String(c.rarity ?? '')) ? `${c.rarity}★` : c.rarity ? tp('rank_letter', c.rarity) : '';
  const element = elementName(game, c.element);
  return `${rarity ? `<span class="rank" data-rank="${esc(String(c.rarity).toLowerCase())}">${esc(rarity)}</span>` : ''}${element ? `<span class="element">${esc(element)}</span>` : ''}`;
}

/** Move up / Move down as one joined control; the ends are disabled. */
function orderControl(action, attrs, idx, total) {
  return `<span class="order" role="group">
    ${iconButton(action, 'up', t('btn_move_up'), `${attrs} data-dir="-1"${idx === 0 ? ' disabled' : ''}`)}
    ${iconButton(action, 'down', t('btn_move_down'), `${attrs} data-dir="1"${idx === total - 1 ? ' disabled' : ''}`)}</span>`;
}

function nextLine(g, item, planItem) {
  const nf = nextFacts(g.game);
  const spend = nf && nf.spend != null ? t('fact_spend', num(nf.spend), tp('unit_' + g.game)) : t('spend_unknown');
  const detailId = `goal-next-${g.id}`;
  return `
    <div>
      <p class="next-line"><span class="tag">${nf && nf.at ? t('next_batch_at', whenLabel(nf.at)) : t('next_batch')}</span>
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
    return `<tr><th scope="row">${t(label)}</th><td class="c" data-cur="${k}">${cur ?? '–'}</td><td class="arrow" aria-hidden="true">→</td><td class="c">${target}</td></tr>`;
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
         stages: () => STATE.catalog?.stages?.zzz || [], sets: () => STATE.catalog?.disc_sets || [] },
  genshin: { subs: [20, 22, 6, 5, 3, 2, 9, 8, 23, 28],
             mains: { 3: [3, 6, 9, 23, 28], 4: [3, 6, 9, 28, 30, 40, 41, 42, 43, 44, 45, 46], 5: [3, 6, 9, 28, 20, 22, 26] },
             kind: 'artifact', unit: 'resin', title: 'art_title', none: 'art_none_yet', help: 'art_help', farm: 'art_farm_switch',
             mainsTitle: 'art_mains_title', stage: 'art_domain', stageAuto: 'art_domain_auto', stageHint: 'art_domain_hint',
             stages: () => STATE.catalog?.stages?.genshin || [], sets: () => STATE.catalog?.artifact_sets || [] }
};
/** Official property name in the UI language; the API's own (Chinese) name for ids this table lacks. */
function propName(id, fallback = '') { const k = 'prop_' + id; return lookup(k) !== k ? t(k) : esc(fallback || id); }
function slotName(game, slot) {
  return game === 'genshin' ? t('art_slot_' + slot) : `<span class="slot" data-slot="${esc(slot)}">${t('gear_slot', slot)}</span>`;
}
function setIcon(game, setId, cls = 'mat-icon') {
  const k = `${game}/${GEAR[game].kind}/${setId}`;
  return setId && ASSETS.has(k) ? `<img class="${cls}" src="/assets/${esc(k)}" alt="" loading="lazy">` : '';
}
function rollsText(r) { return r == null ? '' : `×${Number.isInteger(r) ? r : r.toFixed(1)}`; }
function gearQueueRow(g) { return (STATE.plans?.[g.game]?.equipment?.queue || []).find(r => r.goal_id === g.id); }

function gearStatus(g, ev) {
  const row = gearQueueRow(g);
  const eq = STATE.plans?.[g.game]?.equipment || {};
  if ((ev && ev.done) || (g.gear_owned && g.gear_owned.done)) return '';  // the verdict and the storage box say it
  if (!ev?.target?.farm) return badge('muted', 'minus', t('gear_status_off'), 'off');
  if (row && row.why) return badge('warn', 'clock', esc(row.why), 'waiting');
  if (eq.why) return badge('warn', 'clock', t('gear_status_blocked'), 'blocked');  // gearBlock says why
  if (eq.goal_id === g.id) return badge('info', 'target', t('gear_status_next', esc(row.stage)), 'next');
  if (row && row.stage) return badge('muted', 'list', t('gear_status_queued', esc(row.stage)), 'queued');
  return badge('warn', 'clock', esc(eq.why || ''), 'waiting');
}

/** Why no equipment is farmed for anyone now, under a character that asked for it, with the way to change it when
 *  that is a setting (the continuation off, its budget used up or granted for another role). Nothing is turned on here. */
function gearBlock(g, ev) {
  const row = gearQueueRow(g);
  const eq = STATE.plans?.[g.game]?.equipment || {};
  if ((ev && ev.done) || (g.gear_owned && g.gear_owned.done) || !ev?.target?.farm || (row && row.why) || !eq.why) return '';
  const setting = !eq.enabled || eq.role_ok === false || !eq.left;
  return `<div class="gear-block">${help(esc(eq.why), 'alert')}${setting ? linkButton('#/settings/set-farming', 'sliders', t('btn_farming_settings')) : ''}</div>`;
}

function gearSection(g) {
  const ev = g.gear_eval;
  const id = esc(g.id);
  const cfg = GEAR[g.game];
  const head = `<div class="mats-head"><h3>${t(cfg.title)}</h3>${button('edit-gear', 'edit', t('btn_gear_target'), 'sm', `data-id="${id}"${ev ? '' : ' disabled'}`)}</div>`;
  if (!ev) return `<section class="gear">${head}<p class="ink-2">${g.gear_error ? esc(g.gear_error) : t(cfg.none)}</p></section>`;
  const tg = ev.target;
  const checks = Object.values(ev.checks);
  const verdict = ev.done ? badge('good', 'check', t('gear_verdict_met'), 'met')
    : badge('muted', 'x', t('gear_verdict_below', checks.filter(Boolean).length, checks.length), 'below');
  const state = gearStatus(g, ev);
  const filled = ev.slots.filter(s => s.disc).length;
  const chips = [
    ev.sets.length ? chip(ev.checks.sets ? 'check' : 'x', tp('gear_sets_line', ev.sets.map(s => `${s.name} ${s.have}/${s.count}`).join(' · ')), ev.checks.sets ? 'good' : 'warn') : '',
    ev.checks.main ? chip('check', tp('gear_mains_ok'), 'good') : chip('x', tp('gear_mains_bad'), 'warn'),
    chip(ev.checks.filled ? 'check' : 'x', tp('gear_slots_filled', filled, ev.slots.length), ev.checks.filled ? 'good' : 'warn'),
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
        <div class="gear-score">${verdict}<span class="score-check ${ev.checks.score ? 'ok' : 'no'}">${icon(ev.checks.score ? 'check' : 'x')}<span class="value">${ev.score ?? '–'}</span><span class="ink-2">/ ${tg.score}</span></span>${ev.score == null ? '' : miniMeter(ev.score, tg.score || 100)}</div>
        <div class="gear-checks">${chips}</div>
        ${state ? `<div class="gear-state">${state}</div>` : ''}
      </div>
      ${gearBlock(g, ev)}
      ${ownedBlock(g)}
      <p class="meta ink-2"><span>${src}</span><span>${icon('refresh')}${t('gear_read_' + g.game, relative(ev.at))}</span>${g.gear_runs ? `<span>${t('gear_runs', num(g.gear_runs))}</span>` : ''}${toggleButton(detailId)}</p>
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
    <li>${setIcon(g.game, c.set_id)}<span><b>${slotName(g.game, c.slot)}<span class="colon">:</span></b> <span class="num">${c.was == null ? t('gear_slot_empty') : num(Math.round(c.was * 10) / 10)} → <b>${num(c.score)}</b></span></span>
      <span class="ink-2">${esc(c.set)} · ${propName(c.main?.id, c.main?.name)}</span></li>`).join('');
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
      <p>${icon('box')}<span>${t('inv_line_' + game, relative(inv.at), num(inv.count), num(inv.spare))}</span>${inv.spare ? toggleButton(id) : ''}</p>
      ${inv.spare ? detailPanel(id, `<ul class="spare">${sets}</ul>${help(t('inv_spare_help'))}`, 'mt') : ''}
    </div>`;
}

function discCard(game, s) {
  const d = s.disc;
  if (!d) return `<li class="disc empty" data-slot="${s.slot}"><b>${slotName(game, s.slot)}</b><span class="ink-2">${t('gear_slot_empty')}</span></li>`;
  const main = d.main ? `${propName(d.main.id, d.main.name)} <span class="num">${esc(d.main.value)}</span>` : '–';
  const subs = s.subs.map(x => `
    <li class="${x.weight > 0 ? 'eff' : ''}"><span>${propName(x.id, x.name)}</span><span class="num">${esc(x.value)}</span><span class="rolls num">${rollsText(x.rolls)}</span></li>`).join('');
  return `
    <li class="disc" data-slot="${s.slot}" data-rank="${esc(String(d.rarity).toLowerCase())}">
      <div class="disc-head">${setIcon(game, d.set_id)}<div><b>${slotName(game, s.slot)}</b><span>${esc(d.set)}</span></div>
        <span class="disc-score num" title="${t('gear_disc_score')}">${s.score ?? '–'}</span></div>
      <p class="disc-meta ink-2"><span class="disc-grade"><span class="disc-rank">${t(game === 'genshin' ? 'art_rank' : 'gear_rank', esc(d.rarity))}</span><span>${t(game === 'genshin' ? 'art_lv' : 'gear_lv', d.level)}</span></span>${s.wasted == null || !d.level ? ''
        : s.wasted ? `<span class="wasted">${icon('alert')}${t('gear_wasted', s.wasted)}</span>` : `<span class="all-hit">${icon('check')}${t('gear_all_hit')}</span>`}</p>
      <p class="disc-main${s.main_ok === false ? ' bad' : ''}">${s.main_ok === false ? icon('alert') : ''}${main}</p>
      <ul class="disc-subs">${subs}</ul>
    </li>`;
}

function priorityRow(g) {
  const order = g.category_order || ['level', 'talents', 'weapon'];
  const id = esc(g.id);
  const name = c => t(c === 'level' ? 'cat_level' : `cat_${c}_${g.game}`);
  const editId = `prio-${g.id}`;
  return `
    <div class="priority">
      <p class="priority-sum"><span class="label">${icon('list')}<span>${t('priority_label')}</span></span>
        <span class="priority-order">${order.map((c, i) => `<span><span class="n">${i + 1}</span> ${name(c)}</span>`).join('')}</span>
        ${toggleButton(editId, 'btn_change')}</p>
      ${detailPanel(editId, `<ol class="priority-edit">${order.map((c, i) => `
        <li><span class="n">${i + 1}</span><span>${name(c)}</span>${orderControl('shift-cat', `data-id="${id}" data-index="${i}"`, i, order.length)}</li>`).join('')}</ol>`)}
    </div>`;
}

/** What an item still needs: HTML, or plain text for a title attribute. */
function needText(it, plain = false) {
  const say = plain ? tp : t;
  const mats = it.materials || [];
  if (it.done) return say('status_collected');
  if (mats.some(m => m.remaining == null)) return say('qty_unknown');
  const short = mats.filter(m => m.remaining > 0);
  if (mats.length === 1) return say('need_more', num(short.length ? short[0].remaining : 0));
  const parts = short.slice(0, 2).map(m => `${num(m.remaining)} × ${m.name}`);
  if (short.length > 2) parts.push(`+${short.length - 2}`);
  return say('need_list', parts.join(tp('list_sep')));
}

function miniMeter(value, max) {
  const pct = max > 0 ? Math.min(100, (100 * value) / max) : 0;
  return `<span class="meter mini" aria-hidden="true">${pct > 0 ? `<span class="fill" style="width:${pct.toFixed(1)}%"></span>` : ''}</span>`;
}

function materialRow(g, it, nextKey) {
  const isNext = it.key === nextKey;
  let status;
  if (it.done) status = badge('good', 'check', t('status_collected'), 'collected');
  else if (it.paused) status = badge('muted', 'pause', t('status_paused'), 'paused');
  else if (isNext) status = badge('info', 'target', t('status_next'), 'next');
  else if (it.kind === 'manual') status = badge('muted', 'hand', t('status_manual'), 'manual');
  else if (it.why) status = badge('warn', 'clock', t('status_waiting'), 'waiting');
  else status = badge('muted', 'list', t('status_queued'), 'queued');
  const mats = it.materials || [];
  const top = mats[mats.length - 1];
  const name = top ? top.name : it.label;
  const sub = [it.tint ? `<span class="mat-cat">${t('mat_' + it.tint)}</span>` : '',
    name !== it.label ? `<span>${t('mat_from', it.label)}</span>` : '',
    it.weekdays?.length && it.weekdays.length < 7 ? `<span>${t('open_days', it.days)}</span>` : ''].join('');
  const executed = it.executed || 0;
  const plan = it.units == null || it.done ? '<div class="mat-plan"></div>'
    : `<div class="mat-plan"><span>${t('plan_units', executed, `${it.units}${it.unit_label || ''}`)}</span>${miniMeter(executed, it.units)}</div>`;
  const detailId = `mat-${g.id}-${it.key}`;
  const action = it.done || it.kind === 'manual' ? '' : button('pause-item', it.paused ? 'play' : 'pause', t(it.paused ? 'btn_resume' : 'btn_pause'), 'sm quiet',
    `data-id="${esc(g.id)}" data-key="${esc(it.key)}" data-pause="${it.paused ? '0' : '1'}"`);
  const tiers = mats.map(m => `
    <tr><td><span class="tier-name">${materialIcon(g.game, m.id, '')}${esc(m.name)}</span></td>
      <td class="n">${num(m.need) ?? '–'}</td><td class="n">${num(m.owned) ?? '–'}</td><td class="n">${m.remaining == null ? t('unknown') : num(m.remaining)}</td></tr>`).join('');
  return `
    <li class="mat${it.tint ? ' tint-' + esc(it.tint) : ''}" data-category="${esc(it.tint || 'other')}" data-row="${esc(it.key)}">
      <div class="mat-row">
        <div class="mat-id"><span class="mat-ic" aria-hidden="true">${top ? materialIcon(g.game, top.id) : ''}</span><div><b>${esc(name)}</b><span class="mat-sub">${sub}</span></div></div>
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

const LOGIN_PENDING = ['creating', 'waiting', 'scanned', 'reading'];

/** The one login UI: log in, authorize again or log out. A QR code starts at once when logged out. */
async function openLogin() {
  MODAL = { kind: 'login' };
  openDialog(dialogShell(t('login_title'), '<div id="login-body"></div>', '', 'login'));
  updateLoginDialog();
  const qr = STATE.qr || {};
  if (STATE.logged_in || LOGIN_PENDING.includes(qr.status)) return;
  try {
    STATE.qr = await api('/api/login/start', 'POST', {});
    updateLoginDialog();
  } catch (err) { toast(err.message, 'error'); }
}

function updateLoginDialog() {
  if (MODAL?.kind !== 'login') return;
  const body = document.getElementById('login-body');
  if (!body) return;
  const qr = STATE.qr || {};
  const signature = JSON.stringify(qr) + STATE.logged_in + CURRENT_LANG;
  if (MODAL.signature === signature) return;
  MODAL.signature = signature;
  const pending = LOGIN_PENDING.includes(qr.status);
  const img = ['waiting', 'scanned'].includes(qr.status) && qr.svg
    ? `<img alt="${t('qr_alt')}" src="data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(qr.svg)))}">` : '';
  const statusIcon = { error: 'alert', expired: 'clock', scanned: 'check', confirmed: 'check' }[qr.status] || 'qr';
  const start = ['expired', 'error'].includes(qr.status) ? 'btn_qr_new' : STATE.logged_in ? 'btn_login_again' : 'btn_qr';
  body.innerHTML = `${help(t('acc_desc'), 'shield')}
    ${STATE.logged_in ? help(t('login_shared'), 'check') : ''}
    <div class="qr-box">${img}<div role="status" aria-label="${t('login_status')}">${qr.reason ? help(esc(qr.reason), statusIcon) : ''}</div></div>
    <div class="actions mt">${pending ? button('login-cancel', 'x', t('btn_login_cancel'), 'sm') : button('login-start', 'qr', t(start), 'primary')}
      ${STATE.logged_in ? button('logout', 'logout', t('btn_logout'), 'sm') : ''}</div>`;
  reapplyBusy(body);
}

function openTargets(goal) {
  MODAL = { kind: 'targets', id: goal.id, error: '', dirty: false };
  renderTargetsDialog(goal);
}

function renderTargetsDialog(goal) {
  openDialog(dialogShell(t('dlg_targets_title', goal.name), `
      ${targetTables(goal, true)}
      <p class="meta ink-2" data-read>${readLine(goal)}</p>
      ${help(t('targets_help'))}`,
    `${MODAL.error ? `<span class="err" role="alert">${icon('alert')}${esc(MODAL.error)}</span>` : ''}
      <button type="button" class="btn quiet foot-start" data-action="targets-max">${icon('up')}<span class="txt">${t('btn_max')}</span></button>
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
  const cfg = GEAR[goal.game];
  const built = {
    sets: (ev.build.sets || []).map(s => `${esc(s.name)} ${t('gear_pieces', s.count)}`).join(' + ') || t('gear_set_none'),
    main: Object.keys(cfg.mains).map(slot => `${slotName(goal.game, slot)}<span class="colon">:</span> ${(ev.build.main[slot] || []).map(i => propName(i, ev.plan?.names?.[i])).join(' / ') || '–'}`).join(' · '),
    weights: cfg.subs.filter(i => (ev.official?.[i] || 0) > 0).map(i => `${propName(i)} ${ev.official[i]}`).join(tp('list_sep')) || t('gear_no_weights')
  };
  const follow = (key, sec) => `
    <label class="follow"><input type="checkbox" name="follow_${sec}" data-follow="${sec}" data-change="gear-follow"${own[key] == null ? ' checked' : ''}>
      <span>${t(sec === 'weights' ? 'gear_follow_weights' : 'gear_follow_build')}</span></label>
    <p class="follow-sum" data-sum="${sec}"${own[key] == null ? '' : ' hidden'}>${built[sec]}</p>`;
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
  openDialog(dialogShell(t('dlg_gear_title', esc(goal.name)), `<div data-game="${goal.game}">
      ${switchRow('farm', tg.farm, t(cfg.farm), t('gear_farm_sub'), cfg.unit, 'first')}
      <div class="fields wide">
        ${field(t('gear_score_target'), `<input type="number" name="score" min="0" max="100" step="1" value="${tg.score}">`, t('gear_score_hint'))}
        ${field(t(cfg.stage), `<select name="stage"><option value="">${t(cfg.stageAuto)}</option>
          ${stageOptions(stages, tg.stage)}</select>`, t(cfg.stageHint))}
      </div>
      <div class="sub-block"><h3>${t('gear_sets_title')}</h3>${follow('sets', 'sets')}
        <fieldset data-sec="sets"${own.sets == null ? ' disabled hidden' : ''}>${[0, 1, 2].map(i => setRow(i, tg.sets[i])).join('')}</fieldset></div>
      <div class="sub-block"><h3>${t(cfg.mainsTitle)}</h3>${follow('main', 'main')}
        <fieldset data-sec="main" class="mains"${own.main == null ? ' disabled hidden' : ''}>${Object.keys(cfg.mains).map(mainGroup).join('')}</fieldset></div>
      <div class="sub-block"><h3>${t('gear_weights_title')}</h3>${follow('weights', 'weights')}
        <fieldset data-sec="weights" class="fields weights"${own.weights == null ? ' disabled hidden' : ''}>
          ${cfg.subs.map(i => field(propName(i), `<input type="number" name="w_${i}" min="0" max="1" step="0.01" value="${ev.weights[i] ?? 0}">`)).join('')}
        </fieldset>
        ${help(t('gear_weights_help'))}</div></div>`,
    `${MODAL.error ? `<span class="err" role="alert">${icon('alert')}${esc(MODAL.error)}</span>` : ''}
      <button type="submit" class="btn primary" data-action="save-gear" data-id="${esc(goal.id)}">${icon('check')}<span class="txt">${t('btn_save_changes')}</span></button>`,
    'gear'), true);
}

/** "Follow the build" on: show the build's values in the (disabled) section; off: start editing from them. */
function toggleFollow(box) {
  const goal = findGoal(MODAL.id);
  const ev = goal && goal.gear_eval;
  const form = box.closest('form');
  const sec = form.querySelector(`fieldset[data-sec="${box.dataset.follow}"]`);
  if (!ev || !sec) return;
  sec.disabled = sec.hidden = box.checked;
  form.querySelector(`[data-sum="${box.dataset.follow}"]`).hidden = !box.checked;
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
      ${help(t(m.source === 'roster' ? 'modal_source_roster' : STATE.logged_in ? 'modal_source_offline' : 'modal_source_dataset'))}
      <label class="search">${icon('search')}<input type="search" id="char-search" placeholder="${t('search_placeholder')}" aria-label="${t('search_placeholder')}" value="${esc(m.query)}" autocomplete="off"></label>
      <ul class="char-list" id="char-list" role="listbox" aria-label="${t('search_placeholder')}">${charOptions()}</ul>`,
    `<button type="submit" class="btn primary" id="modal-add" data-action="add-goal-submit"${m.selected ? '' : ' disabled'}>${icon('plus')}<span class="txt">${t(m.selected ? 'btn_add' : 'btn_pick_first')}</span></button>`,
    'add-goal'));
}

// Element names as the datasets (Chinese) and the Genshin roster (English) write them.
const ELEMENTS = {
  genshin: { 火: 'el_pyro', 水: 'el_hydro', 风: 'el_anemo', 雷: 'el_electro', 草: 'el_dendro', 冰: 'el_cryo', 岩: 'el_geo',
             Pyro: 'el_pyro', Hydro: 'el_hydro', Anemo: 'el_anemo', Electro: 'el_electro', Dendro: 'el_dendro', Cryo: 'el_cryo', Geo: 'el_geo' },
  zzz: { 物理: 'el_physical', 火: 'el_fire', 冰: 'el_ice', 电: 'el_electric', 以太: 'el_ether', 风: 'el_wind' }
};
/** A character's element in the UI language; unknown values are left out. */
function elementName(game, value) { const k = ELEMENTS[game]?.[value]; return k ? tp(k) : ''; }

function charOptions() {
  const m = MODAL;
  const taken = new Set((STATE.goals?.[m.game] || []).map(g => String(g.character_id)));
  const q = m.query.trim().toLowerCase();
  const rows = (m.rows || []).filter(c => !q || String(c.name).toLowerCase().includes(q));
  if (!rows.length) return `<li><p class="ink-2" style="padding:12px">${t('no_match')}</p></li>`;
  return rows.map(c => {
    const id = String(c.id);
    const added = taken.has(id);
    const facts = `${agentTags(c, m.game)}${c.level ? `<span>Lv. ${esc(c.level)}</span>` : ''}`;
    const flag = added ? t('already_added') : c.owned === false ? t('not_owned') : '';
    return `<li><button type="button" class="char" role="option" data-action="pick-char" data-id="${esc(id)}" data-name="${esc(c.name)}"
        aria-selected="${m.selected?.id === id}"${added ? ' disabled' : ''}>
        ${portrait(m.game, id, c.name, 'md')}<span><b>${esc(c.name)}</b><span class="char-facts">${facts}</span></span><span class="ink-2">${flag}</span>${icon('check', 'pick')}</button></li>`;
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
    ${days.length ? days.map(day => {
      const told = new Set();  // games whose idle reason this day already shows
      return `
      <section class="panel day">
        <div class="day-head"><h2>${dayLabel(day.at) === dateOf(day.at) ? esc(dateOf(day.at)) : t('day_head', dayLabel(day.at), dateOf(day.at))}</h2>${dayNote(day.at)}</div>
        <ul class="entries">${day.rows.map(r => { const html = entry(r, told); if (!r.task) told.add(r.game); return html; }).join('')}</ul>
      </section>`;
    }).join('') : emptySheet('calendar', t('plan_empty_title'), t('plan_empty'),
        linkButton('#/settings/set-schedule', 'sliders', t('btn_open_settings')))}`;
}

/** Between midnight and the 04:00 reset the calendar day and the game day differ; say so on today's sheet. */
function dayNote(ms) {
  if (dayKeyOf(ms) !== dayKeyOf(nowMs()) || cnParts(nowMs()).h >= 4) return '';
  return `<span class="ink-2">${t('day_before_reset', gameDayLabel())}</span>`;
}

function entry(r, told) {
  const goal = r.goal_id ? findGoal(r.goal_id) : null;
  const next = r.at === STATE.next_slot && STATE.settings?.schedule?.enabled;
  const reason = told.has(r.game) ? t('reason_same') : esc(r.reason || '');
  const detailId = `plan-${r.at}-${r.game}`;
  const unitName = tp('unit_' + r.game);
  const task = r.task
    ? `<div class="task">${goal ? portrait(r.game, goal.character_id, goal.name, 'sm') : ''}<div><b>${esc(r.task)}</b>${next ? `<span class="tag">${t('tag_next')}</span>` : ''}<span>${r.names ? t('for_goal', r.goal, r.names) : esc(r.goal)}</span>${r.phase === 'equipment' ? `<span>${t('phase_equipment')}</span>` : ''}${fullBefore(r)}</div></div>`
    : `<div class="task"><div><b>${t('daily_only')}</b>${next ? `<span class="tag">${t('tag_next')}</span>` : ''}<span>${reason}</span>${told.has(r.game) ? '' : `<span><a href="#/settings/set-farming">${t('idle_fix')}</a></span>`}${fullBefore(r)}</div></div>`;
  const spend = r.spend != null
    ? `<div class="spend"><b>${t('fact_spend', num(r.spend), unitName)}</b>${r.left != null ? `<span>${leftText(r)}</span>` : ''}</div>`
    : `<div class="spend"><span>${r.stamina == null ? t('spend_unknown') : leftText(r)}</span></div>`;
  return `
    <li class="entry${r.task ? '' : ' idle'}${next ? ' next' : ''}" data-game="${r.game}">
      <div class="entry-row">
        <span class="time">${clock(r.at)}</span>
        <span class="game">${t('game_' + r.game)}</span>
        ${task}
        ${spend}
        <span class="more-btn">${toggleButton(detailId)}</span>
      </div>
      ${detailPanel(detailId, detailList(forecastDetails(r)))}
    </li>`;
}

// ----------------------------------------------------------- 4. Runs
function triggerLabel(run) { return run.source === 'schedule' ? t('trigger_schedule', run.slot) : t('trigger_manual'); }

/** "05:00–05:23", or "Today 05:00–05:23" with the day. */
function runSpan(run, withDay = false) {
  const start = toMs(run.started), end = toMs(run.ended);
  if (start == null) return '';
  const span = end == null ? clockOf(start) : `${clockOf(start)}–${clockOf(end)}`;
  return withDay ? `${dayLabel(start)} ${span}` : span;
}

function runGame(g) {
  const item = g.item;
  const unit = item?.unit_label || '';
  const amount = item
    ? (g.completed != null ? t('run_done', `${g.completed}${unit}`, `${item.upper}${unit}`) : t('run_unverified'))
    : '';
  return `
    <div class="run-game" data-game="${g.game}">
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
    ${list.length ? `<section class="panel">
      ${list.map(r => {
        const start = toMs(r.started);
        return `<article class="run" data-state="${esc(String(r.status).toLowerCase())}"><div class="when"><b>${esc(runSpan(r))}</b><span>${esc(start ? dateOf(start) : '')}</span></div><div>${runBody(r)}</div></article>`;
      }).join('')}
      ${!MORE_RUNS && list.length >= 20 ? `<div class="mt">${button('more-runs', 'history', t('btn_more_runs'), 'sm')}</div>` : ''}
    </section>` : emptySheet('history', t('runs_empty_title'), t('runs_empty'), linkButton('#/today', 'home', t('btn_open_today')))}`;
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
    ${pageHead(t('nav_settings'), t('settings_sub'))}
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
  markSettingsSection();
}

/** Mark the settings section at the top of the view in the side navigation. */
function markSettingsSection() {
  if (ROUTE.tab !== 'settings') return;
  const sections = SETTINGS_SECTIONS.map(([id]) => document.getElementById(id)).filter(Boolean);
  const top = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
  const current = sections.filter(sec => sec.getBoundingClientRect().top <= top + 8).pop() || sections[0];
  document.querySelectorAll('.settings-nav [data-key]').forEach(b => {
    if (b.dataset.key === current?.id) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
  });
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
    return `${panelHead('set-account', 'user', button('login-dialog', 'qr', t('btn_login_manage'), 'sm'))}
      <p style="margin-bottom:12px">${badge('good', 'check', t('acc_signed_in'))}</p><div class="kv">${rows}</div>
      <p class="ink-2 mt">${t('login_shared')}</p>`;
  }
  return `${panelHead('set-account', 'user')}
    <p class="ink-2">${t('acc_desc')}</p>
    <div class="actions mt">${button('login-dialog', 'qr', t('btn_qr'), 'primary')}</div>`;
}

function envRow(label, ok, okText, badText, detail = '', kind = 'bad', hint = '') {
  const state = ok ? badge('good', 'check', okText) : badge(kind, kind === 'muted' ? 'minus' : 'alert', badText);
  return `<div class="kv-row"><span class="k">${label}</span><span class="v">${state}${detail ? pathCode(detail) : ''}${hint ? `<span class="ink-2">${hint}</span>` : ''}</span></div>`;
}

/** A file path that wraps at folder boundaries on narrow screens; <wbr> adds nothing when the path is copied. */
function pathCode(path) {
  return `<code>${esc(path).replace(/[\\/]/g, '$&<wbr>')}</code>`;
}

function pathRow(label, path, hint = '') {
  return `<div class="kv-row"><span class="k">${label}</span><span class="v">${pathCode(path || '')}${hint ? `<span class="ink-2">${hint}</span>` : ''}</span></div>`;
}

function envPanel() {
  const c = STATE.check || {};
  const bundled = !STATE.settings?.execution?.bgi_template;
  return `${panelHead('set-env', 'shield')}
    <div class="kv">
      ${STATE.automation === false ? help(t('env_plan_only'), 'monitor') : envRow(t('env_admin'), c.admin, t('env_admin_ok'), t('env_admin_no'), '', 'warn', c.admin ? '' : t('env_admin_hint'))}
      ${envRow(t('env_bgi'), c.genshin?.tool_ok, t('found'), t('missing'), c.genshin?.tool_exe)}
      ${envRow(t('env_bgi_template'), c.genshin?.template_ok, bundled ? t('bundled') : t('found'), t('missing'), bundled ? '' : STATE.settings?.execution?.bgi_template)}
      ${envRow(t('env_od'), c.zzz?.tool_ok, t('found'), t('missing'), c.zzz?.tool_exe)}
      ${envRow(t('env_adapter'), c.zzz?.patch_ok, t('installed'), t('not_installed'), '', 'muted', t('env_adapter_help'))}
      ${envRow(t('env_game_genshin'), c.genshin?.game_ok, t('found'), t('missing'), c.genshin?.game_exe, 'warn')}
      ${envRow(t('env_game_zzz'), c.zzz?.game_ok, t('found'), t('missing'), c.zzz?.game_exe, 'warn')}
      ${pathRow(t('env_data_dir'), STATE.data_dir, t('env_data_dir_hint'))}
      ${pathRow(t('env_log'), STATE.log_file)}
    </div>`;
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
      ${switchRow('features.mute_morning', s.features.mute_morning, t('mute_morning'), t('mute_morning_sub'), 'bell', '', plansOnly)}
      <div class="sub-block">
        <div class="fields">
          ${field(t('sched_times'), input('schedule.times', (s.schedule.times || []).join(', '), 'type="text" data-type="list" spellcheck="false"'), t('sched_times_hint'))}
          ${field(t('catchup'), input('schedule.catchup_hours', s.schedule.catchup_hours, 'type="number" min="0" max="24" step="0.5"'), t('catchup_hint'))}
          ${field(t('timeout'), input('execution.timeout_minutes', s.execution.timeout_minutes, 'type="number" min="10" max="480" step="5"'))}
          ${field(t('if_running'), `<select name="execution.if_game_running">
              <option value="restart"${s.execution.if_game_running === 'restart' ? ' selected' : ''}>${t('opt_restart')}</option>
              <option value="skip"${s.execution.if_game_running === 'skip' ? ' selected' : ''}>${t('opt_skip')}</option></select>`, t('if_running_hint'))}
        </div>
        <fieldset><legend>${t('sched_games')}</legend><div class="check-row">${GAMES.map(g =>
          `<label><input type="checkbox" name="schedule.games" data-type="set" value="${g}"${games.includes(g) ? ' checked' : ''}>${t('game_' + g)}</label>`).join('')}</div></fieldset>
      </div>
    </section>`;
}

function equipUsage(game) {
  const e = STATE.plans?.[game]?.equipment || {};
  // A budget spends one game role's stamina: granted for another role (or before roles were recorded), it waits.
  const role = e.enabled && e.role_ok === false ? `<div class="gear-block">${help(t('equip_role_other'), 'alert')}
    ${button('equip-grant', 'check', t('btn_equip_grant'), 'sm', `data-game="${game}"`)}</div>` : '';
  return `${role}<span class="usage">${icon('list')}<span>${t('equip_used', e.used ?? 0, e.cap ?? 0)}</span>
    ${button('equip-reset', 'refresh', t('btn_reset'), 'sm quiet', `data-game="${game}"${e.used ? '' : ' disabled'}`)}</span>`;
}

function scanStatus(game) {
  const inv = STATE.inventory?.[game];
  return inv ? t('scan_last_' + game, relative(inv.at), num(inv.count)) : t('scan_never');
}

/** Options for a stage or domain, each with the sets it drops; the ones that drop a set some goal targets come first,
 *  and a saved name the list lacks stays selectable. */
function stageOptions(stages, value) {
  const list = [...(stages || [])];
  if (value && !list.some(s => s.name === value)) list.push({ name: value, sets: [] });
  const wanted = new Set(GAMES.flatMap(g => STATE.goals?.[g] || []).flatMap(g => g.gear_eval?.target?.sets || []).map(s => s.name));
  const option = s => `<option value="${esc(s.name)}"${s.name === value ? ' selected' : ''}>${esc(s.sets.length ? `${s.name} — ${s.sets.join(' / ')}` : s.name)}</option>`;
  const needed = list.filter(s => s.sets.some(x => wanted.has(x)));
  if (!needed.length) return list.map(option).join('');
  return `<optgroup label="${t('stages_needed')}">${needed.map(option).join('')}</optgroup>
    <optgroup label="${t('stages_other')}">${list.filter(s => !needed.includes(s)).map(option).join('')}</optgroup>`;
}

/** The fixed equipment stage or domain: empty means only characters' targets steer. */
function pickStage(name, value, stages) {
  return `<select name="${name}"><option value="">${t('equip_none')}</option>${stageOptions(stages, value)}</select>`;
}

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
          ${field(t('artifact_domain'), pickStage('planning.artifact.domain', p.artifact.domain, STATE.catalog?.stages?.genshin), t('equip_fixed_hint'))}
          ${field(t('artifact_cap'), input('planning.artifact.cap', p.artifact.cap, 'type="number" min="0" step="1"'))}
        </div>
        <div data-live="equip-genshin">${equipUsage('genshin')}</div>
        ${switchRow('planning.disc.enabled', p.disc.enabled, t('disc_switch'), t('disc_sub'), 'battery')}
        <div class="fields">
          ${field(t('disc_mission'), pickStage('planning.disc.mission', p.disc.mission, STATE.catalog?.stages?.zzz), t('equip_fixed_hint'))}
          ${field(t('disc_cap'), input('planning.disc.cap', p.disc.cap, 'type="number" min="0" step="1"'))}
        </div>
        <div data-live="equip-zzz">${equipUsage('zzz')}</div>
      </div>
      <div class="sub-block">
        <h3>${icon('search')}<span>${t('scan_title')}</span></h3>
        ${help(t('scan_help'))}
        ${switchRow('features.scan_inventory', s.features.scan_inventory, t('scan_switch'), t('scan_sub'), 'box')}
        <div class="fields paths">
          ${field(t('scan_yas'), input('paths.yas', s.paths.yas, 'type="text" spellcheck="false"'), scanStatus('genshin'))}
          ${field(t('scan_zzz'), input('paths.zzz_scanner', s.paths.zzz_scanner, 'type="text" spellcheck="false"'), scanStatus('zzz'))}
        </div>
        <details class="fold" data-keep="scan-rules"><summary>${icon('chevron', 'chev')}<span>${t('scan_rules_title')}</span></summary>
          <div class="fold-body">${help(t('scan_rules'), 'alert')}</div></details>
      </div>
    </section>`;
}

function dailiesPanel(s) {
  const f = s.features;
  return `
    <section class="panel" id="set-dailies">
      ${panelHead('set-dailies', 'gift')}
      ${switchRow('features.genshin_mail', f.genshin_mail, t('genshin_mail'), '', 'mail', 'first')}
      ${switchRow('features.genshin_daily_reward', f.genshin_daily_reward, t('genshin_daily'), t('genshin_daily_sub'), 'clipboard')}
      ${switchRow('features.genshin_teapot', f.genshin_teapot, t('genshin_teapot'), t('genshin_teapot_sub'), 'cup')}
      ${switchRow('features.zzz_rewards', f.zzz_rewards, t('zzz_rewards'), '', 'gift')}
      <details class="fold mt" data-keep="tools-more"><summary>${icon('chevron', 'chev')}<span>${t('tools_more_title')}</span></summary>
        <div class="fold-body tools-more">
          <p><b>${t('game_zzz')}</b> ${t('tools_zzz_intro')}</p>
          ${textList('tools_zzz_list', `<a href="#/settings/set-farming">${t('set_farming')}</a>`, `<a href="#/settings/set-schedule">${t('set_schedule')}</a>`)}
          <p><b>${t('game_genshin')}</b> ${t('tools_genshin_intro')}</p>
          ${textList('tools_genshin_list')}
          ${alertBox('warn', 'alert', t('tools_more_risk'))}
        </div></details>
    </section>`;
}

/** A translated list of short lines; {0}, {1}… take the given links. */
function textList(key, ...links) {
  return `<ul class="text-list">${lookup(key).map(line => `<li>${format(esc(line), links, false)}</li>`).join('')}</ul>`;
}

function secretField(label, key) {
  const saved = STATE.settings?.secrets_set?.[key];
  const clear = saved ? button('clear-secret', 'x', t('btn_clear'), 'sm', `data-key="${key}"`) : '';
  return field(label, `<span class="with-action"><input name="secret.${key}" type="password" placeholder="${saved ? t('secret_saved') : ''}" autocomplete="new-password">${clear}</span>`,
    t(STATE.automation === false ? 'secret_hint_linux' : 'secret_hint'));
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
      ${switchRow('notify.quiet_success', n.quiet_success, t('ev_quiet'), '', 'check', 'nested')}
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
      <div class="fields paths mt">
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

/** One line of the Run confirmation: what a game would farm now and roughly what it spends. */
function runPreview(game) {
  const item = STATE.plans?.[game]?.item;
  const name = tp('game_' + game);
  if (!item) return tp('confirm_run_idle', name);
  const spend = item.expected != null ? item.expected * item.cost : null;
  return spend == null ? tp('confirm_run_open', name, item.label, item.goal)
    : tp('confirm_run_item', name, item.label, item.goal, num(spend), tp('unit_' + game));
}

const ACTIONS = {
  retry: () => refreshState(),
  refresh: btn => busy(btn, () => refreshState(true)),
  theme: btn => { applyTheme(btn.dataset.key); document.getElementById('look-menu').open = false; },
  mode: btn => { applyMode(btn.dataset.key); document.getElementById('look-menu').open = false; },
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
  run: btn => {
    const games = btn.dataset.games.split(',');
    if (!confirm(tp('confirm_run', games.map(runPreview).join('\n')))) return;
    commit(btn, () => api('/api/run', 'POST', { games }), tp('toast_batch_started'), 'starting');
  },
  stop: btn => commit(btn, () => api('/api/stop', 'POST', {}), tp('toast_stop_sent')),
  'refresh-notes': btn => commit(btn, async () => {
    const res = await api('/api/notes/refresh', 'POST', { game: btn.dataset.game });
    if (res && res.error) throw new Error(res.error);
  }, tp('toast_notes')),
  'goals-game': btn => { GOALS_GAME = btn.dataset.game; store.set('gcl_goals_game', GOALS_GAME); render(true); },
  'add-goal': btn => {
    if (GAMES.includes(btn.dataset.game)) { GOALS_GAME = btn.dataset.game; store.set('gcl_goals_game', GOALS_GAME); }
    openAddGoal();
  },
  'modal-close': () => closeDialog(),
  'pick-char': btn => {
    MODAL.selected = { id: btn.dataset.id, name: btn.dataset.name };
    document.querySelectorAll('#char-list .char').forEach(b => b.setAttribute('aria-selected', String(b === btn)));
    const add = document.getElementById('modal-add');
    add.disabled = false;
    add.querySelector('.txt').textContent = tp('btn_add');
  },
  'targets-max': btn => {
    btn.closest('form').querySelectorAll('input[type="number"][max]').forEach(el => { el.value = el.max; });
    btn.closest('form').dispatchEvent(new Event('input', { bubbles: true }));
  },
  'move-goal': btn => commit(btn, async () => {
    const goal = goalBy(btn);
    const list = (STATE.goals?.[goal.game] || []).filter(g => g.enabled);
    const i = list.findIndex(g => g.id === goal.id), j = i + Number(btn.dataset.dir);
    if (j < 0 || j >= list.length) return;
    [list[i], list[j]] = [list[j], list[i]];
    await api('/api/goals/order', 'POST', { game: goal.game, ids: list.map(g => g.id) });
  }, tp('toast_order'), undefined, goalSel(btn.dataset.id)),
  'sync-goal': btn => syncGoal(btn),
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
  'login-dialog': () => openLogin(),
  'login-start': btn => busy(btn, async () => {
    STATE.qr = await api('/api/login/start', 'POST', {});
    updateLoginDialog();
  }),
  'login-cancel': btn => busy(btn, async () => {
    STATE.qr = await api('/api/login/cancel', 'POST', {});
    updateLoginDialog();
  }),
  logout: btn => {
    if (!confirm(tp('confirm_logout'))) return;
    commit(btn, () => api('/api/logout', 'POST', {}), tp('toast_logged_out'));
  },
  'equip-reset': btn => commit(btn, () => api('/api/equip/reset', 'POST', { game: btn.dataset.game }), tp('toast_equip_reset')),
  'equip-grant': btn => commit(btn, () => api('/api/equip/grant', 'POST', { game: btn.dataset.game }), tp('toast_equip_granted')),
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

/** When the levels were last read from the official tools (a sync that failed to read them does not count). */
function readLine(g) {
  return `${icon('refresh')}<span>${g.observe_at ? t('synced', relative(g.observe_at)) : t('never_synced')}</span>`;
}

/** An open target dialog keeps what the user typed, but its current levels follow every refresh. */
function updateTargetsDialog() {
  if (MODAL?.kind !== 'targets') return;
  const goal = findGoal(MODAL.id);
  if (!goal) return;
  document.querySelectorAll('#modal [data-cur]').forEach(td => { td.textContent = goal.current?.[td.dataset.cur] ?? '–'; });
  const read = document.querySelector('#modal [data-read]');
  if (read) read.innerHTML = readLine(goal);
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
  document.body.dataset.view = ROUTE.tab;
  document.querySelectorAll('#tabs a').forEach(a => {
    if (a.dataset.tab === ROUTE.tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  document.querySelectorAll('main > section').forEach(s => { s.hidden = s.id !== `view-${ROUTE.tab}`; });
  if (ROUTE.tab !== 'runs') MORE_RUNS = null;
  const gameArg = ROUTE.tab === 'goals' && GAMES.includes(ROUTE.arg);  // #/goals/zzz: that game's tab
  if (gameArg) { GOALS_GAME = ROUTE.arg; store.set('gcl_goals_game', GOALS_GAME); }
  if (ROUTE.tab === 'goals' && ROUTE.arg && STATE && !gameArg) {
    const goal = findGoal(ROUTE.arg);
    if (goal) GOALS_GAME = goal.game;
  }
  render(ROUTE.tab !== prev || Boolean(ROUTE.arg));
  if (gameArg) {
    window.scrollTo(0, 0);
  } else if (ROUTE.arg) {
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
  const menu = document.getElementById('look-menu');
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

document.addEventListener('keydown', e => {
  const menu = document.getElementById('look-menu');
  if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); }
});

window.addEventListener('hashchange', showRoute);
let SCROLL_FRAME = 0;
window.addEventListener('scroll', () => {
  if (!SCROLL_FRAME) SCROLL_FRAME = requestAnimationFrame(() => { SCROLL_FRAME = 0; markSettingsSection(); });
}, { passive: true });
window.addEventListener('beforeunload', e => {
  if (SETTINGS_DIRTY || (MODAL && MODAL.dirty)) { e.preventDefault(); e.returnValue = ''; }
});
document.getElementById('modal').addEventListener('close', () => { MODAL = null; });

// ----------------------------------------------------------- start
(function start() {
  applyTheme(THEME);
  applyMode(MODE);
  document.documentElement.lang = CURRENT_LANG === 'zh' ? 'zh-CN' : 'en';
  ROUTE = parseRoute();
  document.body.dataset.view = ROUTE.tab;
  renderShell();
  document.querySelectorAll('main > section').forEach(s => { s.hidden = s.id !== `view-${ROUTE.tab}`; });
  refreshState().then(() => { if (ROUTE.arg) showRoute(); });
  setInterval(() => { if (!document.hidden) refreshState(); }, 5000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshState(); });
})();
