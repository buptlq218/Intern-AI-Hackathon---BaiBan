const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const manifestPath = `${root}/slide_manifest.json`;
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const slide = manifest.slides.find((entry) => entry.slide === 5);
if (!slide) throw new Error("Slide 5 manifest entry missing");
slide.page_execution.page_status = "approved";
slide.page_execution.user_confirmed = true;
slide.page_execution.made_before_next_slide = true;
slide.page_execution.approval_recorded_at = "2026-07-23";
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

const proxyPath = `${root}/qa/slide-05/slide-05-manifest-single.json`;
const proxy = JSON.parse(fs.readFileSync(proxyPath, "utf8"));
proxy.slides[0].page_execution.page_status = "approved";
proxy.slides[0].page_execution.user_confirmed = true;
proxy.slides[0].page_execution.made_before_next_slide = true;
proxy.slides[0].page_execution.approval_recorded_at = "2026-07-23";
fs.writeFileSync(proxyPath, `${JSON.stringify(proxy, null, 2)}\n`);
