const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-07.png";
const render = `${root}/renders/slide-07.png`;
const qa = `${root}/qa/slide-07`;

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
    left: 0, top: 0, width: 1643, height: 201,
  });
  await sideBySide(blueprint, render, `${qa}/features-comparison.png`, {
    left: 31, top: 233, width: 599, height: 490,
  });
  await sideBySide(blueprint, render, `${qa}/rf-comparison.png`, {
    left: 631, top: 223, width: 347, height: 510,
  });
  await sideBySide(blueprint, render, `${qa}/strategy-comparison.png`, {
    left: 1014, top: 219, width: 617, height: 535,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 35, top: 775, width: 1596, height: 113,
  });
  await sharp(blueprint)
    .extract({ left: 1014, top: 219, width: 617, height: 535 })
    .png()
    .toFile(`${qa}/strategy-reference.png`);
  await sharp(render)
    .extract({ left: 1014, top: 219, width: 617, height: 535 })
    .png()
    .toFile(`${qa}/strategy-render.png`);
})();
