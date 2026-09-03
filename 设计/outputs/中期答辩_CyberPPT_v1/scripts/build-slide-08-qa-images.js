const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-08.png";
const render = `${root}/renders/slide-08.png`;
const qa = `${root}/qa/slide-08`;

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
    left: 13, top: 0, width: 1637, height: 201,
  });
  await sideBySide(blueprint, render, `${qa}/strategy-chart-comparison.png`, {
    left: 15, top: 209, width: 883, height: 438,
  });
  await sideBySide(blueprint, render, `${qa}/evidence-rail-comparison.png`, {
    left: 912, top: 209, width: 738, height: 438,
  });
  await sideBySide(blueprint, render, `${qa}/findings-comparison.png`, {
    left: 15, top: 657, width: 1636, height: 170,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 15, top: 837, width: 1636, height: 88,
  });
  await sharp(blueprint)
    .extract({ left: 15, top: 209, width: 883, height: 438 })
    .png()
    .toFile(`${qa}/strategy-chart-reference.png`);
  await sharp(render)
    .extract({ left: 15, top: 209, width: 883, height: 438 })
    .png()
    .toFile(`${qa}/strategy-chart-render.png`);
})();
