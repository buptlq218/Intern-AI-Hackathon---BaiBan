const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-10.png";
const render = `${root}/renders/slide-10.png`;
const qa = `${root}/qa/slide-10`;

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
    left: 9, top: 8, width: 1653, height: 213,
  });
  await sideBySide(blueprint, render, `${qa}/timeline-comparison.png`, {
    left: 61, top: 222, width: 1545, height: 543,
  });
  await sideBySide(blueprint, render, `${qa}/completed-stage-comparison.png`, {
    left: 115, top: 394, width: 367, height: 357,
  });
  await sideBySide(blueprint, render, `${qa}/writing-stage-comparison.png`, {
    left: 636, top: 394, width: 372, height: 325,
  });
  await sideBySide(blueprint, render, `${qa}/defense-stage-comparison.png`, {
    left: 1160, top: 394, width: 384, height: 349,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 61, top: 772, width: 1545, height: 155,
  });
  await sharp(blueprint)
    .extract({ left: 61, top: 222, width: 1545, height: 543 })
    .png()
    .toFile(`${qa}/timeline-reference.png`);
  await sharp(render)
    .extract({ left: 61, top: 222, width: 1545, height: 543 })
    .png()
    .toFile(`${qa}/timeline-render.png`);
})();
