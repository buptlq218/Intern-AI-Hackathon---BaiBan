const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-10.pptx`;
const CROP_DIR = `${ROOT}/assets/slide-10-blueprint-icons`;
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "林渠";
pptx.subject = "研究生中期答辩";
pptx.title = "基于分层强化学习的FMCW雷达抗干扰策略优化";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "PingFang SC",
  bodyFontFace: "PingFang SC",
  lang: "zh-CN",
};
pptx.defineSlideMaster({
  title: "CONTENT_IVORY",
  background: { color: "FCFAF5" },
  objects: [],
});
const slide = pptx.addSlide("CONTENT_IVORY");
slide.background = { color: "FCFAF5" };

const W = 13.333;
const H = 7.5;
const sx = W / 1672;
const sy = H / 941;
const B = (x, y, w, h) => ({ x: x * sx, y: y * sy, w: w * sx, h: h * sy });
const C = {
  ivory: "FCFAF5",
  navy: "07345E",
  navy2: "0A3767",
  navy3: "062B50",
  white: "FFFFFF",
  ink: "0D1014",
  grey: "4D5055",
  lightGrey: "A7AFB8",
  pale1: "E4EDF6",
  pale2: "EDF3F8",
  pale3: "E8F0F7",
  separator: "A9B1BA",
};

const placements = [];
const addPlacement = (id, box, allowOverlap = false) =>
  placements.push({ id, ...box, allowOverlap });
function warnIfSlideElementsOutOfBounds(items, width = W, height = H) {
  for (const item of items) {
    if (
      item.x < 0 ||
      item.y < 0 ||
      item.w <= 0 ||
      item.h <= 0 ||
      item.x + item.w > width + 0.001 ||
      item.y + item.h > height + 0.001
    ) process.stderr.write(`OUT_OF_BOUNDS ${item.id}\n`);
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
function addRect(id, x, y, w, h, fill, line = null, rounded = false, track = false) {
  const box = B(x, y, w, h);
  slide.addShape(rounded ? pptx.ShapeType.roundRect : pptx.ShapeType.rect, {
    ...box,
    fill,
    line: line || { color: fill.color || C.ivory, transparency: 100 },
  });
  if (track) addPlacement(id, box);
}
function addEllipse(id, x, y, w, h, fill, line = null) {
  slide.addShape(pptx.ShapeType.ellipse, {
    ...B(x, y, w, h),
    fill,
    line: line || { color: fill.color || C.ivory, transparency: 100 },
  });
}
function addText(id, text, x, y, w, h, options = {}, track = false) {
  const box = B(x, y, w, h);
  slide.addText(text, {
    ...box,
    fontFace: "PingFang SC",
    color: C.ink,
    margin: 0,
    valign: "mid",
    fit: "shrink",
    paraSpaceAfterPt: 0,
    breakLine: false,
    ...options,
  });
  if (track) addPlacement(id, box, true);
}
function addLine(id, x1, y1, x2, y2, color = C.navy, width = 1.1, dash = "solid") {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const box = B(
    Math.min(x1, x2),
    Math.min(y1, y2),
    Math.max(Math.abs(dx), 0.5),
    Math.max(Math.abs(dy), 0.5)
  );
  slide.addShape(pptx.ShapeType.line, {
    ...box,
    flipV: dx * dy < 0,
    line: { color, width, dash },
  });
}
function addCrop(id, name, x, y, w, h) {
  slide.addImage({
    path: `${CROP_DIR}/${name}.png`,
    ...B(x, y, w, h),
    altText: id,
  });
}

// Header.
addRect("page_badge_body", 9, 8, 57, 51, { color: C.navy3 });
slide.addShape(pptx.ShapeType.triangle, {
  ...B(57, 8, 35, 51),
  rotate: 90,
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addPlacement("page_badge", B(9, 8, 83, 51));
addText("page_number", "10", 20, 10, 48, 46, {
  fontSize: 20,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 448, 14, 775, 46, {
  fontSize: 20,
  bold: true,
  color: C.navy3,
  align: "center",
}, true);
addText("section_label", "计划与进度安排", 1390, 14, 247, 44, {
  fontSize: 18,
  bold: true,
  color: C.navy3,
  align: "right",
}, true);
addRect("top_rule", 9, 64, 1653, 4, { color: C.navy3 });
addText("main_title", "实验闭环已经完成，当前任务是沉淀论文并完成答辩验收", 282, 101, 1107, 61, {
  fontSize: 25,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("subtitle", "研究工作由算法验证阶段转入成果固化与答辩交付阶段", 442, 174, 790, 47, {
  fontSize: 16,
  color: C.grey,
  align: "center",
}, true);

// Timeline background and flow.
addRect("timeline_background", 61, 301, 1545, 464, { color: C.pale2 }, null, true, true);
addRect("timeline_left_tint", 61, 301, 522, 464, { color: C.pale1, transparency: 18 }, null, true);
addRect("timeline_center_tint", 526, 301, 580, 464, { color: C.pale2, transparency: 15 }, null, true);
addRect("timeline_right_tint", 1059, 301, 547, 464, { color: C.pale3, transparency: 15 }, null, true);
addLine("timeline_line_1", 371, 305, 689, 305, C.lightGrey, 5.5);
slide.addShape(pptx.ShapeType.triangle, {
  ...B(680, 290, 31, 31),
  rotate: 90,
  fill: { color: C.lightGrey },
  line: { color: C.lightGrey, transparency: 100 },
});
addLine("timeline_line_2", 913, 305, 1220, 305, C.lightGrey, 5.5);
slide.addShape(pptx.ShapeType.triangle, {
  ...B(1210, 290, 31, 31),
  rotate: 90,
  fill: { color: C.lightGrey },
  line: { color: C.lightGrey, transparency: 100 },
});

// Stage icons from the approved blueprint.
addCrop("stage_complete_icon", "stage-complete", 208, 222, 168, 168);
addCrop("stage_writing_icon", "stage-writing", 748, 222, 166, 168);
addCrop("stage_defense_icon", "stage-defense", 1263, 222, 166, 169);
addText("stage_complete_title", "已完成", 209, 394, 168, 57, {
  fontSize: 24,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("stage_writing_title", "进行中", 748, 394, 166, 57, {
  fontSize: 24,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("stage_defense_title", "下一阶段", 1249, 394, 195, 57, {
  fontSize: 24,
  bold: true,
  color: C.navy3,
  align: "center",
});

// Status dividers.
const stageCenters = [293, 831, 1347];
for (let i = 0; i < stageCenters.length; i += 1) {
  const center = stageCenters[i];
  addLine(`stage_divider_${i}`, center - 164, 454, center + 164, 454, C.navy3, 0.8, "dash");
  addEllipse(`stage_dot_left_${i}`, center - 168, 449, 10, 10, { color: C.navy3 });
  addEllipse(`stage_dot_right_${i}`, center + 158, 449, 10, 10, { color: C.navy3 });
}
addText("status_complete", "实验全部完成", 190, 463, 206, 39, {
  fontSize: 15.5,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("status_writing", "正在撰写论文", 728, 463, 206, 39, {
  fontSize: 15.5,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("status_defense", "答辩准备与验收", 1230, 463, 234, 39, {
  fontSize: 15.5,
  bold: true,
  color: C.navy3,
  align: "center",
});

// Task columns.
const doneItems = [
  ["done-signal", "FMCW建模与仿真环境", 506],
  ["done-brain", "Double DQN+GRU执行层", 557],
  ["done-layers", "Meta-RF元策略", 607],
  ["done-chart", "全部对比与动态跳频实验", 657],
  ["done-document", "实验分析与专利材料", 706],
];
for (let i = 0; i < doneItems.length; i += 1) {
  const [icon, text, y] = doneItems[i];
  addCrop(`done_icon_${i}`, icon, 128, y, 46, i === 3 ? 43 : 45);
  addText(`done_text_${i}`, text, 190, y - 2, 292, 43, {
    fontSize: 13,
    color: C.ink,
  });
  if (i < doneItems.length - 1) addLine(`done_separator_${i}`, 115, y + 47, 477, y + 47, C.separator, 0.55, "dash");
}

const doingItems = [
  ["doing-book", "统一技术主线与章节衔接", 520, 53, 44],
  ["doing-chart", "整理实验图表与结果讨论", 591, 53, 47],
  ["doing-clipboard", "补充局限性与工程实时性", 664, 51, 55],
];
for (let i = 0; i < doingItems.length; i += 1) {
  const [icon, text, y, w, h] = doingItems[i];
  addCrop(`doing_icon_${i}`, icon, 650, y, w, h);
  addText(`doing_text_${i}`, text, 728, y - 2, 280, 45, {
    fontSize: 13,
    color: C.ink,
  });
  if (i < doingItems.length - 1) addLine(`doing_separator_${i}`, 636, y + 57, 1007, y + 57, C.separator, 0.55, "dash");
}

const nextItems = [
  ["next-document", "完成论文定稿与材料提交", 509, 47, 50],
  ["next-presentation", "迭代答辩演示", 577, 51, 42],
  ["next-question", "预演与问题准备", 633, 55, 45],
  ["next-shield", "完成答辩验收", 691, 50, 52],
];
for (let i = 0; i < nextItems.length; i += 1) {
  const [icon, text, y, w, h] = nextItems[i];
  addCrop(`next_icon_${i}`, icon, 1173, y, w, h);
  addText(`next_text_${i}`, text, 1252, y - 2, 286, 45, {
    fontSize: 13,
    color: C.ink,
  });
  if (i < nextItems.length - 1) addLine(`next_separator_${i}`, 1160, y + 60, 1544, y + 60, C.separator, 0.55, "dash");
}

// Final takeaway and caveat footer.
addRect("conclusion_surface", 61, 772, 1545, 101, { color: C.navy2 }, null, true, true);
addCrop("conclusion_icon", "conclusion-clipboard", 151, 781, 95, 82);
addLine("conclusion_divider", 277, 790, 277, 854, "BFD1E2", 0.9);
addText("conclusion_text", "研究方案、核心算法和实验验证已完成；后续聚焦论文质量与答辩交付", 322, 790, 1185, 64, {
  fontSize: 19.5,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addCrop("footer_info_icon", "footer-info", 608, 890, 36, 36);
addText("footer_caveat", "采用阶段表达，不虚构具体日期", 650, 886, 453, 42, {
  fontSize: 13.5,
  color: "777777",
  align: "center",
});
addText("source_footer", "来源：S1:p20；进度状态依据用户补充", 1340, 915, 275, 12, {
  fontSize: 6.5,
  color: "999999",
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
fs.mkdirSync(`${ROOT}/pages`, { recursive: true });
pptx.writeFile({ fileName: OUTPUT });
