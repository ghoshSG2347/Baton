// Isolated browser test. All repository/provider API calls are fixture routes.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.BATON_PLAYWRIGHT_PATH || 'playwright');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../.test-output/workspace-fixtures.json'), 'utf8'));

let browser, page;
(async () => {
  browser = await chromium.launch({ executablePath: process.env.BATON_BROWSER_PATH, headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  page = await context.newPage();
  const failures = []; const calls = []; let staleMode = false;
  page.on('pageerror', error => failures.push(error.message));
  await context.route(/\/api\/(?:v1\/|health(?:$|\?))/, async route => {
    const req = route.request(); const url = new URL(req.url());
    const body = req.method() === 'POST' ? req.postDataJSON() || {} : {}; calls.push({ path: url.pathname, body });
    let response;
    if (url.pathname.endsWith('/branches')) response = { branches: [{ name: 'main', sha: 'commit-1' }, { name: 'feature/ask-book', sha: 'commit-2' }, { name: 'missing', sha: 'unavailable' }] };
    else if (url.pathname.endsWith('/inspect')) response = body.branch === 'missing' ? fixture.unavailable : staleMode ? (body.continue_snapshot ? fixture.continued : fixture.stale) : body.branch === 'feature/ask-book' ? fixture.feature : body.member?.name ? fixture.role : fixture.project;
    else if (url.pathname.endsWith('/chat')) {
      if (staleMode && !body.continue_snapshot) { await route.fulfill({ status: 409, json: { detail: 'Repository intelligence snapshot is stale; the requested commit is not the current branch state.' }, headers: { 'Access-Control-Allow-Origin': '*' } }); return; }
      response = body.message.includes('technical design') ? { ...fixture.chat_artifact, revision: 2 } : body.continue_snapshot ? fixture.continued_chat : fixture.chat;
    }
    else if (url.pathname.endsWith('/source')) response = { path: body.path, content: 'export function askBook() {}', start_line: 1, end_line: 1, partial: false, identity: { commit: body.commit } };
    else if (url.pathname.endsWith('/artifacts')) response = fixture.artifact;
    else if (url.pathname.endsWith('/compare')) response = fixture.comparison;
    else if (url.pathname.includes('/analysis/')) response = { metadata: { commit: 'commit-1' } };
    else response = { status: 'ok', service: 'baton-backend' };
    await route.fulfill({ json: response, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS' } });
  });
  await page.addInitScript(() => {
    localStorage.clear();
    localStorage.setItem('baton-workspace-state', JSON.stringify({
      repo: { owner: 'example', repository: 'project', default_branch: 'main', accessible: true },
      selectedBranch: 'main', selectedFolder: '', repoUrl: 'https://github.com/example/project', isDemoMode: false,
      members: [{ id: 'frontend', name: 'Frontend developer', role: 'Frontend Developer', folders: ['client/'], do_not_touch: ['server/', 'shared/'], job: 'Maintain Ask Book UI', github: '', branch: 'main', depends_on: [], provides_to: [] }],
    }));
  });
  await page.goto(process.env.BATON_PREVIEW_URL || 'http://127.0.0.1:5173/');
  await page.getByRole('button', { name: /Enter Mission Control/i }).first().click();
  await page.getByRole('heading', { name: /Ask Baton/ }).waitFor();
  await page.getByText('complete evidence', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Project scope/ }).click();
  await page.getByLabel('Developer', { exact: true }).selectOption('frontend');
  await page.getByRole('button', { name: 'Apply scope', exact: true }).click();
  await page.getByRole('button', { name: /Frontend developer/ }).waitFor();
  await page.getByRole('textbox', { name: 'Ask about the connected repository' }).fill('What is the Ask Book API?');
  await page.getByRole('button', { name: 'Send repository question', exact: true }).click();
  await page.locator('.ai-assistant-message').getByText('POST /api/ask-book', { exact: true }).waitFor();
  assert(calls.find(call => call.path.endsWith('/chat')).body.member.do_not_touch.includes('server/'));
  assert(calls.find(call => call.path.endsWith('/chat')).body.commit === fixture.project.identity.commit);
  await page.locator('.ai-citations summary').click();
  await page.locator('.ai-file-link').filter({ hasText: 'server/routes.ts' }).first().click();
  await page.getByText('export function askBook() {}', { exact: true }).waitFor();
  assert(calls.find(call => call.path.endsWith('/source')).body.commit === fixture.project.identity.commit);
  await page.getByRole('button', { name: 'AI workspace', exact: true }).click();
  assert.equal(await page.locator('.ai-assistant-message').count(), 1, 'File navigation must preserve chat');
  await page.getByRole('textbox', { name: 'Ask about the connected repository' }).fill('Generate a technical design');
  await page.getByRole('button', { name: 'Send repository question', exact: true }).click();
  await page.getByRole('button', { name: 'View Technical design', exact: true }).waitFor();
  await page.getByRole('button', { name: 'View Technical design', exact: true }).click();
  await page.getByRole('dialog', { name: 'Technical design' }).waitFor();
  await page.keyboard.press('Escape');
  await page.screenshot({ path: '.test-output/workspace-desktop.png', fullPage: true, animations: 'disabled' });
  await page.getByRole('button', { name: 'Generate artifact', exact: true }).click();
  await page.getByRole('dialog', { name: 'Repository context' }).waitFor();
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download', exact: true }).click();
  assert((await downloadEvent).suggestedFilename().endsWith('.md'));
  await page.keyboard.press('Escape');
  await page.getByRole('dialog').waitFor({ state: 'hidden' });
  staleMode = true;
  await page.getByRole('textbox', { name: 'Ask about the connected repository' }).fill('Explain the API');
  await page.getByRole('button', { name: 'Send repository question', exact: true }).click();
  await page.getByRole('button', { name: 'Continue With Snapshot', exact: true }).waitFor();
  assert(await page.getByRole('button', { name: 'Send repository question', exact: true }).isDisabled());
  await page.getByRole('button', { name: 'Continue With Snapshot', exact: true }).click();
  await page.getByRole('button', { name: 'Continue With Snapshot', exact: true }).waitFor({ state: 'hidden' });
  await page.getByRole('textbox', { name: 'Ask about the connected repository' }).fill('What is the Ask Book API?');
  await page.getByRole('button', { name: 'Send repository question', exact: true }).click();
  await page.locator('.ai-assistant-message').getByText(/Based on older snapshot/).waitFor();
  assert(calls.filter(call => call.path.endsWith('/chat')).at(-1).body.continue_snapshot);
  staleMode = false;
  await page.getByLabel('Comparison branch', { exact: true }).selectOption('feature/ask-book');
  await page.getByRole('button', { name: 'Compare snapshots', exact: true }).click();
  await page.getByText('1 changed blobs · 1 contract changes', { exact: true }).waitFor();
  await page.getByLabel('Current repository branch', { exact: true }).selectOption('feature/ask-book');
  await page.getByRole('button', { name: 'Refresh analysis', exact: true }).waitFor();
  await page.locator('.ai-welcome').waitFor();
  await page.getByText('Context switched from main → feature/ask-book', { exact: true }).waitFor();
  assert.equal(await page.locator('.ai-assistant-message').count(), 0);
  assert.equal(await page.locator('.ai-artifact-item').count(), 0);
  assert.equal(await page.locator('.ai-comparison').count(), 0);
  await page.getByRole('button', { name: /Frontend developer/ }).waitFor();
  const stored = await page.evaluate(() => localStorage.getItem('baton-workspace-state'));
  assert(!stored.includes('githubToken') && !stored.includes('batonAccessKey') && !stored.includes('conversation_id'));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Hide evidence panel', exact: true }).click();
  assert.equal(await page.locator('#workspace-navigation').isVisible(), false);
  await page.screenshot({ path: '.test-output/workspace-mobile.png', fullPage: true, animations: 'disabled' });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await page.getByRole('button', { name: 'Open navigation', exact: true }).click();
  await page.getByRole('button', { name: 'AI workspace', exact: true }).waitFor();
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Open navigation', exact: true }).waitFor();
  assert.equal(failures.length, 0, failures.join('\n'));
  assert(!calls.some(call => call.path.includes('/analysis/')), 'Inspection and chat must not silently trigger repository analysis');
  const inspectBefore = calls.filter(call => call.path.endsWith('/inspect')).length;
  await page.getByRole('button', { name: 'Refresh analysis', exact: true }).click();
  await page.getByRole('button', { name: 'Refresh analysis', exact: true }).waitFor();
  await page.waitForFunction(() => !document.querySelector('.ai-loading-line'));
  assert(calls.some(call => call.path.includes('/analysis/')));
  assert(calls.filter(call => call.path.endsWith('/inspect')).length > inspectBefore);
  await page.getByLabel('Current repository branch', { exact: true }).selectOption('missing');
  await page.getByRole('button', { name: 'Analyze Branch', exact: true }).waitFor();
  assert(await page.getByRole('button', { name: 'Send repository question', exact: true }).isDisabled());
  await page.getByRole('button', { name: 'Open navigation', exact: true }).click();
  await page.locator('#sidebar-change-repository-btn').click();
  await page.getByRole('heading', { name: 'Repository', exact: true }).waitFor();
  assert.equal(await page.locator('.ai-assistant-message').count(), 0);
  assert.equal(await page.locator('.ai-artifact-item').count(), 0);
  await browser.close();
  console.log('Browser checks passed: grounded answer, protected role payload, pinned commit, artifact preview/download/Escape, comparison, branch isolation, memory-only credentials, mobile overflow, explicit refresh.');
})().catch(async error => { if (page) { await page.screenshot({ path: '.test-output/workspace-failure.png', fullPage: true }); console.error('Browser title:', await page.title()); console.error('Browser error text:', await page.locator('body').innerText()); } console.error(error.message); if (browser) await browser.close(); process.exitCode = 1; });
