const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-08.pptx`;
const CROP_DIR = `${ROOT}/assets/slide-08-blueprint-icons`;
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
  navy: "12355B",
  navy2: "07345E",
  navy3: "062B50",
  blueGrey: "8097B3",
  blueGrey2: "A7B8CC",
  pale: "E2EAF2",
  white: "FFFFFF",
  ink: "101820",
  grey: "565B61",
  line: "7891AA",
  grid: "B3C1CF",
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
addRect("page_badge_body", 13, 0, 110, 61, { color: C.navy3 });
slide.addShape(pptx.ShapeType.triangle, {
  ...B(13, 52, 110, 31),
  rotate: 180,
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addPlacement("page_badge", B(13, 0, 110, 82));
addText("page_number", "08", 36, 10, 58, 46, {
  fontSize: 20,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 424, 14, 787, 42, {
  fontSize: 20,
  bold: true,
  color: C.navy3,
  align: "center",
}, true);
addText("section_label", "工作成果｜阶段性验证", 1358, 20, 292, 35, {
  fontSize: 12.5,
  bold: true,
  color: C.navy3,
  align: "right",
}, true);
addRect("top_rule", 130, 61, 1538, 4, { color: C.navy3 });
addText("main_title", "联合执行策略和机会驱动特征已得到阶段性验证", 291, 94, 1095, 55, {
  fontSize: 25,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("subtitle", "联合时频策略兼顾性能与稳定性，元控制器主要依赖维度机会特征做判断", 400, 164, 887, 37, {
  fontSize: 14.5,
  color: C.grey,
  align: "center",
}, true);

// Main panel surfaces.
addRect("strategy_surface", 15, 209, 883, 438, { color: C.ivory, transparency: 100 }, { color: "6D8CB0", width: 0.7 }, false, true);
addRect("importance_surface", 912, 209, 738, 287, { color: C.ivory, transparency: 100 }, { color: "6D8CB0", width: 0.7 }, false, true);
addRect("metric_surface", 912, 505, 738, 142, { color: C.ivory, transparency: 100 }, { color: "6D8CB0", width: 0.7 }, false, true);
addText("strategy_title", "四策略平均SINR对比", 340, 219, 355, 34, {
  fontSize: 12.5,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("importance_title", "特征重要性（元控制器）", 1102, 220, 390, 34, {
  fontSize: 12.5,
  bold: true,
  color: C.navy3,
  align: "center",
});

// Strategy chart axes and grid.
const chart = { x: 118, y: 266, w: 753, h: 327 };
const yFor = (value) => chart.y + ((20 - value) / 25) * chart.h;
for (const value of [-5, 0, 5, 10, 15, 20]) {
  const y = yFor(value);
  addLine(`grid_${value}`, chart.x, y, chart.x + chart.w, y, C.grid, 0.65, "dash");
  addText(`ytick_${value}`, `${value}`.replace("-", "−"), 72, y - 12, 33, 24, {
    fontSize: 8.5,
    color: C.ink,
    align: "right",
  });
}
addLine("chart_axis_y", chart.x, chart.y, chart.x, chart.y + chart.h, C.ink, 0.85);
addLine("chart_axis_x", chart.x, chart.y + chart.h, chart.x + chart.w, chart.y + chart.h, C.ink, 0.85);
addText("chart_y_label", "平均SINR（dB）", 0, 407, 96, 34, {
  fontSize: 11,
  color: C.ink,
  rotate: 270,
  align: "center",
});
const strategyData = [
  { name: "Baseline", mean: 2.59, sd: 9.85, x: 155, color: C.blueGrey2 },
  { name: "freq_only", mean: 8.24, sd: 3.20, x: 351, color: C.blueGrey },
  { name: "time_only", mean: 7.78, sd: 4.62, x: 547, color: C.blueGrey },
  { name: "joint", mean: 9.50, sd: 0.57, x: 743, color: C.navy3 },
];
for (let i = 0; i < strategyData.length; i += 1) {
  const datum = strategyData[i];
  const top = yFor(datum.mean);
  addRect(`bar_${i}`, datum.x, top, 107, chart.y + chart.h - top, { color: datum.color });
  const cx = datum.x + 53.5;
  const topError = yFor(Math.min(20, datum.mean + datum.sd));
  const bottomError = yFor(Math.max(-5, datum.mean - datum.sd));
  addLine(`error_${i}`, cx, topError, cx, bottomError, C.ink, 1.0);
  addLine(`error_top_${i}`, cx - 7, topError, cx + 7, topError, C.ink, 1.0);
  addLine(`error_bottom_${i}`, cx - 7, bottomError, cx + 7, bottomError, C.ink, 1.0);
  const valueText = `${datum.mean.toFixed(2)}±${datum.sd.toFixed(2)} dB`;
  addText(`value_${i}`, valueText, datum.x - 6, Math.max(352, topError - 28), 119, 26, {
    fontSize: 9.5,
    bold: true,
    color: C.ink,
    align: "center",
  });
  addText(`category_${i}`, datum.name, datum.x - 17, 600, 141, 34, {
    fontSize: 9.5,
    color: C.ink,
    align: "center",
  });
}

// Feature importance chart.
const featureBars = [
  ["fc_td_ratio", 0.3184, 1052, 266, 505, C.navy3],
  ["td_gap", 0.2247, 1052, 311, 341, C.blueGrey],
  ["fc_gap", 0.2202, 1052, 356, 331, C.blueGrey],
  ["r_avoid", 0.0724, 1052, 402, 123, C.blueGrey2],
  ["H_action", 0.0518, 1052, 447, 93, C.blueGrey2],
];
addLine("feature_axis", 1052, 262, 1052, 483, C.ink, 0.7);
for (let i = 0; i < featureBars.length; i += 1) {
  const [name, value, x, y, w, color] = featureBars[i];
  addRect(`feature_bar_${i}`, x, y, w, 30, { color });
  addText(`feature_name_${i}`, name, 938, y - 2, 102, 34, {
    fontSize: 9.5,
    color: C.ink,
    align: "right",
  });
  addText(`feature_value_${i}`, value.toFixed(4), x + w + 10, y - 2, 75, 34, {
    fontSize: 9.5,
    color: C.ink,
  });
}

// Key metrics.
addLine("metric_divider", 1273, 523, 1273, 629, "8FA3B7", 0.65);
addText("baseline_gain", "+6.91 dB", 959, 528, 285, 60, {
  fontSize: 28,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("baseline_gain_label", "joint相对Baseline", 973, 600, 263, 31, {
  fontSize: 13,
  color: C.ink,
  align: "center",
});
addText("gru_gain", "+2.3 dB", 1330, 528, 274, 60, {
  fontSize: 28,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("gru_gain_label", "GRU组件贡献", 1360, 600, 228, 31, {
  fontSize: 13,
  color: C.ink,
  align: "center",
});

// Findings strip.
addRect("findings_surface", 15, 657, 1636, 91, { color: C.ivory, transparency: 100 }, { color: "6D8CB0", width: 0.7 }, false, true);
addCrop("finding_check_1", "check", 84, 668, 77, 72);
addCrop("finding_check_2", "check", 607, 668, 77, 72);
addCrop("finding_check_3", "check", 1093, 668, 77, 72);
addLine("finding_divider_1", 531, 681, 531, 729, "9BA8B5", 0.65);
addLine("finding_divider_2", 1013, 681, 1013, 729, "9BA8B5", 0.65);
addText("finding_1_title", "joint最终SINR最高", 187, 669, 322, 31, {
  fontSize: 13,
  bold: true,
  color: C.navy3,
});
addText("finding_1_body", "平均SINR达到9.50 dB", 187, 705, 322, 26, {
  fontSize: 10.5,
  color: C.ink,
});
addText("finding_2_title", "joint标准差最低", 699, 669, 307, 31, {
  fontSize: 13,
  bold: true,
  color: C.navy3,
});
addText("finding_2_body", "标准差仅为0.57 dB", 699, 705, 307, 26, {
  fontSize: 10.5,
  color: C.ink,
});
addText("finding_3_title", "前三项特征均刻画维度优化机会", 1190, 669, 417, 31, {
  fontSize: 12.2,
  bold: true,
  color: C.navy3,
});
addText("finding_3_body", "均为机会相关度量，支持机理设计", 1190, 705, 417, 26, {
  fontSize: 10.5,
  color: C.ink,
});

// Caveat.
addRect("caveat_surface", 15, 760, 1636, 67, { color: C.ivory, transparency: 100 }, { color: C.navy3, width: 0.8, dash: "dash" }, false, true);
addCrop("caveat_warning", "warning", 394, 767, 60, 55);
addText("caveat_text", "执行层结果与系统级Meta-RF结果属于不同实验层次", 476, 773, 831, 42, {
  fontSize: 13.5,
  bold: true,
  color: C.navy3,
  align: "center",
});

// Conclusion band.
addRect("conclusion_surface", 15, 837, 1636, 88, { color: C.navy3 }, null, true, true);
addCrop("conclusion_trophy", "trophy", 172, 840, 84, 82);
addText("conclusion_text", "底层证明联合搜索有效，上层进一步学习何时缩小搜索范围", 290, 852, 1116, 54, {
  fontSize: 18,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("source_footer", "来源：E07 / E09；S1:p10–12；S2:p12,p17,p20；S3:p3", 1320, 906, 285, 13, {
  fontSize: 6.5,
  color: "C5D7E9",
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
fs.mkdirSync(`${ROOT}/pages`, { recursive: true });
pptx.writeFile({ fileName: OUTPUT });
