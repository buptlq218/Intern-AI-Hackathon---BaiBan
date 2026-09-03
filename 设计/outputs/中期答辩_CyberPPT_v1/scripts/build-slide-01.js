const pptxgen = require("pptxgenjs");

const OUTPUT =
  "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1/pages/slide-01.pptx";
const ART =
  "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1/assets/slide-01-technical-visual.png";

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "林渠";
pptx.subject = "研究生中期答辩";
pptx.title = "基于分层强化学习的FMCW雷达抗干扰策略优化";
pptx.company = "";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "PingFang SC",
  bodyFontFace: "PingFang SC",
  lang: "zh-CN",
};
pptx.defineSlideMaster({
  title: "COVER_IVORY",
  background: { color: "FCFAF5" },
  objects: [],
});

const slide = pptx.addSlide("COVER_IVORY");
slide.background = { color: "FCFAF5" };

const placements = [];
const addPlacement = (id, x, y, w, h, allowOverlap = false) => {
  placements.push({ id, x, y, w, h, allowOverlap });
};

function warnIfSlideElementsOutOfBounds(items, width = 13.333, height = 7.5) {
  for (const item of items) {
    if (
      item.x < 0 ||
      item.y < 0 ||
      item.w <= 0 ||
      item.h <= 0 ||
      item.x + item.w > width + 0.001 ||
      item.y + item.h > height + 0.001
    ) {
      process.stderr.write(`OUT_OF_BOUNDS ${item.id}\n`);
    }
  }
}

function warnIfSlideHasOverlaps(items) {
  for (let i = 0; i < items.length; i += 1) {
    for (let j = i + 1; j < items.length; j += 1) {
      const a = items[i];
      const b = items[j];
      const overlap =
        a.x < b.x + b.w &&
        a.x + a.w > b.x &&
        a.y < b.y + b.h &&
        a.y + a.h > b.y;
      if (overlap && !(a.allowOverlap || b.allowOverlap)) {
        process.stderr.write(`UNEXPECTED_OVERLAP ${a.id} ${b.id}\n`);
      }
    }
  }
}

// Intentional overlap: the transparent, non-text technical visual sits behind
// the native title and rule system. Its protected text zone is transparent.
slide.addImage({
  path: ART,
  x: 3.0301,
  y: 0.3029,
  w: 10.3029,
  h: 6.8852,
  transparency: 0,
});
addPlacement("technical_visual_asset", 3.0301, 0.3029, 10.3029, 6.8852, true);

const titleStyle = {
  fontFace: "PingFang SC",
  fontSize: 50,
  bold: true,
  color: "00152F",
  margin: 0,
  breakLine: false,
  valign: "mid",
  fit: "shrink",
  charSpacing: 0.25,
  paraSpaceAfterPt: 0,
  lineSpacingMultiple: 1,
};

slide.addText("基于分层强化学习的", {
  x: 0.7737,
  y: 1.7136,
  w: 6.365,
  h: 0.78,
  ...titleStyle,
  charSpacing: 0.55,
});
addPlacement("title_line_1", 0.7737, 1.7136, 6.365, 0.78);

slide.addText("FMCW雷达抗干扰策略优化", {
  x: 0.7817,
  y: 2.5829,
  w: 8.14,
  h: 0.78,
  ...titleStyle,
  fontSize: 48.2,
});
addPlacement("title_line_2", 0.7817, 2.5829, 8.14, 0.78);

slide.addShape(pptx.ShapeType.rect, {
  x: 0.7977,
  y: 3.6188,
  w: 0.4785,
  h: 0.0558,
  line: { color: "12355B", transparency: 100 },
  fill: { color: "12355B" },
});
addPlacement("title_accent_rule", 0.7977, 3.6188, 0.4785, 0.0558);

slide.addShape(pptx.ShapeType.rect, {
  x: 1.2765,
  y: 3.643,
  w: 7.5065,
  h: 0.012,
  line: { color: "C9CDD1", transparency: 100 },
  fill: { color: "C9CDD1" },
});
addPlacement("title_hairline", 1.2765, 3.636, 7.5065, 0.014);

slide.addText("研究生中期答辩", {
  x: 0.8057,
  y: 3.9687,
  w: 2.6402,
  h: 0.3985,
  fontFace: "PingFang SC",
  fontSize: 24,
  bold: true,
  color: "12355B",
  margin: 0,
  valign: "mid",
  fit: "shrink",
  charSpacing: 0.3,
});
addPlacement("subtitle", 0.8057, 3.9687, 2.6402, 0.3985);

slide.addShape(pptx.ShapeType.rect, {
  x: 0.7977,
  y: 5.0771,
  w: 0.1675,
  h: 0.1674,
  line: { color: "12355B", transparency: 100 },
  fill: { color: "12355B" },
});
addPlacement("presenter_bullet", 0.7977, 5.0771, 0.1675, 0.1674);

slide.addText("汇报人：林渠", {
  x: 1.1569,
  y: 4.9894,
  w: 1.675,
  h: 0.3348,
  fontFace: "PingFang SC",
  fontSize: 16.5,
  bold: false,
  color: "101820",
  margin: 0,
  valign: "mid",
  fit: "shrink",
});
addPlacement("presenter_name", 1.1569, 4.9894, 1.675, 0.3348);

slide.addShape(pptx.ShapeType.rect, {
  x: 0.5108,
  y: 7.0935,
  w: 12.315,
  h: 0.0159,
  line: { color: "8DA3BA", transparency: 100 },
  fill: { color: "8DA3BA", transparency: 0 },
});
addPlacement("bottom_rule", 0.5108, 7.0865, 12.315, 0.014, true);

slide.addShape(pptx.ShapeType.rect, {
  x: 0.5187,
  y: 7.0696,
  w: 0.0638,
  h: 0.0638,
  line: { color: "12355B", transparency: 100 },
  fill: { color: "12355B" },
});
addPlacement("bottom_left_endpoint", 0.5187, 7.0696, 0.0638, 0.0638, true);

slide.addShape(pptx.ShapeType.rect, {
  x: 12.793,
  y: 7.0696,
  w: 0.0718,
  h: 0.0638,
  line: { color: "12355B", transparency: 100 },
  fill: { color: "12355B" },
});
addPlacement("bottom_right_endpoint", 12.793, 7.0696, 0.0718, 0.0638, true);

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);

pptx.writeFile({ fileName: OUTPUT });
