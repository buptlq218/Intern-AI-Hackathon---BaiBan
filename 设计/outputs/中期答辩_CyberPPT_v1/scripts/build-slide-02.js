const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-02.pptx`;
const SCENE = `${ROOT}/assets/slide-02-road-scene-clean.png`;
const ICONS = {
  recognition: `${ROOT}/assets/icons/tabler-outline/zoom-scan.svg`,
  adaptation: `${ROOT}/assets/icons/tabler-outline/chart-bar.svg`,
  realtime: `${ROOT}/assets/icons/tabler-outline/clock-bolt.svg`,
};

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
const PX_W = 1672;
const PX_H = 941;
const sx = W / PX_W;
const sy = H / PX_H;
const B = (x, y, w, h) => ({ x: x * sx, y: y * sy, w: w * sx, h: h * sy });

const C = {
  navy: "12355B",
  navy2: "0B2D52",
  blue: "2763B0",
  blueLight: "DCEAF7",
  ivory: "FCFAF5",
  paper: "F4F2EC",
  grey: "5F646B",
  lightGrey: "D9DDE1",
  midGrey: "AAB2BA",
  red: "B4413E",
  redLight: "F1D7D2",
  ink: "101820",
  white: "FFFFFF",
};

const placements = [];
const addPlacement = (id, box, allowOverlap = false) => {
  placements.push({ id, ...box, allowOverlap });
};

function warnIfSlideElementsOutOfBounds(items, width = W, height = H) {
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

function addRect(id, x, y, w, h, fill, line = null, radius = 0, allowOverlap = false) {
  const box = B(x, y, w, h);
  const shape = radius > 0 ? pptx.ShapeType.roundRect : pptx.ShapeType.rect;
  slide.addShape(shape, {
    ...box,
    rectRadius: radius,
    fill,
    line: line || { color: fill.color || C.ivory, transparency: 100 },
  });
  addPlacement(id, box, allowOverlap);
}

function addText(id, text, x, y, w, h, options = {}, allowOverlap = false) {
  const box = B(x, y, w, h);
  slide.addText(text, {
    ...box,
    fontFace: "PingFang SC",
    color: C.ink,
    margin: 0,
    valign: "mid",
    breakLine: false,
    fit: "shrink",
    paraSpaceAfterPt: 0,
    ...options,
  });
  addPlacement(id, box, allowOverlap);
}

function addRotatedBar(id, x, y, w, h, rotate, color, allowOverlap = true) {
  const box = B(x, y, w, h);
  slide.addShape(pptx.ShapeType.rect, {
    ...box,
    rotate,
    fill: { color },
    line: { color, transparency: 100 },
  });
  addPlacement(id, box, allowOverlap);
}

function addSegment(id, x1, y1, x2, y2, thicknessPx, color, allowOverlap = true) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.max(1, Math.sqrt(dx * dx + dy * dy));
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
  const box = B((x1 + x2) / 2 - len / 2, (y1 + y2) / 2 - thicknessPx / 2, len, thicknessPx);
  slide.addShape(pptx.ShapeType.rect, {
    ...box,
    rotate: angle,
    fill: { color },
    line: { color, transparency: 100 },
  });
  addPlacement(id, box, allowOverlap);
}

function svgData(path, color = `#${C.navy}`) {
  const svg = fs
    .readFileSync(path, "utf8")
    .replaceAll("currentColor", color)
    .replace(/stroke="[^"]*"/g, `stroke="${color}"`);
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}

// Header chrome
addRect("page_badge", 17, 15, 66, 41, { color: C.navy });
addText("page_number", "02", 34, 20, 31, 29, {
  fontSize: 16,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText(
  "header_deck_title",
  "基于分层强化学习的FMCW雷达抗干扰策略优化",
  591,
  22,
  523,
  27,
  { fontSize: 12, bold: true, color: C.navy, align: "center", charSpacing: 0.25 }
);
addText("section_label", "研究背景", 1550, 21, 103, 29, {
  fontSize: 13,
  bold: true,
  color: C.navy,
  align: "right",
});
addRect("top_rule", 17, 60, 1639, 2, { color: C.navy });

// Narrative header
addText(
  "main_title",
  "相干干扰使FMCW雷达面临“难识别、难适应、难实时”的复合挑战",
  152,
  94,
  1367,
  53,
  { fontSize: 23.2, bold: true, color: "090B0E", align: "center", charSpacing: 0.05 }
);
addText(
  "subtitle",
  "车载雷达密度上升后，相同调频斜率与PRI会产生形态接近真实目标的窄带干扰",
  346,
  160,
  982,
  37,
  { fontSize: 14.3, color: C.grey, align: "center", charSpacing: 0.05 }
);

// Complex visual asset: road, vehicles and radar beams only.
const sceneBox = B(19, 208, 923, 582);
slide.addImage({
  path: SCENE,
  ...sceneBox,
  transparency: 0,
  altText: "多车FMCW雷达相干干扰道路场景，无文字复杂视觉资产",
});
addPlacement("road_scene_asset", sceneBox, true);

// Native scene annotations.
addText("label_interferer_a", "干扰车A\n（同斜率 / 同PRI）", 96, 230, 134, 51, {
  fontSize: 10.7,
  bold: true,
  color: C.red,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.88,
}, true);
addText("label_interferer_b", "干扰车B\n（异斜率 / 近PRI）", 43, 441, 148, 51, {
  fontSize: 10.7,
  bold: true,
  color: C.red,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.88,
}, true);
addText("label_interferer_c", "干扰车C\n（同斜率 / 异PRI）", 783, 280, 145, 51, {
  fontSize: 10.7,
  bold: true,
  color: C.red,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.88,
}, true);
addText("label_true_target", "真实目标", 470, 216, 96, 25, {
  fontSize: 10.5,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("label_ego_vehicle", "自车（雷达）", 433, 642, 145, 27, {
  fontSize: 11.5,
  bold: true,
  color: C.navy,
  align: "center",
}, true);

// Four-corner target bracket, rebuilt as native bars.
for (const [id, x, y, w, h] of [
  ["target_bracket_tl_h", 442, 245, 16, 3],
  ["target_bracket_tl_v", 442, 245, 3, 16],
  ["target_bracket_tr_h", 558, 245, 16, 3],
  ["target_bracket_tr_v", 571, 245, 3, 16],
  ["target_bracket_bl_h", 442, 340, 16, 3],
  ["target_bracket_bl_v", 442, 327, 3, 16],
  ["target_bracket_br_h", 558, 340, 16, 3],
  ["target_bracket_br_v", 571, 327, 3, 16],
]) {
  addRect(id, x, y, w, h, { color: C.white, transparency: 5 }, null, 0, true);
}

// Native legend panel.
addRect(
  "scene_legend_panel",
  50,
  616,
  219,
  149,
  { color: "F6F4EE", transparency: 5 },
  { color: "AAB4BF", transparency: 18, width: 0.8 },
  0.06,
  true
);
addSegment("legend_beam_line_1", 73, 646, 107, 637, 4, C.blue, true);
addSegment("legend_beam_line_2", 73, 646, 107, 655, 4, C.blue, true);
addText("legend_ego", "自车雷达波束", 119, 630, 126, 32, {
  fontSize: 11.5,
  color: C.ink,
}, true);
const wavePoints = [
  [72, 691], [78, 682], [84, 700], [90, 682], [96, 700], [102, 691],
];
for (let i = 0; i < wavePoints.length - 1; i += 1) {
  addSegment(`legend_wave_${i}`, ...wavePoints[i], ...wavePoints[i + 1], 2.1, C.red, true);
}
addText("legend_interference", "干扰信号", 119, 675, 126, 32, {
  fontSize: 11.5,
  color: C.ink,
}, true);
for (let i = 0; i < 5; i += 1) {
  addRect(`legend_los_dash_${i}`, 72 + i * 8, 732, 5, 2, { color: "8F9AA5" }, null, 0, true);
}
addText("legend_los", "雷达视线方向", 119, 716, 126, 32, {
  fontSize: 11.5,
  color: C.ink,
}, true);

// Native range-Doppler spectrum inset.
addRect(
  "spectrum_panel",
  579,
  552,
  349,
  226,
  { color: "F8F6F0", transparency: 2 },
  { color: "A8B2BD", transparency: 12, width: 0.8 },
  0.04,
  true
);
addText("spectrum_title", "距离-多普勒谱（示意）", 600, 565, 232, 28, {
  fontSize: 12.5,
  bold: true,
  color: C.navy,
});
addText("spectrum_y_label", "幅度（dB）", 597, 600, 64, 22, {
  fontSize: 9,
  color: C.grey,
  rotate: 270,
  align: "center",
});
addText("spectrum_x_label", "距离", 842, 714, 47, 22, {
  fontSize: 9.5,
  color: C.grey,
  align: "center",
});
addRect("spectrum_y_axis", 638, 611, 2, 103, { color: "74808C" }, null, 0, true);
addRect("spectrum_x_axis", 638, 712, 238, 2, { color: "74808C" }, null, 0, true);
const spectrumPoints = [
  [642, 706], [651, 704], [661, 699], [671, 701], [681, 693], [691, 700],
  [701, 688], [710, 697], [720, 682], [730, 643], [739, 673], [748, 690],
  [758, 681], [768, 696], [778, 684], [788, 701], [798, 688], [809, 700],
  [820, 692], [832, 702], [846, 698], [861, 704],
];
for (let i = 0; i < spectrumPoints.length - 1; i += 1) {
  addSegment(`spectrum_curve_${i}`, ...spectrumPoints[i], ...spectrumPoints[i + 1], 2.3, C.blue, true);
}
const targetMarker = B(724, 636, 14, 14);
slide.addShape(pptx.ShapeType.ellipse, {
  ...targetMarker,
  fill: { color: C.white, transparency: 100 },
  line: { color: C.blue, width: 1.5 },
});
addPlacement("spectrum_target_marker", targetMarker, true);
for (const [idx, cx, cy] of [[0, 704, 683], [1, 761, 674], [2, 790, 686], [3, 820, 690]]) {
  addSegment(`spectrum_cross_${idx}_a`, cx - 6, cy - 6, cx + 6, cy + 6, 2.1, C.red, true);
  addSegment(`spectrum_cross_${idx}_b`, cx - 6, cy + 6, cx + 6, cy - 6, 2.1, C.red, true);
  for (let j = 0; j < 5; j += 1) {
    addRect(`spectrum_dashed_${idx}_${j}`, cx - 1, 699 - j * 15, 2, 8, { color: C.red, transparency: 15 }, null, 0, true);
  }
}
addText("spectrum_legend_target", "○ 真实目标", 600, 721, 100, 20, {
  fontSize: 9,
  color: C.blue,
});
addText("spectrum_legend_interference", "× 干扰（伪目标）", 703, 721, 133, 20, {
  fontSize: 9,
  color: C.red,
});
addText(
  "spectrum_note",
  "干扰与真实目标形态接近，易产生虚警/漏检",
  600,
  745,
  304,
  26,
  { fontSize: 8.3, bold: true, color: C.red, align: "center" }
);

// Right-hand challenge rail.
addRect("rail_divider", 962, 228, 2, 547, { color: "9FB0C0" });
const challenges = [
  {
    id: "recognition",
    cy: 237,
    icon: ICONS.recognition,
    titleY: 235,
    bodyY: 286,
    detailY: 326,
    title: "难识别",
    body: "干扰与目标回波形态相似",
    detail: "谱峰位置接近，难以仅凭形态区分真伪",
  },
  {
    id: "adaptation",
    cy: 410,
    icon: ICONS.adaptation,
    titleY: 407,
    bodyY: 458,
    detailY: 497,
    title: "难适应",
    body: "标量SINR难揭示干扰结构",
    detail: "同一SINR下，干扰分布与落点差异大，\n单一指标不足以指导策略选择",
  },
  {
    id: "realtime",
    cy: 597,
    icon: ICONS.realtime,
    titleY: 591,
    bodyY: 642,
    detailY: 675,
    title: "难实时",
    body: "逐chirp动作需快速响应",
    detail: "",
  },
];

for (const item of challenges) {
  const circle = B(995, item.cy, 113, 113);
  slide.addShape(pptx.ShapeType.ellipse, {
    ...circle,
    fill: { color: C.ivory, transparency: 100 },
    line: { color: C.navy, width: 1.3 },
  });
  addPlacement(`${item.id}_circle`, circle, true);
  const iconBox = B(1021, item.cy + 25, 62, 62);
  slide.addImage({
    data: svgData(item.icon),
    ...iconBox,
    altText: `${item.title}线性图标`,
  });
  addPlacement(`${item.id}_icon`, iconBox, true);
  addText(`${item.id}_title`, item.title, 1145, item.titleY, 220, 38, {
    fontSize: 20,
    bold: true,
    color: C.navy,
  });
  addText(`${item.id}_body`, item.body, 1145, item.bodyY, 460, 32, {
    fontSize: 14.6,
    bold: true,
    color: C.ink,
  });
  if (item.detail) {
    addText(`${item.id}_detail`, item.detail, 1145, item.detailY, 468, item.id === "adaptation" ? 54 : 31, {
      fontSize: 12.3,
      color: C.grey,
      breakLine: true,
      lineSpacingMultiple: 0.92,
    });
  }
}
addRect("rail_separator_1", 995, 382, 645, 2, { color: "B8C2CB" });
addRect("rail_separator_2", 995, 566, 645, 2, { color: "B8C2CB" });

addText("kpi_context", "FMCW典型\nchirp间隔", 1146, 694, 134, 53, {
  fontSize: 13,
  bold: true,
  color: C.grey,
  breakLine: true,
  lineSpacingMultiple: 0.9,
});
addText("kpi_number", "50", 1310, 683, 119, 69, {
  fontSize: 40,
  bold: true,
  color: C.navy,
  align: "center",
});
addText("kpi_unit", "μs", 1433, 715, 61, 39, {
  fontSize: 20,
  bold: true,
  color: C.navy,
});
addText("kpi_note", "留给算法决策与执行的时间极短", 1146, 762, 450, 30, {
  fontSize: 12.5,
  color: C.grey,
});

// Bottom SO WHAT band.
addRect(
  "conclusion_band",
  19,
  817,
  1634,
  103,
  { color: "EAF2F8", transparency: 0 },
  { color: C.navy, transparency: 10, width: 1.0, dash: "dash" },
  0.04
);
addRotatedBar("chevron_1a", 108, 841, 39, 9, 45, C.navy, true);
addRotatedBar("chevron_1b", 108, 875, 39, 9, -45, C.navy, true);
addRotatedBar("chevron_2a", 135, 841, 39, 9, 45, C.navy, true);
addRotatedBar("chevron_2b", 135, 875, 39, 9, -45, C.navy, true);
addText(
  "conclusion_text",
  "需要主动感知干扰结构、分离决策时间尺度并减少无效探索",
  264,
  846,
  1240,
  52,
  { fontSize: 24, bold: true, color: C.navy, align: "center", charSpacing: 0.1 }
  ,
  true
);

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements.filter((item) => !item.allowOverlap));

pptx.writeFile({ fileName: OUTPUT });
