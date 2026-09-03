const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-10.png";
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
      id: "three_stage_timeline",
      type: "native_timeline_with_transparent_stage_icons",
      priority: "P0",
      required_subcomponents: ["stage_icons", "flow_arrows", "stage_titles", "status_dividers"],
      must_preserve_type: true,
    },
    {
      id: "progress_task_lists",
      type: "native_task_lists_with_transparent_icons",
      priority: "P0",
      required_subcomponents: ["completed_tasks", "writing_tasks", "defense_tasks"],
      must_preserve_type: true,
    },
    {
      id: "conclusion_band",
      type: "native_so_what_band",
      priority: "P0",
      required_subcomponents: ["transparent_clipboard_icon", "conclusion_text", "caveat_footer", "source_footer"],
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
add("page_badge", "P1", "shape", "page_header", "page_badge", 9, 8, 83, 51, 95);
add("page_number", "P1", "text", "page_header", "page_number", 20, 10, 48, 46, 110);
add("header_deck_title", "P1", "text", "page_header", "header_title", 448, 14, 775, 46, 105);
add("section_label", "P1", "text", "page_header", "section_label", 1390, 14, 247, 44, 105);
add("top_rule", "P1", "line", "page_header", "divider", 9, 64, 1653, 4, 72);
add("main_title", "P0", "text", "narrative_header", "title", 282, 101, 1107, 61, 125);
add("subtitle", "P0", "text", "narrative_header", "subtitle", 442, 174, 790, 47, 115);

add("timeline_background", "P0", "panel", "three_stage_timeline", "timeline_surface", 61, 301, 1545, 464, 72);
add("timeline_flow", "P1", "line_group", "three_stage_timeline", "flow_arrows", 371, 290, 870, 31, 82);
add("stage_complete_icon", "P0", "picture", "three_stage_timeline", "stage_icon", 208, 222, 168, 168, 100);
add("stage_writing_icon", "P0", "picture", "three_stage_timeline", "stage_icon", 748, 222, 166, 168, 100);
add("stage_defense_icon", "P0", "picture", "three_stage_timeline", "stage_icon", 1263, 222, 166, 169, 100);
add("stage_titles", "P0", "text_group", "three_stage_timeline", "stage_titles", 209, 394, 1235, 57, 120);
add("stage_dividers", "P1", "line_group", "three_stage_timeline", "status_dividers", 125, 449, 1402, 10, 78);
add("stage_statuses", "P0", "text_group", "three_stage_timeline", "stage_statuses", 190, 463, 1274, 39, 120);

add("completed_task_icons", "P1", "picture_group", "progress_task_lists", "task_icons", 128, 506, 46, 245, 100);
add("completed_task_text", "P0", "text_group", "progress_task_lists", "task_list", 190, 504, 292, 247, 115);
add("writing_task_icons", "P1", "picture_group", "progress_task_lists", "task_icons", 650, 520, 53, 199, 100);
add("writing_task_text", "P0", "text_group", "progress_task_lists", "task_list", 728, 518, 280, 201, 115);
add("defense_task_icons", "P1", "picture_group", "progress_task_lists", "task_icons", 1173, 509, 55, 234, 100);
add("defense_task_text", "P0", "text_group", "progress_task_lists", "task_list", 1252, 507, 286, 236, 115);
add("task_separators", "P1", "line_group", "progress_task_lists", "row_separators", 115, 553, 1429, 198, 74);

add("conclusion_band_surface", "P0", "panel", "conclusion_band", "so_what", 61, 772, 1545, 101, 76);
add("conclusion_icon", "P1", "picture", "conclusion_band", "clipboard_icon", 151, 781, 95, 82, 100);
add("conclusion_text", "P0", "text", "conclusion_band", "so_what_text", 322, 790, 1185, 64, 125);
add("footer_info_icon", "P1", "picture", "conclusion_band", "info_icon", 608, 890, 36, 36, 100);
add("footer_caveat", "P1", "text", "conclusion_band", "caveat", 650, 886, 453, 42, 115);
add("source_footer", "P1", "text", "conclusion_band", "source", 1340, 915, 275, 12, 92);

const annotations = { elements };
const iconSpecs = [
  ["stage-complete", "完成状态节点", { x: 208, y: 222, w: 168, h: 168 }],
  ["stage-writing", "论文撰写状态节点", { x: 748, y: 222, w: 166, h: 168 }],
  ["stage-defense", "答辩验收状态节点", { x: 1263, y: 222, w: 166, h: 169 }],
  ["done-signal", "FMCW环境任务", { x: 129, y: 506, w: 44, h: 44 }],
  ["done-brain", "执行层任务", { x: 129, y: 557, w: 44, h: 43 }],
  ["done-layers", "元策略任务", { x: 128, y: 606, w: 46, h: 46 }],
  ["done-chart", "实验任务", { x: 128, y: 657, w: 46, h: 43 }],
  ["done-document", "材料任务", { x: 129, y: 706, w: 44, h: 45 }],
  ["doing-book", "论文主线任务", { x: 650, y: 520, w: 53, h: 44 }],
  ["doing-chart", "实验图表任务", { x: 651, y: 591, w: 53, h: 47 }],
  ["doing-clipboard", "局限性任务", { x: 651, y: 664, w: 51, h: 55 }],
  ["next-document", "论文定稿任务", { x: 1176, y: 509, w: 47, h: 50 }],
  ["next-presentation", "答辩演示任务", { x: 1174, y: 577, w: 51, h: 42 }],
  ["next-question", "预演问答任务", { x: 1173, y: 633, w: 55, h: 45 }],
  ["next-shield", "答辩验收任务", { x: 1175, y: 691, w: 50, h: 52 }],
  ["conclusion-clipboard", "成果闭环结论", { x: 151, y: 781, w: 95, h: 82 }],
  ["footer-info", "阶段表达限定", { x: 608, y: 890, w: 36, h: 36 }],
];
const iconPlacements = iconSpecs.map(([name, semantic_meaning, source_bbox_px]) => ({
  placement_id: name,
  icon_id: `approved-blueprint-crop/${name}`,
  source_library: "approved-blueprint-crops",
  semantic_meaning,
  png_path: `${root}/assets/slide-10-blueprint-icons/${name}.png`,
  source_bbox_px,
  contains_key_text: false,
  powerpoint_render_verified: false,
}));

const plan = {
  schema: "cyberppt.blueprint_reconstruction_plan.v1",
  slide: 10,
  blueprint_path: blueprint,
  canvas_size: { width_px: 1672, height_px: 941, width_in: 13.333, height_in: 7.5 },
  background_color_sample: "#FCFAF5",
  surface_system: "continuous ivory paper with a three-stage pale-blue timeline and full-width navy takeaway band",
  layout_regions: [
    { id: "header", bbox_px: { x: 9, y: 8, w: 1653, h: 213 } },
    { id: "timeline", bbox_px: { x: 61, y: 222, w: 1545, h: 543 } },
    { id: "completed_tasks", bbox_px: { x: 115, y: 394, w: 367, h: 357 } },
    { id: "writing_tasks", bbox_px: { x: 636, y: 394, w: 372, h: 325 } },
    { id: "defense_tasks", bbox_px: { x: 1160, y: 394, w: 384, h: 349 } },
    { id: "conclusion_band", bbox_px: { x: 61, y: 772, w: 1545, h: 155 } },
  ],
  header_footer_system: {
    page_badge: "10",
    deck_title: "基于分层强化学习的FMCW雷达抗干扰策略优化",
    section_label: "计划与进度安排",
    footer: "stage-expression caveat and source note",
  },
  so_what_region: { bbox_px: { x: 61, y: 772, w: 1545, h: 101 }, native_text_required: true },
  main_chart_semantics: "Three-stage timeline communicating completed experiments, ongoing thesis writing, and next-stage defense acceptance.",
  density_targets: {
    overall: "medium",
    completed_stage: "five concise task rows",
    writing_stage: "three concise task rows",
    defense_stage: "four concise task rows",
  },
  anchor_targets: elements.map((entry) => ({ element_id: entry.element_id, bbox_px: entry.blueprint_bbox_px })),
  native_rebuild_targets: [
    "all visible text",
    "timeline background and flow arrows",
    "stage titles, statuses and task separators",
    "task lists and final takeaway band",
  ],
  allowed_visual_assets: iconPlacements.map((icon) => ({
    id: icon.placement_id,
    icon_id: icon.icon_id,
    region: icon.semantic_meaning,
    asset_path: icon.png_path,
    source: "Approved slide-10 blueprint crop",
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
    triggered_gates: ["timeline_semantics_gate", "icon_transparency_gate", "spatial_registration_gate"],
    pictures_zero_is_not_goal: true,
    result: "All text, timeline flow, separators and conclusion remain native; seventeen transparent icon placements preserve exact blueprint fidelity.",
  },
};

fs.writeFileSync(`${lockDir}/slide-10-components.json`, `${JSON.stringify(components, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-10-annotations.json`, `${JSON.stringify(annotations, null, 2)}\n`);
fs.writeFileSync(`${lockDir}/slide-10-reconstruction-plan.json`, `${JSON.stringify(plan, null, 2)}\n`);
