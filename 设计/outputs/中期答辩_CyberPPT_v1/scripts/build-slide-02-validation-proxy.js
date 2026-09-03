const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const qaRoot = `${root}/qa/slide-02`;
const manifest = JSON.parse(fs.readFileSync(`${root}/slide_manifest.json`, "utf8"));
const slide = structuredClone(
  manifest.slides.find((entry) => entry.slide === 2)
);
if (!slide) throw new Error("Slide 2 manifest entry missing");
slide.slide = 1;
const proxyManifest = {
  ...manifest,
  slides: [slide],
};
fs.writeFileSync(
  `${qaRoot}/slide-02-manifest-single.json`,
  `${JSON.stringify(proxyManifest, null, 2)}\n`
);

const visualQa = JSON.parse(
  fs.readFileSync(`${qaRoot}/visual_qa_gate-slide-02.json`, "utf8")
);
visualQa.slides[0].slide = 1;
fs.writeFileSync(
  `${qaRoot}/visual_qa_gate-slide-02-single.json`,
  `${JSON.stringify(visualQa, null, 2)}\n`
);

const globalVisualQa = JSON.parse(
  fs.readFileSync(`${root}/visual_qa_gate.json`, "utf8")
);
const slide2Entry = structuredClone(visualQa.slides[0]);
slide2Entry.slide = 2;
globalVisualQa.slides = globalVisualQa.slides.filter(
  (entry) => entry.slide !== 2
);
globalVisualQa.slides.push(slide2Entry);
globalVisualQa.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(
  `${root}/visual_qa_gate.json`,
  `${JSON.stringify(globalVisualQa, null, 2)}\n`
);
