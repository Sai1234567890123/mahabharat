// Record episodes/<ep>/animatic.html to animatic.mp4. No cost: Playwright + ffmpeg only.
//   node studio/tools/record_animatic.js ep01            full video at 12 drawn frames a second
//   node studio/tools/record_animatic.js ep01 sheet      one still per shot, for checking
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
(async () => {
  const ep = process.argv[2] || 'ep01', mode = process.argv[3] || 'video';
  const dir = path.resolve(__dirname, '..', 'episodes', ep);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + path.join(dir, 'animatic.html'));
  const total = await page.evaluate(() => window.TOTAL);
  const grab = async t => Buffer.from((await page.evaluate(t => { window.renderAt(t); return document.getElementById('c').toDataURL('image/jpeg', 0.9); }, t)).split(',')[1], 'base64');
  if (mode === 'sheet') {
    const out = process.argv[4] || path.join(dir, 'check'); fs.mkdirSync(out, { recursive: true });
    const shots = await page.evaluate(() => { let a = 0; return window.EP.shots.map(s => { const r = { id: s.id, t0: a, cut: s.cut_s }; a += s.cut_s; return r; }); });
    for (const s of shots) for (const [k, f] of [['a', 0.2], ['b', 0.5], ['c', 0.85]]) fs.writeFileSync(path.join(out, `${s.id}_${k}.jpg`), await grab(s.t0 + s.cut * f));
  } else {
    const fps = 12, n = Math.round(total * fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-r', '24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', path.join(dir, 'animatic.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) { const b = await grab(i / fps); if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r)); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
  if (errors.length) { console.error('PAGE ERRORS:\n' + [...new Set(errors)].join('\n')); process.exit(1); }
  console.log('ok', mode);
})();
