const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-06.png";
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
      id: "network_panel",
      type: "native_vertical_network_architecture",
      priority: "P0",
      required_subcomponents: ["five_network_blocks", "vertical_connectors", "hidden_state_loop", "selection_note"],
      must_preserve_type: true,
    },
    {
      id: "training_panel",
      type: "native_training_parameter_table",
      priority: "P0",
      required_subcomponents: ["eight_parameter_rows", "training_caveat"],
      must_preserve_type: true,
    },
    {
      id: "reward_panel",
      type: "native_reward_curve_and_metric_panel",
      priority: "P0",
      required_subcomponents: ["positive_reward_curve", "negative_reward_curve", "switch_penalty", "key_metric"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["conclusion_text", "source_footer"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 14, 7, 107, 63, 95);
add("page_number", "P1", "text", "page_header", "page_number", 32, 16, 61, 44, 105);
add("header_deck_title", "P1", "text", "page_header", "header_title", 449, 16, 782, 40, 100);
add("section_label", "P1", "text", "page_header", "section_label", 1368, 20, 281, 36, 100);
add("top_rule", "P1", "line", "page_header", "divider", 107, 67, 1547, 3, 70);
add("main_title", "P0", "text", "narrative_header", "title", 231, 107, 1203, 48, 120);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 383, 176, 907, 34, 110);

add("network_panel_surface", "P0", "panel", "network_panel", "core_panel", 20, 231, 540, 588, 72);
add("network_panel_header", "P1", "panel", "network_panel", "module_header", 20, 231, 540, 49, 72);
add("network_panel_title", "P1", "text", "network_panel", "module_title", 150, 242, 280, 30, 110);
const networkNodes = [
  ["network_input", 61, 299, 398, 51],
  ["network_dense16", 61, 381, 345, 52],
  ["network_gru", 61, 464, 345, 52],
  ["network_dense64", 61, 570, 345, 54],
  ["network_output", 61, 662, 345, 54],
];
for (const [id, x, y, w, h] of networkNodes) {
  add(id, "P0", "panel", "network_panel", "network_block", x, y, w, h, 82);
  add(`${id}_text`, "P1", "text", "network_panel", "network_label", x + 8, y + 8, w - 16, h - 16, 105);
}
add("network_vertical_connectors", "P1", "connector_group", "network_panel", "connector", 247, 350, 13, 312, 78);
add("hidden_state_loop", "P1", "connector_group", "network_panel", "feedback_loop", 405, 488, 84, 203, 82);
add("hidden_state_text", "P1", "text_group", "network_panel", "body", 428, 554, 117, 55, 105);
add("network_note", "P1", "text", "network_panel", "note", 46, 760, 489, 30, 105);

add("training_panel_surface", "P0", "panel", "training_panel", "core_panel", 580, 231, 424, 588, 72);
add("training_panel_header", "P1", "panel", "training_panel", "module_header", 580, 231, 424, 49, 72);
add("training_panel_title", "P1", "text", "training_panel", "module_title", 664, 242, 256, 30, 110);
add("training_table", "P0", "table", "training_panel", "training_table", 596, 299, 391, 429, 82);
const rows = ["scale", "length", "replay", "batch", "gamma", "tau", "epsilon", "lr"];
for (let i = 0; i < rows.length; i += 1) {
  add(`training_${rows[i]}_label`, "P1", "table_cell", "training_panel", "table_label", 596, 299 + i * 53.6, 157, 53.6, 90);
  add(`training_${rows[i]}_value`, "P1", "table_cell", "training_panel", "table_value", 753, 299 + i * 53.6, 234, 53.6, 90);
}
add("training_note", "P0", "text_group", "training_panel", "caveat", 598, 750, 379, 53, 110);

add("reward_panel_surface", "P0", "panel", "reward_panel", "core_panel", 1029, 231, 622, 588, 72);
add("reward_panel_header", "P1", "panel", "reward_panel", "module_header", 1029, 231, 622, 49, 72);
add("reward_panel_title", "P1", "text", "reward_panel", "module_title", 1190, 242, 300, 30, 110);
add("positive_reward_heading", "P1", "text", "reward_panel", "chart_title", 1066, 301, 267, 29, 105);
add("negative_reward_heading", "P1", "text", "reward_panel", "chart_title", 1370, 301, 259, 29, 105);
add("positive_reward_chart", "P0", "chart_group", "reward_panel", "main_chart", 1050, 333, 290, 253, 65);
add("negative_reward_chart", "P0", "chart_group", "reward_panel", "main_chart", 1353, 333, 290, 253, 65);
add("switch_penalty_panel", "P0", "panel", "reward_panel", "reward_constraint", 1049, 603, 580, 99, 80);
add("switch_penalty_title", "P1", "text", "reward_panel", "module_title", 1130, 611, 416, 33, 110);
add("switch_penalty_formula", "P1", "formula", "reward_panel", "formula", 1133, 653, 383, 42, 110);
add("metric_separator", "P1", "line", "reward_panel", "divider", 1040, 719, 598, 2, 70);
add("metric_label", "P0", "text", "reward_panel", "metric_label", 1050, 746, 257, 46, 115);
add("metric_value", "P0", "text", "reward_panel", "key_metric", 1309, 735, 277, 66, 125);
add("metric_unit", "P1", "text", "reward_panel", "unit", 1584, 762, 45, 32, 105);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 20, 843, 1633, 84, 72);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 390, 859, 900, 51, 120);
add("source_footer", "P1", "text", "conclusion_band", "source", 1330, 910, 278, 12, 90);

const annotations = { elements };
const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 6,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with three ruled analysis panels and one navy conclusion band",
  layout_regions: [
    { id: "header", bbox_px: { x: 14, y: 7, w: 1639, h: 203 } },
    { id: "network_panel", bbox_px: { x: 20, y: 231, w: 540, h: 588 } },
    { id: "training_panel", bbox_px: { x: 580, y: 231, w: 424, h: 588 } },
    { id: "reward_panel", bbox_px: { x: 1029, y: 231, w: 622, h: 588 } },
    { id: "conclusion_band", bbox_px: { x: 20, y: 843, w: 1633, h: 84 } },
  ],
  header_footer_system: {
    page_badge: "06",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "研究内容｜DRL执行层",
    footer: "source IDs in conclusion band",
  },
  so_what_region: { bbox_px: { x: 20, y: 843, w: 1633, h: 84 }, native_text_required: true },
  main_chart_semantics: "Double DQN+GRU network, training mechanism ledger, piecewise reward curves, switch penalty, and final joint-policy SINR.",
  density_targets: {
    overall: "high",
    network_panel: "five network blocks and one recurrent hidden-state loop",
    training_panel: "eight complete parameter rows plus a training evidence caveat",
    reward_panel: "two reward curves, switch penalty, and a high-emphasis metric",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text and formulas",
    "five-block network architecture",
    "eight-row training table",
    "positive and negative reward curves",
    "switch penalty formula",
    "key metric and conclusion band",
  ],
  allowed_visual_assets: [],
  icon_style_lock: { library: "none", style_locked: true, icons: [] },
  complex_visual_scan: {
    completed: true,
    complex_visual_candidates: [],
    triggered_gates: ["curve_geometry_gate", "table_density_gate", "label_collision_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All visible content is rebuilt as native editable PowerPoint text, shapes, connectors and curves; no picture objects are needed.",
  },
};

fs.writeFileSync(`${lockDir}/slide-06-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-06-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-06-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
