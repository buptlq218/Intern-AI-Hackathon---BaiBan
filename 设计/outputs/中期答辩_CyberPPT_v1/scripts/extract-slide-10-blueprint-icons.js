const fs = require("fs");
const sharp = require("sharp");

const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-10.png";
const outDir =
  "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1/assets/slide-10-blueprint-icons";
const crops = [
  ["stage-complete", 208, 222, 168, 168],
  ["stage-writing", 748, 222, 166, 168],
  ["stage-defense", 1263, 222, 166, 169],
  ["done-signal", 129, 506, 44, 44],
  ["done-brain", 129, 557, 44, 43],
  ["done-layers", 128, 606, 46, 46],
  ["done-chart", 128, 657, 46, 43],
  ["done-document", 129, 706, 44, 45],
  ["doing-book", 650, 520, 53, 44],
  ["doing-chart", 651, 591, 53, 47],
  ["doing-clipboard", 651, 664, 51, 55],
  ["next-document", 1176, 509, 47, 50],
  ["next-presentation", 1174, 577, 51, 42],
  ["next-question", 1173, 633, 55, 45],
  ["next-shield", 1175, 691, 50, 52],
  ["conclusion-clipboard", 151, 781, 95, 82],
  ["footer-info", 608, 890, 36, 36],
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
