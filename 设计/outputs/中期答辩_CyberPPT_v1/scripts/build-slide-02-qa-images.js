const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-02.png";
const render = `${root}/renders/slide-02.png`;
const qa = `${root}/qa/slide-02`;

async function sideBySide(leftPath, rightPath, outputPath, extract = null, gap = 18) {
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
  await sharp({
    create: {
      width: leftMeta.width * 2 + gap,
      height: leftMeta.height,
      channels: 4,
      background: { r: 18, g: 53, b: 91, alpha: 1 },
    },
  })
    .composite([
      { input: leftBuffer, left: 0, top: 0 },
      { input: rightBuffer, left: leftMeta.width + gap, top: 0 },
    ])
    .png()
    .toFile(outputPath);
}

(async () => {
  fs.mkdirSync(qa, { recursive: true });
  await sideBySide(blueprint, render, `${qa}/side-by-side.png`);
  await sideBySide(
    blueprint,
    render,
    `${qa}/header-comparison.png`,
    { left: 0, top: 0, width: 1672, height: 205 },
    14
  );
  await sideBySide(
    blueprint,
    render,
    `${qa}/scene-comparison.png`,
    { left: 19, top: 208, width: 923, height: 582 },
    14
  );
  await sideBySide(
    blueprint,
    render,
    `${qa}/rail-comparison.png`,
    { left: 962, top: 208, width: 690, height: 590 },
    14
  );
  await sideBySide(
    blueprint,
    render,
    `${qa}/conclusion-comparison.png`,
    { left: 19, top: 817, width: 1634, height: 103 },
    14
  );
  await sharp(blueprint)
    .extract({ left: 19, top: 208, width: 923, height: 582 })
    .png()
    .toFile(`${qa}/scene-reference.png`);
  await sharp(render)
    .extract({ left: 19, top: 208, width: 923, height: 582 })
    .png()
    .toFile(`${qa}/scene-render.png`);
})();
