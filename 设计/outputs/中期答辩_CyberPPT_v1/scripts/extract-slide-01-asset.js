const sharp = require("sharp");

const sourcePath =
  "/private/tmp/codex-presentations/manual-midterm-20260723/graduate-midterm/tmp/blueprints/slide-01.png";
const outputPath =
  "/Users/linqu/Desktop/毕业设计/outputs/中期答辩_CyberPPT_v1/assets/slide-01-technical-visual.png";

const crop = { left: 380, top: 38, width: 1292, height: 864 };
const background = [252, 250, 245];

function keepPixel(globalX, globalY) {
  const protectedTextZone =
    globalX < 1120 && globalY >= 170 && globalY <= 570;
  const upperRadar =
    globalX >= 1018 && globalY <= 666 && !protectedTextZone;
  const waveforms = globalX >= 380 && globalX <= 1452 && globalY >= 568 && globalY <= 875;
  const radarDevice = globalX >= 1420 && globalY >= 605 && globalY <= 902;
  return upperRadar || waveforms || radarDevice;
}

(async () => {
  const { data, info } = await sharp(sourcePath)
    .extract(crop)
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  for (let y = 0; y < info.height; y += 1) {
    for (let x = 0; x < info.width; x += 1) {
      const offset = (y * info.width + x) * info.channels;
      const globalX = x + crop.left;
      const globalY = y + crop.top;
      const diff = Math.max(
        Math.abs(data[offset] - background[0]),
        Math.abs(data[offset + 1] - background[1]),
        Math.abs(data[offset + 2] - background[2])
      );
      const visible = keepPixel(globalX, globalY) && diff >= 5;
      if (!visible) {
        data[offset + 3] = 0;
        data[offset] = background[0];
        data[offset + 1] = background[1];
        data[offset + 2] = background[2];
      } else {
        const original = [data[offset], data[offset + 1], data[offset + 2]];
        const channelAlpha = original.map((value, channel) => {
          const base = background[channel];
          if (value < base) return (base - value) / Math.max(base, 1);
          return (value - base) / Math.max(255 - base, 1);
        });
        const alpha = Math.min(1, Math.max(...channelAlpha, 0.02));
        for (let channel = 0; channel < 3; channel += 1) {
          const base = background[channel];
          const foreground =
            (original[channel] - (1 - alpha) * base) / alpha;
          data[offset + channel] = Math.max(
            0,
            Math.min(255, Math.round(foreground))
          );
        }
        data[offset + 3] = Math.round(alpha * 255);
      }
    }
  }

  await sharp(data, {
    raw: {
      width: info.width,
      height: info.height,
      channels: info.channels,
    },
  })
    .png()
    .toFile(outputPath);

  process.stdout.write(`${outputPath}\n`);
})();
