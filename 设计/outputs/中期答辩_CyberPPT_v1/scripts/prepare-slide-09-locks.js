const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-09.png";
const lockDir = `${root}/locks`;
fs.mkdirSync(lockDir, { recursive: true });

const components = {
  components: [
    {
      id: "page_header",
      type: "native_page_header_system",
      priority: "P1",
      required_subcomponents: ["page_badge", "deck_title", "section_label", "top_rule"],
      must_preserve_type: true,
    },
    {
      id: "narrative_header",
      type: "native_title_and_subtitle",
      priority: "P0",
      required_subcomponents: ["main_title", "subtitle"],
      must_preserve_type: true,
    },
    {
      id: "system_performance",
      type: "native_dual_axis_bar_chart_and_result_table",
      priority: "P0",
      required_subcomponents: ["three_sinr_bars", "three_avoidance_bars", "dual_axes", "result_table"],
      must_preserve_type: true,
    },
    {
      id: "dynamic_recovery",
      type: "native_two_series_recovery_curve",
      priority: "P0",
      required_subcomponents: ["meta_rf_curve", "pure_drl_curve", "jump_marker", "recovery_annotations", "summary_table"],
      must_preserve_type: true,
    },
    {
      id: "engineering_evidence",
      type: "native_metric_and_risk_cards",
      priority: "P0",
      required_subcomponents: ["sinr_gain", "recovery_reduction", "latency_risk", "conservative_scope_note"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["transparent_check_icon", "conclusion_text", "source_footer"],
      must_preserve_type: true,
    },
  ],
};

const elements = [];
const add = (element_id, priority, element_type, source_component_id, role, x, y, w, h, pixel = 100) => {
  elements.push({
    element_id,
    priority,
    element_type,
    source_component_id,
    role,
    measurement_mode: "individual_bbox",
    blueprint_bbox_px: { x, y, w, h },
    must_reproduce: true,
    registration_status: "target_locked",
    pixel_mean_abs_tolerance: pixel,
  });
};

add("background_surface", "P0", "background", "page_surface", "background", 0, 0, 1672, 941, 18);
add("page_badge", "P1", "shape", "page_header", "page_badge", 17, 5, 141, 55, 95);
add("page_number", "P1", "text", "page_header", "page_number", 36, 8, 66, 48, 110);
add("header_deck_title", "P1", "text", "page_header", "header_title", 421, 15, 700, 42, 105);
add("section_label", "P1", "text", "page_header", "section_label", 1272, 16, 352, 40, 105);
add("top_rule", "P1", "line", "page_header", "divider", 17, 63, 1637, 4, 72);
add("main_title", "P0", "text", "narrative_header", "title", 191, 83, 1295, 57, 125);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 309, 143, 1050, 43, 115);

add("system_panel_surface", "P0", "panel", "system_performance", "core_panel", 25, 194, 553, 606, 74);
add("system_panel_header", "P1", "shape", "system_performance", "panel_header", 25, 194, 553, 47, 76);
add("system_panel_title", "P1", "text", "system_performance", "panel_title", 84, 198, 433, 38, 115);
add("system_chart_legend", "P1", "chart_group", "system_performance", "legend", 100, 248, 410, 33, 110);
add("system_chart_axes", "P1", "chart_group", "system_performance", "axes", 37, 294, 527, 329, 82);
add("system_sinr_bars", "P0", "chart_group", "system_performance", "data_bars", 101, 407, 168, 129, 82);
add("system_avoid_bars", "P0", "chart_group", "system_performance", "data_bars", 350, 349, 161, 243, 82);
add("system_data_labels", "P1", "text_group", "system_performance", "data_labels", 101, 326, 417, 210, 115);
add("system_result_table", "P0", "table", "system_performance", "result_table", 36, 627, 528, 154, 90);

add("dynamic_panel_surface", "P0", "panel", "dynamic_recovery", "core_panel", 594, 194, 640, 606, 74);
add("dynamic_panel_header", "P1", "shape", "dynamic_recovery", "panel_header", 594, 194, 640, 47, 76);
add("dynamic_panel_title", "P1", "text", "dynamic_recovery", "panel_title", 674, 198, 480, 38, 115);
add("dynamic_chart_axes", "P1", "chart_group", "dynamic_recovery", "axes", 604, 294, 609, 396, 82);
add("dynamic_curves", "P0", "chart_group", "dynamic_recovery", "two_series_curves", 640, 332, 573, 307, 86);
add("jump_marker", "P0", "chart_group", "dynamic_recovery", "event_marker", 780, 257, 208, 382, 100);
add("recovery_annotations", "P0", "chart_group", "dynamic_recovery", "recovery_intervals", 881, 388, 278, 204, 110);
add("dynamic_summary_table", "P0", "table", "dynamic_recovery", "result_table", 613, 698, 606, 82, 90);

add("evidence_panel_surface", "P0", "panel", "engineering_evidence", "core_panel", 1247, 194, 396, 606, 74);
add("evidence_panel_header", "P1", "shape", "engineering_evidence", "panel_header", 1247, 194, 396, 47, 76);
add("evidence_panel_title", "P1", "text", "engineering_evidence", "panel_title", 1291, 198, 309, 38, 115);
add("sinr_gain_card", "P0", "panel", "engineering_evidence", "key_metric", 1268, 265, 349, 143, 88);
add("sinr_gain_value", "P0", "text", "engineering_evidence", "key_metric_value", 1292, 279, 300, 81, 130);
add("recovery_gain_card", "P0", "panel", "engineering_evidence", "key_metric", 1268, 422, 349, 142, 88);
add("recovery_gain_value", "P0", "text", "engineering_evidence", "key_metric_value", 1293, 432, 300, 78, 130);
add("latency_risk_card", "P0", "panel", "engineering_evidence", "risk_panel", 1268, 581, 349, 155, 94);
add("latency_value", "P0", "text_group", "engineering_evidence", "risk_metric", 1280, 589, 322, 69, 125);
add("latency_warning", "P0", "text", "engineering_evidence", "risk_statement", 1287, 679, 311, 42, 125);
add("caveat_card", "P1", "panel", "engineering_evidence", "scope_note", 1260, 748, 365, 42, 88);
add("caveat_info_icon", "P1", "picture", "engineering_evidence", "info_icon", 1268, 751, 38, 38, 105);
add("caveat_text", "P1", "text", "engineering_evidence", "scope_note_text", 1310, 750, 304, 37, 115);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 25, 818, 1618, 90, 76);
add("conclusion_check_icon", "P1", "picture", "conclusion_band", "check_icon", 132, 831, 65, 64, 105);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 220, 830, 1300, 64, 125);
add("source_footer", "P1", "text", "conclusion_band", "source", 1325, 892, 290, 14, 92);

const annotations = { elements };
const iconPlacements = [
  ["info", "info", "保守耗时口径提示", { x: 1268, y: 751, w: 38, h: 38 }],
  ["check", "check", "证据闭环结论", { x: 132, y: 831, w: 65, h: 64 }],
].map(([placement_id, name, semantic_meaning, source_bbox_px]) => ({
  placement_id,
  icon_id: `approved-blueprint-crop/${name}`,
  source_library: "approved-blueprint-crops",
  semantic_meaning,
  png_path: `${root}/assets/slide-09-blueprint-icons/${name}.png`,
  source_bbox_px,
  contains_key_text: false,
  powerpoint_render_verified: false,
}));

const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 9,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with three evidence panels and one full-width navy conclusion band",
  layout_regions: [
    { id: "header", bbox_px: { x: 17, y: 5, w: 1637, h: 181 } },
    { id: "system_performance", bbox_px: { x: 25, y: 194, w: 553, h: 606 } },
    { id: "dynamic_recovery", bbox_px: { x: 594, y: 194, w: 640, h: 606 } },
    { id: "engineering_evidence", bbox_px: { x: 1247, y: 194, w: 396, h: 606 } },
    { id: "conclusion_band", bbox_px: { x: 25, y: 818, w: 1618, h: 90 } },
  ],
  header_footer_system: {
    page_badge: "09",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "工作成果｜系统验证与问题",
    footer: "source IDs in conclusion band",
  },
  so_what_region: { bbox_px: { x: 25, y: 818, w: 1618, h: 90 }, native_text_required: true },
  main_chart_semantics: "System-level SINR and avoidance comparison, non-stationary jump recovery curves, and engineering latency gap.",
  density_targets: {
    overall: "high",
    system_performance: "six bars, exact values, dual axes and three-row result table",
    dynamic_recovery: "two 37-point curves, jump event, recovery interval annotations and two-row summary table",
    engineering_evidence: "two key metrics, one latency risk card and one conservative-scope note",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text and labels",
    "dual-axis system comparison chart",
    "two-series dynamic recovery curve",
    "result and recovery tables",
    "key metrics, latency warning and conclusion band",
  ],
  allowed_visual_assets: iconPlacements.map((icon) => ({
    id: icon.placement_id,
    icon_id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.png_path,
    source: "Approved slide-09 blueprint crop",
    source_bbox_px: icon.source_bbox_px,
    necessity: "exact restoration of the approved non-text visual symbol",
    contains_key_text: false,
    editable_information_sacrifice: false,
    trace_required: false,
  })),
  icon_style_lock: { library: "approved-blueprint-crops", style_locked: true, icons: iconPlacements },
  complex_visual_scan: {
    completed: true,
    complex_visual_candidates: [],
    triggered_gates: ["dual_axis_chart_gate", "recovery_curve_gate", "icon_transparency_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All charts, curves, tables, values, labels and conclusions remain native; two transparent icon placements preserve exact blueprint fidelity.",
  },
};

fs.writeFileSync(`${lockDir}/slide-09-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-09-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-09-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
