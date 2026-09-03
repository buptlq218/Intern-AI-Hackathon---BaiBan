const fs = require("fs");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const qaRoot = `${root}/qa/slide-04`;
const manifest = JSON.parse(fs.readFileSync(`${root}/slide_manifest.json`, "utf8"));
const slide = structuredClone(manifest.slides.find((entry) => entry.slide === 4));
if (!slide) throw new Error("Slide 4 manifest entry missing");
slide.slide = 1;
fs.writeFileSync(
  `${qaRoot}/slide-04-manifest-single.json`,
  `${JSON.stringify({ ...manifest, slides: [slide] }, null, 2)}\n`
);

const visualQa = JSON.parse(
  fs.readFileSync(`${qaRoot}/visual_qa_gate-slide-04.json`, "utf8")
);
visualQa.slides[0].slide = 1;
fs.writeFileSync(
  `${qaRoot}/visual_qa_gate-slide-04-single.json`,
  `${JSON.stringify(visualQa, null, 2)}\n`
);

const globalQa = JSON.parse(fs.readFileSync(`${root}/visual_qa_gate.json`, "utf8"));
const slide4Entry = structuredClone(visualQa.slides[0]);
slide4Entry.slide = 4;
globalQa.slides = globalQa.slides.filter((entry) => entry.slide !== 4);
globalQa.slides.push(slide4Entry);
globalQa.slides.sort((a, b) => a.slide - b.slide);
fs.writeFileSync(
  `${root}/visual_qa_gate.json`,
  `${JSON.stringify(globalQa, null, 2)}\n`
);
