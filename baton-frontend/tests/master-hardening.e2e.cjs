// Browser fixture acceptance. Does not claim a real Gemini response or billing usage.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { chromium } = require(process.env.BATON_PLAYWRIGHT_PATH || 'playwright');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../.test-output/workspace-fixtures.json'), 'utf8'));
const calls = [], checks = []; let browser, mode = 'normal';
const usage = extra => ({ github_requests: 0, github_downloads: 0, cache_hits: 0, snapshot_hits: 0, ai_requests: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, thinking_tokens: 0, provider_latency_ms: 0, latency_ms: 1, quota: {}, ...extra });
(async () => {
 browser = await chromium.launch({ executablePath: process.env.BATON_BROWSER_PATH, headless: true });
 const context = await browser.newContext({viewport:{width:1440,height:900}}), page = await context.newPage(); const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route(/\/api\/(?:v1\/|health)/, async route => {
  const req=route.request(), p=new URL(req.url()).pathname, body=req.method()==='POST'?req.postDataJSON():{};
  calls.push({path:p,body}); if(p.endsWith('/provider/validate'))assert(!req.postData()); let result={status:'ok'}, stats=usage({}), status=200;
  if(p.endsWith('/validate-repository')) {result={owner:'example',repository:'project',default_branch:'main',accessible:true,authenticated:true,token_source:'request'};stats=usage({github_requests:4,quota:{limit:5000,remaining:4996,used:4}});}
  else if(p.endsWith('/provider/validate')) {if(req.headers()['x-gemini-key']==='synthetic-invalid-ai'){status=401;result={code:'ai_key_invalid',detail:'Gemini API key was rejected.'};}else result={name:'gemini',configured:true,model:req.headers()['x-gemini-model'],key_accepted:true,model_validation:'VERIFIED',generation_validation:'UNVERIFIED',state:'AI_READY'};stats=usage({ai_validation_requests:1});}
  else if(p.endsWith('/branches')) {result={branches:[{name:'main',sha:fixture.project.identity.commit},{name:'feature/ask-book',sha:fixture.feature.identity.commit}]};stats=usage({github_requests:1});}
  else if(p.endsWith('/inspect')) {if(mode==='unreachable'){await route.abort();return;}result=body.branch==='feature/ask-book'?fixture.feature:fixture.project; stats=usage({snapshot_hits:1,cache_hits:1});}
  else if(p.includes('/analysis/')) {status=500;result={code:mode==='github-network'?'github_network_failure':'baton_backend_failure',detail:'Safe failure'};}
  else if(p.endsWith('/chat')) {
   const captured=mode; await new Promise(resolve=>setTimeout(resolve,captured==='stop'?1500:250));
   if(captured==='timeout') {status=504;result={code:'ai_provider_timeout',detail:'AI provider timed out. Retry the request.'};stats=usage({ai_requests:1,input_tokens:null,output_tokens:null,total_tokens:null,thinking_tokens:null,provider_latency_ms:250});}
   else {result={...fixture.chat,conversation_id:body.conversation_id||fixture.chat.conversation_id,revision:(body.revision||0)+1}; stats=usage({ai_requests:1,input_tokens:captured==='unknown'?null:101,output_tokens:captured==='unknown'?null:9,total_tokens:captured==='unknown'?null:115,thinking_tokens:captured==='unknown'?null:5,provider_latency_ms:250,snapshot_hits:1,cache_hits:1});}
  } else if(p.endsWith('/artifacts')) result=fixture.artifact;
  else if(p.endsWith('/source')) result={path:body.path,content:'export function askBook() {}',identity:{commit:body.commit},start_line:1,end_line:1,partial:false};
  else if(p.endsWith('/tree')) result={items:[]};
  try {await route.fulfill({status,json:result,headers:{'X-Baton-Usage':JSON.stringify(stats),'Access-Control-Expose-Headers':'X-Baton-Usage'}});} catch { /* Browser explicitly abandoned the fixture response. */ }
 });

 await page.addInitScript(()=>localStorage.setItem('baton-workspace-state',JSON.stringify({repo:{owner:'example',repository:'project',default_branch:'main'},selectedBranch:'main',selectedFolder:'',members:[]})));
 await page.goto(process.env.BATON_PREVIEW_URL||'http://127.0.0.1:5181/');
 await page.getByRole('button',{name:/Enter Mission Control/}).first().click();
 assert(await page.getByRole('button',{name:'Validate repository access',exact:true}).isDisabled());
 await page.getByLabel('GitHub token for connected repository').fill('synthetic-user-github');
 await page.getByRole('button',{name:'Validate repository access',exact:true}).click();
 await page.getByRole('button',{name:'Repository',exact:true}).click();
 await page.getByLabel('Gemini API key',{exact:true}).fill('synthetic-invalid-ai');
 await page.getByLabel('Gemini model',{exact:true}).fill('fixture-model');
 await page.getByRole('button',{name:'Validate Gemini',exact:true}).click();
 await page.getByText('Gemini API key rejected',{exact:true}).waitFor();
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();
 assert(await page.getByLabel('Ask about the connected repository').isDisabled());
 checks.push('Invalid user AI key is distinct from GitHub/backend errors and disables chat');
 await page.getByRole('button',{name:'Repository',exact:true}).click();
 await page.getByLabel('Gemini API key',{exact:true}).fill('synthetic-valid-ai');
 await page.getByRole('button',{name:'Validate Gemini',exact:true}).click();
 await page.getByText('AI ready · fixture-model',{exact:true}).waitFor();
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();
 const composer=page.getByLabel('Ask about the connected repository');await composer.fill('What is the API?');await page.getByRole('button',{name:'Send repository question',exact:true}).click();await page.locator('.ai-assistant-message').waitFor();
 await page.getByRole('button',{name:'Repository',exact:true}).click();
 await page.getByRole('button',{name:'Clear Gemini key',exact:true}).click();
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();
 assert(await composer.isDisabled());assert.equal(await page.locator('.ai-assistant-message').count(),0);
 checks.push('Validated user key enables chat; clearing it invalidates history and prevents server fallback');
 mode='unreachable';await page.getByLabel('Current repository branch').selectOption('feature/ask-book');
 await page.getByText("Can't reach Baton right now",{exact:true}).first().waitFor();assert((await page.locator('h1').innerText()).includes('service unavailable'));
 await page.getByRole('button',{name:'Overview',exact:true}).click();await page.getByRole('heading',{name:"Can't reach Baton right now",exact:true}).waitFor();await page.getByText('UNREACHABLE',{exact:true}).waitFor();assert.equal(await page.getByText('CONNECTED',{exact:true}).count(),0);await page.getByRole('button',{name:'AI workspace',exact:true}).click();checks.push('Fetch rejection clearly separates remembered repository/branch from unavailable service in Ask Baton and Overview');
 mode='backend500';await page.locator('.ai-refresh').click();await page.getByText('Baton encountered a server error',{exact:true}).first().waitFor();
 mode='github-network';await page.locator('.ai-refresh').click();await page.getByText('GitHub is temporarily unreachable',{exact:true}).first().waitFor();
 checks.push('Backend 5xx and backend-to-GitHub network failure receive different classifications');
 const saved=JSON.stringify(await page.evaluate(()=>({...localStorage,...sessionStorage})));assert(!saved.includes('synthetic-valid-ai')&&!saved.includes('synthetic-user-github')&&!saved.includes('synthetic-invalid-ai'));assert.deepEqual(errors,[]);
 checks.push('User GitHub/Gemini credentials absent from browser persistence');
 console.log(JSON.stringify({status:'passed',checks},null,2));
})().catch(e=>{console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close()});
