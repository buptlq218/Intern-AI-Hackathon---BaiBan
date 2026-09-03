const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-01.png";
const render = `${root}/renders/slide-01.png`;
const qa = `${root}/qa/slide-01`;

async function sideBySide(
  leftPath,
  rightPath,
  outputPath,
  extract = null,
  gap = 18
) {
  let left = sharp(leftPath);
  let right = sharp(rightPath);
  if (extract) {
    left = left.extract(extract);
    right = right.extract(extract);
  }
  const [leftBuffer, rightBuffer, leftMeta] = await Promise.all([
    left.png().toBuffer(),
    right.png().toBuffer(),
    left.metadata(),
  ]);
  const width = leftMeta.width;
  const height = leftMeta.height;
  await sharp({
    create: {
      width: width * 2 + gap,
      height,
      channels: 4,
      background: { r: 18, g: 53, b: 91, alpha: 1 },
    },
  })
    .composite([
      { input: leftBuffer, left: 0, top: 0 },
      { input: rightBuffer, left: width + gap, top: 0 },
    ])
    .png()
    .toFile(outputPath);
}

(async () => {
  await sideBySide(blueprint, render, `${qa}/side-by-side.png`);
  await sideBySide(
    blueprint,
    render,
    `${qa}/title-comparison.png`,
    { left: 70, top: 180, width: 1080, height: 400 },
    14
  );
  await sideBySide(
    blueprint,
    render,
    `${qa}/technical-visual-comparison.png`,
    { left: 380, top: 38, width: 1292, height: 864 },
    14
  );
  await sideBySide(
    blueprint,
    render,
    `${qa}/footer-comparison.png`,
    { left: 50, top: 875, width: 1580, height: 36 },
    14
  );
  await sharp(blueprint)
    .extract({ left: 380, top: 38, width: 1292, height: 864 })
    .png()
    .toFile(`${qa}/technical-reference.png`);
  await sharp(render)
    .extract({ left: 380, top: 38, width: 1292, height: 864 })
    .png()
    .toFile(`${qa}/technical-render.png`);
})();
