const fs = require("fs");
const crypto = require("crypto");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const contentLockPath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/slide-content-lock.json";
const signaturePath = `${root}/locks/slide-04-component-signature.json`;
const registryPath = `${root}/locks/slide-04-visual-element-registry.json`;
const planPath = `${root}/locks/slide-04-reconstruction-plan.json`;
const manifestPath = `${root}/slide_manifest.json`;
const readJson = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const sha256 = (path) =>
  crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

const manifest = readJson(manifestPath);
const registry = readJson(registryPath);
const plan = readJson(planPath);
const signature = readJson(signaturePath);
const slide = {
  slide: 4,
  role: "Resolution",
  layout_reference:
    "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-04.png",
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
    single_page_pptx_path: `${root}/pages/slide-04.pptx`,
    blueprint_render_path:
      "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-04.png",
    ppt_render_path: `${root}/renders/slide-04.png`,
    side_by_side_path: `${root}/qa/slide-04/side-by-side.png`,
    local_comparison_artifacts: [
      `${root}/qa/slide-04/header-comparison.png`,
      `${root}/qa/slide-04/mechanism-comparison.png`,
      `${root}/qa/slide-04/matrix-comparison.png`,
      `${root}/qa/slide-04/right-rail-comparison.png`,
      `${root}/qa/slide-04/conclusion-comparison.png`,
    ],
    page_status: "review_ready",
    user_confirmed: false,
    made_before_next_slide: false,
  },
  blueprint_reconstruction_plan: plan,
  expected_pictures: 6,
  image_assets: plan.allowed_visual_assets,
  text_objects: [
    { id: "page_number", role: "T1", font_size_pt: 16, editable: true },
    { id: "header_deck_title", role: "T3", font_size_pt: 11.5, editable: true },
    { id: "section_label", role: "T4", font_size_pt: 11.5, editable: true },
    { id: "main_title", role: "T2", font_size_pt: 23, editable: true },
    { id: "subtitle", role: "T3", font_size_pt: 14, editable: true },
    { id: "module_titles", role: "T4", font_size_pt: 11.5, editable: true },
    { id: "body_text", role: "T7", font_size_pt: 9.5, editable: true },
    { id: "formula_text", role: "T8", font_size_pt: 10.5, editable: true },
    { id: "table_labels", role: "T11", font_size_pt: 8.8, editable: true },
    { id: "conclusion_text", role: "T8", font_size_pt: 15.5, editable: true },
    { id: "source_footer", role: "T14", font_size_pt: 6.5, editable: true },
  ],
  native_components: [
    { id: "page_header", type: "native_text_and_shapes", reason: "仅修改页眉并保持可编辑" },
    { id: "mechanism_panel", type: "native_text_shapes_and_curves", reason: "机理流程、曲线和公式必须可编辑" },
    { id: "action_matrix", type: "native_matrix", reason: "9个动作组合必须可编辑" },
    { id: "parameter_panel", type: "native_table_shapes", reason: "参数表必须可编辑" },
    { id: "mdp_panel", type: "native_text_and_shapes", reason: "MDP定义必须可编辑" },
    { id: "conclusion_band", type: "native_text_shapes_and_library_icons", reason: "结论条必须可编辑" },
  ],
  icon_assets: plan.icon_style_lock.icons,
  label_collision_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["mechanism_panel", "action_matrix", "parameter_panel", "mdp_panel", "conclusion_band"],
    collisions: [],
    allowed_text_overlaps: [],
  },
  spatial_registration_check: {
    passed: false,
    status: "pending_powerpoint_render",
    reference_crop: `${root}/qa/slide-04/mechanism-reference.png`,
    rendered_crop: `${root}/qa/slide-04/mechanism-render.png`,
    checked_groups: [],
    failures: [],
  },
  container_overflow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["mechanism_panel", "action_matrix", "parameter_panel", "mdp_panel", "conclusion_band"],
  },
  continuous_text_flow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_text_runs: ["main_title", "subtitle", "mechanism_labels", "matrix_labels", "parameter_table", "mdp_definition", "conclusion_text"],
  },
  table_text_objects: [
    { id: "parameter_names", semantic_role: "table_label", role: "T11", font_size_pt: 8.8 },
    { id: "parameter_values", semantic_role: "table_body", role: "T7", font_size_pt: 9.5 },
    { id: "matrix_cell_labels", semantic_role: "table_label", role: "T11", font_size_pt: 8.8 },
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

manifest.slides = manifest.slides.filter((entry) => entry.slide !== 4);
manifest.slides.push(slide);
manifest.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
