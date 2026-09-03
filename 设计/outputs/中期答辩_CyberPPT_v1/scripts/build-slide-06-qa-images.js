const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-06.png";
const render = `${root}/renders/slide-06.png`;
const qa = `${root}/qa/slide-06`;

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
    left: 14, top: 7, width: 1639, height: 203,
  });
  await sideBySide(blueprint, render, `${qa}/network-comparison.png`, {
    left: 20, top: 231, width: 540, height: 588,
  });
  await sideBySide(blueprint, render, `${qa}/training-comparison.png`, {
    left: 580, top: 231, width: 424, height: 588,
  });
  await sideBySide(blueprint, render, `${qa}/reward-comparison.png`, {
    left: 1029, top: 231, width: 622, height: 588,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 20, top: 843, width: 1633, height: 84,
  });
  await sharp(blueprint)
    .extract({ left: 1029, top: 231, width: 622, height: 588 })
    .png()
    .toFile(`${qa}/reward-reference.png`);
  await sharp(render)
    .extract({ left: 1029, top: 231, width: 622, height: 588 })
    .png()
    .toFile(`${qa}/reward-render.png`);
})();
