// Opt-in assembled runtime: browser -> real FastAPI -> real GitHub -> MOCKED Gemini wire.
// Start: python -B -m uvicorn tests.phase3_runtime:app --host 127.0.0.1 --port 8013
const assert = require('node:assert/strict'), {execFileSync}=require('node:child_process'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.BATON_PLAYWRIGHT_PATH||'playwright');
let browser, token=''; const measurements=[],checks=[];
(async()=>{
 const credential=execFileSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\n\n',encoding:'utf8',stdio:['pipe','pipe','pipe'],env:{...process.env,GIT_TERMINAL_PROMPT:'0',GCM_INTERACTIVE:'Never'}});
 token=credential.split(/\r?\n/).find(line=>line.startsWith('password='))?.slice(9)||'';assert(token);
 browser=await chromium.launch({executablePath:process.env.BATON_BROWSER_PATH,headless:true});const page=await browser.newPage({viewport:{width:1440,height:900}});
 const jobs=[], sent=[];
 page.on('request',req=>{if(new URL(req.url()).pathname.endsWith('/chat')){const body=req.postDataJSON();sent.push({hasId:!!body.conversation_id,revision:body.revision,commit:body.commit});}});
 page.on('response',response=>{if(new URL(response.url()).pathname.startsWith('/api/v1/'))jobs.push((async()=>{const header=await response.headerValue('x-baton-usage');measurements.push({operation:new URL(response.url()).pathname,status:response.status(),usage:header?JSON.parse(header):null});})());});
 await page.goto(process.env.BATON_PREVIEW_URL||'http://127.0.0.1:5184/');await page.getByRole('button',{name:/Enter Mission Control/}).first().click();
 await page.getByRole('button',{name:'Open workspace settings'}).click();await page.getByLabel('Baton access key').fill('synthetic-wire-operator-key');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Repository',exact:true}).click();await page.getByPlaceholder('https://github.com/owner/repository').fill('https://github.com/octocat/Hello-World');await page.getByLabel('Fine-grained GitHub token').fill(token);await page.getByRole('button',{name:'CONNECT REPOSITORY',exact:true}).click();
 await page.getByLabel('GitHub token for connected repository').waitFor();await page.getByRole('button',{name:'AI workspace',exact:true}).click();await page.locator('.ai-refresh:not(:disabled)').waitFor({timeout:60000});
 const started=Date.now();await page.locator('.ai-refresh').click();await page.waitForFunction(()=>document.querySelector('.ai-grounding')?.textContent==='Repository grounded',null,{timeout:120000});
 const analysisMs=Date.now()-started;await page.locator('.ai-refresh:not(:disabled)').waitFor();checks.push('Real authenticated public GitHub preflight, explicit collection and exact-commit snapshot');
 await Promise.all(jobs);const before=measurements.filter(m=>m.operation.includes('/analysis/')||m.operation.endsWith('/inspect')).length;
 await page.getByRole('button',{name:'New chat',exact:true}).click();await Promise.all(jobs);assert.equal(measurements.filter(m=>m.operation.includes('/analysis/')||m.operation.endsWith('/inspect')).length,before);
 const composer=page.getByLabel('Ask about the connected repository');await composer.fill('What is this project?');await page.getByRole('button',{name:'Send repository question',exact:true}).click();await page.locator('.ai-assistant-message').waitFor();
 await composer.fill('Explain that repository evidence');await page.getByRole('button',{name:'Send repository question',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.ai-assistant-message').length===2);await Promise.all(jobs);
 assert.equal(sent[0].hasId,false);assert.equal(sent[1].hasId,true);assert.equal(sent[1].revision,1);assert.equal(sent[0].commit,sent[1].commit);
 const chats=measurements.filter(m=>m.operation.endsWith('/chat'));assert.equal(chats.length,2);assert(chats.every(m=>m.status===200&&m.usage.ai_requests===1&&m.usage.github_requests===0&&m.usage.snapshot_hits===1));
 checks.push('Real backend creates/reuses conversation ID and revision; wire Gemini validates evidence; each chat has zero GitHub HTTP calls and zero collection');
 await page.locator('.ai-citations summary').first().click();
 const pinned=page.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/source'));
 await page.locator('.ai-citations .ai-file-link').first().click();
 const source=await (await pinned).json();assert.equal(source.identity.commit,sent[0].commit);assert(source.content);
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();assert.equal(await page.locator('.ai-assistant-message').count(),2);
 await page.getByRole('button',{name:'Generate artifact',exact:true}).click();await page.getByRole('dialog').waitFor();await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Context Builder',exact:true}).click();await page.getByRole('button',{name:'GENERATE CONTEXT',exact:true}).click();await page.getByRole('button',{name:'COPY',exact:true}).waitFor();
 await page.getByRole('button',{name:'Usage Center',exact:true}).click();await page.getByRole('region',{name:'Current conversation'}).waitFor();await Promise.all(jobs);
 assert(measurements.filter(m=>m.operation.endsWith('/artifacts')).every(m=>m.usage.ai_requests===0));assert.equal(measurements.filter(m=>m.operation.includes('/analysis/')).length,1);
 assert.equal(measurements.filter(m=>m.operation.endsWith('/source')).length,1,'One citation click must fetch one pinned source');
 checks.push('Pinned cited source, deterministic artifact integrity, Context Builder and Usage Center reuse the snapshot');
 await page.getByRole('button',{name:'AI workspace',exact:true}).click();const branch=page.getByLabel('Current repository branch');const alternatives=await branch.locator('option').evaluateAll(options=>options.map(o=>o.value));const current=await branch.inputValue();const other=alternatives.find(value=>value&&value!==current);
 if(other){await branch.selectOption(other);await page.locator('.ai-refresh:not(:disabled)').waitFor({timeout:60000});assert(await composer.isDisabled());assert.equal(await page.locator('.ai-assistant-message').count(),0);checks.push('Actual branch switch blocks missing snapshot and invalidates conversation');}
 await page.getByRole('button',{name:'Change repository',exact:true}).click();await page.getByLabel('Fine-grained GitHub token').waitFor();assert.equal(await page.locator('.ai-assistant-message').count(),0);assert(!await page.evaluate(()=>JSON.stringify({...localStorage}).includes('synthetic-wire-operator-key')));
 checks.push('Repository change removes old state; credentials absent from browser persistence');
 const report={status:'passed',liveGemini:false,provider:'MOCKED Gemini HTTP transport',fineGrainedCredential:token.startsWith('github_pat_'),commit:sent[0].commit,analysisMs,checks,measurements};
 fs.writeFileSync(path.join(__dirname,'../.test-output/phase3-live-result.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({...report,measurements:measurements.filter(m=>/\/(repository|chat|source|artifacts|context)$/.test(m.operation))},null,2));
})().catch(error=>{console.error(String(error.message||error).split(token||'\0').join('[REDACTED]'));process.exitCode=1;}).finally(async()=>{await browser?.close();token='';});
