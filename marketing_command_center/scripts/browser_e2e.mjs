/** Run the primary user journey (service, write, check, review, record) in a real local Chrome instance through CDP. */
import{spawn}from"node:child_process";
import{mkdtemp,rm}from"node:fs/promises";
import net from"node:net";
import os from"node:os";
import path from"node:path";
import assert from"node:assert/strict";
import{fileURLToPath}from"node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const chrome="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const freePort=()=>new Promise((resolve,reject)=>{const server=net.createServer();server.once("error",reject);server.listen(0,"127.0.0.1",()=>{const{port}=server.address();server.close(()=>resolve(port))})});

async function waitForJson(url,attempts=60){for(let i=0;i<attempts;i++){try{const response=await fetch(url);if(response.ok)return await response.json()}catch{}await wait(100)}throw new Error(`endpoint not ready: ${url}`)} // qa:allow CWE-390 - polling retry: failures are expected until the server is ready; the loop throws after the attempts

async function connectCdp(url){
  const socket=new WebSocket(url),pending=new Map();let id=0;const consoleErrors=[];
  await new Promise((resolve,reject)=>{socket.addEventListener("open",resolve,{once:true});socket.addEventListener("error",reject,{once:true})});
  socket.addEventListener("message",event=>{const message=JSON.parse(event.data);if(message.id&&pending.has(message.id)){const{resolve,reject}=pending.get(message.id);pending.delete(message.id);message.error?reject(new Error(message.error.message)):resolve(message.result);return}if(message.method==="Runtime.exceptionThrown")consoleErrors.push(message.params.exceptionDetails.text);if(message.method==="Log.entryAdded"&&message.params.entry.level==="error")consoleErrors.push(`${message.params.entry.url||"unknown"} ${message.params.entry.text}`)});
  const send=(method,params={})=>new Promise((resolve,reject)=>{const current=++id;pending.set(current,{resolve,reject});socket.send(JSON.stringify({id:current,method,params}))});
  return{socket,send,consoleErrors};
}

const GOOD="매주 월요일마다 광고 성과를 엑셀로 옮기느라 한 시간씩 쓰시나요?\\nHermes는 채널별 숫자를 한 화면에 모아 줍니다. 직접 써 보고 불편한 점을 댓글로 알려 주세요.";
const BAD="Hermes는 100% 무조건 성공을 보장합니다. 역대급 대박 서비스!!! 지금 써 보세요.";
const REVIEW={status:"reviewed",review:{score:7,hook:"질문으로 시작해 좋습니다.",persuasion:"이득이 더 구체적이면 좋습니다.",risks:["수치 근거 없음"],rewrite:"AI 개선안 본문입니다. Hermes를 써 보고 댓글로 알려 주세요."},model:"gpt-6-luna",usage:{input_tokens:80,output_tokens:120,total_tokens:200}};

async function main(){
  const appPort=await freePort(),debugPort=await freePort(),profile=await mkdtemp(path.join(os.tmpdir(),"hermes-marketing-e2e-"));
  const server=spawn(process.env.PYTHON||"python",["serve.py","--host","127.0.0.1","--port",String(appPort)],{cwd:root,stdio:"ignore",windowsHide:true,env:{...process.env,DISCORD_WEBHOOK_URL:"your_discord_webhook"}});
  const browser=spawn(chrome,["--headless","--no-sandbox","--disable-gpu","--disable-software-rasterizer","--disable-dev-shm-usage",`--remote-debugging-port=${debugPort}`,`--user-data-dir=${profile}`,"about:blank"],{stdio:"ignore",windowsHide:true});
  let cdp;
  try{
    await waitForJson(`http://127.0.0.1:${appPort}/api/health`);
    const targets=await waitForJson(`http://127.0.0.1:${debugPort}/json/list`),target=targets.find(item=>item.type==="page");if(!target)throw new Error("Chrome page target missing");
    cdp=await connectCdp(target.webSocketDebuggerUrl);await cdp.send("Runtime.enable");await cdp.send("Log.enable");await cdp.send("Page.enable");await cdp.send("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:1,mobile:true});await cdp.send("Page.navigate",{url:`http://127.0.0.1:${appPort}/`});
    const run=async expression=>{const result=await cdp.send("Runtime.evaluate",{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw new Error(`${result.exceptionDetails.text} ${result.exceptionDetails.exception?.description||""}`);return result.result.value};
    for(let i=0;i<60;i++){if(await run("document.readyState==='complete'&&document.querySelectorAll('#channelSelect option').length>=5"))break;if(i===59)throw new Error("application did not render");await wait(100)}
    const setup=`window.confirm=()=>true;const fire=(element,type='input')=>element.dispatchEvent(new Event(type,{bubbles:true}));const stub=(body,status=200)=>{window.fetch=()=>Promise.resolve(new Response(JSON.stringify(body),{status}))};const wait=ms=>new Promise(r=>setTimeout(r,ms));`;

    // 0c. The page reports its own load problems, and one button restores the example posts over any saved state.
    assert.equal(await run("document.body.dataset.ready==='1'&&bootProblem.hidden"),true,"healthy page must be marked ready with no problem banner");
    const banner=await run(`(()=>{window.dispatchEvent(new ErrorEvent('error',{message:'simulated load failure'}));return{hidden:bootProblem.hidden,text:bootProblem.textContent}})()`);
    assert.equal(banner.hidden,false);assert.match(banner.text,/simulated load failure/);
    await run(`localStorage.setItem('hermes-marketing-simple-v1',JSON.stringify({services:[{id:'z',name:'다른 서비스',description:'d'}],activeId:'z',channel:'x',topic:'',drafts:{x:'내가 쓰던 글'},posts:[]}))`);
    await cdp.send("Page.reload",{ignoreCache:true});await wait(400);
    const loaded=await run(`(async()=>{window.confirm=()=>true;const before=postText.value;loadStarterButton.click();const out={before,service:serviceName.value,channel:channelSelect.value,text:postText.value,verdict:verdict.dataset.verdict};channelSelect.value='instagram';channelSelect.dispatchEvent(new Event('change',{bubbles:true}));out.instagram=postText.value;return out})()`);
    assert.equal(loaded.before,"내가 쓰던 글");assert.equal(loaded.service,"마사지 연습");assert.match(loaded.text,/비용이 부담됐다면/);assert.equal(loaded.verdict,"ready");assert.match(loaded.instagram,/#마사지연습/);

    // 0b. A saved state from an older build keeps the user's own text and gains posts for channels it lacked.
    await run(`localStorage.setItem('hermes-marketing-simple-v1',JSON.stringify({services:[{id:'a',name:'마사지 연습',description:'d'}],activeId:'a',channel:'threads',topic:'',drafts:{threads:'내 글 유지',community:''},posts:[]}))`);
    await cdp.send("Page.reload",{ignoreCache:true});await wait(400);
    const merged=await run(`(()=>{const out={threads:postText.value};for(const channel of ['community','x','instagram']){channelSelect.value=channel;channelSelect.dispatchEvent(new Event('change',{bubbles:true}));out[channel]=postText.value}return out})()`);
    assert.equal(merged.threads,"내 글 유지");assert.equal(merged.community,"","a draft the user cleared must stay cleared");assert.match(merged.x,/비용이 부담됐다면/);assert.match(merged.instagram,/#마사지연습/);

    // 0a. A browser that already saved an empty state from an earlier visit still gets the starter content.
    await run(`localStorage.setItem('hermes-marketing-simple-v1',JSON.stringify({services:[],activeId:'',channel:'threads',topic:'',text:'',posts:[]}))`);
    await cdp.send("Page.reload",{ignoreCache:true});await wait(400);
    assert.equal(await run("serviceName.value"),"마사지 연습","empty saved state must not hide the starter content");

    // 0. First run opens with the massage-practice service and a ready post per channel.
    const first=await run(`(async()=>{${setup}const out={service:serviceName.value,threads:postText.value,verdict:verdict.dataset.verdict};channelSelect.value='community';fire(channelSelect,'change');out.community=postText.value;out.communityVerdict=verdict.dataset.verdict;channelSelect.value='threads';fire(channelSelect,'change');return out})()`);
    assert.equal(first.service,"마사지 연습");assert.match(first.threads,/비용이 부담됐다면/);assert.match(first.community,/\[미리 알려 드릴 점\]/);
    assert.equal(first.verdict,"ready");assert.equal(first.communityVerdict,"ready");
    const navigation=await run(`(()=>{const before={today:!document.querySelector('[data-view="today"]').hidden,content:!document.querySelector('[data-view="content"]').hidden};document.querySelector('[data-view-target="content"]').click();return{before,after:{today:!document.querySelector('[data-view="today"]').hidden,content:!document.querySelector('[data-view="content"]').hidden},current:document.querySelector('[data-view-target="content"]').getAttribute('aria-current')}})()`);
    assert.deepEqual(navigation.before,{today:true,content:false});assert.deepEqual(navigation.after,{today:false,content:true});assert.equal(navigation.current,"page");
    const everyChannel=await run(`(()=>{const out={};for(const option of channelSelect.options){channelSelect.value=option.value;channelSelect.dispatchEvent(new Event('change',{bubbles:true}));out[option.value]=[verdict.dataset.verdict,postText.value.length]}channelSelect.value='threads';channelSelect.dispatchEvent(new Event('change',{bubbles:true}));return out})()`);
    assert.equal(Object.keys(everyChannel).length,6);
    for(const[channel,[state,length]]of Object.entries(everyChannel))assert.ok(state==="ready"&&length>0,`${channel}: ${state}, ${length} chars`);

    // 1. Save a second service, write a good post, see it pass the rules.
    const ready=await run(`(async()=>{${setup}newServiceButton.click();serviceName.value='Hermes';serviceDesc.value='광고 성과를 한 화면에 모아 주는 1인용 도구';saveServiceButton.click();channelSelect.value='threads';fire(channelSelect,'change');postText.value="${GOOD}";fire(postText);return{verdict:verdict.dataset.verdict,issues:issueList.children.length,services:serviceSelect.options.length,status:statusText.textContent}})()`);
    assert.equal(ready.verdict,"ready",JSON.stringify(ready));assert.equal(ready.services,2);

    // 2. A hyped, guarantee-style post is blocked and the offending words are named.
    const bad=await run(`(async()=>{${setup}postText.value="${BAD}";fire(postText);return{verdict:verdict.dataset.verdict,text:issueList.textContent}})()`);
    assert.equal(bad.verdict,"fix");assert.match(bad.text,/100%/);assert.match(bad.text,/역대급/);

    // 3. AI draft and review render from server-shaped replies, and every failure kind has its own copy.
    const communityBrief=await run(`(async()=>{${setup}objectiveInput.value='질문 받기';fire(objectiveInput);contentPillarInput.value='혼자 하는 마케팅';fire(contentPillarInput);communityContextInput.value='구체적인 시행착오를 선호';fire(communityContextInput);conversationQuestionInput.value='가장 오래 걸리는 일은?';fire(conversationQuestionInput);evidenceUrlInput.value='https://example.com/source';fire(evidenceUrlInput);successSignalInput.value='구체적인 답글';fire(successSignalInput);let payload;window.fetch=(url,options)=>{payload=JSON.parse(options.body);return Promise.resolve(new Response(JSON.stringify({status:'generated',text:'초안',model:'gpt-6-luna',usage:{input_tokens:1,output_tokens:1,total_tokens:2}}),{status:200}))};draftButton.click();await wait(60);return payload})()`);
    assert.equal(communityBrief.objective,"질문 받기");assert.equal(communityBrief.content_pillar,"혼자 하는 마케팅");assert.equal(communityBrief.community_context,"구체적인 시행착오를 선호");assert.equal(communityBrief.conversation_question,"가장 오래 걸리는 일은?");assert.equal(communityBrief.evidence_url,"https://example.com/source");assert.equal(communityBrief.success_signal,"구체적인 답글");
    const ai=await run(`(async()=>{${setup}stub({status:'generated',text:'AI 초안 본문입니다. Hermes를 써 보고 댓글로 알려 주세요.',model:'gpt-6-luna',usage:{input_tokens:50,output_tokens:60,total_tokens:110}});draftButton.click();await wait(80);const draft=postText.value;
      stub(${JSON.stringify(REVIEW)});reviewButton.click();await wait(80);const review=aiResult.textContent;applyRewriteButton.click();const applied=postText.value;
      const copies={};for(const kind of ['auth','rate_limit','timeout','network','provider','empty_response','not_configured']){stub({status:'error',kind},502);reviewButton.click();await wait(60);copies[kind]=statusText.textContent}
      return{draft,review,applied,copies}})()`);
    assert.match(ai.draft,/AI 초안 본문/);assert.match(ai.review,/AI 평가 7\/10/);assert.match(ai.review,/수치 근거 없음/);assert.match(ai.applied,/AI 개선안 본문/);
    const copies=Object.values(ai.copies);assert.equal(new Set(copies).size,7,JSON.stringify(ai.copies));assert.ok(copies.every(text=>text&&!text.includes("AI가 작업하는 중")));

    // 4. Recording is blocked until a human rule review is saved for the exact text.
    const record=await run(`(async()=>{${setup}Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.__copied=text}},configurable:true});postText.value="${GOOD}";fire(postText);copyButton.click();await wait(40);
      postedButton.click();const blocked=statusText.textContent;
      policyUrl.value='https://community.example/rules';policyCheckedDate.value=new Date().toISOString().slice(0,10);policyReviewer.value='테스트 검수자';policyApproved.checked=true;savePolicyReviewButton.click();
      postedButton.click();const input=document.querySelector('#historyList input[data-field=conversions]');input.value='3';fire(input);
      postText.value=postText.value+' 변경';fire(postText);postedButton.click();
      return{copied:window.__copied,blocked,rows:historyList.children.length,summary:historySummary.textContent,changed:statusText.textContent,review:policyReviewStatus.textContent}})()`);
    assert.match(record.copied,/Hermes는 채널별 숫자/);assert.match(record.blocked,/규칙 검수/);assert.equal(record.rows,1);assert.match(record.summary,/Threads/);assert.match(record.summary,/가입·문의 3/);assert.match(record.changed,/규칙 검수/);assert.match(record.review,/다시 확인/);

    // 4a. Integration readiness is explicit: missing credentials are not ready, and discontinued APIs stay unsupported.
    const readiness=await run(`(()=>({text:integrationList.textContent,items:integrationList.children.length}))()`);
    assert.equal(readiness.items,14);assert.match(readiness.text,/Threads/);assert.match(readiness.text,/Telegram/);assert.match(readiness.text,/NOT_CONFIGURED/);assert.match(readiness.text,/Discord: INVALID_CONFIG/);assert.match(readiness.text,/DISCORD_WEBHOOK_URL/);assert.ok(!readiness.text.includes("your_discord_webhook"));assert.match(readiness.text,/Naver 공유: MANUAL/);assert.match(readiness.text,/YouTube: HOLD/);assert.match(readiness.text,/Naver Blog/);assert.match(readiness.text,/UNSUPPORTED/);

    // 4b. A channel-specific HTTPS destination is stored, then copy-and-open hands off without auto-posting.
    const integration=await run(`(async()=>{${setup}let opened='';window.open=url=>{opened=url};Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.__copied=text}},configurable:true});communityUrl.value='https://community.example/write';saveCommunityButton.click();postText.value="${GOOD}";fire(postText);openCommunityButton.click();await wait(40);return{opened,copied:window.__copied,saved:JSON.parse(localStorage.getItem('hermes-marketing-simple-v1')).communityUrls.threads,status:statusText.textContent}})()`);
    assert.equal(integration.opened,"https://community.example/write");assert.equal(integration.saved,"https://community.example/write");assert.match(integration.copied,/Hermes는 채널별 숫자/);assert.match(integration.status,/커뮤니티를 열었습니다/);

    // 5. Media checklist is manual and counts progress.
    const media=await run(`(async()=>{const boxes=[...document.querySelectorAll('#mediaChecklist input')];const before=mediaResult.textContent;boxes.forEach(box=>{box.checked=true});mediaChecklist.dispatchEvent(new Event('change',{bubbles:true}));return{count:boxes.length,before,after:mediaResult.textContent}})()`);
    assert.ok(media.count>=4);assert.match(media.before,new RegExp(`0/${media.count}`));assert.match(media.after,/모든 항목/);

    // 6. Everything survives a reload; the page stays within a 390px phone width.
    await cdp.send("Page.reload",{ignoreCache:true});await wait(400);
    const after=await run(`({communityDraft:JSON.parse(localStorage.getItem("hermes-marketing-simple-v1")).drafts.community.includes("[미리 알려 드릴 점]"),service:serviceName.value,text:postText.value.slice(0,10),rows:historyList.children.length,conversions:document.querySelector('#historyList input[data-field=conversions]').value,overflow:document.documentElement.scrollWidth-window.innerWidth})`);
    assert.equal(after.service,"Hermes");assert.equal(after.communityDraft,true);assert.equal(after.rows,1);assert.equal(after.conversions,"3");assert.ok(after.text.length>0);assert.ok(after.overflow<=0,`mobile horizontal overflow: ${after.overflow}`);
    assert.deepEqual(cdp.consoleErrors,[],`browser console errors: ${cdp.consoleErrors.join(" | ")}`);
    console.log("PASS browser e2e: focused navigation, community brief payload, service, rule check, human review evidence, integration readiness, AI draft/review, error copy, copy, record, media checklist, reload, 390px, console");
  }finally{
    if(cdp?.socket)cdp.socket.close();
    browser.kill();server.kill();await wait(300);await rm(profile,{recursive:true,force:true}).catch(()=>{}); // qa:allow CWE-390 - temp browser profile cleanup after the test must not mask the test result
  }
}

main().catch(error=>{console.error(error.stack||error);process.exitCode=1});
