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
  calls.push({path:p,body}); let result={status:'ok'}, stats=usage({}), status=200;
  if(p.endsWith('/validate-repository')) {result={owner:'example',repository:'project',default_branch:'main',accessible:true,authenticated:true,token_source:'request'};stats=usage({github_requests:4,quota:{limit:5000,remaining:4996,used:4}});}
  else if(p.endsWith('/branches')) {result={branches:[{name:'main',sha:fixture.project.identity.commit},{name:'feature/ask-book',sha:fixture.feature.identity.commit}]};stats=usage({github_requests:1});}
  else if(p.endsWith('/inspect')) {result=body.branch==='feature/ask-book'?fixture.feature:fixture.project; stats=usage({snapshot_hits:1,cache_hits:1});}
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
 await page.getByLabel('GitHub token for connected repository').fill('fixture-browser-credential');
 await page.getByRole('button',{name:'Validate repository access',exact:true}).click();
 const composer=page.getByLabel('Ask about the connected repository'); await composer.fill('What is the Ask Book API?');
 await page.locator('.ai-composer').evaluate(form=>{form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));});
 await page.locator('.ai-assistant-message').waitFor();
 assert.equal(calls.filter(c=>c.path.endsWith('/chat')).length,1);
 const first=calls.filter(c=>c.path.endsWith('/chat'))[0].body; assert.equal(first.conversation_id,undefined);
 await composer.fill('Explain that API'); await page.getByRole('button',{name:'Send repository question',exact:true}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.ai-assistant-message').length===2);
 const second=calls.filter(c=>c.path.endsWith('/chat'))[1].body;assert.equal(second.conversation_id,fixture.chat.conversation_id);assert.equal(second.revision,1);
 assert(!calls.some(c=>c.path.includes('/analysis/')));checks.push('Immediate duplicate send creates one request; follow-up sends scoped ID and revision without analysis');
 await page.getByRole('button',{name:'Usage Center',exact:true}).click();
 const current=page.getByRole('region',{name:'Current conversation'}), session=page.getByRole('region',{name:'Current Baton session'});
 const count=async(region,label)=>region.locator('div').filter({has:page.locator('dt').filter({hasText:new RegExp('^'+label+'$')})}).locator('dd').textContent();
 assert.equal(await count(current,'AI requests'),'2');assert.equal(await count(current,'Input tokens'),'202');assert.equal(await count(current,'Total tokens'),'230');assert.equal(await count(session,'AI requests'),'2');
 checks.push('Usage Center shows exact fixture-provider conversation/session counts and distinct GitHub quota');
 await page.getByRole('button',{name:'AI workspace',exact:true}).click(); await composer.waitFor();
 const before=calls.filter(c=>c.path.endsWith('/inspect')||c.path.includes('/analysis/')).length;
 await page.getByRole('button',{name:'New chat',exact:true}).click();assert(await composer.evaluate(el=>el===document.activeElement));
 await page.getByRole('button',{name:'Usage Center',exact:true}).click();
 assert.equal(await count(current,'AI requests'),'0'); assert.equal(await count(session,'AI requests'),'2');
 assert.equal(calls.filter(c=>c.path.endsWith('/inspect')||c.path.includes('/analysis/')).length,before);
 checks.push('New Chat preserves snapshot/session totals, resets conversation usage and causes zero inspect/analysis calls');
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();mode='stop';await composer.fill('Explain architecture');await page.getByRole('button',{name:'Send repository question',exact:true}).click();
 await page.getByRole('button',{name:'Stop waiting for the response'}).click();
 await page.getByText(/Stopped waiting\. Remote work may still finish/).waitFor();
 await page.waitForTimeout(200); assert.equal(calls.filter(call=>call.path.endsWith('/chat')).length,3,'Stop must not submit the restored draft');
 assert.equal(await composer.inputValue(),'Explain architecture'); assert.equal(await page.getByRole('button',{name:'Stop waiting for the response'}).count(),0);
 await page.getByRole('button',{name:'Usage Center',exact:true}).click();assert.equal(await count(current,'Abandoned operations'),'1');assert.equal(await count(current,'Total tokens'),'UNKNOWN');
 checks.push('Stop clears waiting/draft safely; abandoned usage is UNKNOWN and remote cancellation is not claimed');
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();await page.getByRole('button',{name:'New chat',exact:true}).click();mode='timeout';await composer.fill('Explain the repository');await page.getByRole('button',{name:'Send repository question',exact:true}).click();await page.getByText('Gemini response timed out',{exact:true}).waitFor();
 mode='unknown';await page.getByRole('button',{name:'New chat',exact:true}).click();await composer.fill('Explain the repository');await page.getByRole('button',{name:'Send repository question',exact:true}).click();await page.locator('.ai-assistant-message').waitFor();
 await page.getByRole('button',{name:'Usage Center',exact:true}).click();assert.equal(await count(current,'AI requests'),'1');assert.equal(await count(current,'Total tokens'),'UNKNOWN');
 checks.push('Provider timeout has useful classification; absent token metadata remains UNKNOWN');
 assert.deepEqual(errors,[]);assert(!JSON.stringify(await page.evaluate(()=>({...localStorage}))).includes('fixture-browser-credential'));
 console.log(JSON.stringify({status:'passed',checks},null,2));
})().catch(e=>{console.error(e);process.exitCode=1}).finally(async()=>{await browser?.close()});
