// Write Spanish and English SRT captions plus YouTube chapters from the page's scene list.
// Usage: node captions.js VIDEO.html OUTDIR
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [file, outdir] = process.argv.slice(2);
  const browser = await chromium.launch(); const page = await (await browser.newContext()).newPage();
  await page.goto('file://' + path.resolve(file)); await page.evaluate(() => window.VIDEO.ready);
  const sc = await page.evaluate(() => window.VIDEO.scenes()); const total = await page.evaluate(() => window.VIDEO.total());
  const meta = await page.evaluate(() => window.VIDEO.meta ? window.VIDEO.meta() : {});
  await browser.close();
  const ts = s => { const ms = Math.round(s * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, x = Math.floor(ms / 1000) % 60; return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
  const clean = s => String(s).replace(/\*/g, '');
  for (const lang of ['es', 'en']) {
    const cues = [];
    sc.forEach((s, k) => {
      const end = s.t0 + s.dur;
      if (s.captions) s.captions[lang].forEach(c => cues.push([s.t0 + c[0], s.t0 + c[1], c[2]]));
      s.steps.forEach((st, j) => { if (!st[lang]) return; const e = j + 1 < s.steps.length ? s.t0 + s.steps[j + 1].at : end; cues.push([s.t0 + st.at + 0.3, e - 0.1, (s.title ? (lang === 'es' ? s.title[0] : s.title[1]) + '. ' : '') + clean(st[lang])]); });
    });
    cues.sort((a, b) => a[0] - b[0]);
    fs.writeFileSync(path.join(outdir, `simon-vallarta.${lang}.srt`), cues.map((c, i) => `${i + 1}\n${ts(c[0])} --> ${ts(c[1])}\n${c[2]}\n`).join('\n'));
  }
  const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  fs.writeFileSync(path.join(outdir, 'chapters.json'), JSON.stringify(sc.map(s => ({ t: mmss(s.t0), id: s.id, title: s.title })), null, 1));
  console.log('captions and chapters written; total', total, 's');
})();
