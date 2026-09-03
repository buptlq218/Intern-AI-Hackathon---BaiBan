const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-03.pptx`;
const ICON_DIR = `${ROOT}/assets/icons/tabler-outline`;
const ICONS = {
  clock: `${ICON_DIR}/clock.svg`,
  puzzle: `${ICON_DIR}/puzzle.svg`,
  chart: `${ICON_DIR}/chart-bar-popular.svg`,
  hierarchy: `${ICON_DIR}/hierarchy.svg`,
  eye: `${ICON_DIR}/eye.svg`,
  target: `${ICON_DIR}/target.svg`,
  atom: `${ICON_DIR}/atom.svg`,
  shield: `${ICON_DIR}/shield-check.svg`,
  clockBolt: `${ICON_DIR}/clock-bolt.svg`,
  brain: `${ICON_DIR}/brain.svg`,
  antenna: `${ICON_DIR}/antenna.svg`,
  cpu: `${ICON_DIR}/cpu.svg`,
  flask: `${ICON_DIR}/flask.svg`,
  trophy: `${ICON_DIR}/trophy.svg`,
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
  paper: "F7F5EF",
  navy: "12355B",
  navy2: "0A345D",
  navy3: "062B50",
  ink: "101820",
  grey: "535A61",
  mid: "AAB3BC",
  pale: "E8F0F6",
  white: "FFFFFF",
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

function svgData(path, color) {
  const hex = `#${color}`;
  const svg = fs
    .readFileSync(path, "utf8")
    .replaceAll("currentColor", hex)
    .replace(/stroke="[^"]*"/g, `stroke="${hex}"`);
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}

function addIcon(id, path, x, y, w, h, color = C.navy) {
  const box = B(x, y, w, h);
  slide.addImage({ data: svgData(path, color), ...box, altText: id });
}

function addDownArrow(id, cx, y1, y2, color = C.navy) {
  addRect(`${id}_stem`, cx - 1.2, y1, 2.4, Math.max(2, y2 - y1 - 9), { color }, null, false);
  const head = B(cx - 6, y2 - 11, 12, 12);
  slide.addShape(pptx.ShapeType.triangle, {
    ...head,
    rotate: 180,
    fill: { color },
    line: { color, transparency: 100 },
  });
}

function addRightArrow(id, x1, x2, cy, color = C.navy) {
  addRect(`${id}_stem`, x1, cy - 1.2, Math.max(2, x2 - x1 - 11), 2.4, { color }, null, false);
  const head = B(x2 - 13, cy - 7, 14, 14);
  slide.addShape(pptx.ShapeType.triangle, {
    ...head,
    rotate: 90,
    fill: { color },
    line: { color, transparency: 100 },
  });
}

// Page chrome.
addRect("page_badge", 0, 3, 92, 55, { color: C.navy3 }, null, false, true);
addText("page_number", "03", 24, 10, 46, 40, {
  fontSize: 16,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText(
  "header_deck_title",
  "基于分层强化学习的FMCW雷达抗干扰策略优化",
  507,
  17,
  557,
  31,
  { fontSize: 11.5, bold: true, color: C.navy, align: "center" },
  true
);
addText("section_label", "研究内容｜研究问题与技术路线", 1272, 17, 368, 31, {
  fontSize: 12,
  bold: true,
  color: C.navy,
  align: "right",
}, true);
addRect("top_rule", 0, 57, 1660, 3, { color: C.navy });

addText(
  "main_title",
  "研究核心是同时解决时间尺度分离、结构信息缺失和动态探索效率问题",
  148,
  77,
  1240,
  41,
  { fontSize: 20.8, bold: true, color: "090B0E", align: "center" },
  true
);
addText(
  "subtitle",
  "以物理机理为基础，沿“建模—执行—认知—验证”形成完整技术路线",
  327,
  128,
  1016,
  37,
  { fontSize: 14.5, color: C.grey, align: "center" },
  true
);

// Connectors are created before the nodes so they remain behind the panels.
for (const [id, cx] of [["time", 270], ["structure", 686], ["exploration", 1124]]) {
  addDownArrow(`${id}_arrow_1`, cx, 232, 255, C.navy);
  addDownArrow(`${id}_arrow_2`, cx, 349, 372, C.navy);
}
addRect("convergence_h", 259, 487, 866, 2, { color: C.navy });
for (const [id, cx] of [["time", 259], ["structure", 695], ["exploration", 1124]]) {
  addRect(`${id}_converge_v`, cx - 1, 471, 2, 18, { color: C.navy });
}
addDownArrow("framework_in_1", 457, 489, 519, C.navy);
addDownArrow("framework_in_2", 694, 489, 519, C.navy);

// Objective connector: bracket and arrow.
addRect("objective_bracket_v", 1364, 283, 2, 276, { color: C.navy });
addRect("objective_bracket_top", 1349, 283, 17, 2, { color: C.navy });
addRect("objective_bracket_bottom", 1349, 557, 17, 2, { color: C.navy });
addRightArrow("objective_arrow", 1366, 1395, 390, C.navy);

// Route arrows.
addRightArrow("route_arrow_1", 440, 477, 700, C.navy);
addRightArrow("route_arrow_2", 859, 896, 700, C.navy);
addRightArrow("route_arrow_3", 1224, 1261, 700, C.navy);

addText("evidence_label", "证据", 25, 281, 52, 35, {
  fontSize: 12.5,
  bold: true,
  color: C.navy,
  align: "center",
});
addText("response_label", "回应", 25, 400, 52, 35, {
  fontSize: 12.5,
  bold: true,
  color: C.navy,
  align: "center",
});

const branches = [
  {
    id: "time",
    x: 107,
    w: 345,
    icon: ICONS.clock,
    responseIcon: ICONS.hierarchy,
    title: "时间尺度矛盾",
    evidence: "逐chirp决策为50 μs级；稳定干扰模式需跨数十个chirp观察",
    response: "分层分时决策：\n上层低频场景判断，\n下层高频动作执行",
  },
  {
    id: "structure",
    x: 523,
    w: 345,
    icon: ICONS.puzzle,
    responseIcon: ICONS.eye,
    title: "结构信息缺失",
    evidence: "单一SINR无法说明频域或时域哪一维更有优化空间",
    response: "结构语义重建：\n构建12维场景语义特征，\n补足干扰结构信息",
  },
  {
    id: "exploration",
    x: 946,
    w: 373,
    icon: ICONS.chart,
    responseIcon: ICONS.target,
    title: "动态探索低效",
    evidence: "9维联合空间在环境突变后需重新试错，探索成本高",
    response: "元策略引导：\n引导动作子空间与探索方向，\n减少环境突变后的无效试错",
  },
];

for (const branch of branches) {
  addRect(
    `${branch.id}_header_panel`,
    branch.x,
    177,
    branch.w,
    56,
    { color: C.ivory, transparency: 100 },
    { color: C.navy, width: 1.0 },
    true,
    true
  );
  addIcon(`${branch.id}_header_icon`, branch.icon, branch.x + 28, 184, 43, 43, C.navy);
  addText(`${branch.id}_header_title`, branch.title, branch.x + 92, 188, branch.w - 112, 34, {
    fontSize: 13.5,
    bold: true,
    color: C.navy,
    align: "center",
  });
  addRect(
    `${branch.id}_evidence_panel`,
    branch.x - 18,
    255,
    branch.w + 36,
    94,
    { color: C.ivory, transparency: 100 },
    { color: C.navy, width: 0.9, dash: "dash" },
    true,
    true
  );
  addText(`${branch.id}_evidence_text`, branch.evidence, branch.x, 266, branch.w, 70, {
    fontSize: 10.5,
    color: C.ink,
    align: "center",
    breakLine: true,
    lineSpacingMultiple: 0.9,
  });
  addRect(
    `${branch.id}_response_panel`,
    branch.x - 18,
    372,
    branch.w + 36,
    99,
    { color: C.navy2 },
    { color: C.navy2, transparency: 100 },
    true,
    true
  );
  addIcon(`${branch.id}_response_icon`, branch.responseIcon, branch.x, 390, 61, 61, C.white);
  addText(`${branch.id}_response_text`, branch.response, branch.x + 75, 382, branch.w - 61, 78, {
    fontSize: 10.4,
    bold: true,
    color: C.white,
    align: "center",
    breakLine: true,
    lineSpacingMultiple: 0.88,
  });
}

// Central framework convergence panel.
addRect(
  "framework_panel",
  327,
  519,
  813,
  86,
  { color: C.ivory, transparency: 100 },
  { color: C.navy, width: 1.2 },
  true,
  true
);
addIcon("framework_icon", ICONS.atom, 371, 528, 70, 67, C.navy);
addText("framework_title", "分层强化学习抗干扰框架", 476, 541, 335, 43, {
  fontSize: 15.2,
  bold: true,
  color: C.navy,
  align: "center",
});
addRect("framework_divider", 837, 529, 2, 62, { color: "8EA3B7" });
addText(
  "framework_rationale",
  "• 分层缓解时间尺度矛盾\n• 12维语义补足结构信息\n• 元策略提升动态探索效率",
  858,
  529,
  257,
  62,
  { fontSize: 9.4, bold: true, color: C.navy, breakLine: true, lineSpacingMultiple: 0.86 }
);

// Objective rail.
addRect(
  "objective_rail_panel",
  1402,
  107,
  245,
  518,
  { color: C.ivory, transparency: 100 },
  { color: C.navy, width: 1.0 },
  false,
  true
);
addText("objective_rail_title", "研究目标", 1402, 110, 245, 39, {
  fontSize: 14.5,
  bold: true,
  color: C.navy,
  align: "center",
});
addRect("objective_header_rule", 1402, 148, 245, 2, { color: C.navy });
addRect("objective_separator_1", 1407, 325, 230, 2, { color: "8EA3B7" });
addRect("objective_separator_2", 1407, 482, 230, 2, { color: "8EA3B7" });

const objectives = [
  {
    id: "performance",
    y: 150,
    icon: ICONS.shield,
    title: "性能与稳定性",
    body: "• 联合时频抗干扰性能提升\n• 策略稳定收敛",
  },
  {
    id: "recovery",
    y: 326,
    icon: ICONS.clockBolt,
    title: "突变恢复速度",
    body: "• 缩短策略恢复时间\n• 降低恢复期性能损失",
  },
  {
    id: "interpretability",
    y: 484,
    icon: ICONS.brain,
    title: "可解释性",
    body: "• 决策路径可追溯\n• 物理机理与策略一致\n• 工程实时性另行评估",
  },
];
for (const objective of objectives) {
  addIcon(`${objective.id}_icon`, objective.icon, 1418, objective.y + 19, 55, 55, C.navy);
  addText(`${objective.id}_title`, objective.title, 1488, objective.y + 19, 142, 34, {
    fontSize: 11.6,
    bold: true,
    color: C.navy,
  });
  addText(`${objective.id}_body`, objective.body, 1488, objective.y + 54, 142, objective.id === "interpretability" ? 76 : 88, {
    fontSize: 8.6,
    color: C.ink,
    breakLine: true,
    lineSpacingMultiple: 0.88,
  });
}

// Technical route.
addRect("route_label_panel", 14, 659, 70, 89, { color: C.navy2 }, null, true, true);
addText("route_label", "技术\n路线", 14, 659, 70, 89, {
  fontSize: 13,
  bold: true,
  color: C.white,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.8,
});

const routes = [
  {
    id: "modeling",
    x: 98,
    w: 336,
    icon: ICONS.antenna,
    title: "物理机理与POMDP建模",
    body: "• 相干干扰机理\n• 状态、动作与奖励定义\n• 物理约束与部分可观测建模",
  },
  {
    id: "execution",
    x: 483,
    w: 371,
    icon: ICONS.cpu,
    title: "Double DQN+GRU执行层",
    body: "• 逐chirp动作生成\n• Q值过估计抑制\n• 时序记忆与在线更新",
  },
  {
    id: "cognition",
    x: 901,
    w: 318,
    icon: ICONS.brain,
    title: "Meta-RF元控制器",
    body: "• 12维场景语义表征\n• 动作子空间与探索方向引导\n• 非平稳干扰快速迁移",
  },
  {
    id: "validation",
    x: 1264,
    w: 304,
    icon: ICONS.flask,
    title: "多场景实验验证",
    body: "• 静态性能与扩展性\n• 收敛性与动态突变\n• 泛化能力综合评估",
  },
];
for (const route of routes) {
  addRect(
    `${route.id}_panel`,
    route.x,
    630,
    route.w,
    145,
    { color: C.ivory, transparency: 100 },
    { color: C.navy, width: 1.0 },
    true,
    true
  );
  addIcon(`${route.id}_icon`, route.icon, route.x + 15, 650, 65, 91, C.navy);
  addText(`${route.id}_title`, route.title, route.x + 89, 647, route.w - 104, 32, {
    fontSize: 11.7,
    bold: true,
    color: C.navy,
    align: "center",
  });
  addText(`${route.id}_body`, route.body, route.x + 89, 682, route.w - 104, 73, {
    fontSize: 8.9,
    color: C.ink,
    breakLine: true,
    lineSpacingMultiple: 0.85,
  });
}

// Bottom contribution statement.
addRect(
  "conclusion_band_surface",
  30,
  796,
  1610,
  129,
  { color: C.navy2 },
  { color: C.navy2, transparency: 100 },
  true,
  true
);
addIcon("conclusion_trophy_icon", ICONS.trophy, 49, 814, 80, 88, C.white);
addText(
  "conclusion_text",
  "贡献不只是更换算法，而是重构抗干扰决策的层级与信息基础",
  149,
  828,
  676,
  53,
  { fontSize: 13.2, bold: true, color: C.white, align: "center" }
);
addRect("conclusion_divider", 852, 810, 2, 98, { color: "D5E3EE" });
addText(
  "conclusion_support",
  "✓ 分层结构缓解时间尺度矛盾\n✓ 12维语义特征补足结构信息\n✓ 元策略引导减少无效探索\n✓ 四类实验形成闭环验证",
  892,
  807,
  695,
  103,
  { fontSize: 10.6, bold: true, color: C.white, breakLine: true, lineSpacingMultiple: 0.88 }
);

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);

pptx.writeFile({ fileName: OUTPUT });
