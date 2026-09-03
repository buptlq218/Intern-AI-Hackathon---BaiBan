const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-09.png";
const render = `${root}/renders/slide-09.png`;
const qa = `${root}/qa/slide-09`;

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
    left: 17, top: 5, width: 1637, height: 181,
  });
  await sideBySide(blueprint, render, `${qa}/system-performance-comparison.png`, {
    left: 25, top: 194, width: 553, height: 606,
  });
  await sideBySide(blueprint, render, `${qa}/dynamic-recovery-comparison.png`, {
    left: 594, top: 194, width: 640, height: 606,
  });
  await sideBySide(blueprint, render, `${qa}/engineering-evidence-comparison.png`, {
    left: 1247, top: 194, width: 396, height: 606,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 25, top: 818, width: 1618, height: 90,
  });
  await sharp(blueprint)
    .extract({ left: 594, top: 194, width: 640, height: 606 })
    .png()
    .toFile(`${qa}/dynamic-recovery-reference.png`);
  await sharp(render)
    .extract({ left: 594, top: 194, width: 640, height: 606 })
    .png()
    .toFile(`${qa}/dynamic-recovery-render.png`);
})();
