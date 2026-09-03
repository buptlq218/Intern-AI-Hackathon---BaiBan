const fs = require("fs");
const sharp = require("sharp");

const root = "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1";
const blueprint =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-03.png";
const render = `${root}/renders/slide-03.png`;
const qa = `${root}/qa/slide-03`;

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
    left: 0, top: 0, width: 1672, height: 166,
  });
  await sideBySide(blueprint, render, `${qa}/issue-tree-comparison.png`, {
    left: 14, top: 177, width: 1305, height: 428,
  });
  await sideBySide(blueprint, render, `${qa}/objective-comparison.png`, {
    left: 1345, top: 107, width: 302, height: 518,
  });
  await sideBySide(blueprint, render, `${qa}/route-comparison.png`, {
    left: 14, top: 630, width: 1554, height: 145,
  });
  await sideBySide(blueprint, render, `${qa}/conclusion-comparison.png`, {
    left: 30, top: 796, width: 1610, height: 129,
  });
  await sharp(blueprint)
    .extract({ left: 14, top: 177, width: 1305, height: 428 })
    .png()
    .toFile(`${qa}/issue-tree-reference.png`);
  await sharp(render)
    .extract({ left: 14, top: 177, width: 1305, height: 428 })
    .png()
    .toFile(`${qa}/issue-tree-render.png`);
})();
