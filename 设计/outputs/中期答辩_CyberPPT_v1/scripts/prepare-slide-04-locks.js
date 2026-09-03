const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-04.png";
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
      id: "mechanism_panel",
      type: "native_dechirp_lpf_mechanism",
      priority: "P0",
      required_subcomponents: ["process_labels", "chirp_plot", "received_plot", "mix_formula", "beat_spectrum", "lpf_band", "principle_band"],
      must_preserve_type: true,
    },
    {
      id: "action_matrix",
      type: "native_3x3_action_matrix",
      priority: "P0",
      required_subcomponents: ["carrier_headers", "delay_headers", "nine_cells", "mapping_note", "caveat"],
      must_preserve_type: true,
    },
    {
      id: "parameter_panel",
      type: "native_key_parameter_table",
      priority: "P1",
      required_subcomponents: ["panel_header", "five_parameter_rows"],
      must_preserve_type: true,
    },
    {
      id: "mdp_panel",
      type: "native_mdp_definition_panel",
      priority: "P0",
      required_subcomponents: ["state", "action_mapping", "reward_and_depth"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["so_what_anchor", "conclusion_text", "three_implications", "source"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 26, 0, 56, 52, 90);
add("page_number", "P1", "text", "page_header", "page_number", 36, 7, 37, 35, 100);
add("header_deck_title", "P1", "text", "page_header", "header_title", 102, 12, 489, 27, 85);
add("section_label", "P1", "text", "page_header", "section_label", 1426, 12, 199, 27, 90);
add("top_rule", "P1", "line", "page_header", "divider", 102, 45, 1544, 3, 70);
add("main_title", "P0", "text", "narrative_header", "title", 70, 72, 1133, 48, 120);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 70, 126, 684, 35, 110);

add("mechanism_panel_surface", "P0", "panel", "mechanism_panel", "core_panel", 28, 170, 794, 585, 70);
add("mechanism_top_banner", "P1", "panel", "mechanism_panel", "module_header", 153, 183, 536, 37, 70);
add("mechanism_top_banner_text", "P1", "text", "mechanism_panel", "module_title", 169, 188, 505, 27, 105);
const stages = [
  ["stage_tx", 38, 232, 120, 64],
  ["stage_rx", 38, 330, 120, 63],
  ["stage_dechirp", 38, 408, 120, 52],
  ["stage_spectrum", 38, 470, 120, 62],
  ["stage_lpf", 38, 568, 120, 57],
];
for (const [id, x, y, w, h] of stages) {
  add(id, "P1", "text_panel", "mechanism_panel", "process_stage", x, y, w, h, 95);
}
add("stage_arrows", "P1", "connector_group", "mechanism_panel", "connector", 84, 295, 22, 274, 80);
add("chirp_plot", "P1", "chart_group", "mechanism_panel", "chart_curve", 204, 226, 565, 80, 65);
add("received_plot", "P1", "chart_group", "mechanism_panel", "chart_curve", 204, 314, 565, 83, 65);
add("mix_formula", "P1", "formula", "mechanism_panel", "formula", 244, 412, 451, 36, 100);
add("beat_spectrum", "P1", "chart_group", "mechanism_panel", "main_chart", 204, 458, 565, 108, 60);
add("lpf_spectrum", "P1", "chart_group", "mechanism_panel", "main_chart", 204, 569, 565, 70, 60);
add("principle_band", "P0", "panel", "mechanism_panel", "so_what", 39, 653, 768, 90, 70);
add("principle_label", "P1", "text_panel", "mechanism_panel", "module_title", 47, 664, 101, 67, 100);
add("principle_formula", "P1", "formula", "mechanism_panel", "formula", 166, 674, 190, 47, 100);
add("principle_explanation", "P1", "text_group", "mechanism_panel", "body", 365, 670, 244, 55, 100);
add("principle_condition", "P1", "formula_panel", "mechanism_panel", "formula", 617, 658, 173, 79, 100);

add("matrix_panel_surface", "P0", "panel", "action_matrix", "core_panel", 842, 170, 456, 585, 70);
add("matrix_header", "P1", "panel", "action_matrix", "module_header", 856, 187, 430, 37, 70);
add("matrix_title", "P1", "text", "action_matrix", "module_title", 874, 191, 393, 28, 105);
add("matrix_carrier_axis", "P1", "text", "action_matrix", "axis_label", 994, 245, 186, 30, 100);
add("matrix_delay_axis", "P1", "text", "action_matrix", "axis_label", 848, 328, 39, 217, 100);
add("matrix_column_headers", "P1", "text_group", "action_matrix", "axis_label", 915, 284, 349, 31, 100);
add("matrix_row_headers", "P1", "text_group", "action_matrix", "axis_label", 879, 336, 39, 270, 100);
const matrixCells = [
  [1, 922, 325], [2, 1041, 325], [3, 1161, 325],
  [4, 922, 435], [5, 1041, 435], [6, 1161, 435],
  [7, 922, 544], [8, 1041, 544], [9, 1161, 544],
];
for (const [n, x, y] of matrixCells) {
  add(`matrix_cell_${n}`, "P1", "panel", "action_matrix", "matrix_cell", x, y, 109, 99, 80);
  add(`matrix_cell_${n}_text`, "P1", "text_group", "action_matrix", "matrix_cell_text", x + 7, y + 13, 95, 67, 100);
}
add("matrix_note_panel", "P1", "panel", "action_matrix", "note", 871, 664, 409, 72, 75);
add("matrix_note_icon", "P1", "icon", "action_matrix", "icon", 889, 680, 42, 42, 100);
add("matrix_note_text", "P1", "text_group", "action_matrix", "body", 949, 675, 314, 50, 100);

add("parameter_panel_surface", "P1", "panel", "parameter_panel", "core_panel", 1311, 170, 318, 260, 70);
add("parameter_header", "P1", "panel", "parameter_panel", "module_header", 1350, 187, 235, 37, 70);
add("parameter_title", "P1", "text", "parameter_panel", "module_title", 1373, 191, 188, 28, 105);
add("parameter_table", "P1", "table", "parameter_panel", "table_body", 1325, 236, 289, 181, 85);

add("mdp_panel_surface", "P0", "panel", "mdp_panel", "core_panel", 1311, 441, 318, 314, 70);
add("mdp_header", "P1", "panel", "mdp_panel", "module_header", 1352, 454, 232, 37, 70);
add("mdp_title", "P1", "text", "mdp_panel", "module_title", 1373, 458, 190, 28, 105);
add("mdp_state_block", "P1", "text_group", "mdp_panel", "body", 1327, 499, 284, 91, 100);
add("mdp_action_block", "P1", "text_group", "mdp_panel", "body", 1327, 598, 284, 87, 100);
add("mdp_depth_block", "P1", "text_group", "mdp_panel", "body", 1327, 692, 284, 46, 100);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 29, 769, 1612, 117, 70);
add("so_what_anchor", "P1", "icon_text_group", "conclusion_band", "so_what_icon", 55, 786, 139, 85, 100);
add("conclusion_bulb", "P1", "icon", "conclusion_band", "so_what_icon", 234, 796, 60, 60, 100);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 299, 809, 686, 45, 120);
add("conclusion_chevrons", "P1", "shape_group", "conclusion_band", "connector", 1008, 812, 39, 37, 90);
add("implication_success", "P1", "icon_text_group", "conclusion_band", "body", 1060, 793, 187, 72, 100);
add("implication_adaptation", "P1", "icon_text_group", "conclusion_band", "body", 1262, 793, 175, 72, 100);
add("implication_burden", "P1", "icon_text_group", "conclusion_band", "body", 1452, 793, 166, 72, 100);
add("source_footer", "P1", "text", "conclusion_band", "source", 1170, 868, 430, 12, 90);

const annotations = { elements };
const icons = [
  ["tabler-outline/cube", "动作组合选择"],
  ["tabler-outline/target", "SO WHAT锚点"],
  ["tabler-outline/bulb", "联合空间启示"],
  ["tabler-outline/target", "避干扰成功率"],
  ["tabler-outline/chart-area-line", "环境适应性"],
  ["tabler-outline/compass", "探索负担"],
].map(([icon_id, semantic_meaning]) => ({
  icon_id,
  source_library: "tabler-outline",
  semantic_meaning,
  svg_path: `${root}/assets/icons/${icon_id}.svg`,
  viewBox: "0 0 24 24",
  powerpoint_render_verified: false,
}));

const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 4,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with three ruled analysis regions and a navy conclusion band",
  layout_regions: [
    { id: "header", bbox_px: { x: 26, y: 0, w: 1620, h: 161 } },
    { id: "mechanism_panel", bbox_px: { x: 28, y: 170, w: 794, h: 585 } },
    { id: "action_matrix", bbox_px: { x: 842, y: 170, w: 456, h: 585 } },
    { id: "parameter_mdp", bbox_px: { x: 1311, y: 170, w: 318, h: 585 } },
    { id: "conclusion_band", bbox_px: { x: 29, y: 769, w: 1612, h: 117 } },
  ],
  header_footer_system: {
    page_badge: "04",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "研究内容｜机理与建模",
    footer: "source IDs in conclusion band",
  },
  so_what_region: { bbox_px: { x: 29, y: 769, w: 1612, h: 117 }, native_text_required: true },
  main_chart_semantics: "Dechirp beat-frequency shifting and LPF rejection, coupled with a 3x3 fc/td action matrix and MDP definition",
  density_targets: {
    overall: "high",
    mechanism_panel: "five-stage signal flow plus two spectra and principle strip",
    action_matrix: "3x3 cells with exact carrier/delay combinations",
    parameter_mdp: "five-row parameter ledger plus three MDP definitions",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text and formulas",
    "waveforms and spectra",
    "LPF passband",
    "3x3 action matrix",
    "parameter table",
    "MDP definition",
    "bottom conclusion band",
  ],
  allowed_visual_assets: icons.map((icon) => ({
    id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.svg_path,
    source: "CyberPPT tabler-outline icon library",
    necessity: "consistent line-art icon semantics",
    contains_key_text: false,
    editable_information_sacrifice: false,
    trace_required: false,
  })),
  icon_style_lock: { library: "tabler-outline", style_locked: true, icons },
  complex_visual_scan: {
    completed: true,
    complex_visual_candidates: [],
    triggered_gates: ["precise_curve_gate", "table_density_gate", "icon_library_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All charts, formulas, matrix cells and tables are rebuilt natively; only six non-text library icons are admitted.",
  },
};

fs.writeFileSync(`${lockDir}/slide-04-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-04-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-04-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
