// Render each graphic in each language to PNG (2x) and JPEG. Usage: node render_png.js PAGE.html OUTDIR [scale]
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [file, out, sc] = process.argv.slice(2); const scale = +(sc || 2); fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch(); const page = await (await browser.newContext({ viewport: { width: 1080, height: 1620 }, deviceScaleFactor: scale })).newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('file://' + file); await page.evaluate(() => window.READY);
  for (const g of ['wind', 'rain', 'flood', 'timing', 'models']) for (const lang of ['es', 'en']) {
    await page.evaluate(([g, l]) => window.render(g, l), [g, lang]);
    const el = await page.$('#cv'); const name = `simon_${g}_${lang}`;
    await el.screenshot({ path: path.join(out, name + '.png') });
    await el.screenshot({ path: path.join(out, name + '.jpg'), type: 'jpeg', quality: 88 });
    console.log(name, errs.length ? 'ERR ' + errs.join(' | ') : 'ok'); errs.length = 0;
  }
  await browser.close();
})();
