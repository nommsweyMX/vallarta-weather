// Build the report HTML (fonts + image paths) and print it to PDF with Chromium.
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs'), path = require('path');
const S = process.argv[2], H = '/home/user/vallarta-weather/hurricane-simon';
let css = fs.readFileSync(H + '/video/fonts/fonts.css', 'utf8').replace(/url\(([^)]+\.woff2)\)/g, (m, f) => 'url(file://' + H + '/video/fonts/' + f + ')');
let html = fs.readFileSync(S + '/report/simon_report.html', 'utf8').replace('__FONTS__', css).replace(/__OUT__/g, 'file://' + S + '/bay/out').replace(/__REP__/g, 'file://' + S + '/report');
fs.writeFileSync(S + '/report/simon_report_built.html', html);
(async () => {
  const browser = await chromium.launch(); const page = await browser.newPage();
  await page.goto('file://' + S + '/report/simon_report_built.html', { waitUntil: 'load' }); await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(800);
  await page.pdf({ path: S + '/report/Simon_Puerto_Vallarta_models_verification_uncertainty.pdf', format: 'Letter', printBackground: true, displayHeaderFooter: true,
    headerTemplate: '<div></div>', footerTemplate: '<div style="font-family: DejaVu Sans, Arial, sans-serif; font-size: 7.5px; color: #6b6a66; width: 100%; padding: 0 16mm; display: flex; justify-content: space-between;"><span>Hurricane Simon and Puerto Vallarta · verification and uncertainty · 11 Oct 2026, 3 pm · not an official forecast</span><span>page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>',
    margin: { top: '17mm', bottom: '18mm', left: '16mm', right: '16mm' } });
  await browser.close(); console.log('pdf ok');
})();
