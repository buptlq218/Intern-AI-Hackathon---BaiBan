const fs = require("fs");
const sharp = require("sharp");

const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-05.png";
const outDir =
  "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1/assets/slide-05-blueprint-icons";

const crops = [
  ["history-visual", 233, 241, 147, 56],
  ["meta-rf-tree", 697, 247, 110, 91],
  ["confidence-chart", 918, 249, 122, 97],
  ["dam-gears", 378, 434, 66, 47],
  ["state-sequence", 212, 564, 160, 50],
  ["dqn-network", 444, 560, 117, 76],
  ["epsilon-scale", 944, 562, 98, 70],
  ["action-grid", 1179, 565, 71, 69],
  ["environment-satellite", 366, 750, 59, 62],
  ["environment-wave", 466, 752, 84, 61],
  ["environment-small-cars", 608, 766, 89, 48],
  ["environment-large-cars", 733, 758, 84, 57],
  ["environment-antenna", 853, 750, 62, 63],
  ["meta-clock", 1393, 234, 99, 99],
  ["execution-gauge", 1397, 442, 96, 78],
  ["warning", 1392, 682, 70, 70],
  ["school", 53, 853, 68, 68],
];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const records = [];
  for (const [name, left, top, width, height] of crops) {
    const extracted = sharp(blueprint)
      .extract({ left, top, width, height })
      .ensureAlpha();
    const { data, info } = await extracted.raw().toBuffer({ resolveWithObject: true });
    const corners = [
      0,
      (info.width - 1) * 4,
      (info.height - 1) * info.width * 4,
      ((info.height - 1) * info.width + info.width - 1) * 4,
    ];
    const bg = [0, 1, 2].map((channel) =>
      Math.round(corners.reduce((sum, index) => sum + data[index + channel], 0) / corners.length)
    );
    for (let i = 0; i < data.length; i += 4) {
      const distance = Math.sqrt(
        (data[i] - bg[0]) ** 2 +
        (data[i + 1] - bg[1]) ** 2 +
        (data[i + 2] - bg[2]) ** 2
      );
      if (distance <= 12) data[i + 3] = 0;
      else if (distance < 48) data[i + 3] = Math.round(data[i + 3] * ((distance - 12) / 36));
    }
    let transparentPixels = 0;
    let partialAlphaPixels = 0;
    for (let i = 3; i < data.length; i += 4) {
      if (data[i] === 0) transparentPixels += 1;
      else if (data[i] < 255) partialAlphaPixels += 1;
    }
    await sharp(data, {
      raw: { width: info.width, height: info.height, channels: 4 },
    })
      .png()
      .toFile(`${outDir}/${name}.png`);
    const pixelCount = info.width * info.height;
    records.push({
      name,
      source_bbox_px: { left, top, width, height },
      background_rgb: bg,
      transparent_pixel_ratio: Number((transparentPixels / pixelCount).toFixed(4)),
      partial_alpha_pixel_ratio: Number((partialAlphaPixels / pixelCount).toFixed(4)),
      verified_has_transparency: transparentPixels > 0 && partialAlphaPixels > 0,
    });
  }
  fs.writeFileSync(
    `${outDir}/transparency-verification.json`,
    `${JSON.stringify({ icons: records }, null, 2)}\n`
  );
})();
