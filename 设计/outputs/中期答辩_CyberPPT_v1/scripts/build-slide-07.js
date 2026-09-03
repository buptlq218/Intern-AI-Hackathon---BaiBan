const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-07.pptx`;
const CROP_DIR = `${ROOT}/assets/slide-07-blueprint-icons`;
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
  bluePale: "E7F0F8",
  white: "FFFFFF",
  ink: "101820",
  grey: "565B61",
  line: "8BA0B5",
  grid: "8EA4B9",
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
function addDownArrow(id, cx, y1, y2, color = C.navy3) {
  addRect(`${id}_stem`, cx - 1.2, y1, 2.4, Math.max(2, y2 - y1 - 8), { color });
  slide.addShape(pptx.ShapeType.triangle, {
    ...B(cx - 6, y2 - 11, 12, 12),
    rotate: 180,
    fill: { color },
    line: { color, transparency: 100 },
  });
}
function addRightArrow(id, x1, x2, cy, color = C.navy3) {
  addRect(`${id}_stem`, x1, cy - 2, Math.max(2, x2 - x1 - 14), 4, { color });
  slide.addShape(pptx.ShapeType.triangle, {
    ...B(x2 - 15, cy - 9, 17, 18),
    rotate: 90,
    fill: { color },
    line: { color, transparency: 100 },
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
addRect("page_badge_body", 0, 0, 91, 72, { color: C.navy3 });
slide.addShape(pptx.ShapeType.triangle, {
  ...B(82, 0, 38, 72),
  rotate: 90,
  fill: { color: C.navy3 },
  line: { color: C.white, width: 0.7 },
});
addPlacement("page_badge", B(0, 0, 120, 73));
addText("page_number", "07", 21, 9, 60, 47, {
  fontSize: 20,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 437, 18, 781, 38, {
  fontSize: 20,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("section_label", "研究内容｜元策略控制器", 1338, 21, 305, 35, {
  fontSize: 12.5,
  bold: true,
  color: C.navy3,
  align: "right",
}, true);
addRect("top_rule", 0, 72, 1672, 4, { color: C.navy3 });
addText("main_title", "元控制器利用12维语义特征，把盲目探索转化为方向明确的策略引导", 182, 99, 1327, 51, {
  fontSize: 25,
  bold: true,
  color: C.ink,
  align: "center",
}, true);
addText("subtitle", "机会敏感性特征判断频域或时域的潜在收益，随机森林输出策略及置信度", 391, 163, 923, 38, {
  fontSize: 14.5,
  color: C.grey,
  align: "center",
}, true);

// Left feature matrix.
for (const y of [233, 359, 505, 614, 722]) {
  addLine(`feature_rule_${y}`, 31, y, 499, y, "B4B4B4", 0.55);
}
const featureGroups = [
  {
    id: "signal",
    icon: [48, 253, 90, 90],
    title: "信号质量统计（4维）：",
    count: "4维",
    formula: "μ、σ、Δ、SINR_min",
    titleBox: [176, 263, 275, 34],
    formulaBox: [176, 305, 290, 35],
  },
  {
    id: "action",
    icon: [47, 382, 89, 94],
    title: "动作行为（3维）：",
    count: "3维",
    formula: "H_action、频域切换率、\n时域切换率",
    titleBox: [176, 384, 275, 34],
    formulaBox: [176, 428, 290, 62],
  },
  {
    id: "shield",
    icon: [52, 518, 76, 85],
    title: "避干扰效能（2维）：",
    count: "2维",
    formula: "r_avoid、SINR增益",
    titleBox: [176, 526, 275, 34],
    formulaBox: [176, 567, 290, 35],
  },
  {
    id: "target",
    icon: [47, 625, 83, 85],
    title: "维度敏感性（3维）：",
    count: "3维",
    formula: "fc_gap、td_gap、fc_td_ratio",
    titleBox: [176, 632, 275, 34],
    formulaBox: [176, 674, 305, 35],
  },
];
for (const group of featureGroups) {
  addCrop(`feature_${group.id}_icon`, `feature-${group.id}`, ...group.icon);
  addText(`feature_${group.id}_title`, group.title, ...group.titleBox, {
    fontSize: 11,
    bold: true,
    color: C.navy3,
  });
  addText(`feature_${group.id}_count`, group.count, 455, group.titleBox[1], 43, 34, {
    fontSize: 11,
    bold: true,
    color: C.navy3,
    align: "right",
  });
  addText(`feature_${group.id}_formula`, group.formula, ...group.formulaBox, {
    fontSize: 11,
    italic: true,
    color: C.ink,
    breakLine: true,
  });
}
// Bracket and twelve-feature arrow.
addLine("feature_bracket_top", 500, 233, 518, 233, C.navy3, 1.0);
addLine("feature_bracket_upper", 518, 233, 536, 447, C.navy3, 1.0);
addLine("feature_bracket_mid", 536, 447, 536, 508, C.navy3, 1.0);
addLine("feature_bracket_lower", 536, 508, 518, 722, C.navy3, 1.0);
addLine("feature_bracket_bottom", 518, 722, 500, 722, C.navy3, 1.0);
addText("feature_total_label", "12维\n特征", 540, 448, 67, 72, {
  fontSize: 12,
  bold: true,
  color: C.navy3,
  align: "center",
});
addRightArrow("feature_to_rf", 606, 631, 472);

// Central RF pipeline.
addRect("rf_panel_surface", 631, 223, 347, 510, { color: C.ivory, transparency: 100 }, { color: "6D8CB0", width: 0.75 }, true, true);
addRect("rf_panel_header", 631, 223, 347, 55, { color: C.navy3 }, null, true);
addText("rf_panel_title", "随机森林（元策略分类器）", 671, 238, 270, 31, {
  fontSize: 12.5,
  bold: true,
  color: C.white,
  align: "center",
});
const rfStages = [
  ["rf-database", "4000个场景", 656, 292, 296, 57],
  ["rf-pie", "训练/测试 = 8:2", 656, 367, 296, 57],
  ["rf-clipboard", "5折交叉验证", 656, 442, 296, 57],
  ["rf-trees", "200棵树", 656, 518, 296, 57],
  ["rf-gear", "max_depth=12，leaf=5", 656, 590, 296, 57],
  ["rf-target", "准确率约80%—85%", 656, 665, 296, 57],
];
for (let i = 0; i < rfStages.length; i += 1) {
  const [icon, text, x, y, w, h] = rfStages[i];
  addRect(`rf_stage_${i}`, x, y, w, h, { color: "F7F8F8" }, { color: "93A8BC", width: 0.55 }, true);
  const crop = {
    "rf-database": [668, 289, 62, 62],
    "rf-pie": [669, 366, 61, 62],
    "rf-clipboard": [669, 441, 61, 64],
    "rf-trees": [666, 519, 67, 60],
    "rf-gear": [668, 593, 63, 63],
    "rf-target": [669, 666, 62, 62],
  }[icon];
  addCrop(`rf_stage_${i}_icon`, icon, ...crop);
  addText(`rf_stage_${i}_text`, text, x + 90, y + 8, 193, h - 16, {
    fontSize: 11,
    color: C.ink,
    align: "center",
  });
  if (i < rfStages.length - 1) {
    addDownArrow(`rf_arrow_${i}`, 700, y + h, rfStages[i + 1][3]);
    addDownArrow(`rf_arrow_right_${i}`, 812, y + h, rfStages[i + 1][3], "6D8CB0");
  }
}

// RF to strategy.
addLine("strategy_separator", 1014, 219, 1014, 754, "B6B6B6", 0.55, "dash");
addRightArrow("rf_to_strategy", 978, 1031, 472);

// Strategy table.
addRect("strategy_header", 1053, 223, 570, 55, { color: C.navy3 }, null, true);
addText("strategy_title", "三类策略输出（含置信度 p ∈ [0,1]）", 1120, 238, 437, 31, {
  fontSize: 12.5,
  bold: true,
  color: C.white,
  align: "center",
});
const colX = [1053, 1168, 1297, 1523, 1623];
const headerLabels = ["策略编号", "策略名称", "动作空间约束（下一层HRL）", "置信度 p"];
for (let c = 0; c < 4; c += 1) {
  addRect(`strategy_head_${c}`, colX[c], 292, colX[c + 1] - colX[c], 49, { color: "E5EBF0" }, { color: C.grid, width: 0.6 });
  addText(`strategy_head_text_${c}`, headerLabels[c], colX[c] + 5, 298, colX[c + 1] - colX[c] - 10, 37, {
    fontSize: 8.5,
    bold: true,
    color: C.ink,
    align: "center",
  });
}
const strategyRows = [
  ["1", "频域优先", "固定td，开放3个fc", "p₁"],
  ["2", "时域优先", "固定fc，开放3个td", "p₂"],
  ["3", "联合探索", "开放9个动作", "p₃"],
];
for (let r = 0; r < 3; r += 1) {
  const y = 341 + r * 56;
  for (let c = 0; c < 4; c += 1) {
    addRect(`strategy_${r}_${c}`, colX[c], y, colX[c + 1] - colX[c], 56, { color: C.ivory, transparency: 100 }, { color: C.grid, width: 0.6 });
  }
  slide.addShape(pptx.ShapeType.ellipse, {
    ...B(1091, y + 11, 34, 34),
    fill: { color: C.navy3 },
    line: { color: C.navy3, transparency: 100 },
  });
  addText(`strategy_num_${r}`, strategyRows[r][0], 1091, y + 11, 34, 34, {
    fontSize: 10,
    bold: true,
    color: C.white,
    align: "center",
  });
  addText(`strategy_name_${r}`, strategyRows[r][1], 1177, y + 8, 111, 40, {
    fontSize: 10,
    bold: true,
    color: C.navy3,
    align: "center",
  });
  addText(`strategy_constraint_${r}`, strategyRows[r][2], 1304, y + 8, 211, 40, {
    fontSize: 9.5,
    color: C.ink,
    align: "center",
  });
  addText(`strategy_conf_${r}`, strategyRows[r][3], 1530, y + 8, 86, 40, {
    fontSize: 11,
    italic: true,
    color: C.ink,
    align: "center",
  });
}

// Soft guidance and caveat.
addRect("soft_guidance_surface", 1053, 530, 570, 145, { color: C.ivory, transparency: 100 }, { color: "6D8CB0", width: 0.7 }, true, true);
addCrop("guidance_bulb", "guidance-bulb", 1063, 546, 98, 98);
addLine("guidance_divider", 1158, 548, 1158, 658, "8FA3B7", 0.65);
addText("guidance_title", "软引导机制（Soft Guidance）", 1175, 544, 420, 34, {
  fontSize: 12,
  bold: true,
  color: C.navy3,
});
addText("guidance_body", "•  bonus = 12.0 × p²\n•  min_strategy_steps = 5\n•  不强制屏蔽其他动作", 1175, 579, 420, 82, {
  fontSize: 10.5,
  color: C.ink,
  valign: "top",
  breakLine: true,
  lineSpacingMultiple: 0.86,
});
addRect("caveat_surface", 1044, 684, 587, 64, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 0.75, dash: "dash" }, true);
addCrop("caveat_warning", "warning", 1051, 691, 56, 52);
addText("caveat_text", "分类并非100%准确，因此采用软引导而非硬掩码", 1114, 694, 500, 43, {
  fontSize: 11,
  bold: true,
  color: C.ink,
  align: "center",
});

// Bottom conclusion.
addRect("conclusion_panel_surface", 35, 775, 1596, 113, { color: C.ivory, transparency: 100 }, { color: C.navy3, width: 0.9 }, true, true);
addCrop("conclusion_check", "conclusion-check", 61, 792, 76, 76);
addText("conclusion_statement", "元控制器判断的是“哪个维度存在更好的干扰空穴”", 169, 805, 742, 53, {
  fontSize: 17.5,
  bold: true,
  color: C.navy3,
  align: "center",
}, true);
addLine("conclusion_divider", 931, 790, 931, 874, "9BA8B5", 0.65);
addText("conclusion_explanation", "通过12维语义特征感知机会，随机森林识别最有潜力的探索方向，\n以软引导将探索资源集中到收益更高的维度，提升整体抗干扰效能。", 965, 799, 607, 65, {
  fontSize: 10.5,
  color: C.ink,
  breakLine: true,
  lineSpacingMultiple: 0.9,
});
addText("source_footer", "来源：E08 / E09 / E10；S1:p14–16；S2:p7–10,p16–17；S3:p3", 1300, 868, 305, 14, {
  fontSize: 6.5,
  color: C.grey,
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
fs.mkdirSync(`${ROOT}/pages`, { recursive: true });
pptx.writeFile({ fileName: OUTPUT });
