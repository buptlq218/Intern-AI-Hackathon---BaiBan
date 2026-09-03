const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-08.png";
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
      id: "strategy_chart",
      type: "native_bar_chart_with_error_bars",
      priority: "P0",
      required_subcomponents: ["four_bars", "four_error_bars", "data_labels", "axes"],
      must_preserve_type: true,
    },
    {
      id: "importance_chart",
      type: "native_horizontal_feature_importance_chart",
      priority: "P0",
      required_subcomponents: ["five_feature_bars", "value_labels"],
      must_preserve_type: true,
    },
    {
      id: "key_metrics",
      type: "native_two_metric_panel",
      priority: "P0",
      required_subcomponents: ["baseline_gain", "gru_contribution"],
      must_preserve_type: true,
    },
    {
      id: "interpretation_strip",
      type: "native_three_finding_strip",
      priority: "P0",
      required_subcomponents: ["three_check_icons", "three_findings"],
      must_preserve_type: true,
    },
    {
      id: "caveat_strip",
      type: "native_experiment_level_caveat",
      priority: "P0",
      required_subcomponents: ["warning_icon", "caveat_text"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["trophy_icon", "conclusion_text", "source_footer"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 13, 0, 110, 82, 95);
add("page_number", "P1", "text", "page_header", "page_number", 36, 13, 58, 43, 105);
add("header_deck_title", "P1", "text", "page_header", "header_title", 424, 14, 787, 42, 100);
add("section_label", "P1", "text", "page_header", "section_label", 1358, 20, 292, 35, 100);
add("top_rule", "P1", "line", "page_header", "divider", 130, 61, 1538, 4, 70);
add("main_title", "P0", "text", "narrative_header", "title", 291, 94, 1095, 55, 120);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 400, 164, 887, 37, 110);

add("strategy_chart_surface", "P0", "panel", "strategy_chart", "core_panel", 15, 209, 883, 438, 72);
add("strategy_chart_title", "P1", "text", "strategy_chart", "chart_title", 340, 219, 355, 34, 110);
add("strategy_chart_axes", "P1", "chart_group", "strategy_chart", "axes", 118, 266, 753, 327, 75);
const barBoxes = [
  ["baseline", 155, 492, 106, 101],
  ["freq", 351, 419, 107, 174],
  ["time", 547, 424, 108, 169],
  ["joint", 743, 400, 107, 193],
];
for (const [id, x, y, w, h] of barBoxes) {
  add(`strategy_bar_${id}`, "P0", "bar", "strategy_chart", "data_bar", x, y, w, h, 75);
}
add("strategy_error_bars", "P0", "chart_group", "strategy_chart", "error_bars", 202, 365, 597, 228, 75);
add("strategy_data_labels", "P1", "text_group", "strategy_chart", "data_label", 152, 367, 700, 107, 110);
add("strategy_axis_labels", "P1", "text_group", "strategy_chart", "axis_label", 33, 253, 838, 383, 105);

add("importance_chart_surface", "P0", "panel", "importance_chart", "core_panel", 912, 209, 738, 287, 72);
add("importance_chart_title", "P1", "text", "importance_chart", "chart_title", 1102, 220, 390, 34, 110);
const importanceBars = [
  ["ratio", 1052, 266, 505, 30],
  ["td", 1052, 311, 341, 30],
  ["fc", 1052, 356, 331, 30],
  ["avoid", 1052, 402, 123, 30],
  ["entropy", 1052, 447, 93, 30],
];
for (const [id, x, y, w, h] of importanceBars) {
  add(`importance_${id}_bar`, "P0", "bar", "importance_chart", "data_bar", x, y, w, h, 75);
}
add("importance_labels", "P1", "text_group", "importance_chart", "axis_and_value_labels", 938, 261, 686, 222, 110);

add("metric_panel_surface", "P0", "panel", "key_metrics", "metric_panel", 912, 505, 738, 142, 72);
add("metric_divider", "P1", "line", "key_metrics", "divider", 1273, 523, 2, 106, 72);
add("metric_baseline_value", "P0", "text", "key_metrics", "key_metric", 959, 528, 285, 60, 125);
add("metric_baseline_label", "P1", "text", "key_metrics", "metric_label", 973, 600, 263, 31, 110);
add("metric_gru_value", "P0", "text", "key_metrics", "key_metric", 1330, 528, 274, 60, 125);
add("metric_gru_label", "P1", "text", "key_metrics", "metric_label", 1360, 600, 228, 31, 110);

add("interpretation_surface", "P0", "panel", "interpretation_strip", "finding_strip", 15, 657, 1636, 91, 72);
for (let i = 0; i < 3; i += 1) {
  const x = [84, 607, 1093][i];
  add(`interpretation_icon_${i + 1}`, "P1", "picture", "interpretation_strip", "check_icon", x, 668, 77, 72, 100);
}
add("interpretation_finding_1", "P0", "text_group", "interpretation_strip", "finding", 187, 669, 322, 67, 110);
add("interpretation_finding_2", "P0", "text_group", "interpretation_strip", "finding", 699, 669, 307, 67, 110);
add("interpretation_finding_3", "P0", "text_group", "interpretation_strip", "finding", 1190, 669, 417, 67, 110);
add("interpretation_dividers", "P1", "line_group", "interpretation_strip", "divider", 531, 681, 482, 48, 72);

add("caveat_surface", "P0", "panel", "caveat_strip", "caveat", 15, 760, 1636, 67, 78);
add("caveat_icon", "P1", "picture", "caveat_strip", "warning_icon", 394, 767, 60, 55, 100);
add("caveat_text", "P0", "text", "caveat_strip", "caveat_text", 476, 773, 831, 42, 115);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 15, 837, 1636, 88, 72);
add("trophy_icon", "P1", "picture", "conclusion_band", "icon", 172, 840, 84, 82, 100);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 290, 852, 1116, 54, 120);
add("source_footer", "P1", "text", "conclusion_band", "source", 1320, 906, 285, 13, 90);

const annotations = { elements };
const iconPlacements = [
  ["check-1", "check", "结论一", { x: 84, y: 668, w: 77, h: 72 }],
  ["check-2", "check", "结论二", { x: 607, y: 668, w: 77, h: 72 }],
  ["check-3", "check", "结论三", { x: 1093, y: 668, w: 77, h: 72 }],
  ["warning", "warning", "实验层次限定", { x: 394, y: 767, w: 60, h: 55 }],
  ["trophy", "trophy", "阶段成果", { x: 172, y: 840, w: 84, h: 82 }],
].map(([placement_id, name, semantic_meaning, source_bbox_px]) => ({
  placement_id,
  icon_id: `approved-blueprint-crop/${name}`,
  source_library: "approved-blueprint-crops",
  semantic_meaning,
  png_path: `${root}/assets/slide-08-blueprint-icons/${name}.png`,
  source_bbox_px,
  contains_key_text: false,
  powerpoint_render_verified: false,
}));

const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 8,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with a large strategy chart, right evidence rail, finding strip, caveat strip and navy conclusion band",
  layout_regions: [
    { id: "header", bbox_px: { x: 13, y: 0, w: 1637, h: 201 } },
    { id: "strategy_chart", bbox_px: { x: 15, y: 209, w: 883, h: 438 } },
    { id: "importance_and_metrics", bbox_px: { x: 912, y: 209, w: 738, h: 438 } },
    { id: "interpretation_strip", bbox_px: { x: 15, y: 657, w: 1636, h: 91 } },
    { id: "caveat_strip", bbox_px: { x: 15, y: 760, w: 1636, h: 67 } },
    { id: "conclusion_band", bbox_px: { x: 15, y: 837, w: 1636, h: 88 } },
  ],
  header_footer_system: {
    page_badge: "08",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "工作成果｜阶段性验证",
    footer: "source IDs in conclusion band",
  },
  so_what_region: { bbox_px: { x: 15, y: 837, w: 1636, h: 88 }, native_text_required: true },
  main_chart_semantics: "Four-policy mean SINR with standard-deviation error bars, feature importance ranking, two key metrics, and three evidence interpretations.",
  density_targets: {
    overall: "high",
    strategy_chart: "four bars, four uncertainty ranges, four exact data labels",
    importance_chart: "five horizontal ranked features with exact values",
    evidence_strips: "two key metrics, three findings, one experiment-level caveat",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text and formulas",
    "four-strategy bar chart and uncertainty",
    "feature importance chart",
    "two metric numbers",
    "three findings, caveat and conclusion band",
  ],
  allowed_visual_assets: iconPlacements.map((icon) => ({
    id: icon.placement_id,
    icon_id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.png_path,
    source: "Approved slide-08 blueprint crop",
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
    triggered_gates: ["error_bar_gate", "chart_semantics_gate", "icon_transparency_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All charts, values, labels and conclusions remain native; five transparent icon placements preserve exact blueprint fidelity.",
  },
};

fs.writeFileSync(`${lockDir}/slide-08-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-08-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-08-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
