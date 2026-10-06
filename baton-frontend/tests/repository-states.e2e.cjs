// Real React UI transitions against isolated canonical service fixtures.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.BATON_PLAYWRIGHT_PATH || 'playwright');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../.test-output/workspace-fixtures.json'), 'utf8'));
const clone = value => JSON.parse(JSON.stringify(value));
let browser, page, mode = 'missing', analysisFailure = null, analysisDelay = 0;
let delayedBranch = '', releaseBranch, analysisCount = 0;
const calls = [], failures = [], checks = [];
const heads = { main: fixture.project.identity.current_head, 'feature/ask-book': fixture.feature.identity.current_head, missing: '3a7a550985975a73805974c0e8017c720b6dc8f0' };
const baseState = { repo: { owner: 'example', repository: 'project', default_branch: 'main', accessible: true }, selectedBranch: 'main', selectedFolder: '', repoUrl: 'https://github.com/example/project', isDemoMode: false, members: [] };
const preview = process.env.BATON_PREVIEW_URL || 'http://127.0.0.1:5174/';
async function loaded() { await page.waitForFunction(() => { const button = document.querySelector('.ai-refresh'); return button && (!button.disabled || document.querySelector('.ai-lifecycle')?.textContent === 'GitHub API limit reached'); }); }
async function start(nextMode, branch = 'main') {
 mode = nextMode; analysisFailure = null; delayedBranch = '';
 await page.goto(preview);
 await page.evaluate(state => localStorage.setItem('baton-workspace-state', JSON.stringify(state)), { ...baseState, selectedBranch: branch });
 await page.reload();
 await page.getByRole('button', { name: /Enter Mission Control/i }).first().click();
 await page.getByRole('heading', { name: /Ask Baton/ }).waitFor(); await loaded();
}
async function check(name, callback) { await callback(); checks.push(name); console.log('Passed: ' + name); }
function inspection(body) {
 const base = clone(body.branch === 'feature/ask-book' ? fixture.feature : fixture.project);
 const unavailable = clone(fixture.unavailable);
 unavailable.identity = { ...unavailable.identity, branch: body.branch, repository: body.owner + '/' + body.repo, current_head: heads[body.branch] || heads.main, project_root: body.folder || '' };
 unavailable.state = 'NOT_ANALYZED'; unavailable.identity.snapshot_status = 'NOT_ANALYZED';
 if (mode === 'missing' || body.branch === 'missing') return unavailable;
 if (mode === 'stale') return { ...clone(fixture.stale), identity: { ...fixture.stale.identity, branch: body.branch, current_head: 'new-current-head' }, state: 'STALE' };
 if (mode === 'invalid') return { ...base, identity: { ...base.identity, branch: 'different-branch' } };
 if (mode === 'empty') return { ...unavailable, state: 'EMPTY_REPOSITORY', identity: { ...unavailable.identity, current_head: null, snapshot_status: 'EMPTY_REPOSITORY' } };
 if (mode === 'limited') { base.completeness.status = 'PARTIAL'; base.completeness.files_omitted = 16; }
 if (mode === 'spec') base.project_types = ['Documentation / Specification Only'];
 if (mode === 'config') base.provider.configured = false;
 base.identity.analysis_timestamp = new Date(1700000000000 + analysisCount * 1000).toISOString();
 return base;
}
(async () => {
 browser = await chromium.launch({ executablePath: process.env.BATON_BROWSER_PATH, headless: true });
 const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
 page = await context.newPage(); page.on('pageerror', error => failures.push(error.message));
 await context.route(/\/api\/(?:v1\/|health(?:$|\?))/, async route => {
  const req = route.request(), url = new URL(req.url());
  const body = req.method() === 'POST' ? req.postDataJSON() || {} : {}; calls.push({ path: url.pathname, body });
  const send = (response, status = 200) => route.fulfill({ status, json: response, headers: { 'Access-Control-Allow-Origin': '*' } });
  if (req.method() === 'OPTIONS') return send({});
  if (url.pathname.endsWith('/access')) return send({authenticated:true,token_present:true,token_source:'request',upstream_status:200,rate_limit:{limit:5000,remaining:4999,reset_at:2000000000}});
  if (url.pathname.endsWith('/branches')) return send({ branches: Object.entries(heads).map(([name, sha]) => ({ name, sha })) });
  if (url.pathname.endsWith('/inspect')) {
   if (mode === 'network') return route.abort('failed');
   if (typeof mode === 'object') return send({ detail: 'Synthetic safe diagnostic', ...mode }, mode.status);
   const result = inspection(body);
   if (body.branch === delayedBranch) await new Promise(resolve => { releaseBranch = resolve; });
   return send(result);
  }
  if (url.pathname.includes('/analysis/')) {
   if (analysisDelay) await new Promise(resolve => setTimeout(resolve, analysisDelay));
   if (analysisFailure) return send(analysisFailure, 500);
   analysisCount++; mode = 'ready';
   return send(clone(fixture.analysis));
  }
  if (url.pathname.endsWith('/validate-repository')) return send(baseState.repo);
  if (url.pathname.endsWith('/chat')) return send(fixture.chat);
  if (url.pathname.endsWith('/artifacts')) return send(fixture.artifact);
  if (url.pathname.endsWith('/tree')) return send({ items: [] });
  return send({ status: 'ok', service: 'baton-backend' });
 });
 await start('ready');
 await check('Conflict Radar preserves a failed branch read instead of reporting no conflicts', async () => {
  await page.getByRole('button', { name: 'Conflict Radar', exact: true }).click();
  await page.locator('textarea:visible').fill('main\nmissing');
  await page.route('**/api/v1/github/tree?**', route => route.fulfill({ status: 404, json: { detail: 'GitHub repository or resource not found, or inaccessible.', code: 'github_not_found' } }));
  const before = calls.filter(call => call.path.endsWith('/conflicts')).length;
  await page.getByRole('button', { name: 'SCAN FOR CONFLICTS', exact: true }).click();
  await page.getByText('Repository or branch not found', { exact: true }).waitFor();
  await page.getByText('Technical details', { exact: true }).click();
  assert((await page.locator('.baton-status pre').innerText()).includes('HTTP 404 · github_not_found'));
  assert.equal(calls.filter(call => call.path.endsWith('/conflicts')).length, before);
  assert.equal(await page.getByText('NO CONFLICTS DETECTED', { exact: true }).count(), 0);
  await page.unroute('**/api/v1/github/tree?**');
 });
 await start('missing', 'missing');
 await check('connected without analysis: neutral grounding, known HEAD, neutral role/ownership, disabled composer', async () => {
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository connected');
  assert((await page.locator('.ai-visible-state').innerText()).includes('3a7a55'));
  assert((await page.locator('.ai-visible-state').innerText()).includes('Role: Unassigned'));
  assert((await page.locator('.ai-visible-state').innerText()).includes('Ownership: Project-wide'));
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
  assert(await page.getByText('No analysis snapshot yet', { exact: true }).isVisible());
  assert.equal(await page.locator('.ai-analysis-status').getAttribute('role'), 'status');
  assert(!calls.some(call => call.path.includes('/analysis/')));
 });
 await page.screenshot({ path: '.test-output/analysis-required-desktop.png', fullPage: true, animations: 'disabled' });
 await check('analysis running does not claim grounding and retains HEAD', async () => {
  await page.getByLabel('Current repository branch').selectOption('main'); await loaded();
  analysisDelay = 700; await page.locator('.ai-refresh').click();
  await page.getByText('Analyzing repository', { exact: true }).waitFor();
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
  assert((await page.locator('.ai-visible-state').innerText()).includes(heads.main.slice(0,7)));
  await loaded(); analysisDelay = 0;
 });

 await check('analysis success enables canonical grounded chat', async () => {
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository grounded');
  assert(await page.getByLabel('Ask about the connected repository').isEnabled());
  assert.equal(await page.locator('.ai-refresh').innerText(), 'Refresh analysis');
 });
 await check('refresh sends force_refresh and creates a current reinspection', async () => {
  const before = analysisCount; await page.locator('.ai-refresh').click(); await loaded();
  assert.equal(analysisCount, before + 1);
  assert.equal(calls.filter(call => call.path.includes('/analysis/')).at(-1).body.force_refresh, true);
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository grounded');
 });
 await check('branch switch cannot reuse previous snapshot', async () => {
  await page.getByLabel('Current repository branch').selectOption('missing'); await loaded();
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository connected');
  assert.equal(await page.locator('.ai-refresh').innerText(), 'Analyze branch');
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
 });
 await start('missing');
 await check('analysis in Analysis view updates the existing Ask Baton workspace', async () => {
  await page.getByRole('button', {name: 'Analysis', exact: true}).click();
  await page.getByRole('button', {name: 'ANALYZE PROJECT', exact: true}).click();
  await page.getByRole('button', {name: 'RE-ANALYZE', exact: true}).waitFor();
  await page.getByRole('button', {name: 'AI workspace', exact: true}).click(); await loaded();
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository grounded');
 });
 await start('stale');
 await check('changed commit is stale, known current SHA, no grounded chat', async () => {
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository snapshot stale');
  assert.equal(await page.locator('.ai-refresh').innerText(), 'Re-analyze branch');
  assert((await page.locator('.ai-visible-state').innerText()).includes('new-cur'));
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
 });
 await start('missing');
 await check('failed analysis offers retry, not a normal missing-analysis warning', async () => {
  analysisFailure = { detail: 'Synthetic safe backend failure', code: 'baton_backend_failure' };
  await page.locator('.ai-refresh').click(); await loaded();
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Analysis failed');
  assert.equal(await page.locator('.ai-analysis-status').getAttribute('role'), 'alert');
  assert.equal(await page.locator('.ai-refresh').innerText(), 'Retry analysis');
  assert(!(await page.locator('.ai-analysis-status').innerText()).includes('Synthetic'));
  await page.getByRole('button', {name:'New chat',exact:true}).click();
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Analysis failed', 'New chat must not erase a repository failure');
 });
 for (const [status, code, title] of [[401,'github_authentication_failure','GitHub authentication failed'],[403,'github_permission_failure','GitHub denied the request'],[404,'github_not_found','Repository or branch not found'],[429,'github_rate_limit','GitHub API limit reached'],[502,'github_network_failure','Could not reach the repository service']]) {
  await start({status,code});
  await check('HTTP ' + status + ' category is safe and chat remains disabled', async () => {
   assert((await page.locator('.ai-analysis-status').innerText()).includes(title));
   assert(await page.getByLabel('Ask about the connected repository').isDisabled());
   assert(!(await page.locator('.ai-analysis-status').innerText()).includes('Synthetic'));
  });
 }
 await start({status:429, code:'github_rate_limit', rate_limit_kind:'primary', rate_limit:{limit:60,remaining:0,used:60,reset_at:Math.floor(Date.now()/1000)+120}});
 await check('primary rate limit shows remaining/reset and disables all analysis retries', async () => {
  const text = await page.locator('.ai-analysis-status').innerText();
  assert(text.includes('Requests remaining: 0') && text.includes('Reset:'));
  assert(await page.locator('.ai-refresh').isDisabled());
  const retryButtons = page.getByRole('button', {name:'Retry analysis',exact:true});
  for (const button of await retryButtons.all()) assert(await button.isDisabled());
  const before = analysisCount; await page.locator('.ai-refresh').evaluate(button => button.click());
  assert.equal(analysisCount, before);
 });
 await start({status:429, code:'github_rate_limit', rate_limit_kind:'secondary', retry_after:1, rate_limit:{limit:5000,remaining:4999}});
 await check('secondary backoff expires without an automatic analysis retry', async () => {
  assert((await page.locator('.ai-analysis-status').innerText()).includes('secondary limit'));
  assert(await page.locator('.ai-refresh').isDisabled());
  const before = analysisCount; await page.locator('.ai-refresh:not(:disabled)').waitFor();
  assert.equal(analysisCount, before);
 });
 await start('ready');
 await check('opening chat and Context Builder never triggers analysis', async () => {
  const before = analysisCount;
  await page.getByRole('button',{name:'Context Builder',exact:true}).click();
  await page.getByRole('button',{name:'AI workspace',exact:true}).click(); await loaded();
  assert.equal(analysisCount, before);
 });
 await check('connected repository accepts a token again and keeps it out of storage', async () => {
  await page.getByRole('button',{name:'Repository',exact:true}).click();
  await page.getByLabel('GitHub token for connected repository').fill('audit-token-canary');
  await page.getByRole('button',{name:'Check GitHub access',exact:true}).click();
  await page.getByText(/GitHub accepted the token/).waitFor();
  assert(!(await page.evaluate(() => JSON.stringify(localStorage) + JSON.stringify(sessionStorage))).includes('audit-token-canary'));
 });
 await start('network'); await check('browser network failure is distinguished', async () => {
  assert((await page.locator('.ai-analysis-status').innerText()).includes('Could not reach the repository service'));
 });
 await start({status:504,code:'baton_backend_failure'}); await check('timeout has a distinct actionable error', async () => { assert((await page.locator('.ai-analysis-status').innerText()).includes('Request timed out')); });
 await start('invalid'); await check('mismatched branch identity cannot be grounded', async () => {
  assert((await page.locator('.ai-analysis-status').innerText()).includes('Analysis needs to be rebuilt'));
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
 });
 await start('empty'); await check('empty repository uses neutral empty-state presentation', async () => {
  assert((await page.locator('.ai-analysis-status').innerText()).includes('No repository files to analyze'));
  assert.equal(await page.locator('.ai-analysis-status').getAttribute('role'), 'status');
 });
 await start('limited'); await check('16 omitted files remain an explicit warning', async () => {
  assert(await page.getByText('Analysis completed with limited coverage', { exact: true }).isVisible());
  assert((await page.locator('.baton-status-warning').innerText()).includes('16 source files'));
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository grounded');
 });
 await start('spec'); await check('specification evidence does not imply implementation', async () => {
  assert(await page.getByText('Documentation and specifications found', { exact: true }).isVisible());
 });
 await start('config'); await check('provider configuration is separate from snapshot readiness', async () => {
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository grounded');
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
  assert(await page.getByRole('button', { name: 'Generate artifact', exact: true }).isEnabled());
 });
 await start('ready');
 await check('late branch inspection cannot replace the current branch', async () => {
  delayedBranch = 'missing'; await page.getByLabel('Current repository branch').selectOption('missing');
  await page.getByText('Checking branch', { exact: true }).first().waitFor();
  await page.getByLabel('Current repository branch').selectOption('main'); await loaded();
  if (releaseBranch) releaseBranch(); delayedBranch = '';
  await page.getByText('Repository grounded', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('Current repository branch').inputValue(), 'main');
 });
 await start('missing');
 await check('late analysis completion cannot activate another branch', async () => {
  analysisDelay = 600;
  const response = page.waitForResponse(result => result.url().includes('/api/v1/analysis/'));
  await page.locator('.ai-refresh').click();
  await page.getByText('Analyzing repository', {exact:true}).waitFor();
  await page.getByLabel('Current repository branch').selectOption('missing');
  await response; await loaded(); analysisDelay = 0;
  assert.equal(await page.getByLabel('Current repository branch').inputValue(), 'missing');
  assert.equal(await page.locator('.ai-grounding').innerText(), 'Repository connected');
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
 });
 await check('repository switch clears active intelligence and persisted identity', async () => {
  await page.locator('#sidebar-change-repository-btn').click();
  await page.getByRole('heading', { name: 'Repository', exact: true }).waitFor();
  await page.getByRole('button', { name: 'AI workspace', exact: true }).click();
  assert.equal(await page.locator('.ai-grounding').innerText(), 'No repository connected');
  assert(await page.getByLabel('Ask about the connected repository').isDisabled());
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('baton-workspace-state')));
  assert.equal(stored.repo, null);
  assert(!('githubToken' in stored) && !('batonAccessKey' in stored));
 });
 await start('missing', 'missing'); await page.setViewportSize({ width: 390, height: 844 });
 await page.getByRole('button', { name: 'Hide evidence panel', exact: true }).click();
 await check('mobile missing-analysis presentation has no horizontal overflow', async () => assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)));
 await page.screenshot({ path: '.test-output/analysis-required-mobile.png', fullPage: true, animations: 'disabled' });
 assert.equal(failures.length, 0, failures.join('\n'));
 await browser.close(); console.log(`Repository state UI: ${checks.length} checks passed.\n` + checks.join('\n'));
})().catch(async error => { if (page) await page.screenshot({path:'.test-output/repository-states-failure.png',fullPage:true}); console.error(error); if(browser) await browser.close(); process.exitCode=1; });
