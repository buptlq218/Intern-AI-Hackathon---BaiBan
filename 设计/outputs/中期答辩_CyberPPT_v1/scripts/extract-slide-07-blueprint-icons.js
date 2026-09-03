const fs = require("fs");
const sharp = require("sharp");

const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-07.png";
const outDir =
  "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1/assets/slide-07-blueprint-icons";

const crops = [
  ["feature-signal", 48, 253, 90, 90],
  ["feature-action", 47, 382, 89, 94],
  ["feature-shield", 52, 518, 76, 85],
  ["feature-target", 47, 625, 83, 85],
  ["rf-database", 668, 289, 62, 62],
  ["rf-pie", 669, 366, 61, 62],
  ["rf-clipboard", 669, 441, 61, 64],
  ["rf-trees", 666, 519, 67, 60],
  ["rf-gear", 668, 593, 63, 63],
  ["rf-target", 669, 666, 62, 62],
  ["guidance-bulb", 1063, 546, 98, 98],
  ["warning", 1051, 691, 56, 52],
  ["conclusion-check", 61, 792, 76, 76],
];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const records = [];
  for (const [name, left, top, width, height] of crops) {
    const { data, info } = await sharp(blueprint)
      .extract({ left, top, width, height })
      .ensureAlpha()
      .raw()
      .toBuffer({ resolveWithObject: true });
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
    await sharp(data, { raw: { width: info.width, height: info.height, channels: 4 } })
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
