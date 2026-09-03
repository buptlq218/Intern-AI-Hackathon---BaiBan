const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-05.png";
const render = `${root}/renders/slide-05.png`;
const qa = `${root}/qa/slide-05`;

async function sideBySide(leftPath, rightPath, outputPath, extract = null, gap = 18) {
  let left = sharp(leftPath);
  let right = sharp(rightPath);
  if (extract) {
    left = left.extract(extract);
    right = right.extract(extract);
  }
  const [leftBuffer, rightBuffer, meta] = await Promise.all([
    left.png().toBuffer(),
    right.png().toBuffer(),
    left.metadata(),
  ]);
  await sharp({
    create: {
      width: meta.width * 2 + gap,
      height: meta.height,
      channels: 4,
      background: { r: 18, g: 53, b: 91, alpha: 1 },
    },
  })
    .composite([
      { input: leftBuffer, left: 0, top: 0 },
      { input: rightBuffer, left: meta.width + gap, top: 0 },
    ])
    .png()
    .toFile(outputPath);
}

(async () => {
  fs.mkdirSync(qa, { recursive: true });
  await sideBySide(blueprint, render, `${qa}/side-by-side.png`);
  await sideBySide(blueprint, render, `${qa}/header-comparison.png`, {
    left: 8, top: 5, width: 1639, height: 173,
  });
  await sideBySide(blueprint, render, `${qa}/meta-layer-comparison.png`, {
    left: 15, top: 182, width: 1308, height: 223,
  });
  await sideBySide(blueprint, render, `${qa}/dam-execution-comparison.png`, {
    left: 15, top: 430, width: 1308, height: 268,
  });
  await sideBySide(blueprint, render, `${qa}/environment-comparison.png`, {
    left: 91, top: 697, width: 1156, height: 125,
  });
  await sideBySide(blueprint, render, `${qa}/right-rail-comparison.png`, {
    left: 1375, top: 131, width: 272, height: 680,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 24, top: 847, width: 1625, height: 78,
  });
  await sharp(blueprint)
    .extract({ left: 15, top: 182, width: 1308, height: 223 })
    .png()
    .toFile(`${qa}/meta-layer-reference.png`);
  await sharp(render)
    .extract({ left: 15, top: 182, width: 1308, height: 223 })
    .png()
    .toFile(`${qa}/meta-layer-render.png`);
})();
