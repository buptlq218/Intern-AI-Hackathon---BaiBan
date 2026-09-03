const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-09.pptx`;
const CROP_DIR = `${ROOT}/assets/slide-09-blueprint-icons`;
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
  blue: "2F6FB5",
  paleBlue: "A8BCD2",
  midBlue: "7295C0",
  white: "FFFFFF",
  ink: "0E1114",
  grey: "4F5257",
  grid: "B9C7D4",
  border: "7D9AB9",
  red: "B51618",
  orange: "C87900",
  orangePale: "FFF8E8",
  greyPale: "F2F2EF",
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
    radius: rounded ? 0.05 : undefined,
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

// Header system.
addRect("page_badge_body", 17, 5, 108, 55, { color: C.navy3 });
slide.addShape(pptx.ShapeType.triangle, {
  ...B(114, 5, 44, 55),
  rotate: 90,
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addPlacement("page_badge", B(17, 5, 141, 55));
addText("page_number", "09", 36, 8, 66, 48, {
  fontSize: 21,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 421, 15, 700, 42, {
  fontSize: 19,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("section_label", "工作成果｜系统验证与问题", 1272, 16, 352, 40, {
  fontSize: 14,
  bold: true,
  color: C.navy3,
  align: "right",
}, true);
addRect("top_rule", 17, 63, 1637, 4, { color: C.navy3 });
addText("main_title", "Meta-RF提升了系统性能与突变恢复速度，但实时部署仍是关键缺口", 191, 83, 1295, 57, {
  fontSize: 24,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("subtitle", "元策略增益在非平稳干扰中最突出，当前仿真实现尚未满足工程时延要求", 309, 143, 1050, 43, {
  fontSize: 15.5,
  color: C.grey,
  align: "center",
}, true);

// Three main evidence panels.
addRect("system_panel", 25, 194, 553, 606, { color: C.ivory, transparency: 100 }, { color: "A9BACB", width: 0.75 }, false, false);
addRect("dynamic_panel", 594, 194, 640, 606, { color: C.ivory, transparency: 100 }, { color: "A9BACB", width: 0.75 }, false, false);
addRect("evidence_panel", 1247, 194, 396, 606, { color: C.ivory, transparency: 100 }, { color: "A9BACB", width: 0.75 }, false, false);
addRect("system_panel_header", 25, 194, 553, 47, { color: C.navy2 });
addRect("dynamic_panel_header", 594, 194, 640, 47, { color: C.navy2 });
addRect("evidence_panel_header", 1247, 194, 396, 47, { color: C.navy2 });
addText("system_panel_title", "系统级平均SINR与避开率", 84, 198, 433, 38, {
  fontSize: 15,
  bold: true,
  color: C.white,
  align: "center",
});
addText("dynamic_panel_title", "动态跳频突变恢复过程（平均SINR, dB）", 674, 198, 480, 38, {
  fontSize: 14,
  bold: true,
  color: C.white,
  align: "center",
});
addText("evidence_panel_title", "关键证据与工程缺口", 1291, 198, 309, 38, {
  fontSize: 15,
  bold: true,
  color: C.white,
  align: "center",
});

// Left panel legend.
const legendItems = [
  ["Baseline", 100, C.paleBlue],
  ["Pure DRL", 246, C.blue],
  ["Meta-RF", 405, C.navy2],
];
for (let i = 0; i < legendItems.length; i += 1) {
  const [name, x, color] = legendItems[i];
  addRect(`legend_box_${i}`, x, 256, 18, 18, { color });
  addText(`legend_text_${i}`, name, x + 26, 248, 105, 33, {
    fontSize: 11,
    color: C.ink,
  });
}

// Left panel combo chart: SINR and avoidance rate.
const lChart = { x: 75, y: 329, w: 450, h: 263 };
const ySinr = (v) => lChart.y + ((10 - v) / 30) * lChart.h;
const yAvoid = (v) => lChart.y + ((100 - v) / 100) * lChart.h;
for (const value of [-20, -15, -10, -5, 0, 5, 10]) {
  const y = ySinr(value);
  addLine(`left_grid_${value}`, lChart.x, y, lChart.x + lChart.w, y, C.grid, 0.6, "dash");
  addText(`left_y_${value}`, String(value).replace("-", "−"), 37, y - 11, 29, 22, {
    fontSize: 8.5,
    align: "right",
  });
}
for (const value of [0, 20, 40, 60, 80, 100]) {
  const y = yAvoid(value);
  addText(`right_y_${value}`, String(value), 530, y - 11, 34, 22, {
    fontSize: 8.5,
    align: "left",
  });
}
addLine("left_axis_y", lChart.x, lChart.y, lChart.x, lChart.y + lChart.h, C.ink, 0.8);
addLine("left_axis_right", lChart.x + lChart.w, lChart.y, lChart.x + lChart.w, lChart.y + lChart.h, C.ink, 0.8);
addLine("left_zero_axis", lChart.x, ySinr(0), lChart.x + lChart.w, ySinr(0), C.ink, 0.95);
addText("left_axis_title", "平均SINR (dB)", 37, 294, 118, 26, { fontSize: 8.5 });
addText("right_axis_title", "避开率 (%)", 488, 294, 76, 26, { fontSize: 8.5, align: "right" });

const sinrValues = [
  ["Baseline", -12.26, 109, C.paleBlue],
  ["Pure DRL", -6.42, 165, C.blue],
  ["Meta-RF", -1.32, 220, C.navy2],
];
for (let i = 0; i < sinrValues.length; i += 1) {
  const [name, value, x, color] = sinrValues[i];
  const y0 = ySinr(0);
  const yv = ySinr(value);
  addRect(`sinr_bar_${i}`, x, y0, 40, yv - y0, { color });
  addText(`sinr_label_${i}`, value.toFixed(2), x - 8, yv - 2, 56, 27, {
    fontSize: 9.5,
    color: C.ink,
    align: "center",
  });
}
const avoidValues = [
  [75.9, 357, C.paleBlue],
  [85.5, 411, C.blue],
  [90.0, 465, C.navy2],
];
for (let i = 0; i < avoidValues.length; i += 1) {
  const [value, x, color] = avoidValues[i];
  const top = yAvoid(value);
  addRect(`avoid_bar_${i}`, x, top, 40, lChart.y + lChart.h - top, { color });
  addText(`avoid_label_${i}`, value.toFixed(1), x - 7, top - 25, 54, 25, {
    fontSize: 9.5,
    color: C.ink,
    align: "center",
  });
}
addText("sinr_group_label", "平均SINR (dB)", 92, 595, 188, 28, {
  fontSize: 10,
  align: "center",
});
addText("avoid_group_label", "避开率 (%)", 342, 595, 184, 28, {
  fontSize: 10,
  align: "center",
});

// Left panel result table.
const tableX = [36, 194, 405, 564];
const tableY = [627, 665, 704, 742, 781];
for (let r = 0; r < 4; r += 1) {
  for (let c = 0; c < 3; c += 1) {
    const fill = r === 0 ? { color: C.navy2 } : { color: C.ivory, transparency: 100 };
    addRect(`table_cell_${r}_${c}`, tableX[c], tableY[r], tableX[c + 1] - tableX[c], tableY[r + 1] - tableY[r], fill, {
      color: r === 0 ? C.white : "C9D3DD",
      width: 0.45,
    });
  }
}
const tableRows = [
  ["方法", "平均SINR (dB)", "避开率 (%)"],
  ["■  Baseline", "−12.26±7.65 dB", "75.9%"],
  ["■  Pure DRL", "−6.42±10.03 dB", "85.5%"],
  ["■  Meta-RF", "−1.32±10.54 dB", "90.0%"],
];
for (let r = 0; r < tableRows.length; r += 1) {
  for (let c = 0; c < tableRows[r].length; c += 1) {
    const color = r === 0 ? C.white : C.ink;
    const bulletColor = r > 0 ? [C.paleBlue, C.blue, C.navy2][r - 1] : color;
    addText(`table_text_${r}_${c}`, tableRows[r][c], tableX[c] + 8, tableY[r], tableX[c + 1] - tableX[c] - 16, tableY[r + 1] - tableY[r], {
      fontSize: r === 0 ? 10.5 : 9.5,
      bold: r === 0,
      color: c === 0 && r > 0 ? bulletColor : color,
      align: c === 0 ? "left" : "center",
    });
  }
}

// Center panel dynamic recovery chart.
const dChart = { x: 640, y: 332, w: 573, h: 307 };
const xStep = (step) => dChart.x + (step / 36) * dChart.w;
const yDyn = (value) => dChart.y + ((6 - value) / 16) * dChart.h;
for (const value of [-10, -8, -6, -4, -2, 0, 2, 4, 6]) {
  const y = yDyn(value);
  addLine(`dyn_grid_${value}`, dChart.x, y, dChart.x + dChart.w, y, C.grid, 0.55, "dash");
  addText(`dyn_y_${value}`, String(value).replace("-", "−"), 604, y - 11, 29, 22, {
    fontSize: 8.5,
    align: "right",
  });
}
for (const value of [0, 5, 10, 15, 20, 25, 30, 35]) {
  const x = xStep(value);
  addLine(`dyn_tick_${value}`, x, dChart.y + dChart.h, x, dChart.y + dChart.h + 6, C.ink, 0.65);
  addText(`dyn_x_${value}`, String(value), x - 14, 644, 28, 22, {
    fontSize: 8.5,
    align: "center",
  });
}
addLine("dyn_axis_y", dChart.x, dChart.y, dChart.x, dChart.y + dChart.h, C.ink, 0.8);
addLine("dyn_axis_x", dChart.x, dChart.y + dChart.h, dChart.x + dChart.w, dChart.y + dChart.h, C.ink, 0.8);
addText("dyn_y_title", "平均SINR (dB)", 604, 294, 108, 26, { fontSize: 8.5 });
addText("dyn_x_title", "时间步", 868, 666, 115, 26, { fontSize: 10, align: "center" });
addLine("legend_meta_line", 1074, 270, 1118, 270, C.navy3, 1.8);
addText("legend_meta_text", "Meta-RF", 1127, 254, 86, 32, { fontSize: 10.5 });
addLine("legend_drl_line_1", 1074, 302, 1085, 302, C.blue, 1.8);
addLine("legend_drl_line_2", 1090, 302, 1101, 302, C.blue, 1.8);
addLine("legend_drl_line_3", 1106, 302, 1118, 302, C.blue, 1.8);
addText("legend_drl_text", "Pure DRL", 1127, 286, 86, 32, { fontSize: 10.5 });

const meta = [2.0,1.9,1.8,2.0,1.9,2.1,1.9,2.0,1.8,1.6,1.3,0.8,0.0,-1.0,-2.2,-3.0,-3.5,-3.8,-4.0,-3.6,-2.8,-1.8,-0.7,0.1,0.8,1.1,1.4,1.7,1.9,2.0,2.1,2.2,2.3,2.1,2.2,2.3,2.2];
const pure = [-0.6,-0.7,-0.8,-0.6,-0.7,-0.8,-0.9,-1.0,-1.1,-1.2,-1.6,-2.0,-2.8,-3.8,-4.8,-5.5,-5.2,-5.0,-5.1,-5.2,-5.4,-5.3,-4.8,-4.0,-3.5,-3.0,-2.5,-2.0,-1.5,-1.0,-0.6,-0.2,0.1,0.5,0.9,0.9,1.0];
for (let i = 0; i < meta.length - 1; i += 1) {
  addLine(`meta_segment_${i}`, xStep(i), yDyn(meta[i]), xStep(i + 1), yDyn(meta[i + 1]), C.navy3, 1.55);
  const x0 = xStep(i);
  const y0 = yDyn(pure[i]);
  const x1 = xStep(i + 1);
  const y1 = yDyn(pure[i + 1]);
  const fraction = 0.58;
  addLine(
    `pure_segment_${i}`,
    x0,
    y0,
    x0 + (x1 - x0) * fraction,
    y0 + (y1 - y0) * fraction,
    C.blue,
    1.45
  );
}
const eventX = xStep(15);
addLine("jump_event", eventX, 291, eventX, 639, C.red, 0.8, "dash");
addText("jump_event_label", "第15步随机跳频", eventX - 104, 257, 208, 36, {
  fontSize: 12,
  bold: true,
  color: C.red,
  align: "center",
});
addText("meta_before", "+2.0 dB", 655, 366, 92, 28, { fontSize: 11.5, bold: true, color: C.navy3 });
addText("pure_before", "−0.5 dB", 655, 468, 92, 28, { fontSize: 11.5, bold: true, color: C.blue });
addText("meta_low", "−4.0 dB", 881, 521, 90, 28, { fontSize: 11.5, bold: true, color: C.navy3 });
addText("pure_low", "−5.5 dB", 891, 572, 90, 28, { fontSize: 11.5, bold: true, color: C.blue });

// Recovery interval markers.
addLine("meta_start_marker", xStep(18), 407, xStep(18), 552, C.navy3, 0.75, "dash");
addLine("meta_end_marker", xStep(23), 407, xStep(23), 552, C.navy3, 0.75, "dash");
addLine("meta_arrow", xStep(18), 424, xStep(23), 424, C.navy3, 1.0);
addText("meta_steps", "5步", xStep(19.1), 388, 70, 31, { fontSize: 12.5, bold: true, color: C.navy3, align: "center" });
addLine("pure_start_marker", xStep(23), 446, xStep(23), 592, C.blue, 0.75, "dash");
addLine("pure_end_marker", xStep(33), 446, xStep(33), 592, C.blue, 0.75, "dash");
addLine("pure_arrow", xStep(23), 568, xStep(33), 568, C.blue, 1.0);
addText("pure_steps", "8步", xStep(26.5), 532, 80, 31, { fontSize: 12.5, bold: true, color: C.blue, align: "center" });

// Center summary table.
const dX = [613, 768, 929, 1080, 1219];
const dY = [698, 739, 780];
for (let r = 0; r < 2; r += 1) {
  for (let c = 0; c < 4; c += 1) {
    addRect(`dyn_table_${r}_${c}`, dX[c], dY[r], dX[c + 1] - dX[c], dY[r + 1] - dY[r], { color: C.ivory, transparency: 100 }, {
      color: "4E6176",
      width: 0.6,
    });
  }
}
const dRows = [
  ["━  Meta-RF", "突变前：+2.0 dB", "最低点：−4.0 dB", "恢复约：5步"],
  ["┄  Pure DRL", "突变前：−0.5 dB", "最低点：−5.5 dB", "恢复约：8步"],
];
for (let r = 0; r < 2; r += 1) {
  for (let c = 0; c < 4; c += 1) {
    addText(`dyn_table_text_${r}_${c}`, dRows[r][c], dX[c] + 6, dY[r], dX[c + 1] - dX[c] - 12, dY[r + 1] - dY[r], {
      fontSize: 9.5,
      bold: c === 0 || c === 3,
      color: r === 0 ? C.navy3 : C.blue,
      align: c === 0 ? "left" : "center",
    });
  }
}

// Right evidence cards.
addRect("metric_51_card", 1268, 265, 349, 143, { color: C.ivory, transparency: 100 }, { color: C.navy3, width: 0.9 }, false, true);
addText("metric_51", "+5.1 dB", 1292, 279, 300, 81, {
  fontSize: 34,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("metric_51_label", "Meta-RF相对Pure DRL", 1290, 360, 305, 37, {
  fontSize: 14,
  bold: true,
  color: C.ink,
  align: "center",
});
addRect("metric_375_card", 1268, 422, 349, 142, { color: C.ivory, transparency: 100 }, { color: C.navy3, width: 0.9 }, false, true);
addText("metric_375", "37.5 %", 1293, 432, 300, 78, {
  fontSize: 34,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("metric_375_label", "恢复步数减少", 1293, 510, 300, 38, {
  fontSize: 14,
  color: C.ink,
  align: "center",
});
addRect("latency_card", 1268, 581, 349, 155, { color: C.orangePale }, { color: C.orange, width: 0.9 }, false, true);
addText("latency_value", "99.6", 1280, 589, 136, 69, {
  fontSize: 27,
  bold: true,
  color: C.orange,
  align: "right",
});
addText("latency_unit", "ms", 1419, 604, 49, 46, {
  fontSize: 17,
  bold: true,
  color: C.orange,
});
addLine("latency_divider", 1284, 666, 1600, 666, C.orange, 0.9, "dash");
addLine("latency_label_separator", 1476, 601, 1476, 650, C.orange, 0.7);
addText("latency_label", "当前仿真实现耗时", 1483, 604, 121, 46, {
  fontSize: 8.5,
  bold: true,
  color: C.ink,
  align: "center",
});
addText("latency_warning", "尚未满足50 μs工程时延", 1287, 679, 311, 42, {
  fontSize: 15.5,
  bold: true,
  color: C.red,
  align: "center",
});
addRect("caveat_card", 1260, 748, 365, 42, { color: C.greyPale }, { color: "9A9A96", width: 0.7 }, false, true);
addCrop("caveat_info", "info", 1268, 751, 38, 38);
addText("caveat_text", "耗时采用专利说明书中的保守口径", 1310, 750, 304, 37, {
  fontSize: 9.7,
  color: C.ink,
  align: "center",
});

// Bottom conclusion band.
addRect("conclusion_surface", 25, 818, 1618, 90, { color: C.navy2 }, null, true, true);
addCrop("conclusion_check", "check", 132, 831, 65, 64);
addText("conclusion_text", "算法有效性已形成证据闭环，后续重点是实时化、鲁棒性与部署验证", 220, 830, 1300, 64, {
  fontSize: 20.5,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("source_footer", "来源：E11 / E12 / E13；S2:p11–12,p18–20；S3:p4", 1325, 892, 290, 14, {
  fontSize: 6.5,
  color: "C5D7E9",
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
fs.mkdirSync(`${ROOT}/pages`, { recursive: true });
pptx.writeFile({ fileName: OUTPUT });
