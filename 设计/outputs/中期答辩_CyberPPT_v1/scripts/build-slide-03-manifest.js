const fs = require("fs");
const crypto = require("crypto");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const contentLockPath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/slide-content-lock.json";
const signaturePath = `${root}/locks/slide-03-component-signature.json`;
const registryPath = `${root}/locks/slide-03-visual-element-registry.json`;
const planPath = `${root}/locks/slide-03-reconstruction-plan.json`;
const manifestPath = `${root}/slide_manifest.json`;
const readJson = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const sha256 = (path) =>
  crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

const manifest = readJson(manifestPath);
const registry = readJson(registryPath);
const plan = readJson(planPath);
const signature = readJson(signaturePath);
const slide = {
  slide: 3,
  role: "Complication",
  layout_reference:
    "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-03.png",
  slide_content_lock: {
    path: contentLockPath,
    sha256: sha256(contentLockPath),
    locked: true,
  },
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
    single_page_pptx_path: `${root}/pages/slide-03.pptx`,
    blueprint_render_path:
      "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-03.png",
    ppt_render_path: `${root}/renders/slide-03.png`,
    side_by_side_path: `${root}/qa/slide-03/side-by-side.png`,
    local_comparison_artifacts: [
      `${root}/qa/slide-03/header-comparison.png`,
      `${root}/qa/slide-03/issue-tree-comparison.png`,
      `${root}/qa/slide-03/route-comparison.png`,
      `${root}/qa/slide-03/objective-comparison.png`,
      `${root}/qa/slide-03/conclusion-comparison.png`,
    ],
    page_status: "review_ready",
    user_confirmed: false,
    made_before_next_slide: false,
  },
  blueprint_reconstruction_plan: plan,
  expected_pictures: 15,
  image_assets: plan.allowed_visual_assets,
  text_objects: [
    { id: "page_number", role: "T1", font_size_pt: 16, editable: true },
    { id: "header_deck_title", role: "T3", font_size_pt: 11.5, editable: true },
    { id: "section_label", role: "T4", font_size_pt: 12, editable: true },
    { id: "main_title", role: "T2", font_size_pt: 23, editable: true },
    { id: "subtitle", role: "T3", font_size_pt: 14.5, editable: true },
    { id: "module_titles", role: "T4", font_size_pt: 13.5, editable: true },
    { id: "body_text", role: "T7", font_size_pt: 10.5, editable: true },
    { id: "route_text", role: "T7", font_size_pt: 9.6, editable: true },
    { id: "conclusion_text", role: "T8", font_size_pt: 18.5, editable: true },
  ],
  native_components: [
    { id: "page_header", type: "native_text_and_shapes", reason: "页眉必须可编辑" },
    { id: "issue_tree", type: "native_text_shapes_and_connectors", reason: "三分支问题树必须可编辑" },
    { id: "central_framework", type: "native_text_and_shapes", reason: "框架收敛区必须可编辑" },
    { id: "objective_rail", type: "native_text_and_shapes", reason: "研究目标侧栏必须可编辑" },
    { id: "technical_route", type: "native_text_shapes_and_connectors", reason: "四阶段路线必须可编辑" },
    { id: "conclusion_band", type: "native_text_and_shapes", reason: "SO WHAT结论条必须可编辑" },
  ],
  icon_assets: plan.icon_style_lock.icons,
  label_collision_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["issue_tree", "objective_rail", "technical_route", "conclusion_band"],
    collisions: [],
    allowed_text_overlaps: [],
  },
  spatial_registration_check: {
    passed: false,
    status: "pending_powerpoint_render",
    reference_crop: `${root}/qa/slide-03/issue-tree-reference.png`,
    rendered_crop: `${root}/qa/slide-03/issue-tree-render.png`,
    checked_groups: [],
    failures: [],
  },
  container_overflow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_regions: ["issue_tree", "central_framework", "objective_rail", "technical_route", "conclusion_band"],
  },
  continuous_text_flow_check: {
    passed: false,
    status: "pending_powerpoint_render",
    checked_text_runs: ["main_title", "subtitle", "issue_bodies", "route_bodies", "objective_bodies", "conclusion_text"],
  },
  table_text_objects: [],
  table_density_check: { passed: true, status: "not_applicable" },
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

manifest.slides = manifest.slides.filter((entry) => entry.slide !== 3);
manifest.slides.push(slide);
manifest.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
