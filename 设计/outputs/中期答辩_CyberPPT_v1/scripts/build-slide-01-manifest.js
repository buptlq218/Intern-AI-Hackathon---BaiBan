const fs = require("fs");
const crypto = require("crypto");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const contentLockPath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/slide-content-lock.json";
const signaturePath = `${root}/locks/slide-01-component-signature.json`;
const registryPath = `${root}/locks/slide-01-visual-element-registry.json`;
const planPath = `${root}/locks/slide-01-reconstruction-plan.json`;
const manifestPath = `${root}/slide_manifest.json`;

const readJson = (path) => JSON.parse(fs.readFileSync(path, "utf8"));
const sha256 = (path) =>
  crypto.createHash("sha256").update(fs.readFileSync(path)).digest("hex");

const registry = readJson(registryPath);
const plan = readJson(planPath);
const signature = readJson(signaturePath);

const slide = {
  slide: 1,
  role: "Cover",
  layout_reference:
    "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-01.png",
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
    single_page_pptx_path: `${root}/pages/slide-01.pptx`,
    blueprint_render_path:
      "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-01.png",
    ppt_render_path: `${root}/renders/slide-01.png`,
    side_by_side_path: `${root}/qa/slide-01/side-by-side.png`,
    local_comparison_artifacts: [
      `${root}/qa/slide-01/title-comparison.png`,
      `${root}/qa/slide-01/technical-visual-comparison.png`,
      `${root}/qa/slide-01/footer-comparison.png`,
    ],
    page_status: "review_ready",
    user_confirmed: false,
    made_before_next_slide: false,
  },
  blueprint_reconstruction_plan: plan,
  expected_pictures: 1,
  image_assets: plan.allowed_visual_assets,
  text_objects: [
    { id: "title_line_1", role: "C0", font_size_pt: 50, editable: true },
    { id: "title_line_2", role: "C0", font_size_pt: 48.2, editable: true },
    { id: "subtitle", role: "T3", font_size_pt: 24, editable: true },
    { id: "presenter_name", role: "T14", font_size_pt: 16.5, editable: true },
  ],
  native_components: [
    {
      id: "cover_typography",
      type: "native_text",
      reason: "主标题、副标题和汇报人必须可编辑",
    },
    {
      id: "cover_rule_system",
      type: "native_shapes",
      reason: "分隔线与端点使用原生形状精确对齐",
    },
  ],
  label_collision_check: {
    passed: true,
    checked_regions: ["title_zone", "presenter_zone", "technical_visual_zone"],
    collisions: [],
    allowed_text_overlaps: [],
  },
  spatial_registration_check: {
    passed: false,
    status: "pending_powerpoint_render_measurement",
    reference_crop: `${root}/qa/slide-01/technical-reference.png`,
    rendered_crop: `${root}/qa/slide-01/technical-render.png`,
    checked_groups: [],
    failures: [],
  },
  container_overflow_check: {
    passed: false,
    status: "pending_powerpoint_render_measurement",
    checked_containers: ["title_line_1", "title_line_2", "subtitle", "presenter_name"],
  },
  continuous_text_flow_check: {
    passed: false,
    status: "pending_powerpoint_render_measurement",
    checked_text: ["title_line_1", "title_line_2", "subtitle", "presenter_name"],
  },
  qa_expectations: {
    pictures_must_be_zero: false,
    all_key_text_editable: true,
    typography_scale_required: true,
    dual_gate_required: true,
    visual_semantics_required: true,
    visual_qa_required: true,
    spatial_registration_required: true,
    container_overflow_check_required: true,
    continuous_text_flow_check_required: true,
    table_semantic_typography_required: false,
    table_density_check_required: false,
  },
};

const manifest = {
  schema: "cyberppt.slide_manifest.v1",
  deck: "林渠_研究生中期答辩",
  delivery_mode: "single_page_execution",
  slides: [slide],
  final_merge: {
    method: "merge_approved_single_page_pptx",
    regenerated_pages: false,
    source_single_page_pptx: [],
    merge_regression_rendered: false,
    merge_regression_pass: false,
  },
};

fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
process.stdout.write(`${manifestPath}\n`);
