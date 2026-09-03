const fs = require("fs");
const crypto = require("crypto");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const contentLockPath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/slide-content-lock.json";
const signaturePath = `${root}/locks/slide-08-component-signature.json`;
const registryPath = `${root}/locks/slide-08-visual-element-registry.json`;
const planPath = `${root}/locks/slide-08-reconstruction-plan.json`;
const manifestPath = `${root}/slide_manifest.json`;
const readJson = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const sha256 = (path) =>
  crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

const manifest = readJson(manifestPath);
const registry = readJson(registryPath);
const plan = readJson(planPath);
const signature = readJson(signaturePath);
const slide = {
  slide: 8,
  role: "成果",
  layout_reference:
    "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-08.png",
  slide_content_lock: { path: contentLockPath, sha256: sha256(contentLockPath), locked: true },
  blueprint_component_signature: {
    path: signaturePath,
    sha256: sha256(signaturePath),
    locked: signature.locked === true,
    components: signature.components,
  },
  visual_element_registry: registry.elements,
  visual_element_inventory: registry.elements,
  blueprint_measurement_table: {
    path: registryPath,
    blueprint_canvas_px: registry.blueprint_canvas_px,
    ppt_canvas_in: registry.ppt_canvas_in,
    scale_x: registry.scale_x,
    scale_y: registry.scale_y,
  },
  generation_engine: {
    tool: "pptxgenjs",
    version: "4.0.1",
    fallback_reason: null,
    visual_fidelity_not_reduced: true,
  },
  page_execution: {
    mode: "single_page",
    single_page_pptx_path: `${root}/pages/slide-08.pptx`,
    blueprint_render_path:
      "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-08.png",
    ppt_render_path: `${root}/renders/slide-08.png`,
    side_by_side_path: `${root}/qa/slide-08/side-by-side.png`,
    local_comparison_artifacts: [
      `${root}/qa/slide-08/header-comparison.png`,
      `${root}/qa/slide-08/strategy-chart-comparison.png`,
      `${root}/qa/slide-08/evidence-rail-comparison.png`,
      `${root}/qa/slide-08/findings-comparison.png`,
      `${root}/qa/slide-08/conclusion-comparison.png`,
    ],
    page_status: "building",
    user_confirmed: false,
    made_before_next_slide: false,
  },
  blueprint_reconstruction_plan: plan,
  expected_pictures: 5,
  image_assets: plan.allowed_visual_assets,
  text_objects: [
    { id: "page_number", role: "T1", font_size_pt: 20, editable: true },
    { id: "header_deck_title", role: "T3", font_size_pt: 20, editable: true },
    { id: "section_label", role: "T4", font_size_pt: 12.5, editable: true },
    { id: "main_title", role: "T2", font_size_pt: 25, editable: true },
    { id: "subtitle", role: "T3", font_size_pt: 14.5, editable: true },
    { id: "chart_titles", role: "T4", font_size_pt: 12.5, editable: true },
    { id: "axis_labels", role: "T11", font_size_pt: 8.5, editable: true },
    { id: "data_labels", role: "T12", font_size_pt: 9.5, editable: true },
    { id: "metric_values", role: "T13", font_size_pt: 28, editable: true },
    { id: "body_text", role: "T7", font_size_pt: 9.5, editable: true },
    { id: "conclusion_text", role: "T10", font_size_pt: 18, editable: true },
    { id: "source_footer", role: "T14", font_size_pt: 6.5, editable: true },
  ],
  native_components: [
    { id: "page_header", type: "native_text_and_shapes", reason: "页眉系统必须可编辑" },
    { id: "strategy_chart", type: "native_bars_error_bars_axes_and_labels", reason: "均值、标准差和数据标签必须可编辑" },
    { id: "importance_chart", type: "native_horizontal_bars_and_labels", reason: "特征重要性排序必须可编辑" },
    { id: "key_metrics", type: "native_text_and_shapes", reason: "关键数字必须可编辑" },
    { id: "interpretation_strip", type: "native_text_shapes_and_transparent_crops", reason: "实验解读必须可编辑" },
    { id: "caveat_strip", type: "native_text_shape_and_transparent_crop", reason: "实验层次限定必须可编辑" },
    { id: "conclusion_band", type: "native_text_shape_and_transparent_crop", reason: "结论条必须可编辑" },
  ],
  icon_assets: plan.icon_style_lock.icons,
  label_collision_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["strategy_chart", "importance_chart", "key_metrics", "interpretation_strip", "caveat_strip", "conclusion_band"],
    collisions: [],
    allowed_text_overlaps: [],
  },
  spatial_registration_check: {
    passed: false,
    status: "pending_powerpoint_render",
    reference_crop: `${root}/qa/slide-08/strategy-chart-reference.png`,
    rendered_crop: `${root}/qa/slide-08/strategy-chart-render.png`,
    checked_groups: [],
    failures: [],
  },
  container_overflow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["strategy_chart", "importance_chart", "key_metrics", "interpretation_strip", "caveat_strip", "conclusion_band"],
  },
  continuous_text_flow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_text_runs: ["main_title", "subtitle", "chart_labels", "metric_labels", "findings", "caveat", "conclusion_text"],
  },
  table_text_objects: [],
  table_density_check: { passed: true, status: "not_applicable", checked_cells: [] },
  qa_expectations: {
    pictures_must_be_zero: false,
    all_key_text_editable: true,
    typography_scale_required: true,
    dual_gate_required: true,
    visual_semantics_required: true,
    visual_qa_required: true,
    label_collision_check_required: true,
    spatial_registration_required: true,
    container_overflow_check_required: true,
    continuous_text_flow_check_required: true,
    table_semantic_typography_required: false,
    table_density_check_required: false,
  },
};

manifest.slides = manifest.slides.filter((entry) => entry.slide !== 8);
manifest.slides.push(slide);
manifest.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
