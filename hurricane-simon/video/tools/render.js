// Render the explainer to MP4: frames are drawn by the page's render(t) and piped to ffmpeg in parallel segments.
// Usage: node render.js VIDEO.html OUT.mp4 [fps=30] [workers=3] [from=0] [to=total]
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
(async () => {
  const [file, out, fpsArg, wArg, fromArg, toArg] = process.argv.slice(2);
  const fps = +(fpsArg || 30), workers = +(wArg || 3), tmp = out + '.parts'; fs.mkdirSync(tmp, { recursive: true });
  const browser = await chromium.launch();
  const probe = await (await browser.newContext({ viewport: { width: 1920, height: 1080 } })).newPage();
  await probe.goto('file://' + path.resolve(file)); await probe.evaluate(() => window.VIDEO.ready);
  const total = await probe.evaluate(() => window.VIDEO.total());
  const t0 = +(fromArg || 0), t1 = Math.min(total, +(toArg || total)), n = Math.round((t1 - t0) * fps), per = Math.ceil(n / workers);
  console.log('total', total, 's; frames', n, 'workers', workers);
  const started = Date.now();
  const segs = await Promise.all([...Array(workers).keys()].map(async w => {
    const a = w * per, b = Math.min(n, a + per); if (a >= b) return null;
    const page = await (await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })).newPage();
    const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.goto('file://' + path.resolve(file)); await page.evaluate(() => window.VIDEO.ready);
    const seg = path.join(tmp, `seg_${String(w).padStart(2, '0')}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-g', String(fps * 2), '-r', String(fps), seg], { stdio: ['pipe', 'inherit', 'inherit'] });
    const cv = await page.$('#cv');
    for (let f = a; f < b; f++) {
      await page.evaluate(t => window.VIDEO.render(t), t0 + f / fps);
      const buf = await cv.screenshot({ type: 'jpeg', quality: 95 });   // JPEG q95 is visually lossless here and encodes several times faster than PNG
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((f - a) % 300 === 0) console.log(`worker ${w}: ${f - a}/${b - a} (${((Date.now() - started) / 1000).toFixed(0)} s)`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    if (errs.length) console.log('worker', w, 'errors', errs.slice(0, 3));
    return seg;
  }));
  await browser.close();
  const list = path.join(tmp, 'list.txt'); fs.writeFileSync(list, segs.filter(Boolean).map(s => `file '${s}'`).join('\n') + '\n');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', out]);
  console.log('wrote', out, (fs.statSync(out).size / 1e6).toFixed(1), 'MB in', ((Date.now() - started) / 1000).toFixed(0), 's');
})();
