const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-03.png";
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
      type: "native_conclusion_title_and_subtitle",
      priority: "P0",
      required_subcomponents: ["main_title", "subtitle"],
      must_preserve_type: true,
    },
    {
      id: "issue_tree",
      type: "three_branch_native_issue_tree",
      priority: "P0",
      required_subcomponents: [
        "time_scale_branch",
        "structure_branch",
        "exploration_branch",
        "evidence_and_response_labels",
        "convergence_connectors",
      ],
      must_preserve_type: true,
    },
    {
      id: "central_framework",
      type: "native_framework_convergence_panel",
      priority: "P0",
      required_subcomponents: ["framework_title", "framework_icon", "framework_rationale"],
      must_preserve_type: true,
    },
    {
      id: "objective_rail",
      type: "three_group_native_objective_rail",
      priority: "P0",
      required_subcomponents: ["performance", "recovery", "interpretability"],
      must_preserve_type: true,
    },
    {
      id: "technical_route",
      type: "four_stage_native_route",
      priority: "P0",
      required_subcomponents: ["modeling", "execution", "cognition", "validation"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["trophy_icon", "conclusion_text", "supporting_checks"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 0, 3, 92, 55, 90);
add("page_number", "P1", "text", "page_header", "page_number", 24, 10, 46, 40, 100);
add("header_deck_title", "P1", "text", "page_header", "header_title", 507, 17, 557, 31, 85);
add("section_label", "P1", "text", "page_header", "section_label", 1272, 17, 368, 31, 90);
add("top_rule", "P1", "line", "page_header", "divider", 0, 57, 1660, 3, 70);
add("main_title", "P0", "text", "narrative_header", "title", 148, 77, 1374, 41, 120);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 327, 128, 1016, 37, 110);
add("evidence_label", "P1", "text", "issue_tree", "row_label", 25, 281, 52, 35, 100);
add("response_label", "P1", "text", "issue_tree", "row_label", 25, 400, 52, 35, 100);

const branches = [
  { id: "time", x: 89, w: 363 },
  { id: "structure", x: 505, w: 363 },
  { id: "exploration", x: 928, w: 391 },
];
for (const branch of branches) {
  add(`${branch.id}_header_panel`, "P1", "panel", "issue_tree", "branch_header", branch.x, 177, branch.w, 56, 75);
  add(`${branch.id}_header_icon`, "P1", "icon", "issue_tree", "icon", branch.x + 28, 184, 43, 43, 100);
  add(`${branch.id}_header_title`, "P1", "text", "issue_tree", "module_title", branch.x + 92, 188, branch.w - 112, 34, 110);
  add(`${branch.id}_down_arrow_1`, "P1", "connector", "issue_tree", "connector", branch.x + branch.w / 2 - 8, 232, 16, 23, 80);
  add(`${branch.id}_evidence_panel`, "P1", "panel", "issue_tree", "evidence", branch.x - 18, 255, branch.w + 36, 94, 75);
  add(`${branch.id}_evidence_text`, "P1", "text", "issue_tree", "body", branch.x, 266, branch.w, 70, 100);
  add(`${branch.id}_down_arrow_2`, "P1", "connector", "issue_tree", "connector", branch.x + branch.w / 2 - 8, 349, 16, 22, 80);
  add(`${branch.id}_response_panel`, "P1", "panel", "issue_tree", "response", branch.x - 18, 372, branch.w + 36, 99, 65);
  add(`${branch.id}_response_icon`, "P1", "icon", "issue_tree", "icon", branch.x, 390, 61, 61, 100);
  add(`${branch.id}_response_text`, "P1", "text", "issue_tree", "body", branch.x + 75, 382, branch.w - 58, 78, 100);
}
add("convergence_connectors", "P1", "connector_group", "issue_tree", "main_flow", 259, 470, 866, 50, 70);
add("framework_panel", "P0", "panel", "central_framework", "core_panel", 327, 519, 813, 86, 65);
add("framework_icon", "P1", "icon", "central_framework", "icon", 371, 528, 70, 67, 100);
add("framework_title", "P0", "text", "central_framework", "main_flow_title", 476, 541, 335, 43, 115);
add("framework_rationale", "P1", "text_group", "central_framework", "body", 858, 529, 257, 62, 100);
add("framework_to_objective", "P1", "connector", "objective_rail", "connector", 1345, 282, 48, 280, 80);

add("objective_rail_panel", "P0", "panel", "objective_rail", "core_panel", 1402, 107, 245, 518, 70);
add("objective_rail_title", "P1", "text", "objective_rail", "module_title", 1402, 110, 245, 39, 110);
const objectives = [
  { id: "performance", y: 150, h: 175 },
  { id: "recovery", y: 326, h: 157 },
  { id: "interpretability", y: 484, h: 140 },
];
for (const objective of objectives) {
  add(`${objective.id}_icon`, "P1", "icon", "objective_rail", "icon", 1418, objective.y + 19, 55, 55, 100);
  add(`${objective.id}_title`, "P1", "text", "objective_rail", "module_title", 1488, objective.y + 19, 142, 34, 105);
  add(`${objective.id}_body`, "P1", "text_group", "objective_rail", "body", 1488, objective.y + 54, 142, objective.h - 61, 100);
}
add("objective_separator_1", "P1", "line", "objective_rail", "divider", 1407, 325, 230, 2, 70);
add("objective_separator_2", "P1", "line", "objective_rail", "divider", 1407, 482, 230, 2, 70);

add("route_label", "P1", "text", "technical_route", "row_label", 14, 659, 70, 89, 100);
const routes = [
  { id: "modeling", x: 98, w: 336 },
  { id: "execution", x: 483, w: 371 },
  { id: "cognition", x: 901, w: 318 },
  { id: "validation", x: 1264, w: 304 },
];
for (const route of routes) {
  add(`${route.id}_panel`, "P1", "panel", "technical_route", "route_stage", route.x, 630, route.w, 145, 70);
  add(`${route.id}_icon`, "P1", "icon", "technical_route", "icon", route.x + 15, 650, 65, 91, 100);
  add(`${route.id}_title`, "P1", "text", "technical_route", "module_title", route.x + 89, 647, route.w - 104, 32, 105);
  add(`${route.id}_body`, "P1", "text_group", "technical_route", "body", route.x + 89, 682, route.w - 104, 73, 100);
}
add("route_arrow_1", "P1", "connector", "technical_route", "connector", 440, 685, 37, 30, 90);
add("route_arrow_2", "P1", "connector", "technical_route", "connector", 859, 685, 37, 30, 90);
add("route_arrow_3", "P1", "connector", "technical_route", "connector", 1224, 685, 37, 30, 90);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 30, 796, 1610, 129, 70);
add("conclusion_trophy_icon", "P1", "icon", "conclusion_band", "so_what_icon", 49, 814, 80, 88, 100);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 149, 828, 676, 53, 120);
add("conclusion_divider", "P1", "line", "conclusion_band", "divider", 852, 810, 2, 98, 70);
add("conclusion_support", "P1", "text_group", "conclusion_band", "body", 892, 807, 695, 103, 100);

const annotations = { elements };

const icons = [
  ["tabler-outline/clock", "时间尺度矛盾"],
  ["tabler-outline/puzzle", "结构信息缺失"],
  ["tabler-outline/chart-bar-popular", "动态探索低效"],
  ["tabler-outline/hierarchy", "分层决策"],
  ["tabler-outline/eye", "结构感知"],
  ["tabler-outline/target", "元策略引导"],
  ["tabler-outline/atom", "分层强化学习框架"],
  ["tabler-outline/shield-check", "性能与稳定性"],
  ["tabler-outline/clock-bolt", "突变恢复速度"],
  ["tabler-outline/brain", "可解释性"],
  ["tabler-outline/antenna", "物理机理与POMDP建模"],
  ["tabler-outline/cpu", "Double DQN与GRU执行"],
  ["tabler-outline/brain", "Meta-RF元控制"],
  ["tabler-outline/flask", "多场景实验验证"],
  ["tabler-outline/trophy", "研究贡献"],
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
  slide: 3,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with navy response blocks, ruled objective rail and thin connectors",
  layout_regions: [
    { id: "header", bbox_px: { x: 0, y: 0, w: 1672, h: 166 } },
    { id: "issue_tree", bbox_px: { x: 14, y: 177, w: 1305, h: 294 } },
    { id: "central_framework", bbox_px: { x: 327, y: 519, w: 813, h: 86 } },
    { id: "objective_rail", bbox_px: { x: 1345, y: 107, w: 302, h: 518 } },
    { id: "technical_route", bbox_px: { x: 14, y: 630, w: 1554, h: 145 } },
    { id: "conclusion_band", bbox_px: { x: 30, y: 796, w: 1610, h: 129 } },
  ],
  header_footer_system: {
    page_badge: "03",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "研究内容｜研究问题与技术路线",
    footer: "none",
  },
  so_what_region: {
    bbox_px: { x: 30, y: 796, w: 1610, h: 129 },
    native_text_required: true,
  },
  main_chart_semantics: "three issue branches converge into a hierarchical reinforcement learning framework and continue through a four-stage technical route",
  density_targets: {
    overall: "high",
    issue_tree: "three headers plus evidence and response blocks",
    objective_rail: "three objectives with icons and evidence bullets",
    technical_route: "four linked stages with concise descriptors",
  },
  anchor_targets: elements.map((entry) => ({
    element_id: entry.element_id,
    bbox_px: entry.blueprint_bbox_px,
  })),
  native_rebuild_targets: [
    "all visible text",
    "all panels and dashed evidence boxes",
    "all connectors and arrows",
    "issue tree",
    "objective rail",
    "technical route",
    "conclusion band",
  ],
  allowed_visual_assets: icons.map((icon) => ({
    id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.svg_path,
    source: "CyberPPT tabler-outline icon library",
    necessity: "maintain consistent line-art icon semantics without hand-drawn approximations",
    contains_key_text: false,
    editable_information_sacrifice: false,
    trace_required: false,
  })),
  icon_style_lock: {
    library: "tabler-outline",
    style_locked: true,
    icons,
  },
  complex_visual_scan: {
    completed: true,
    complex_visual_candidates: [],
    triggered_gates: ["icon_library_gate", "label_collision_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "No photo or complex infographic asset is admitted; only verified non-text SVG icons are used.",
  },
};

fs.writeFileSync(`${lockDir}/slide-03-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-03-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-03-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
