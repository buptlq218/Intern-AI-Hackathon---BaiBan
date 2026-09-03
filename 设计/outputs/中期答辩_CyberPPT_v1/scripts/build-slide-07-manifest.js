const fs = require("fs");
const crypto = require("crypto");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const contentLockPath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/slide-content-lock.json";
const signaturePath = `${root}/locks/slide-07-component-signature.json`;
const registryPath = `${root}/locks/slide-07-visual-element-registry.json`;
const planPath = `${root}/locks/slide-07-reconstruction-plan.json`;
const manifestPath = `${root}/slide_manifest.json`;
const readJson = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const sha256 = (path) =>
  crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

const manifest = readJson(manifestPath);
const registry = readJson(registryPath);
const plan = readJson(planPath);
const signature = readJson(signaturePath);
const slide = {
  slide: 7,
  role: "Resolution",
  layout_reference:
    "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-07.png",
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
    single_page_pptx_path: `${root}/pages/slide-07.pptx`,
    blueprint_render_path:
      "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-07.png",
    ppt_render_path: `${root}/renders/slide-07.png`,
    side_by_side_path: `${root}/qa/slide-07/side-by-side.png`,
    local_comparison_artifacts: [
      `${root}/qa/slide-07/header-comparison.png`,
      `${root}/qa/slide-07/features-comparison.png`,
      `${root}/qa/slide-07/rf-comparison.png`,
      `${root}/qa/slide-07/strategy-comparison.png`,
      `${root}/qa/slide-07/conclusion-comparison.png`,
    ],
    page_status: "building",
    user_confirmed: false,
    made_before_next_slide: false,
  },
  blueprint_reconstruction_plan: plan,
  expected_pictures: 13,
  image_assets: plan.allowed_visual_assets,
  text_objects: [
    { id: "page_number", role: "T1", font_size_pt: 20, editable: true },
    { id: "header_deck_title", role: "T3", font_size_pt: 20, editable: true },
    { id: "section_label", role: "T4", font_size_pt: 12.5, editable: true },
    { id: "main_title", role: "T2", font_size_pt: 25, editable: true },
    { id: "subtitle", role: "T3", font_size_pt: 14.5, editable: true },
    { id: "module_titles", role: "T4", font_size_pt: 12.5, editable: true },
    { id: "feature_group_titles", role: "T6", font_size_pt: 11, editable: true },
    { id: "body_text", role: "T7", font_size_pt: 9.5, editable: true },
    { id: "formula_text", role: "T8", font_size_pt: 11, editable: true },
    { id: "table_labels", role: "T11", font_size_pt: 8.5, editable: true },
    { id: "conclusion_text", role: "T10", font_size_pt: 17.5, editable: true },
    { id: "source_footer", role: "T14", font_size_pt: 6.5, editable: true },
  ],
  native_components: [
    { id: "page_header", type: "native_text_and_shapes", reason: "页眉系统必须可编辑" },
    { id: "feature_matrix", type: "native_text_formulas_connectors_and_transparent_crops", reason: "12维特征与维度计数必须可编辑" },
    { id: "rf_pipeline", type: "native_text_shapes_connectors_and_transparent_crops", reason: "RF训练流程和参数必须可编辑" },
    { id: "strategy_panel", type: "native_table_text_formula_and_transparent_crops", reason: "三元策略、置信度与软引导必须可编辑" },
    { id: "conclusion_panel", type: "native_text_shape_and_transparent_crop", reason: "结论解释必须可编辑" },
  ],
  icon_assets: plan.icon_style_lock.icons,
  label_collision_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["feature_matrix", "rf_pipeline", "strategy_panel", "conclusion_panel"],
    collisions: [],
    allowed_text_overlaps: [],
  },
  spatial_registration_check: {
    passed: false,
    status: "pending_powerpoint_render",
    reference_crop: `${root}/qa/slide-07/strategy-reference.png`,
    rendered_crop: `${root}/qa/slide-07/strategy-render.png`,
    checked_groups: [],
    failures: [],
  },
  container_overflow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["feature_matrix", "rf_pipeline", "strategy_panel", "conclusion_panel"],
  },
  continuous_text_flow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_text_runs: ["main_title", "subtitle", "feature_labels", "rf_pipeline_labels", "strategy_table", "guidance", "caveat", "conclusion_text"],
  },
  table_text_objects: [
    { id: "strategy_headers", semantic_role: "table_label", role: "T11", font_size_pt: 8.5 },
    { id: "strategy_body", semantic_role: "table_body", role: "T7", font_size_pt: 9.5 },
  ],
  table_density_check: { passed: false, status: "pending_powerpoint_render", checked_cells: [] },
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
    table_semantic_typography_required: true,
    table_density_check_required: true,
  },
};

manifest.slides = manifest.slides.filter((entry) => entry.slide !== 7);
manifest.slides.push(slide);
manifest.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
