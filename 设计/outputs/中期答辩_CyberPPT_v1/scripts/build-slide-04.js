const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const OUTPUT = `${ROOT}/pages/slide-04.pptx`;
const ICON_DIR = `${ROOT}/assets/icons/tabler-outline`;
const ICONS = {
  cube: `${ICON_DIR}/cube.svg`,
  target: `${ICON_DIR}/target.svg`,
  bulb: `${ICON_DIR}/bulb.svg`,
  chart: `${ICON_DIR}/chart-area-line.svg`,
  compass: `${ICON_DIR}/compass.svg`,
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
  navy2: "07345E",
  navy3: "062B50",
  blue: "2763B0",
  blueLight: "DCEAF7",
  red: "C6423E",
  redLight: "F2D6D2",
  grey: "4F565D",
  mid: "AAB3BC",
  white: "FFFFFF",
  ink: "101820",
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
function addSegment(id, x1, y1, x2, y2, thickness, color) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.max(1, Math.sqrt(dx * dx + dy * dy));
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
  const box = B((x1 + x2) / 2 - len / 2, (y1 + y2) / 2 - thickness / 2, len, thickness);
  slide.addShape(pptx.ShapeType.rect, {
    ...box,
    rotate: angle,
    fill: { color },
    line: { color, transparency: 100 },
  });
}
function addPolyline(id, points, color, thickness = 1.7) {
  for (let i = 0; i < points.length - 1; i += 1) {
    addSegment(`${id}_${i}`, ...points[i], ...points[i + 1], thickness, color);
  }
}
function addDownArrow(id, cx, y1, y2, color = C.navy) {
  addRect(`${id}_stem`, cx - 1.2, y1, 2.4, Math.max(2, y2 - y1 - 9), { color });
  const head = B(cx - 6, y2 - 11, 12, 12);
  slide.addShape(pptx.ShapeType.triangle, {
    ...head,
    rotate: 180,
    fill: { color },
    line: { color, transparency: 100 },
  });
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

// Header: this is the only intentional content change from the user's approved body reference.
addRect("page_badge", 26, 0, 56, 52, { color: C.navy3 }, null, false, true);
addText("page_number", "04", 36, 7, 37, 35, {
  fontSize: 16,
  bold: true,
  color: C.white,
  align: "center",
}, true);
addText("header_deck_title", "基于分层强化学习的FMCW雷达抗干扰策略优化", 102, 12, 489, 27, {
  fontSize: 11.5,
  bold: true,
  color: C.navy,
}, true);
addText("section_label", "研究内容｜机理与建模", 1360, 12, 265, 27, {
  fontSize: 10.8,
  bold: true,
  color: C.navy,
  align: "right",
}, true);
addRect("top_rule", 102, 45, 1544, 3, { color: C.navy });
addText(
  "main_title",
  "时频联合调控通过改变差拍频率，将干扰主动推出接收通带",
  70,
  72,
  1133,
  48,
  { fontSize: 23, bold: true, color: C.navy3 },
  true
);
addText(
  "subtitle",
  "三个载波频点与三个发射时延构成9维联合动作空间",
  70,
  126,
  684,
  35,
  { fontSize: 14, color: C.navy3 },
  true
);

// Main panel surfaces.
addRect("mechanism_panel_surface", 28, 170, 794, 585, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 1.0 }, false, true);
addRect("matrix_panel_surface", 842, 170, 456, 585, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 1.0 }, false, true);
addRect("parameter_panel_surface", 1311, 170, 318, 260, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 1.0 }, false, true);
addRect("mdp_panel_surface", 1311, 441, 318, 314, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 1.0 }, false, true);

// Left mechanism panel.
addRect("mechanism_top_banner", 153, 183, 536, 37, { color: C.navy2 }, null, true);
addText("mechanism_top_banner_text", "通过改变 f_c 或 t_d，增大差拍频率，使干扰超出接收通带", 169, 188, 505, 27, {
  fontSize: 11.3,
  bold: true,
  color: C.white,
  align: "center",
});

const stages = [
  ["发射\n(LFM Chirp)", 232, 64],
  ["接收\n(目标 + 干扰)", 330, 63],
  ["Dechirp\n混频", 408, 52],
  ["差拍频谱\n(Beat Spectrum)", 470, 62],
  ["接收通带\n(LPF)", 568, 57],
];
for (let i = 0; i < stages.length; i += 1) {
  const [text, y, h] = stages[i];
  addRect(`stage_${i}`, 38, y, 120, h, { color: C.ivory, transparency: 100 }, { color: "6D8DB0", width: 0.8 }, true);
  addText(`stage_${i}_text`, text, 43, y + 4, 110, h - 8, {
    fontSize: i === 2 ? 10.2 : 9.4,
    bold: true,
    color: C.navy,
    align: "center",
    breakLine: true,
    lineSpacingMultiple: 0.84,
  });
}
addDownArrow("stage_arrow_1", 96, 297, 326);
addDownArrow("stage_arrow_2", 96, 393, 406);
addDownArrow("stage_arrow_3", 96, 460, 468);
addDownArrow("stage_arrow_4", 96, 533, 566);

// Chirp plot and axes.
addText("chirp_amp", "幅度", 184, 225, 39, 18, { fontSize: 7.4, color: C.grey });
addText("chirp_label", "线性调频脉冲", 395, 225, 144, 18, { fontSize: 8.4, bold: true, color: C.navy, align: "center" });
addRect("chirp_axis_x", 204, 294, 565, 1.5, { color: "74808C" });
addRect("chirp_axis_y", 204, 241, 1.5, 54, { color: "74808C" });
const chirpPts = [];
const chirpCycles = 30;
for (let i = 0; i < chirpCycles; i += 1) {
  const x0 = 210 + i * 17.5;
  chirpPts.push([x0, 287], [x0 + 14, 249], [x0 + 17.5, 287]);
}
addPolyline("chirp_wave", chirpPts, C.blue, 1.25);
addText("chirp_time", "时间", 733, 288, 38, 18, { fontSize: 7.4, color: C.grey, align: "right" });
addText("chirp_tsw", "T_sw", 713, 303, 44, 18, { fontSize: 7.4, italic: true, color: C.grey, align: "center" });

// Received target + interference waveform.
addText("rx_amp", "幅度", 184, 313, 39, 18, { fontSize: 7.4, color: C.grey });
addText("rx_target_label", "目标回波 (τ_tar)", 309, 314, 139, 18, { fontSize: 8.2, bold: true, color: C.blue, align: "center" });
addText("rx_intf_label", "干扰回波 (τ_intf)", 518, 314, 142, 18, { fontSize: 8.2, bold: true, color: C.red, align: "center" });
addRect("rx_axis_x", 204, 385, 565, 1.5, { color: "74808C" });
addRect("rx_axis_y", 204, 330, 1.5, 56, { color: "74808C" });
const targetPts = [];
const intfPts = [];
for (let i = 0; i <= 70; i += 1) {
  const x = 210 + i * 4.3;
  const amp = (Math.sin(i * 1.7) + 0.55 * Math.sin(i * 3.1)) * (20 + 5 * Math.sin(i * 0.3));
  targetPts.push([x, 360 - amp * 0.5]);
}
for (let i = 0; i <= 67; i += 1) {
  const x = 467 + i * 4.2;
  const amp = (Math.sin(i * 0.95) + 0.4 * Math.sin(i * 2.4)) * (22 + 4 * Math.sin(i * 0.2));
  intfPts.push([x, 360 - amp * 0.55]);
}
addPolyline("rx_target", targetPts, C.blue, 1.15);
addPolyline("rx_intf", intfPts, C.red, 1.15);
addText("rx_time", "时间", 733, 379, 38, 18, { fontSize: 7.4, color: C.grey, align: "right" });
addText("rx_tsw", "T_sw", 713, 397, 44, 18, { fontSize: 7.4, italic: true, color: C.grey, align: "center" });

// Dechirp formula.
addRect("mix_formula_panel", 244, 412, 451, 36, { color: C.ivory, transparency: 100 }, { color: "8BA2B8", width: 0.7 });
addText("mix_formula", "s_mix(t) = s_rx(t) · s_tx*(t)", 260, 416, 419, 27, {
  fontSize: 10,
  italic: true,
  color: C.ink,
  align: "center",
});

// Beat spectrum.
addText("beat_amp", "幅度", 184, 457, 39, 18, { fontSize: 7.4, color: C.grey });
addText("beat_title", "差拍频率  f_beat", 396, 450, 148, 22, { fontSize: 8.7, bold: true, color: C.navy, align: "center" });
addRect("beat_axis_x", 204, 532, 565, 1.5, { color: "74808C" });
addRect("beat_axis_y", 204, 476, 1.5, 57, { color: "74808C" });
const beatBlue = [
  [213, 531], [328, 531], [370, 530], [386, 527], [396, 516], [402, 482], [408, 516], [420, 528], [452, 531],
];
const beatRed = [
  [520, 531], [581, 531], [598, 526], [611, 516], [622, 479], [631, 516], [643, 527], [675, 531], [720, 531],
];
addPolyline("beat_blue", beatBlue, C.blue, 1.7);
addPolyline("beat_red", beatRed, C.red, 1.7);
addText("beat_target", "目标 f_beat,tar", 315, 472, 136, 18, { fontSize: 7.7, bold: true, color: C.blue, align: "center" });
addText("beat_intf", "干扰 f_beat,intf", 564, 472, 142, 18, { fontSize: 7.7, bold: true, color: C.red, align: "center" });
addText("beat_lpf_cut", "LPF截断", 686, 474, 78, 18, { fontSize: 7.8, bold: true, color: C.navy, align: "center" });
for (const x of [418, 559]) {
  for (let j = 0; j < 5; j += 1) addRect(`beat_dash_${x}_${j}`, x, 480 + j * 10, 1.5, 6, { color: "7C96B0" });
}
addText("beat_ticks", "−20   −16   −12   −8   −4    0     4     8    12    16    20", 208, 538, 535, 16, {
  fontSize: 6.9,
  color: C.grey,
  align: "center",
});
addText("beat_freq", "频率 (MHz)", 702, 538, 72, 16, { fontSize: 7, color: C.grey, align: "right" });

// LPF passband.
addText("lpf_amp", "幅度", 184, 568, 39, 18, { fontSize: 7.4, color: C.grey });
addRect("lpf_axis_x", 204, 622, 565, 1.5, { color: "74808C" });
addRect("lpf_axis_y", 204, 584, 1.5, 39, { color: "74808C" });
addRect("lpf_band", 376, 604, 224, 18, { color: C.blueLight, transparency: 10 }, { color: "6D92B8", width: 0.6 });
addText("lpf_formula", "LPF通带：|f_beat| ≤ f_bmax", 343, 576, 293, 24, {
  fontSize: 9.5,
  bold: true,
  color: C.navy,
  align: "center",
});
addText("lpf_ticks", "−20   −16   −12   −8   −4    0     4     8    12    16    20", 208, 626, 535, 16, {
  fontSize: 6.9,
  color: C.grey,
  align: "center",
});
addText("lpf_freq", "频率 (MHz)", 702, 626, 72, 16, { fontSize: 7, color: C.grey, align: "right" });

// Principle strip.
addRect("principle_band", 39, 653, 768, 90, { color: C.ivory, transparency: 100 }, { color: C.navy, width: 0.9, dash: "dash" }, true);
addRect("principle_label_panel", 47, 664, 101, 67, { color: C.navy2 }, null, true);
addText("principle_label", "干扰推出\n通带原理", 52, 668, 91, 59, {
  fontSize: 11,
  bold: true,
  color: C.white,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.82,
});
addText("principle_formula", "差拍频率与时延成正比：\nf_beat,intf = K × τ_intf", 166, 674, 190, 47, {
  fontSize: 8.6,
  bold: true,
  color: C.navy,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.86,
});
addText("principle_explanation", "改变载频 f_c 或发射时延 t_d\n→ 等效干扰时延变化\n→ 差拍频率移动", 365, 670, 244, 55, {
  fontSize: 8.2,
  color: C.navy,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.82,
});
addRect("principle_condition_panel", 617, 658, 173, 79, { color: C.ivory, transparency: 100 }, { color: "7E9BB8", width: 0.8 }, true);
addText("principle_condition", "当满足：\n|f_beat,intf| > f_bmax\n干扰被LPF滤除", 626, 663, 155, 68, {
  fontSize: 8.7,
  bold: true,
  color: C.navy,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.82,
});

// 3x3 action matrix.
addRect("matrix_header", 856, 187, 430, 37, { color: C.navy2 }, null, true);
addText("matrix_title", "9维联合动作空间（3 × 3 = 9 种配置）", 874, 191, 393, 28, {
  fontSize: 11.5,
  bold: true,
  color: C.white,
  align: "center",
});
addText("matrix_carrier_axis", "载波频率  f_c  (GHz)", 994, 245, 186, 30, {
  fontSize: 10,
  bold: true,
  color: C.navy,
  align: "center",
});
addText("matrix_delay_axis", "发射\n时延\n t_d\n(μs)", 848, 328, 39, 217, {
  fontSize: 7.4,
  bold: true,
  color: C.navy,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.9,
});
for (const [text, x] of [["76.25", 922], ["76.75", 1041], ["77.25", 1161]]) {
  addText(`matrix_col_${text}`, text, x, 284, 109, 31, {
    fontSize: 10.2,
    bold: true,
    color: C.navy,
    align: "center",
  });
}
for (const [text, y] of [["0\nμs", 344], ["0.8\nμs", 454], ["1.6\nμs", 563]]) {
  addText(`matrix_row_${y}`, text, 879, y, 39, 55, {
    fontSize: 9.6,
    bold: true,
    color: C.navy,
    align: "center",
    breakLine: true,
    lineSpacingMultiple: 0.82,
  });
}
const carrier = ["76.25", "76.75", "77.25"];
const delays = ["0", "0.8", "1.6"];
let config = 1;
for (let r = 0; r < 3; r += 1) {
  for (let c = 0; c < 3; c += 1) {
    const x = [922, 1041, 1161][c];
    const y = [325, 435, 544][r];
    addRect(`matrix_cell_${config}`, x, y, 109, 99, { color: "F7F8F8", transparency: 5 }, { color: "6E90B0", width: 0.7 }, true);
    addText(`matrix_cell_${config}_number`, `${config}`, x + 31, y + 13, 47, 31, {
      fontSize: 12,
      bold: true,
      color: C.navy,
      align: "center",
    });
    addText(`matrix_cell_${config}_combo`, `(${carrier[c]}, ${delays[r]} μs)`, x + 7, y + 49, 95, 25, {
      fontSize: 7.8,
      color: C.navy,
      align: "center",
    });
    config += 1;
  }
}
addRect("matrix_note_panel", 871, 664, 409, 72, { color: C.ivory, transparency: 100 }, { color: "7E9BB8", width: 0.7, dash: "dash" }, true);
addIcon("matrix_note_icon", ICONS.cube, 889, 680, 42, 42, C.navy);
addText(
  "matrix_note_text",
  "选择不同 f_c 或 t_d，改变 τ_intf 与 f_beat,intf\n动作索引 a∈{0,…,8}；76.75 GHz 为统一中间频点",
  949,
  675,
  314,
  50,
  { fontSize: 8.2, bold: true, color: C.navy, align: "center", breakLine: true, lineSpacingMultiple: 0.86 }
);

// System parameter table.
addRect("parameter_header", 1350, 187, 235, 37, { color: C.navy2 }, null, true);
addText("parameter_title", "系统关键参数", 1373, 191, 188, 28, {
  fontSize: 11.5,
  bold: true,
  color: C.white,
  align: "center",
});
const params = [
  ["调频斜率  K", "10 MHz/μs"],
  ["扫频时长  T_sw", "50 μs"],
  ["采样频率  f_s", "20 MHz"],
  ["最大探测距离  d_max", "120 m"],
  ["接收通带半宽  f_bmax", "8 MHz"],
];
const tableX = 1325;
const tableY = 236;
const rowH = 36;
for (let i = 0; i < params.length; i += 1) {
  const y = tableY + i * rowH;
  addRect(`param_row_${i}`, tableX, y, 289, rowH, { color: C.ivory, transparency: 100 }, { color: "A7B4C0", width: 0.5 });
  addRect(`param_div_${i}`, tableX + 164, y, 1, rowH, { color: "A7B4C0" });
  addText(`param_name_${i}`, params[i][0], tableX + 9, y + 4, 146, rowH - 8, {
    fontSize: 8.6,
    color: C.grey,
  });
  addText(`param_value_${i}`, params[i][1], tableX + 172, y + 4, 109, rowH - 8, {
    fontSize: 9,
    color: C.grey,
    align: "center",
  });
}

// MDP panel.
addRect("mdp_header", 1352, 454, 232, 37, { color: C.navy2 }, null, true);
addText("mdp_title", "联合决策建模（MDP）", 1358, 458, 220, 28, {
  fontSize: 10.2,
  bold: true,
  color: C.white,
  align: "center",
});
addText("mdp_state_label", "• 状态向量", 1327, 499, 112, 24, { fontSize: 9.4, bold: true, color: C.navy });
addRect("mdp_state_formula_panel", 1342, 523, 263, 58, { color: C.ivory, transparency: 100 }, { color: "7E9BB8", width: 0.7 }, true);
addText("mdp_state_formula", "s_t = [a(t−1), r(t−1), SINR(t)]", 1350, 527, 247, 29, {
  fontSize: 9.7,
  italic: true,
  color: C.navy,
  align: "center",
});
addText("mdp_state_note", "历史动作    接收特征    信干噪比", 1355, 554, 236, 20, {
  fontSize: 7.2,
  color: C.grey,
  align: "center",
});
addText("mdp_action_label", "• 动作空间", 1327, 598, 112, 24, { fontSize: 9.4, bold: true, color: C.navy });
addRect("mdp_action_formula_panel", 1342, 622, 263, 58, { color: C.ivory, transparency: 100 }, { color: "7E9BB8", width: 0.7 }, true);
addText("mdp_action_formula", "A={(f_c,i, t_d,j)}, i,j∈{1,2,3}, |A|=9", 1350, 627, 247, 45, {
  fontSize: 9,
  italic: true,
  color: C.navy,
  align: "center",
});
addText("mdp_depth_label", "• 奖励与规划深度", 1327, 692, 138, 22, { fontSize: 9.2, bold: true, color: C.navy });
addRect("mdp_depth_panel", 1342, 714, 263, 31, { color: C.ivory, transparency: 100 }, { color: "7E9BB8", width: 0.7 }, true);
addText("mdp_depth_value", "R = r_s + r_AC；k = 20", 1350, 717, 247, 25, {
  fontSize: 9.5,
  italic: true,
  color: C.navy,
  align: "center",
});

// Bottom conclusion band.
addRect("conclusion_band_surface", 29, 769, 1612, 117, { color: C.navy2 }, { color: C.navy2, transparency: 100 }, true, true);
addIcon("so_what_icon", ICONS.target, 55, 786, 66, 66, C.white);
addText("so_what_text", "SO\nWHAT", 127, 792, 67, 62, {
  fontSize: 12,
  bold: true,
  color: C.white,
  align: "center",
  breakLine: true,
  lineSpacingMultiple: 0.8,
});
addRect("conclusion_divider_1", 216, 787, 2, 78, { color: "D4E3EF" });
addIcon("conclusion_bulb", ICONS.bulb, 234, 796, 60, 60, C.white);
addText("conclusion_text", "联合空间扩大避干扰机会，也把探索负担由3维提高到9维", 299, 809, 686, 45, {
  fontSize: 15.5,
  bold: true,
  color: C.white,
  align: "center",
});
for (const x of [1013, 1031]) {
  addSegment(`chevron_${x}_a`, x, 815, x + 18, 832, 5, C.white);
  addSegment(`chevron_${x}_b`, x, 849, x + 18, 832, 5, C.white);
}
const implications = [
  ["implication_success", ICONS.target, 1060, "更高\n避干扰成功率"],
  ["implication_adaptation", ICONS.chart, 1262, "更强\n环境适应性"],
  ["implication_burden", ICONS.compass, 1452, "更重\n探索负担"],
];
for (const [id, icon, x, text] of implications) {
  addIcon(`${id}_icon`, icon, x, 793, 55, 55, C.white);
  addText(`${id}_text`, text, x + 64, 797, 116, 57, {
    fontSize: 9.5,
    bold: true,
    color: C.white,
    breakLine: true,
    lineSpacingMultiple: 0.82,
  });
}
addText("source_footer", "来源：E02、E03、S2:p3-p6、S2:p14-p15", 1170, 868, 430, 12, {
  fontSize: 6.5,
  color: "BFD0DE",
  align: "right",
});

warnIfSlideElementsOutOfBounds(placements);
warnIfSlideHasOverlaps(placements);
pptx.writeFile({ fileName: OUTPUT });
