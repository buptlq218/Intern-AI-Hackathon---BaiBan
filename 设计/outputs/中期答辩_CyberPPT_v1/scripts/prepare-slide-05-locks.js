const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-05.png";
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
      id: "meta_layer",
      type: "native_meta_policy_architecture",
      priority: "P0",
      required_subcomponents: ["layer_label", "history", "features", "meta_rf", "confidence", "strategy_outputs"],
      must_preserve_type: true,
    },
    {
      id: "dam_band",
      type: "native_soft_guidance_band",
      priority: "P0",
      required_subcomponents: ["dam_label", "bonus_formula", "hold_rule", "vertical_connectors"],
      must_preserve_type: true,
    },
    {
      id: "execution_layer",
      type: "native_double_dqn_gru_architecture",
      priority: "P0",
      required_subcomponents: ["layer_label", "state_sequence", "double_dqn_gru", "q_bonus", "epsilon_greedy", "action_output"],
      must_preserve_type: true,
    },
    {
      id: "environment_feedback",
      type: "native_closed_loop_environment",
      priority: "P0",
      required_subcomponents: ["environment_panel", "feedback_sinr", "feedback_action", "closed_loop_arrows"],
      must_preserve_type: true,
    },
    {
      id: "time_scale_rail",
      type: "native_dual_time_scale_comparison",
      priority: "P1",
      required_subcomponents: ["panel_header", "meta_scale", "execution_scale"],
      must_preserve_type: true,
    },
    {
      id: "warning_panel",
      type: "native_engineering_caveat",
      priority: "P0",
      required_subcomponents: ["warning_icon", "caveat_text", "latency_emphasis"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["school_icon", "conclusion_text", "source_footer"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 8, 5, 92, 61, 95);
add("page_number", "P1", "text", "page_header", "page_number", 26, 12, 56, 43, 105);
add("header_deck_title", "P1", "text", "page_header", "header_title", 357, 14, 916, 41, 95);
add("section_label", "P1", "text", "page_header", "section_label", 1340, 20, 305, 32, 95);
add("top_rule", "P1", "line", "page_header", "divider", 0, 66, 1672, 4, 70);
add("main_title", "P0", "text", "narrative_header", "title", 255, 91, 1080, 45, 120);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 312, 147, 1022, 31, 110);

add("meta_layer_surface", "P0", "panel", "meta_layer", "core_panel", 15, 182, 1308, 223, 72);
add("meta_layer_label", "P0", "text_group", "meta_layer", "layer_label", 28, 238, 145, 82, 110);
const metaNodes = [
  ["meta_history", 217, 198, 179, 192],
  ["meta_features", 454, 199, 160, 190],
  ["meta_rf", 673, 201, 157, 188],
  ["meta_confidence", 892, 201, 175, 188],
  ["meta_strategy", 1152, 199, 155, 190],
];
for (const [id, x, y, w, h] of metaNodes) {
  add(id, "P0", "panel", "meta_layer", "architecture_node", x, y, w, h, 82);
  add(`${id}_title`, "P1", "text", "meta_layer", "node_title", x + 8, y + 8, w - 16, 29, 105);
}
add("meta_connectors", "P1", "connector_group", "meta_layer", "connector", 396, 269, 756, 39, 82);
add("history_chart", "P1", "chart_group", "meta_layer", "sparkline", 233, 241, 75, 52, 72);
add("history_database", "P1", "icon", "meta_layer", "icon", 326, 244, 48, 48, 100);
add("history_bullets", "P1", "text_group", "meta_layer", "body", 231, 305, 150, 74, 105);
add("feature_grid", "P1", "shape_group", "meta_layer", "feature_grid", 482, 255, 105, 84, 82);
add("feature_labels", "P1", "text_group", "meta_layer", "formula", 480, 347, 109, 29, 100);
add("meta_rf_tree", "P1", "diagram_group", "meta_layer", "classifier_tree", 700, 248, 105, 86, 80);
add("meta_rf_caption", "P1", "text", "meta_layer", "body", 690, 349, 124, 28, 100);
add("confidence_chart", "P1", "chart_group", "meta_layer", "bar_chart", 919, 250, 115, 94, 75);
add("confidence_formula", "P1", "text", "meta_layer", "formula", 918, 350, 121, 27, 100);
add("strategy_outputs", "P0", "panel_group", "meta_layer", "strategy_output", 1152, 199, 155, 190, 82);

add("dam_band_surface", "P0", "panel", "dam_band", "guidance_band", 218, 430, 997, 57, 75);
add("dam_icon", "P1", "icon", "dam_band", "icon", 379, 436, 53, 43, 100);
add("dam_label", "P0", "text", "dam_band", "module_title", 473, 440, 146, 33, 110);
add("dam_bonus", "P0", "formula", "dam_band", "formula", 670, 440, 201, 33, 110);
add("dam_hold_rule", "P0", "text", "dam_band", "rule", 908, 440, 231, 33, 110);
add("dam_dividers", "P1", "line_group", "dam_band", "divider", 630, 439, 254, 36, 75);
add("dam_vertical_connectors", "P1", "connector_group", "dam_band", "connector", 360, 389, 632, 135, 80);

add("execution_layer_surface", "P0", "panel", "execution_layer", "core_panel", 15, 510, 1308, 188, 72);
add("execution_layer_label", "P0", "text_group", "execution_layer", "layer_label", 29, 553, 142, 80, 110);
const execNodes = [
  ["exec_state", 197, 524, 187, 163],
  ["exec_dqn", 428, 524, 215, 163],
  ["exec_q_bonus", 687, 524, 174, 163],
  ["exec_epsilon", 906, 524, 165, 163],
  ["exec_output", 1117, 524, 195, 163],
];
for (const [id, x, y, w, h] of execNodes) {
  add(id, "P0", "panel", "execution_layer", "architecture_node", x, y, w, h, 82);
  add(`${id}_title`, "P1", "text", "execution_layer", "node_title", x + 8, y + 7, w - 16, 28, 105);
}
add("exec_connectors", "P1", "connector_group", "execution_layer", "connector", 384, 581, 733, 36, 82);
add("state_sequence_plot", "P1", "chart_group", "execution_layer", "sparkline", 215, 566, 150, 42, 75);
add("state_sequence_bullets", "P1", "text_group", "execution_layer", "body", 211, 616, 159, 60, 105);
add("dqn_network", "P1", "diagram_group", "execution_layer", "neural_network", 449, 561, 109, 70, 80);
add("gru_cell", "P1", "panel", "execution_layer", "gru_cell", 564, 576, 63, 53, 85);
add("dqn_caption", "P1", "text", "execution_layer", "body", 452, 643, 170, 27, 100);
add("q_bar_chart", "P1", "chart_group", "execution_layer", "bar_chart", 705, 569, 136, 77, 75);
add("q_bonus_caption", "P1", "text", "execution_layer", "formula", 711, 650, 126, 23, 100);
add("epsilon_scale", "P1", "icon", "execution_layer", "icon", 938, 563, 100, 66, 100);
add("epsilon_caption", "P1", "text", "execution_layer", "body", 920, 642, 138, 28, 100);
add("action_grid", "P1", "shape_group", "execution_layer", "action_grid", 1183, 569, 63, 62, 80);
add("action_caption", "P1", "text", "execution_layer", "body", 1139, 640, 154, 35, 100);

add("environment_panel", "P0", "panel", "environment_feedback", "environment", 304, 725, 678, 97, 78);
add("environment_title", "P0", "text", "environment_feedback", "module_title", 519, 737, 251, 32, 110);
add("environment_icons", "P1", "icon_group", "environment_feedback", "environment_icons", 368, 754, 534, 56, 100);
add("feedback_sinr", "P0", "text_group", "environment_feedback", "feedback", 157, 728, 141, 88, 105);
add("feedback_action", "P0", "text_group", "environment_feedback", "feedback", 1003, 727, 133, 91, 105);
add("feedback_left_arrow", "P1", "connector_group", "environment_feedback", "feedback_loop", 91, 401, 54, 372, 80);
add("feedback_right_arrow", "P1", "connector_group", "environment_feedback", "feedback_loop", 1131, 697, 116, 77, 80);

add("time_scale_surface", "P1", "panel", "time_scale_rail", "side_panel", 1381, 131, 266, 452, 72);
add("time_scale_header", "P1", "panel", "time_scale_rail", "module_header", 1381, 131, 266, 65, 72);
add("time_scale_title", "P1", "text", "time_scale_rail", "module_title", 1421, 150, 188, 33, 110);
add("meta_clock_icon", "P1", "icon", "time_scale_rail", "icon", 1396, 237, 91, 91, 100);
add("meta_scale_text", "P1", "text_group", "time_scale_rail", "body", 1500, 236, 132, 132, 110);
add("time_scale_divider", "P1", "line", "time_scale_rail", "divider", 1394, 400, 239, 2, 75);
add("exec_gauge_icon", "P1", "icon", "time_scale_rail", "icon", 1402, 446, 85, 76, 100);
add("exec_scale_text", "P1", "text_group", "time_scale_rail", "body", 1500, 444, 132, 99, 110);

add("warning_surface", "P0", "panel", "warning_panel", "caveat", 1375, 637, 272, 174, 75);
add("warning_icon", "P1", "icon", "warning_panel", "icon", 1395, 685, 64, 64, 100);
add("warning_title", "P1", "text", "warning_panel", "module_title", 1478, 661, 131, 29, 110);
add("warning_text", "P0", "text_group", "warning_panel", "body", 1476, 695, 146, 59, 115);
add("warning_latency", "P0", "text", "warning_panel", "emphasis", 1476, 759, 151, 27, 120);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 24, 847, 1625, 78, 72);
add("school_icon", "P1", "icon", "conclusion_band", "icon", 56, 856, 61, 61, 100);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 320, 867, 1120, 41, 120);
add("source_footer", "P1", "text", "conclusion_band", "source", 1328, 906, 283, 11, 90);

const annotations = { elements };
const cropRecords = [
  ["history-visual", "SINR折线与动作历史存储", { x: 233, y: 241, w: 147, h: 56 }],
  ["meta-rf-tree", "Meta-RF分类树", { x: 697, y: 247, w: 110, h: 91 }],
  ["confidence-chart", "策略置信度柱形图", { x: 918, y: 249, w: 122, h: 97 }],
  ["dam-gears", "DAM软引导", { x: 378, y: 434, w: 66, h: 47 }],
  ["state-sequence", "状态序列", { x: 212, y: 564, w: 160, h: 50 }],
  ["dqn-network", "Double DQN网络", { x: 444, y: 560, w: 117, h: 76 }],
  ["epsilon-scale", "探索与利用平衡", { x: 944, y: 562, w: 98, h: 70 }],
  ["action-grid", "时频联合动作网格", { x: 1179, y: 565, w: 71, h: 69 }],
  ["environment-satellite", "雷达卫星图标", { x: 366, y: 750, w: 59, h: 62 }],
  ["environment-wave", "FMCW波形图标", { x: 466, y: 752, w: 84, h: 61 }],
  ["environment-small-cars", "小型车辆目标", { x: 608, y: 766, w: 89, h: 48 }],
  ["environment-large-cars", "车辆目标", { x: 733, y: 758, w: 84, h: 57 }],
  ["environment-antenna", "环境反馈天线", { x: 853, y: 750, w: 62, h: 63 }],
  ["meta-clock", "元策略时间尺度", { x: 1393, y: 234, w: 99, h: 99 }],
  ["execution-gauge", "执行层逐chirp节奏", { x: 1397, y: 442, w: 96, h: 78 }],
  ["warning", "工程时延提示", { x: 1392, y: 682, w: 70, h: 70 }],
  ["school", "SO WHAT结论锚点", { x: 53, y: 853, w: 68, h: 68 }],
].map(([name, semantic_meaning, source_bbox_px]) => ({
  placement_id: name,
  icon_id: `approved-blueprint-crop/${name}`,
  source_library: "approved-blueprint-crops",
  semantic_meaning,
  png_path: `${root}/assets/slide-05-blueprint-icons/${name}.png`,
  source_bbox_px,
  contains_key_text: false,
  powerpoint_render_verified: false,
}));

const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 5,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with two pale-blue architecture layers, one guidance band, a right comparison rail, and a navy conclusion band",
  layout_regions: [
    { id: "header", bbox_px: { x: 8, y: 5, w: 1639, h: 173 } },
    { id: "meta_layer", bbox_px: { x: 15, y: 182, w: 1308, h: 223 } },
    { id: "dam_band", bbox_px: { x: 218, y: 430, w: 997, h: 57 } },
    { id: "execution_layer", bbox_px: { x: 15, y: 510, w: 1308, h: 188 } },
    { id: "environment_feedback", bbox_px: { x: 91, y: 697, w: 1156, h: 125 } },
    { id: "right_rail", bbox_px: { x: 1375, y: 131, w: 272, h: 680 } },
    { id: "conclusion_band", bbox_px: { x: 24, y: 847, w: 1625, h: 78 } },
  ],
  header_footer_system: {
    page_badge: "05",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "研究内容｜分层系统架构",
    footer: "source IDs in conclusion band",
  },
  so_what_region: { bbox_px: { x: 24, y: 847, w: 1625, h: 78 }, native_text_required: true },
  main_chart_semantics: "Closed-loop hierarchical architecture: Meta-RF provides confidence-weighted dimension guidance to a Double DQN+GRU execution policy through DAM Q-value biasing.",
  density_targets: {
    overall: "high",
    meta_layer: "five sequential strategic decision nodes plus three outputs",
    execution_layer: "five sequential tactical decision nodes",
    environment_feedback: "two feedback ledgers and a closed loop",
    right_rail: "two time scales plus one explicit engineering caveat",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text and formulas",
    "architecture panels and connectors",
    "feature grid and confidence bars",
    "Meta-RF tree and Q-value bars",
    "action grid and feedback loops",
    "time-scale comparison",
    "warning panel and conclusion band",
  ],
  allowed_visual_assets: cropRecords.map((icon) => ({
    id: icon.placement_id,
    icon_id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.png_path,
    source: "Approved slide-05 blueprint crop",
    source_bbox_px: icon.source_bbox_px,
    necessity: "exact restoration of the approved non-text visual symbol",
    contains_key_text: false,
    editable_information_sacrifice: false,
    trace_required: false,
  })),
  icon_style_lock: { library: "approved-blueprint-crops", style_locked: true, icons: cropRecords },
  complex_visual_scan: {
    completed: true,
    complex_visual_candidates: [],
    triggered_gates: ["architecture_gate", "icon_library_gate", "label_collision_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All architecture logic, labels, formulas and plots remain native; seventeen non-text visual crops from the approved blueprint are admitted for exact icon fidelity.",
  },
};

fs.writeFileSync(`${lockDir}/slide-05-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-05-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-05-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
