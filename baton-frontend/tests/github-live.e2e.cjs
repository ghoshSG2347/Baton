// Opt-in live test: actual React -> FastAPI -> GitHub. No API fixture routes.
// Obtain the existing Git login in memory; never write/log the credential.
const { execFileSync } = require('node:child_process');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.BATON_PLAYWRIGHT_PATH || 'playwright');
const preview = process.env.BATON_PREVIEW_URL || 'http://localhost:5173/';
let token = '', browser;
const checks = [], calls = [];
async function check(name, run) { await run(); checks.push(name); console.log('Passed: ' + name); }
(async () => {
  const credential = execFileSync('git', ['credential', 'fill'], {
    input: 'protocol=https\nhost=github.com\n\n', encoding: 'utf8',
    env: { ...process.env, GIT_TERMINAL_PROMPT: '0', GCM_INTERACTIVE: 'Never' },
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  token = credential.split(/\r?\n/).find(line => line.startsWith('password='))?.slice(9) || '';
  assert(token.length > 0, 'A valid existing GitHub login is required for this opt-in test.');
  browser = await chromium.launch({ executablePath: process.env.BATON_BROWSER_PATH, headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', () => errors.push('Browser runtime error'));
  page.on('request', req => {
    const url = new URL(req.url());
    if (!url.pathname.startsWith('/api/')) return;
    // Only presence/match booleans are retained, never header contents.
    const header = req.headers()['x-github-token'];
    calls.push({ path: url.pathname, method: req.method(), tokenPresent: !!header, tokenMatches: header === token });
  });
  await page.goto(preview);
  await page.getByRole('button', { name: /Enter Mission Control/i }).first().click();
  await page.getByRole('button', { name: 'Repository', exact: true }).click();
  await page.getByPlaceholder('https://github.com/owner/repository').fill('https://github.com/ghoshSG2347/Alzheimer-Disease-Prediction-Model');
  const validation = page.waitForResponse(r => r.url().endsWith('/validate-repository') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'VALIDATE REPOSITORY', exact: true }).click();
  const response = await validation;
  const connected = response.status() === 200;
  await check('A: public connection succeeds or correctly reports an exhausted anonymous bucket', async () => {
    assert([200, 429].includes(response.status()), 'Unexpected public connection failure.');
    assert(calls.some(c => c.path.endsWith('/validate-repository') && !c.tokenPresent));
  });
  if (connected) {
    await page.getByLabel('GitHub token for connected repository').waitFor();
    await page.getByRole('button', { name: 'Check GitHub access', exact: true }).click();
    await page.getByText(/Using public unauthenticated access/).waitFor();
    console.log('Public access: ' + await page.getByText(/Using public unauthenticated access/).innerText());
    await page.getByRole('button', { name: 'AI workspace', exact: true }).click();
    await page.locator('.ai-refresh:not(:disabled)').waitFor({ timeout: 60000 });
    await page.locator('.ai-refresh').click();
    await page.waitForFunction(() => !document.querySelector('.ai-refresh .ai-spin'), null, { timeout: 120000 });
    await check('A: unauthenticated analysis succeeds or reports the exhausted bucket', async () => {
      const text = await page.locator('.ai-state-row').innerText();
      assert(text.includes('Current') || text.includes('GitHub API limit reached'));
      console.log('Public analysis status: ' + text.replace(/\s+/g, ' '));
    });
    await page.getByRole('button', { name: 'Repository', exact: true }).click();
  } else {
    await page.getByRole('heading', { name: 'GitHub API limit reached', exact: true }).waitFor();
  }
  const input = connected ? page.getByLabel('GitHub token for connected repository') : page.getByPlaceholder('ghp_...');
  const submit = () => page.getByRole('button', { name: connected ? 'Check GitHub access' : 'VALIDATE REPOSITORY', exact: true }).click();
  await input.fill('invalid-audit-token'); await submit();
  await check('C: invalid token is authentication failure, not rate limit', async () => {
    await page.getByRole('heading', { name: 'GitHub authentication failed', exact: true }).waitFor();
  });
  await input.fill(token); await submit();
  if (!connected) {
    await page.getByLabel('GitHub token for connected repository').waitFor();
    await page.getByRole('button', { name: 'Check GitHub access', exact: true }).click();
  }
  await page.getByText(/GitHub accepted the token/).waitFor();
  await check('B: token accepted through Baton shared GitHubService and authenticated bucket', async () => {
    const text = await page.getByText(/GitHub accepted the token/).innerText();
    assert(text.includes('5000'), 'Expected authenticated GitHub bucket.');
    console.log('Authenticated access: ' + text);
  });
  await page.getByRole('button', { name: 'AI workspace', exact: true }).click();
  await page.locator('.ai-refresh:not(:disabled)').waitFor({ timeout: 60000 });
  const before = calls.filter(c => c.path.includes('/analysis/')).length;
  // Two events in one render must issue only one analysis POST.
  await page.locator('.ai-refresh').evaluate(button => { button.click(); button.click(); });
  await page.waitForFunction(() => document.querySelector('.ai-grounding')?.textContent === 'Repository grounded', null, { timeout: 120000 });
  await page.locator('.ai-refresh:not(:disabled)').waitFor();
  await check('B/D: authenticated analysis succeeds, double click sends one analysis request', async () => {
    const requests = calls.filter(c => c.path.includes('/analysis/'));
    assert(requests.length === before + 1, 'Double click duplicated analysis POST.');
    assert(requests[requests.length - 1].tokenMatches, 'Analysis did not forward the valid in-memory token.');
  });
  await page.getByRole('button', {name:'Analysis', exact:true}).click();
  await page.getByRole('button', {name:'ANALYZE PROJECT', exact:true}).click();
  await page.getByRole('button', {name:'RE-ANALYZE', exact:true}).waitFor({timeout:60000});
  await check('D: ordinary repeated analysis returns the existing same-commit snapshot', async () => {
    assert(calls.filter(c => c.path.includes('/analysis/')).length === before + 2);
  });
  await page.getByRole('button', {name:'AI workspace', exact:true}).click();
  const after = calls.filter(c => c.path.includes('/analysis/')).length;
  await page.getByRole('button', { name: 'Context Builder', exact: true }).click();
  const generate = page.getByRole('button', { name: /GENERATE CONTEXT/ });
  await generate.click();
  await page.getByText('GENERATED', { exact: true }).waitFor({ timeout: 60000 });
  await check('F: Context Builder consumes canonical snapshot without analysis POST', async () => {
    assert(calls.filter(c => c.path.includes('/analysis/')).length === after);
  });
  await page.getByRole('button', { name: 'AI workspace', exact: true }).click();
  await check('E: reopening chat uses snapshot without analysis POST', async () => {
    await page.locator('.ai-refresh:not(:disabled)').waitFor();
    assert(calls.filter(c => c.path.includes('/analysis/')).length === after);
  });
  await check('token never persisted in browser storage', async () => {
    const safe = await page.evaluate(secret => !JSON.stringify(localStorage).includes(secret) && !JSON.stringify(sessionStorage).includes(secret), token);
    assert(safe, 'Credential was persisted.');
  });
  const reloadStart = calls.length;
  await page.reload();
  await page.getByRole('button', { name: /Enter Mission Control/i }).first().click();
  await page.waitForFunction(() => {
    const status = document.querySelector('.ai-lifecycle')?.textContent;
    return status === 'Current' || status === 'GitHub API limit reached';
  }, null, {timeout:60000});
  await page.getByRole('button', {name:'Repository',exact:true}).click();
  await page.getByLabel('GitHub token for connected repository').fill(token);
  await page.getByRole('button', {name:'Check GitHub access',exact:true}).click();
  await page.getByText(/GitHub accepted the token/).waitFor();
  await page.getByRole('button', {name:'AI workspace',exact:true}).click();
  await page.locator('.ai-refresh:not(:disabled)').waitFor({timeout:60000});
  await check('reload clears token; re-entry restores authenticated snapshot without a rescan', async () => {
    assert(calls.slice(reloadStart).some(c => c.path.endsWith('/inspect') && !c.tokenPresent));
    assert(calls.filter(c => c.path.includes('/analysis/')).length === after);
    assert(await page.locator('.ai-grounding').innerText() === 'Repository grounded');
  });
  assert(errors.length === 0, 'Browser runtime errors occurred.');
  console.log(JSON.stringify({ passed: checks.length, api_calls: calls }, null, 2));
  await browser.close(); token = '';
})().catch(async error => {
  const safeMessage = String(error.message || 'Live audit failed').split(token || '\0').join('[REDACTED]');
  console.error(safeMessage);
  if (browser) await browser.close();
  token = ''; process.exitCode = 1;
});
