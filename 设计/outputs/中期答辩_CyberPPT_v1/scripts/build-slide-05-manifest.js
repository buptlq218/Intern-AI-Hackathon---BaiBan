const fs = require("fs");
const crypto = require("crypto");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const contentLockPath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/slide-content-lock.json";
const signaturePath = `${root}/locks/slide-05-component-signature.json`;
const registryPath = `${root}/locks/slide-05-visual-element-registry.json`;
const planPath = `${root}/locks/slide-05-reconstruction-plan.json`;
const manifestPath = `${root}/slide_manifest.json`;
const readJson = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const sha256 = (path) =>
  crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

const manifest = readJson(manifestPath);
const registry = readJson(registryPath);
const plan = readJson(planPath);
const signature = readJson(signaturePath);
const slide = {
  slide: 5,
  role: "Resolution",
  layout_reference:
    "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-05.png",
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
    single_page_pptx_path: `${root}/pages/slide-05.pptx`,
    blueprint_render_path:
      "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-05.png",
    ppt_render_path: `${root}/renders/slide-05.png`,
    side_by_side_path: `${root}/qa/slide-05/side-by-side.png`,
    local_comparison_artifacts: [
      `${root}/qa/slide-05/header-comparison.png`,
      `${root}/qa/slide-05/meta-layer-comparison.png`,
      `${root}/qa/slide-05/dam-execution-comparison.png`,
      `${root}/qa/slide-05/environment-comparison.png`,
      `${root}/qa/slide-05/right-rail-comparison.png`,
      `${root}/qa/slide-05/conclusion-comparison.png`,
    ],
    page_status: "building",
    user_confirmed: false,
    made_before_next_slide: false,
  },
  blueprint_reconstruction_plan: plan,
  expected_pictures: 17,
  image_assets: plan.allowed_visual_assets,
  text_objects: [
    { id: "page_number", role: "T1", font_size_pt: 18, editable: true },
    { id: "header_deck_title", role: "T3", font_size_pt: 24.5, editable: true },
    { id: "section_label", role: "T4", font_size_pt: 12.5, editable: true },
    { id: "main_title", role: "T2", font_size_pt: 22, editable: true },
    { id: "subtitle", role: "T3", font_size_pt: 13, editable: true },
    { id: "layer_labels", role: "T4", font_size_pt: 12, editable: true },
    { id: "node_titles", role: "T6", font_size_pt: 11, editable: true },
    { id: "node_body", role: "T7", font_size_pt: 9.5, editable: true },
    { id: "dam_formula", role: "T8", font_size_pt: 11, editable: true },
    { id: "right_rail_text", role: "T7", font_size_pt: 9.5, editable: true },
    { id: "warning_text", role: "T7", font_size_pt: 9.5, editable: true },
    { id: "conclusion_text", role: "T10", font_size_pt: 17.5, editable: true },
    { id: "source_footer", role: "T14", font_size_pt: 6.5, editable: true },
  ],
  native_components: [
    { id: "page_header", type: "native_text_and_shapes", reason: "页眉系统必须保持可编辑" },
    { id: "meta_layer", type: "native_text_shapes_charts_and_connectors", reason: "战略判断流程与置信度必须可编辑" },
    { id: "dam_band", type: "native_text_formula_and_connectors", reason: "软引导公式和保持规则必须可编辑" },
    { id: "execution_layer", type: "native_text_shapes_charts_and_connectors", reason: "执行层网络、Q值和动作映射必须可编辑" },
    { id: "environment_feedback", type: "native_text_shapes_connectors_and_library_icons", reason: "闭环反馈必须可编辑" },
    { id: "time_scale_rail", type: "native_text_shapes_and_library_icons", reason: "双时间尺度比较必须可编辑" },
    { id: "warning_panel", type: "native_text_shapes_and_library_icon", reason: "工程时延限定必须可编辑" },
    { id: "conclusion_band", type: "native_text_shape_and_library_icon", reason: "结论条必须可编辑" },
  ],
  icon_assets: plan.icon_style_lock.icons,
  label_collision_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["meta_layer", "dam_band", "execution_layer", "environment_feedback", "time_scale_rail", "warning_panel", "conclusion_band"],
    collisions: [],
    allowed_text_overlaps: [],
  },
  spatial_registration_check: {
    passed: false,
    status: "pending_powerpoint_render",
    reference_crop: `${root}/qa/slide-05/meta-layer-reference.png`,
    rendered_crop: `${root}/qa/slide-05/meta-layer-render.png`,
    checked_groups: [],
    failures: [],
  },
  container_overflow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["meta_layer", "dam_band", "execution_layer", "environment_feedback", "time_scale_rail", "warning_panel", "conclusion_band"],
  },
  continuous_text_flow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_text_runs: ["main_title", "subtitle", "meta_layer_labels", "dam_rules", "execution_layer_labels", "feedback_ledgers", "time_scale_text", "warning_text", "conclusion_text"],
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

manifest.slides = manifest.slides.filter((entry) => entry.slide !== 5);
manifest.slides.push(slide);
manifest.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
