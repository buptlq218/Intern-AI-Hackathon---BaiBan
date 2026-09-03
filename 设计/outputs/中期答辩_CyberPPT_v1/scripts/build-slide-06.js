const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-06.pptx`;
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
  blue: "2569C3",
  blueMid: "4D87D0",
  bluePale: "DDEAF8",
  panel: "FFFFFF",
  line: "7891AA",
  grid: "B8BEC5",
  grey: "565B61",
  ink: "101820",
  white: "FFFFFF",
  red: "D91E18",
  redPale: "F9DEDC",
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
function addLine(id, x1, y1, x2, y2, color = C.navy, width = 1.2, dash = "solid", endArrow = null) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const box = B(
    Math.min(x1, x2),
    Math.min(y1, y2),
    Math.max(Math.abs(dx), 0.5),
    Math.max(Math.abs(dy), 0.5)
  );
  const line = { color, width, dash };
  if (endArrow) line.endArrowType = endArrow;
  slide.addShape(pptx.ShapeType.line, { ...box, flipV: dx * dy < 0, line });
}
function addPolyline(id, points, color, width = 1.5) {
  for (let i = 0; i < points.length - 1; i += 1) {
    addLine(`${id}_${i}`, points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], color, width);
  }
}
function addDownArrow(id, cx, y1, y2, color = C.navy3) {
  addRect(`${id}_stem`, cx - 1.2, y1, 2.4, Math.max(2, y2 - y1 - 8), { color });
  slide.addShape(pptx.ShapeType.triangle, {
    ...B(cx - 6, y2 - 11, 12, 12),
    rotate: 180,
    fill: { color },
    line: { color, transparency: 100 },
  });
}

// Header and narrative.
addRect("page_badge_body", 14, 7, 80, 63, { color: C.navy3 });
slide.addShape(pptx.ShapeType.triangle, {
  ...B(84, 7, 38, 63),
  rotate: 90,
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addPlacement("page_badge", B(14, 7, 107, 63));
addText("page_number", "06", 31, 15, 61, 45, {
  fontSize: 20,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 449, 16, 782, 40, {
  fontSize: 20,
  bold: true,
  color: C.navy3,
  align: "center",
}, true);
addText("section_label", "研究内容｜DRL执行层", 1368, 20, 281, 36, {
  fontSize: 12.5,
  bold: true,
  color: C.navy3,
  align: "right",
}, true);
addRect("top_rule", 107, 67, 1547, 3, { color: C.navy3 });
addText("main_title", "Double DQN+GRU执行层在9维动作空间中实现稳定的时序决策", 231, 107, 1203, 48, {
  fontSize: 25,
  bold: true,
  color: C.navy3,
  align: "center",
}, true);
addText("subtitle", "GRU负责记忆干扰演变，Double DQN降低Q值过估计，奖励函数约束策略抖动", 383, 176, 907, 34, {
  fontSize: 14.5,
  color: C.grey,
  align: "center",
}, true);

// Three main panel surfaces and headers.
addRect("network_panel_surface", 20, 231, 540, 588, { color: C.panel, transparency: 100 }, { color: "B5BCC4", width: 0.65 }, false, true);
addRect("training_panel_surface", 580, 231, 424, 588, { color: C.panel, transparency: 100 }, { color: "B5BCC4", width: 0.65 }, false, true);
addRect("reward_panel_surface", 1029, 231, 622, 588, { color: C.panel, transparency: 100 }, { color: "B5BCC4", width: 0.65 }, false, true);
for (const [id, x, w, title] of [
  ["network", 20, 540, "执行网络结构（在线网络）"],
  ["training", 580, 424, "训练机制与超参数设置"],
  ["reward", 1029, 622, "奖励函数设计与性能结果"],
]) {
  addRect(`${id}_header`, x, 231, w, 49, { color: C.navy3 });
  addText(`${id}_header_text`, title, x + 15, 241, w - 30, 31, {
    fontSize: 12.5,
    bold: true,
    color: C.white,
    align: "center",
  });
}

// Network panel.
const networkBlocks = [
  ["动作One-Hot（9维）+ 当前SINR", 61, 299, 398, 51, C.bluePale, C.navy3],
  ["Dense(16)×2", 61, 381, 345, 52, C.bluePale, C.navy3],
  ["GRU(32, stateful=True)", 61, 464, 345, 52, C.blueMid, C.white],
  ["Dense(64)", 61, 570, 345, 54, C.bluePale, C.navy3],
  ["Q值输出（9维）", 61, 662, 345, 54, C.bluePale, C.navy3],
];
for (let i = 0; i < networkBlocks.length; i += 1) {
  const [text, x, y, w, h, fill, color] = networkBlocks[i];
  addRect(`network_block_${i}`, x, y, w, h, { color: fill }, { color: "6D8CB0", width: 0.65 }, true);
  addText(`network_block_text_${i}`, text, x + 8, y + 7, w - 16, h - 14, {
    fontSize: 12,
    bold: i === 2,
    color,
    align: "center",
  });
}
for (const [i, cx, y1, y2] of [
  [0, 252, 350, 380],
  [1, 252, 433, 463],
  [2, 252, 516, 569],
  [3, 252, 624, 661],
]) addDownArrow(`network_arrow_${i}`, cx, y1, y2);
addLine("hidden_top", 406, 490, 480, 490, C.navy3, 1.2, "dash");
addLine("hidden_right", 480, 490, 480, 690, C.navy3, 1.2, "dash");
addLine("hidden_bottom", 480, 690, 406, 690, C.navy3, 1.2, "dash");
slide.addShape(pptx.ShapeType.triangle, {
  ...B(399, 483, 13, 14),
  rotate: 270,
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addText("hidden_state_text", "隐藏状态 hₜ\n（带入下一步）", 428, 554, 117, 55, {
  fontSize: 9.5,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("network_note", "注：输出对应9维动作的Q值，选择最大Q值对应的动作执行", 46, 760, 489, 30, {
  fontSize: 9.5,
  bold: true,
  color: C.navy3,
  align: "center",
});

// Training table.
const trainingRows = [
  ["训练规模", "15000 episodes"],
  ["交互长度", "每episode 30步"],
  ["经验回放", "容量50000"],
  ["批次大小", "256"],
  ["折扣因子 γ", "0.95"],
  ["软更新系数 τ", "0.005"],
  ["探索率 ε", "1.0→0.05"],
  ["学习率", "1e-3→1e-5"],
];
const rowH = 53.6;
for (let i = 0; i < trainingRows.length; i += 1) {
  const y = 299 + i * rowH;
  addRect(`training_label_${i}`, 596, y, 157, rowH, { color: C.bluePale }, { color: C.grid, width: 0.55 });
  addRect(`training_value_${i}`, 753, y, 234, rowH, { color: C.panel }, { color: C.grid, width: 0.55 });
  addText(`training_label_text_${i}`, trainingRows[i][0], 603, y + 6, 143, rowH - 12, {
    fontSize: 10.5,
    bold: true,
    color: C.navy3,
    align: "center",
  });
  addText(`training_value_text_${i}`, trainingRows[i][1], 760, y + 6, 220, rowH - 12, {
    fontSize: 10.5,
    color: C.ink,
    align: "center",
  });
}
addText(
  "training_note",
  "注：15000 episodes来自文字记录；Double DQN、软更新\n与经验回放共同稳定训练",
  598,
  750,
  379,
  53,
  { fontSize: 9.5, bold: true, color: C.navy3, align: "center", breakLine: true }
);

// Reward panel headings.
addText("positive_heading", "奖励：SINR ≥ 0 dB（正向激励）", 1066, 301, 267, 29, {
  fontSize: 9.5,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("negative_heading", "奖励：SINR < 0 dB（线性惩罚）", 1370, 301, 259, 29, {
  fontSize: 9.5,
  bold: true,
  color: C.red,
  align: "center",
});

// Positive reward chart.
const pos = { x: 1070, y: 350, w: 250, h: 175 };
for (let i = 0; i < 28; i += 1) {
  const xv = (i / 27) * 32;
  const value = 1 - Math.exp(-xv / 7.5);
  const px = pos.x + (i / 28) * pos.w;
  const barW = pos.w / 28 + 0.8;
  const py = pos.y + pos.h * (1 - value);
  addRect(`pos_fill_${i}`, px, py, barW, Math.max(0.5, pos.y + pos.h - py), { color: C.bluePale, transparency: 5 });
}
addLine("pos_axis_x", pos.x, pos.y + pos.h, pos.x + pos.w + 9, pos.y + pos.h, C.ink, 0.8, "solid", "triangle");
addLine("pos_axis_y", pos.x, pos.y + pos.h, pos.x, pos.y - 4, C.ink, 0.8);
slide.addShape(pptx.ShapeType.triangle, {
  ...B(pos.x - 5, pos.y - 13, 10, 11),
  fill: { color: C.ink },
  line: { color: C.ink, transparency: 100 },
});
const posCurve = [];
for (let i = 0; i <= 32; i += 1) {
  const value = 1 - Math.exp(-i / 7.5);
  posCurve.push([pos.x + (i / 32) * pos.w, pos.y + pos.h * (1 - value)]);
}
addPolyline("positive_curve", posCurve, C.blue, 1.7);
addLine("positive_one_line", pos.x, pos.y + 3, pos.x + pos.w, pos.y + 3, "6D8CB0", 0.7, "dash");
addText("pos_y_label", "r", 1047, 334, 21, 20, { fontSize: 9, italic: true, color: C.ink, align: "center" });
addText("pos_ticks_y", "1.0\n\n0.5\n\n0", 1038, 352, 29, 180, {
  fontSize: 8.5,
  color: C.ink,
  align: "right",
  valign: "top",
});
addText("pos_ticks_x", "0              10              20              30", 1062, 530, 267, 21, {
  fontSize: 8.5,
  color: C.ink,
  align: "center",
});
addText("pos_x_label", "SINR (dB)", 1115, 553, 160, 28, { fontSize: 9.5, color: C.ink, align: "center" });
addText("positive_formula", "r = 1 − e^(−SINR/10)", 1136, 431, 165, 30, {
  fontSize: 10.5,
  italic: true,
  color: C.ink,
  align: "center",
});

// Negative reward chart.
const neg = { x: 1380, y: 350, w: 239, h: 175 };
for (let i = 0; i < 24; i += 1) {
  const value = i / 23;
  const px = neg.x + value * neg.w;
  const py = neg.y + neg.h * (1 - value);
  addRect(`neg_fill_${i}`, px, py, neg.w / 24 + 0.8, Math.max(0.5, neg.y + neg.h - py), { color: C.redPale, transparency: 5 });
}
addLine("neg_axis_x", neg.x, neg.y + neg.h, neg.x + neg.w + 8, neg.y + neg.h, C.ink, 0.8, "solid", "triangle");
addLine("neg_axis_y", neg.x, neg.y + neg.h, neg.x, neg.y - 4, C.ink, 0.8);
slide.addShape(pptx.ShapeType.triangle, {
  ...B(neg.x - 5, neg.y - 13, 10, 11),
  fill: { color: C.ink },
  line: { color: C.ink, transparency: 100 },
});
addLine("negative_curve", neg.x, neg.y + neg.h, neg.x + neg.w, neg.y, C.red, 1.7);
slide.addShape(pptx.ShapeType.ellipse, {
  ...B(neg.x + neg.w - 5, neg.y - 5, 10, 10),
  fill: { color: C.panel },
  line: { color: C.ink, width: 0.7 },
});
addText("neg_y_label", "r", 1357, 334, 21, 20, { fontSize: 9, italic: true, color: C.ink, align: "center" });
addText("neg_ticks_y", "0\n\n−0.5\n\n−1.0", 1340, 352, 36, 180, {
  fontSize: 8.5,
  color: C.ink,
  align: "right",
  valign: "top",
});
addText("neg_ticks_x", "−30          −20          −10            0", 1370, 530, 259, 21, {
  fontSize: 8.5,
  color: C.ink,
  align: "center",
});
addText("neg_x_label", "SINR (dB)", 1420, 553, 160, 28, { fontSize: 9.5, color: C.ink, align: "center" });
addText("negative_formula", "r = SINR / 10", 1483, 455, 138, 28, {
  fontSize: 10.5,
  italic: true,
  color: C.ink,
  align: "center",
});

// Switch penalty and metric.
addRect("switch_penalty_panel", 1049, 603, 580, 99, { color: C.panel, transparency: 100 }, { color: "6D8CB0", width: 0.65 }, true);
addText("switch_penalty_title", "切换惩罚（约束策略抖动）", 1130, 611, 416, 33, {
  fontSize: 12,
  bold: true,
  color: C.navy3,
  align: "center",
});
addRect("switch_formula_box", 1133, 653, 383, 42, { color: "F7F7F7" }, { color: "8FA3B7", width: 0.6 }, true);
addText("switch_formula", "r_AC = −0.05 × 切换次数", 1150, 658, 349, 32, {
  fontSize: 13,
  italic: true,
  color: C.navy3,
  align: "center",
});
addLine("metric_separator", 1040, 719, 1638, 719, "6D8CB0", 0.7, "dash");
addText("metric_label", "联合策略最终SINR", 1050, 746, 257, 46, {
  fontSize: 14,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("metric_value", "9.50 ± 0.57", 1309, 735, 277, 66, {
  fontSize: 29,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("metric_unit", "dB", 1584, 762, 45, 32, {
  fontSize: 13,
  color: C.navy3,
  align: "center",
});

// Conclusion.
addRect("conclusion_band_surface", 20, 843, 1633, 84, { color: C.navy3 }, null, false, true);
addText("conclusion_text", "执行层已具备在联合时频空间中稳定寻优的能力", 390, 859, 900, 51, {
  fontSize: 19,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("source_footer", "来源：E05 / E06 / E07；S1:p6–12；S2:p4–6,p15–16", 1310, 908, 300, 14, {
  fontSize: 6.5,
  color: "C5D7E9",
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
fs.mkdirSync(`${ROOT}/pages`, { recursive: true });
pptx.writeFile({ fileName: OUTPUT });
