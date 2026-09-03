const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-05.pptx`;
const ICON_DIR = `${ROOT}/assets/icons/tabler-outline`;
const CROP_DIR = `${ROOT}/assets/slide-05-blueprint-icons`;
const ICONS = {
  database: `${ICON_DIR}/database.svg`,
  settings: `${ICON_DIR}/settings.svg`,
  scale: `${ICON_DIR}/scale.svg`,
  satellite: `${ICON_DIR}/satellite.svg`,
  car: `${ICON_DIR}/car.svg`,
  antenna: `${ICON_DIR}/antenna.svg`,
  clock: `${ICON_DIR}/clock.svg`,
  gauge: `${ICON_DIR}/gauge.svg`,
  alert: `${ICON_DIR}/alert-triangle.svg`,
  school: `${ICON_DIR}/school.svg`,
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
const sx = W / 1672;
const sy = H / 941;
const B = (x, y, w, h) => ({ x: x * sx, y: y * sy, w: w * sx, h: h * sy });
const C = {
  ivory: "FCFAF5",
  navy: "12355B",
  navy2: "07345E",
  navy3: "062B50",
  blue: "2E6DB4",
  blue2: "4A87C5",
  pale: "EEF4FA",
  pale2: "E5EFF8",
  card: "FBFCFD",
  line: "6C89A8",
  grey: "4F565D",
  mid: "8795A5",
  white: "FFFFFF",
  ink: "101820",
  warning: "D99A16",
  warningPale: "FFF9EC",
  red: "D0201C",
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
    rectRadius: rounded ? 0.05 : undefined,
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
function addLine(id, x1, y1, x2, y2, color = C.navy, width = 1.3, dash = "solid", endArrow = null) {
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
  slide.addShape(pptx.ShapeType.line, {
    ...box,
    flipV: dx * dy < 0,
    line,
  });
}
function addRightArrow(id, x1, x2, cy, color = C.navy) {
  addRect(`${id}_stem`, x1, cy - 2, Math.max(2, x2 - x1 - 13), 4, { color });
  slide.addShape(pptx.ShapeType.triangle, {
    ...B(x2 - 14, cy - 9, 16, 18),
    rotate: 90,
    fill: { color },
    line: { color, transparency: 100 },
  });
}
function addDownArrow(id, cx, y1, y2, color = C.navy, dashed = false) {
  if (dashed) {
    addLine(`${id}_line`, cx, y1, cx, y2 - 10, color, 1.2, "dash");
  } else {
    addRect(`${id}_stem`, cx - 1.4, y1, 2.8, Math.max(2, y2 - y1 - 9), { color });
  }
  slide.addShape(pptx.ShapeType.triangle, {
    ...B(cx - 6, y2 - 11, 12, 12),
    rotate: 180,
    fill: { color },
    line: { color, transparency: 100 },
  });
}
function addPolyline(id, points, color, width = 1.5) {
  for (let i = 0; i < points.length - 1; i += 1) {
    addLine(`${id}_${i}`, points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], color, width);
  }
}
function svgData(path, color) {
  const hex = `#${color}`;
  const svg = fs
    .readFileSync(path, "utf8")
    .replaceAll("currentColor", hex)
    .replace(/stroke="[^"]*"/g, `stroke="${hex}"`);
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}
function addIcon(id, path, x, y, w, h, color) {
  slide.addImage({ data: svgData(path, color), ...B(x, y, w, h), altText: id });
}
function addCrop(id, name, x, y, w, h) {
  slide.addImage({
    path: `${CROP_DIR}/${name}.png`,
    ...B(x, y, w, h),
    altText: id,
  });
}
function addNode(id, x, y, w, h, title) {
  addRect(id, x, y, w, h, { color: C.card }, { color: C.line, width: 0.75 }, true);
  addText(`${id}_title`, title, x + 7, y + 7, w - 14, 27, {
    fontSize: 11,
    bold: true,
    color: C.ink,
    align: "center",
  });
}
function addGrid(id, x, y, cols, rows, cellW, cellH, fill = C.pale2, line = C.navy) {
  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < cols; c += 1) {
      addRect(`${id}_${r}_${c}`, x + c * cellW, y + r * cellH, cellW - 3, cellH - 3, { color: fill }, { color: line, width: 0.55 }, true);
    }
  }
}

// Header.
addRect("page_badge_body", 8, 5, 72, 61, { color: C.navy3 });
slide.addShape(pptx.ShapeType.triangle, {
  ...B(71, 5, 30, 61),
  rotate: 90,
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addPlacement("page_badge", B(8, 5, 92, 61));
addText("page_number", "05", 25, 12, 52, 43, {
  fontSize: 18,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 357, 14, 916, 41, {
  fontSize: 24.5,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addLine("header_separator", 1312, 11, 1312, 59, "8A8A8A", 0.8);
addText("section_label", "研究内容｜分层系统架构", 1340, 20, 305, 32, {
  fontSize: 12.5,
  bold: true,
  color: C.navy,
  align: "right",
}, true);
addRect("top_rule", 0, 66, 1672, 4, { color: C.navy3 });
addText("main_title", "分层架构将场景级战略判断与逐chirp战术执行解耦", 255, 91, 1080, 45, {
  fontSize: 22,
  bold: true,
  color: C.navy3,
  align: "center",
}, true);
addText("subtitle", "上层识别“应探索哪个维度”，下层回答“下一步采用哪个具体参数”", 312, 147, 1022, 31, {
  fontSize: 13,
  color: C.ink,
  align: "center",
}, true);

// Meta-policy layer surface and behind-card connectors.
addRect("meta_layer_surface", 15, 182, 1308, 223, { color: C.pale, transparency: 8 }, { color: C.navy, width: 0.65 }, true, true);
addRightArrow("meta_arrow_1", 396, 453, 286);
addRightArrow("meta_arrow_2", 614, 672, 286);
addRightArrow("meta_arrow_3", 830, 891, 286);
addRightArrow("meta_arrow_4", 1067, 1151, 286);
addText("meta_layer_label", "元策略层\n场景级战略判断", 28, 238, 145, 82, {
  fontSize: 10,
  bold: true,
  color: C.navy3,
  align: "center",
  lineSpacingMultiple: 0.9,
});
addNode("meta_history", 217, 198, 179, 192, "SINR与动作历史");
addNode("meta_features", 454, 199, 160, 190, "12维特征");
addNode("meta_rf", 673, 201, 157, 188, "Meta-RF");
addNode("meta_confidence", 892, 201, 175, 188, "策略标签与置信度 p");

// History node: exact non-text visual restored from the approved blueprint.
addCrop("history_visual", "history-visual", 233, 241, 147, 56);
const historyLines = ["• 当前SINR", "• 干扰类型指示", "• 最近动作序列", "• 场景上下文"];
for (let i = 0; i < historyLines.length; i += 1) {
  addText(`history_line_${i}`, historyLines[i], 231, 304 + i * 18, 151, 16, {
    fontSize: 7.3,
    color: C.ink,
    valign: "mid",
  });
}

// Feature grid.
addGrid("feature_grid", 482, 255, 4, 3, 27, 29, "D4E2F0", C.navy);
addText("feature_formula", "f₁   ···   f₁₂", 478, 347, 112, 27, {
  fontSize: 9,
  italic: true,
  color: C.ink,
  align: "center",
});

// Meta-RF classifier visual.
addCrop("meta_rf_tree", "meta-rf-tree", 697, 247, 110, 91);
addText("rf_caption", "随机森林分类器", 690, 349, 124, 28, {
  fontSize: 7.6,
  color: C.ink,
  align: "center",
});

// Confidence chart.
addCrop("confidence_chart", "confidence-chart", 918, 249, 122, 97);
addText("confidence_formula", "p ∈ [0,1]", 918, 350, 121, 27, {
  fontSize: 9,
  italic: true,
  color: C.ink,
  align: "center",
});

// Strategy output cards.
const strategies = [
  ["“freq_only”", "（频率维度）", 199],
  ["“time_only”", "（时延维度）", 267],
  ["“joint”", "（联合维度）", 335],
];
for (const [name, desc, y] of strategies) {
  addRect(`strategy_${y}`, 1152, y, 155, 55, { color: C.card }, { color: C.line, width: 0.65 }, true);
  addText(`strategy_name_${y}`, name, 1160, y + 8, 139, 21, {
    fontSize: 8.9,
    bold: true,
    color: C.navy,
    align: "center",
  });
  addText(`strategy_desc_${y}`, desc, 1160, y + 30, 139, 17, {
    fontSize: 7.2,
    color: C.navy,
    align: "center",
  });
}
addLine("strategy_split_1", 1080, 285, 1144, 218, C.navy, 1.1, "solid", "triangle");
addLine("strategy_split_2", 1080, 294, 1144, 294, C.navy, 1.1, "solid", "triangle");
addLine("strategy_split_3", 1080, 303, 1144, 365, C.navy, 1.1, "solid", "triangle");

// DAM soft-guidance band and vertical coupling.
for (const x of [535, 753, 920]) addDownArrow(`meta_to_dam_${x}`, x, 391, 429, C.ink, true);
addRect("dam_band_surface", 218, 430, 997, 57, { color: C.pale, transparency: 2 }, { color: C.navy, width: 0.8, dash: "dash" }, true, true);
addCrop("dam_gears", "dam-gears", 378, 434, 66, 47);
addText("dam_label", "DAM软引导", 473, 440, 146, 33, {
  fontSize: 11,
  bold: true,
  color: C.navy3,
  align: "center",
});
addLine("dam_divider_1", 630, 439, 630, 476, C.navy, 0.7, "dash");
addText("dam_bonus", "bonus = 12.0 × p²", 670, 440, 201, 33, {
  fontSize: 11,
  bold: true,
  color: C.navy3,
  align: "center",
});
addLine("dam_divider_2", 884, 439, 884, 476, C.navy, 0.7, "dash");
addText("dam_hold", "策略至少保持5步", 908, 440, 231, 33, {
  fontSize: 10.7,
  bold: true,
  color: C.navy3,
  align: "center",
});

// Execution layer surface and connectors.
addRect("execution_layer_surface", 15, 510, 1308, 188, { color: C.pale, transparency: 8 }, { color: C.navy, width: 0.65 }, true, true);
addRightArrow("exec_arrow_1", 384, 427, 596);
addRightArrow("exec_arrow_2", 643, 686, 596);
addRightArrow("exec_arrow_3", 861, 905, 596);
addRightArrow("exec_arrow_4", 1071, 1116, 596);
for (const x of [364, 540, 754, 987]) addDownArrow(`dam_to_exec_${x}`, x, 487, 523, C.ink, true);
addText("execution_layer_label", "执行层\n逐chirp战术动作", 29, 553, 142, 80, {
  fontSize: 9.8,
  bold: true,
  color: C.navy3,
  align: "center",
  lineSpacingMultiple: 0.9,
});
addNode("exec_state", 197, 524, 187, 163, "状态序列");
addNode("exec_dqn", 428, 524, 215, 163, "Double DQN+GRU");
addNode("exec_q_bonus", 687, 524, 174, 163, "Q 值 + bonus");
addNode("exec_epsilon", 906, 524, 165, 163, "ε-greedy");
addNode("exec_output", 1117, 524, 195, 163, "(fc_index, td_index)");

// State sequence.
addCrop("state_sequence", "state-sequence", 212, 564, 160, 50);
const stateLines = ["• 最近N=32 chirp观测", "• SINR序列", "• 选定维度上下文"];
for (let i = 0; i < stateLines.length; i += 1) {
  addText(`state_line_${i}`, stateLines[i], 211, 616 + i * 18, 159, 16, {
    fontSize: 7.1,
    color: C.ink,
  });
}

// Double DQN visual; GRU remains a native editable cell.
addCrop("dqn_network", "dqn-network", 444, 560, 117, 76);
addRightArrow("network_to_gru", 552, 565, 601, C.navy3);
addRect("gru_cell", 564, 576, 63, 53, { color: C.card }, { color: C.line, width: 0.65 }, true);
addText("gru_label", "GRU", 569, 580, 53, 19, {
  fontSize: 8.5,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("gru_loop", "↻", 576, 598, 40, 25, {
  fontSize: 16,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("dqn_caption", "时序建模 + 价值估计", 452, 643, 170, 27, {
  fontSize: 8,
  color: C.ink,
  align: "center",
});

// Q bars.
addLine("q_axis", 704, 645, 845, 645, C.ink, 0.8);
for (const [x, h, label] of [[714,55,"Q₁"],[752,47,"Q₂"],[824,61,"Qₙ"]]) {
  addRect(`qbar_${label}`, x, 644 - h, 15, h, { color: C.blue2 }, { color: C.navy3, width: 0.55 });
  addText(`qlabel_${label}`, label, x - 5, 565, 25, 20, {
    fontSize: 7.3,
    color: C.ink,
    align: "center",
  });
}
addText("q_ellipsis", "···", 782, 583, 28, 24, { fontSize: 11, color: C.ink, align: "center" });
addText("q_bonus_caption", "+ bonus", 711, 650, 126, 23, {
  fontSize: 8.7,
  bold: true,
  color: C.ink,
  align: "center",
});

// Epsilon-greedy and action map.
addCrop("epsilon_scale", "epsilon-scale", 944, 562, 98, 70);
addText("epsilon_caption", "探索(ε) / 利用(1−ε)", 920, 642, 138, 28, {
  fontSize: 7.8,
  color: C.ink,
  align: "center",
});
addCrop("action_grid", "action-grid", 1179, 565, 71, 69);
addText("action_caption_1", "频率索引 / 时延索引", 1139, 640, 154, 18, {
  fontSize: 7.4,
  color: C.ink,
  align: "center",
});
addText("action_caption_2", "具体参数组合", 1139, 658, 154, 16, {
  fontSize: 7.3,
  color: C.ink,
  align: "center",
});

// Environment and feedback loops.
addLine("feedback_left_horizontal", 98, 772, 145, 772, C.navy3, 1.4);
addLine("feedback_left_vertical", 100, 771, 100, 405, C.navy3, 1.4);
slide.addShape(pptx.ShapeType.triangle, {
  ...B(93, 398, 14, 14),
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addLine("feedback_right_horizontal", 1130, 772, 1245, 772, C.navy3, 1.4);
addLine("feedback_right_vertical", 1245, 772, 1245, 703, C.navy3, 1.4);
slide.addShape(pptx.ShapeType.triangle, {
  ...B(1238, 694, 14, 14),
  fill: { color: C.navy3 },
  line: { color: C.navy3, transparency: 100 },
});
addText("feedback_sinr", "反馈: SINR\n• 实测SINR\n• 干扰强度变化\n• 检测结果", 157, 728, 141, 88, {
  fontSize: 7.3,
  color: C.ink,
  valign: "top",
  lineSpacingMultiple: 0.82,
});
addText("feedback_action", "反馈: 动作记录\n• fc_index\n• td_index\n• 时间戳", 1003, 727, 133, 91, {
  fontSize: 7.3,
  color: C.ink,
  valign: "top",
  lineSpacingMultiple: 0.82,
});
addRect("environment_panel", 304, 725, 678, 97, { color: "FFFDF8" }, { color: "A78958", width: 0.65 }, true, true);
addText("environment_title", "FMCW雷达环境", 519, 737, 251, 32, {
  fontSize: 11,
  bold: true,
  color: C.navy3,
  align: "center",
});
addCrop("environment_satellite", "environment-satellite", 366, 750, 59, 62);
addCrop("environment_wave", "environment-wave", 466, 752, 84, 61);
addCrop("environment_small_cars", "environment-small-cars", 608, 766, 89, 48);
addCrop("environment_large_cars", "environment-large-cars", 733, 758, 84, 57);
addCrop("environment_antenna", "environment-antenna", 853, 750, 62, 63);

// Right rail: time-scale comparison.
addRect("time_scale_surface", 1381, 131, 266, 452, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 0.75 }, false, true);
addRect("time_scale_header", 1381, 131, 266, 65, { color: C.navy3 });
addText("time_scale_title", "时间尺度对比", 1421, 150, 188, 33, {
  fontSize: 13,
  bold: true,
  color: C.white,
  align: "center",
});
addCrop("meta_clock", "meta-clock", 1393, 234, 99, 99);
addText("meta_scale_heading", "元策略层:", 1500, 236, 132, 24, {
  fontSize: 9.7,
  bold: true,
  color: C.navy3,
});
addText("meta_scale_body", "测试阶段每\nK=3步触发", 1500, 266, 132, 57, {
  fontSize: 9.2,
  color: C.ink,
  valign: "top",
  lineSpacingMultiple: 0.92,
});
addText("meta_scale_note", "(3个chirp更新一次)", 1461, 339, 171, 27, {
  fontSize: 8.4,
  color: C.ink,
  align: "center",
});
addLine("time_scale_divider", 1394, 400, 1633, 400, C.line, 0.7, "dash");
addCrop("exec_gauge", "execution-gauge", 1397, 442, 96, 78);
addText("exec_scale_heading", "执行层:", 1500, 444, 132, 24, {
  fontSize: 9.7,
  bold: true,
  color: C.navy3,
});
addText("exec_scale_body", "逐chirp运行", 1500, 474, 132, 30, {
  fontSize: 9.2,
  color: C.ink,
});
addText("exec_scale_note", "(每个chirp都决策)", 1461, 517, 171, 27, {
  fontSize: 8.4,
  color: C.ink,
  align: "center",
});

// Engineering caveat.
addRect("warning_surface", 1375, 637, 272, 174, { color: C.warningPale }, { color: "A78958", width: 0.7 }, true, true);
addCrop("warning_icon", "warning", 1392, 682, 70, 70);
addText("warning_title", "注意事项:", 1478, 661, 131, 29, {
  fontSize: 10.7,
  bold: true,
  color: C.navy3,
  align: "center",
});
addText("warning_text", "决策分工不等于\n当前实现已满足", 1476, 695, 146, 59, {
  fontSize: 9.2,
  bold: true,
  color: C.ink,
  valign: "top",
  breakLine: true,
  lineSpacingMultiple: 0.9,
});
addText("warning_latency", "50 μs工程时延", 1476, 759, 151, 27, {
  fontSize: 10.5,
  bold: true,
  color: C.red,
  align: "center",
});

// Conclusion band.
addRect("conclusion_band_surface", 24, 847, 1625, 78, { color: C.navy3 }, null, true, true);
addCrop("school_icon", "school", 53, 853, 68, 68);
addText("conclusion_text", "宏观认知与微观控制解耦，使快速执行获得结构化探索方向", 320, 867, 1120, 41, {
  fontSize: 17.5,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("source_footer", "来源：E04 / E05 / E10；S2:p3,p9–11；S3:p2", 1250, 904, 362, 14, {
  fontSize: 6.5,
  color: "C5D7E9",
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
fs.mkdirSync(`${ROOT}/pages`, { recursive: true });
pptx.writeFile({ fileName: OUTPUT });
