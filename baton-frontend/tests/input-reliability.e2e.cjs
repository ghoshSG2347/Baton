// Real browser input checks with isolated API fixtures; no provider or hardware claims.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.BATON_PLAYWRIGHT_PATH || 'playwright');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../.test-output/workspace-fixtures.json'), 'utf8'));
const checks = [];
let browser;
const url = process.env.BATON_PREVIEW_URL || 'http://127.0.0.1:5181/';
async function native(page) {
  assert(await page.evaluate(() => [...document.querySelectorAll('body,button,a,input,textarea,select')].every(el => getComputedStyle(el).cursor !== 'none')));
  assert.equal(await page.evaluate(() => document.body.style.overflow), '');
}
async function wheel(page, locator, delta = 600) {
  await locator.hover();
  const before = await locator.evaluate(el => el.scrollTop);
  await page.mouse.wheel(0, delta);
  await page.waitForTimeout(400);
  const after = await locator.evaluate(el => el.scrollTop);
  assert(delta > 0 ? after > before : after < before, `Native wheel failed (${before} -> ${after})`);
}
(async () => {
  browser = await chromium.launch({ executablePath: process.env.BATON_BROWSER_PATH, headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 800 } });
  const page = await context.newPage(); const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await context.route(/\/api\/(?:v1\/|health)/, async route => {
    const p = new URL(route.request().url()).pathname;
    let result = { status: 'ok' };
    if (p.endsWith('/validate-repository')) result = { owner: 'example', repository: 'project', default_branch: 'main', accessible: true, authenticated: true, token_source: 'request' };
    if (p.endsWith('/branches')) result = { branches: [{ name: 'main', sha: fixture.project.identity.commit }] };
    if (p.endsWith('/inspect')) result = fixture.project;
    if (p.endsWith('/chat')) result = { ...fixture.chat, answer: '# Long answer\n' + ('Repository evidence paragraph.\n\n'.repeat(120)) };
    if (p.endsWith('/artifacts')) result = fixture.artifact;
    if (p.endsWith('/tree')) result = { items: [] };
    await route.fulfill({ json: result });
  });
  await page.addInitScript(() => localStorage.setItem('baton-workspace-state', JSON.stringify({ repo: { owner: 'example', repository: 'project', default_branch: 'main' }, selectedBranch: 'main', members: [] })));
  await page.goto(url); await native(page);
  await page.mouse.move(350, 300);
  await page.locator('[data-decorative-cursor="ring"]').waitFor();
  assert.equal(await page.locator('[data-decorative-cursor="ring"]').evaluate(el => getComputedStyle(el).pointerEvents), 'none');
  const start = await page.evaluate(() => scrollY);
  await page.mouse.wheel(0, 700); await page.waitForTimeout(400);
  assert(await page.evaluate(() => scrollY) > start);
  await page.keyboard.press('Home'); await page.waitForTimeout(400);
  await page.keyboard.press('PageDown'); await page.waitForTimeout(400);
  assert(await page.evaluate(() => scrollY) > 0);
  checks.push('Landing native cursor, decorative hit testing, wheel and keyboard scroll');
  await page.getByRole('button', { name: /Enter Mission Control/ }).first().click();
  await page.getByLabel('GitHub token for connected repository').fill('fixture-browser-credential');
  await page.getByRole('button', { name: 'Validate repository access', exact: true }).click();
  const composer = page.getByLabel('Ask about the connected repository');
  await composer.fill('Explain this repository');
  await page.getByRole('button', { name: 'Send repository question', exact: true }).click();
  await page.locator('.ai-assistant-message').waitFor();
  await native(page);
  const conversation = page.locator('.ai-conversation');
  await conversation.evaluate(el => { el.scrollTop = 0; });
  await wheel(page, conversation); await wheel(page, conversation, -400);
  await composer.focus(); assert.equal(await composer.evaluate(el => getComputedStyle(el).cursor), 'text');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle), 'solid');
  checks.push('Long AI response scrolls both ways; composer keeps native text cursor and visible keyboard focus');
  for (const name of ['Overview', 'Repository', 'Analysis', 'Team & Ownership', 'Context Builder', 'Prompt Builder', 'Conflict Radar', 'Integration', 'AI workspace']) {
    await page.getByRole('button', { name, exact: true }).click(); await native(page);
    const main = page.getByRole('main', { name: 'Workspace content' });
    if (await main.evaluate(el => el.scrollHeight > el.clientHeight + 20)) {
      await main.evaluate(el => { el.scrollTop = 0; });
      await main.focus(); await page.keyboard.press('PageDown'); await page.waitForTimeout(400);
      assert(await main.evaluate(el => el.scrollTop) > 0, `${name} keyboard scroll`);
    }
  }
  await page.getByRole('button', { name: 'Open workspace settings' }).click();
  await page.getByLabel('Baton access key').focus(); await page.keyboard.press('Escape');
  assert(await page.getByRole('button', { name: 'Open workspace settings' }).evaluate(el => el === document.activeElement));
  assert.equal(await page.getByLabel('Baton access key').count(), 0);
  await page.getByRole('button', { name: 'New chat', exact: true }).click();
  assert(await composer.evaluate(el => el === document.activeElement));
  checks.push('Every existing section and settings Escape preserve native input and unlocked body');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.getByRole('button', { name: 'Return to Baton landing page' }).click();
  await page.getByRole('button', { name: /Enter Mission Control/ }).first().waitFor();
  assert.equal(await page.locator('[data-decorative-cursor]').count(), 0);
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior), 'auto');
  await native(page); checks.push('Runtime reduced-motion change disables decorative cursor and smooth scrolling');
  assert.deepEqual(errors, []);
  await context.close();
  const mobile = await browser.newContext({ viewport: { width: 390, height: 740 }, isMobile: true, hasTouch: true });
  const touch = await mobile.newPage(); await touch.goto(url);
  assert.equal(await touch.locator('[data-decorative-cursor]').count(), 0);
  const cdp = await mobile.newCDPSession(touch);
  await touch.getByRole('button', { name: /Enter Mission Control/ }).first().waitFor();
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 190, y: 600 }] });
  for (let y = 550; y >= 150; y -= 50) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 190, y }] });
    await touch.waitForTimeout(50);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await touch.waitForTimeout(400); assert(await touch.evaluate(() => scrollY) > 0);
  await touch.getByRole('button', { name: /Enter Mission Control/ }).first().tap();
  await touch.getByRole('button', { name: 'Open navigation' }).tap();
  await touch.keyboard.press('Escape');
  assert(await touch.getByRole('button', { name: 'Open navigation' }).evaluate(el => el === document.activeElement));
  await native(touch); checks.push('Emulated touch scroll/tap, no custom cursor, mobile navigation Escape restores focus');
  await mobile.close();
  const failedEffect = await browser.newContext();
  await failedEffect.addInitScript(() => { HTMLCanvasElement.prototype.getContext = () => null; });
  const failed = await failedEffect.newPage(); await failed.goto(url);
  await failed.getByRole('button', { name: /Enter Mission Control/ }).first().click();
  await failed.getByRole('main', { name: 'Workspace content' }).waitFor(); await native(failed);
  checks.push('Unavailable decorative canvas still permits entry and native workspace interaction');
  await failedEffect.close();
  const fallback = await browser.newContext({ javaScriptEnabled: false });
  const bare = await fallback.newPage(); await bare.goto(url); await native(bare);
  checks.push('Native cursor CSS survives JavaScript being unavailable (SPA requires JavaScript for content)');
  await fallback.close();
  console.log(JSON.stringify({ status: 'passed', browser: process.env.BATON_BROWSER_PATH, checks }, null, 2));
})().catch(e => { console.error(e); process.exitCode = 1; }).finally(async () => { await browser?.close(); });
