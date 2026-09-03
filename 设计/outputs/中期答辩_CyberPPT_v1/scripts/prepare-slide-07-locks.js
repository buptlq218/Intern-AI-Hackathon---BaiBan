const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-07.png";
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
      id: "feature_matrix",
      type: "native_four_group_feature_matrix",
      priority: "P0",
      required_subcomponents: ["four_feature_groups", "dimension_counts", "twelve_feature_bracket"],
      must_preserve_type: true,
    },
    {
      id: "rf_pipeline",
      type: "native_random_forest_training_pipeline",
      priority: "P0",
      required_subcomponents: ["six_training_stages", "stage_connectors", "training_parameters"],
      must_preserve_type: true,
    },
    {
      id: "strategy_panel",
      type: "native_three_strategy_table",
      priority: "P0",
      required_subcomponents: ["strategy_table", "confidence_column", "soft_guidance", "accuracy_caveat"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_panel",
      type: "native_so_what_panel",
      priority: "P0",
      required_subcomponents: ["conclusion_icon", "core_statement", "explanation", "source_footer"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 0, 0, 120, 73, 95);
add("page_number", "P1", "text", "page_header", "page_number", 23, 11, 58, 45, 105);
add("header_deck_title", "P1", "text", "page_header", "header_title", 437, 18, 781, 38, 100);
add("section_label", "P1", "text", "page_header", "section_label", 1338, 21, 305, 35, 100);
add("top_rule", "P1", "line", "page_header", "divider", 0, 72, 1672, 4, 70);
add("main_title", "P0", "text", "narrative_header", "title", 182, 99, 1327, 51, 120);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 391, 163, 923, 38, 110);

const featureRows = [
  ["signal", 31, 233, 469, 126],
  ["action", 31, 360, 469, 145],
  ["avoid", 31, 506, 469, 108],
  ["sensitivity", 31, 615, 469, 107],
];
for (const [id, x, y, w, h] of featureRows) {
  add(`feature_${id}_row`, "P0", "group", "feature_matrix", "feature_group", x, y, w, h, 78);
  add(`feature_${id}_icon`, "P1", "picture", "feature_matrix", "icon", x + 16, y + 18, 90, Math.min(94, h - 25), 100);
  add(`feature_${id}_title`, "P1", "text", "feature_matrix", "group_title", x + 145, y + 25, 280, 32, 110);
  add(`feature_${id}_formula`, "P1", "formula", "feature_matrix", "formula", x + 145, y + 66, 285, h - 72, 110);
}
add("feature_dimension_counts", "P1", "text_group", "feature_matrix", "dimension_count", 455, 260, 44, 429, 105);
add("feature_bracket", "P1", "connector_group", "feature_matrix", "bracket", 500, 233, 130, 490, 82);
add("feature_total_label", "P0", "text", "feature_matrix", "total_features", 540, 448, 80, 72, 110);

add("rf_panel_surface", "P0", "panel", "rf_pipeline", "core_panel", 631, 223, 347, 510, 72);
add("rf_panel_header", "P1", "panel", "rf_pipeline", "module_header", 631, 223, 347, 55, 72);
add("rf_panel_title", "P1", "text", "rf_pipeline", "module_title", 671, 238, 270, 31, 110);
const rfStages = [
  ["scenes", 656, 292, 296, 57],
  ["split", 656, 367, 296, 57],
  ["cv", 656, 442, 296, 57],
  ["trees", 656, 518, 296, 57],
  ["depth", 656, 590, 296, 57],
  ["accuracy", 656, 665, 296, 57],
];
for (const [id, x, y, w, h] of rfStages) {
  add(`rf_${id}_stage`, "P0", "panel", "rf_pipeline", "pipeline_stage", x, y, w, h, 82);
  add(`rf_${id}_icon`, "P1", "picture", "rf_pipeline", "icon", x + 10, y - 3, 68, h + 8, 100);
  add(`rf_${id}_text`, "P1", "text", "rf_pipeline", "stage_label", x + 92, y + 8, 185, h - 16, 110);
}
add("rf_connectors", "P1", "connector_group", "rf_pipeline", "connector", 690, 349, 126, 316, 82);

add("strategy_table_header", "P1", "panel", "strategy_panel", "module_header", 1053, 223, 570, 55, 72);
add("strategy_table_title", "P1", "text", "strategy_panel", "module_title", 1120, 238, 437, 31, 110);
add("strategy_table", "P0", "table", "strategy_panel", "strategy_table", 1053, 292, 570, 217, 82);
add("strategy_row_1", "P1", "table_row", "strategy_panel", "strategy_row", 1053, 341, 570, 56, 90);
add("strategy_row_2", "P1", "table_row", "strategy_panel", "strategy_row", 1053, 397, 570, 56, 90);
add("strategy_row_3", "P1", "table_row", "strategy_panel", "strategy_row", 1053, 453, 570, 56, 90);
add("soft_guidance_surface", "P0", "panel", "strategy_panel", "guidance", 1053, 530, 570, 145, 78);
add("soft_guidance_icon", "P1", "picture", "strategy_panel", "icon", 1063, 546, 98, 98, 100);
add("soft_guidance_text", "P0", "text_group", "strategy_panel", "guidance_text", 1175, 545, 420, 117, 110);
add("accuracy_caveat_surface", "P0", "panel", "strategy_panel", "caveat", 1044, 684, 587, 64, 78);
add("accuracy_caveat_icon", "P1", "picture", "strategy_panel", "icon", 1051, 691, 56, 52, 100);
add("accuracy_caveat_text", "P0", "text", "strategy_panel", "caveat_text", 1114, 694, 500, 43, 110);
add("rf_to_strategy_arrow", "P1", "connector_group", "strategy_panel", "connector", 978, 449, 74, 44, 82);
add("strategy_vertical_separator", "P1", "line", "strategy_panel", "divider", 1014, 219, 2, 535, 72);

add("conclusion_panel_surface", "P0", "panel", "conclusion_panel", "so_what", 35, 775, 1596, 113, 78);
add("conclusion_icon", "P1", "picture", "conclusion_panel", "icon", 61, 792, 76, 76, 100);
add("conclusion_statement", "P0", "text", "conclusion_panel", "core_statement", 169, 805, 742, 53, 120);
add("conclusion_divider", "P1", "line", "conclusion_panel", "divider", 931, 790, 2, 84, 72);
add("conclusion_explanation", "P0", "text_group", "conclusion_panel", "body", 965, 799, 607, 65, 110);
add("source_footer", "P1", "text", "conclusion_panel", "source", 1325, 869, 280, 12, 90);

const annotations = { elements };
const cropSpecs = [
  ["feature-signal", "信号质量统计", { x: 48, y: 253, w: 90, h: 90 }],
  ["feature-action", "动作行为", { x: 47, y: 382, w: 89, h: 94 }],
  ["feature-shield", "避干扰效能", { x: 52, y: 518, w: 76, h: 85 }],
  ["feature-target", "维度敏感性", { x: 47, y: 625, w: 83, h: 85 }],
  ["rf-database", "4000场景", { x: 668, y: 289, w: 62, h: 62 }],
  ["rf-pie", "训练测试划分", { x: 669, y: 366, w: 61, h: 62 }],
  ["rf-clipboard", "交叉验证", { x: 669, y: 441, w: 61, h: 64 }],
  ["rf-trees", "随机森林树", { x: 666, y: 519, w: 67, h: 60 }],
  ["rf-gear", "树深参数", { x: 668, y: 593, w: 63, h: 63 }],
  ["rf-target", "分类准确率", { x: 669, y: 666, w: 62, h: 62 }],
  ["guidance-bulb", "软引导", { x: 1063, y: 546, w: 98, h: 98 }],
  ["warning", "准确率限定", { x: 1051, y: 691, w: 56, h: 52 }],
  ["conclusion-check", "SO WHAT", { x: 61, y: 792, w: 76, h: 76 }],
].map(([name, semantic_meaning, source_bbox_px]) => ({
  placement_id: name,
  icon_id: `approved-blueprint-crop/${name}`,
  source_library: "approved-blueprint-crops",
  semantic_meaning,
  png_path: `${root}/assets/slide-07-blueprint-icons/${name}.png`,
  source_bbox_px,
  contains_key_text: false,
  powerpoint_render_verified: false,
}));

const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 7,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with a left feature ledger, central RF pipeline, right strategy ledger, and bordered conclusion panel",
  layout_regions: [
    { id: "header", bbox_px: { x: 0, y: 0, w: 1643, h: 201 } },
    { id: "feature_matrix", bbox_px: { x: 31, y: 233, w: 599, h: 490 } },
    { id: "rf_pipeline", bbox_px: { x: 631, y: 223, w: 347, h: 510 } },
    { id: "strategy_panel", bbox_px: { x: 1014, y: 219, w: 617, h: 535 } },
    { id: "conclusion_panel", bbox_px: { x: 35, y: 775, w: 1596, h: 113 } },
  ],
  header_footer_system: {
    page_badge: "07",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "研究内容｜元策略控制器",
    footer: "source IDs in conclusion panel",
  },
  so_what_region: { bbox_px: { x: 35, y: 775, w: 1596, h: 113 }, native_text_required: true },
  main_chart_semantics: "Twelve semantic features feed a random-forest meta-policy classifier, which outputs three confidence-weighted exploration strategies and soft guidance.",
  density_targets: {
    overall: "high",
    feature_matrix: "four semantic feature groups and exact 4+3+2+3 dimension counts",
    rf_pipeline: "six classifier training stages",
    strategy_panel: "three-row strategy table, guidance formula, persistence and accuracy caveat",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text and formulas",
    "four feature groups and bracket",
    "six-stage RF training pipeline",
    "three-row strategy table",
    "soft guidance and accuracy caveat",
    "bottom conclusion panel",
  ],
  allowed_visual_assets: cropSpecs.map((icon) => ({
    id: icon.placement_id,
    icon_id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.png_path,
    source: "Approved slide-07 blueprint crop",
    source_bbox_px: icon.source_bbox_px,
    necessity: "exact restoration of the approved non-text visual symbol",
    contains_key_text: false,
    editable_information_sacrifice: false,
    trace_required: false,
  })),
  icon_style_lock: { library: "approved-blueprint-crops", style_locked: true, icons: cropSpecs },
  complex_visual_scan: {
    completed: true,
    complex_visual_candidates: [],
    triggered_gates: ["table_density_gate", "icon_transparency_gate", "label_collision_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All labels, formulas, tables and connectors remain native; thirteen transparent non-text crops from the approved blueprint preserve exact icon fidelity.",
  },
};

fs.writeFileSync(`${lockDir}/slide-07-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-07-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-07-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
