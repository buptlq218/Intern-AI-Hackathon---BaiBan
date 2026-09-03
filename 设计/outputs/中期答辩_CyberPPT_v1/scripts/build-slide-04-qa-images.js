const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-04.png";
const render = `${root}/renders/slide-04.png`;
const qa = `${root}/qa/slide-04`;

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
    left: 26, top: 0, width: 1620, height: 161,
  });
  await sideBySide(blueprint, render, `${qa}/mechanism-comparison.png`, {
    left: 28, top: 170, width: 794, height: 585,
  });
  await sideBySide(blueprint, render, `${qa}/matrix-comparison.png`, {
    left: 842, top: 170, width: 456, height: 585,
  });
  await sideBySide(blueprint, render, `${qa}/right-rail-comparison.png`, {
    left: 1311, top: 170, width: 318, height: 585,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 29, top: 769, width: 1612, height: 117,
  });
  await sharp(blueprint)
    .extract({ left: 28, top: 170, width: 794, height: 585 })
    .png()
    .toFile(`${qa}/mechanism-reference.png`);
  await sharp(render)
    .extract({ left: 28, top: 170, width: 794, height: 585 })
    .png()
    .toFile(`${qa}/mechanism-render.png`);
})();
