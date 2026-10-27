import{CHANNELS,MEDIA_CHECKLISTS,checkPost}from"./quality.js";
import{STARTER}from"./starter.js";
import{POLICY_SOURCES,evaluateExperiment,ruleReviewStatus,textHash}from"./evidence.js";

const STORAGE_KEY="hermes-marketing-simple-v1";
const $=id=>document.getElementById(id);
const ERROR_COPY={
  not_configured:"로컬 API 키 설정이 필요합니다.",
  auth:"API 키가 거부됐습니다. 키를 확인하세요.",
  rate_limit:"요청 한도를 넘었습니다. 잠시 후 다시 시도하세요.",
  timeout:"응답 시간이 초과됐습니다. 다시 시도하세요.",
  network:"OpenAI에 연결하지 못했습니다. 네트워크를 확인하세요.",
  provider:"OpenAI 서버 오류입니다. 잠시 후 다시 시도하세요.",
  empty_response:"모델이 결과를 만들지 못했습니다. 입력을 바꿔 다시 시도하세요.",
  response:"모델 응답을 읽지 못했습니다. 다시 시도하세요.",
  invalid_input:"서비스 이름·설명과 본문을 확인하세요."
};
const VERDICT_COPY={ready:"규칙 기준으로는 올려도 좋습니다",review:"다듬으면 좋아집니다",fix:"수정한 뒤 올리세요"};
function uid(){return crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random().toString(16).slice(2)}`}
let state=load();

function load(){
  const fallback={services:[],activeId:"",channel:"threads",topic:"",brief:{audience:"",benefit:"",proof:"",cta:"",objective:"도움 주기",content_pillar:"",community_context:"",conversation_question:"",evidence_url:"",success_signal:""},drafts:{},posts:[],communityUrls:{},ruleReviews:{},experiment:{id:"",variant:"none",change:""},activeView:"today"};
  let raw=null;
  try{raw=localStorage.getItem(STORAGE_KEY)}catch{} // qa:allow CWE-390 - localStorage can be blocked; raw stays null and the starter data is used
    const starter=()=>{const id=uid();return{...fallback,services:[{id,...STARTER.service}],activeId:id,channel:STARTER.channel,brief:{...STARTER.brief},drafts:{...STARTER.drafts}}};
  if(raw===null)return starter();
  try{
    const saved=JSON.parse(raw);
    if(!saved||!Array.isArray(saved.services)||!Array.isArray(saved.posts))return starter();
    const merged={...fallback,...saved,brief:{...fallback.brief,...saved.brief},communityUrls:{...fallback.communityUrls,...saved.communityUrls},ruleReviews:{...fallback.ruleReviews,...saved.ruleReviews},experiment:{...fallback.experiment,...saved.experiment}};
    if(typeof saved.text==="string"&&saved.text&&!Object.keys(merged.drafts).length)merged.drafts={[merged.channel]:saved.text};
    delete merged.text;
    if(merged.services.some(service=>service.name===STARTER.service.name))for(const[channel,text]of Object.entries(STARTER.drafts))if(!(channel in merged.drafts))merged.drafts[channel]=text;
    const untouched=!merged.services.length&&!merged.posts.length&&!Object.values(merged.drafts).some(text=>String(text).trim());
    return untouched?starter():merged;
  }catch{return starter()}
}
function save(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state))}catch{say("브라우저 저장소를 쓸 수 없어 이번 변경은 새로고침하면 사라집니다.")}}
function say(message){$("statusText").textContent=message}
function activeService(){return state.services.find(service=>service.id===state.activeId)||null}
function el(tag,text,attrs={}){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;for(const[key,value]of Object.entries(attrs))node.setAttribute(key,value);return node}

function showView(view){
  state.activeView=view;save();
  document.querySelectorAll("[data-view]").forEach(panel=>{panel.hidden=panel.dataset.view!==view});
  document.querySelectorAll("[data-view-target]").forEach(button=>{const active=button.dataset.viewTarget===view;button.classList.toggle("ghost",!active);if(active)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current")});
  renderToday();
}

function renderToday(){
  const text=state.drafts[state.channel]||"",review=state.ruleReviews[state.channel],service=activeService();
  $("todaySummary").replaceChildren(
    el("p",service?`작업 서비스: ${service.name}`:"먼저 서비스를 저장하세요."),
    el("p",text.trim()?`${CHANNELS[state.channel].label} 초안 ${text.trim().length}자 · 이어서 점검하세요.`:"아직 초안이 없습니다. 콘텐츠 작성을 시작하세요."),
    el("p",review?.approved?"현재 문안의 사람 검수 증거가 있습니다.":"게시 전 커뮤니티 규칙을 사람이 확인해야 합니다.")
  );
}

function renderServices(){
  const select=$("serviceSelect");select.replaceChildren();
  for(const service of state.services)select.append(el("option",service.name,{value:service.id}));
  if(!state.services.length)select.append(el("option","(저장된 서비스 없음)",{value:""}));
  select.value=state.activeId;
  const service=activeService();
  $("serviceName").value=service?service.name:"";
  $("serviceDesc").value=service?service.description:"";
}

function renderCheck(){
  const text=$("postText").value,service=activeService(),result=checkPost({text,channel:state.channel,serviceName:service?service.name:""});
  $("charCount").textContent=`${text.trim().length}자 · ${CHANNELS[state.channel].label} 권장 ${CHANNELS[state.channel].maxLength}자`;
  const verdict=$("verdict");
  if(!text.trim()){verdict.dataset.verdict="empty";verdict.textContent="본문을 쓰면 규칙 점검이 바로 나옵니다.";$("issueList").replaceChildren();return result}
  verdict.dataset.verdict=result.verdict;
  verdict.textContent=`${VERDICT_COPY[result.verdict]} (규칙 점검 ${result.issues.length}건)`;
  $("issueList").replaceChildren(...result.issues.map(issue=>el("li",issue.message,{"data-level":issue.level})));
  return result;
}

function renderHistory(){
  const list=$("historyList");list.replaceChildren();
  for(const post of [...state.posts].reverse()){
    const item=el("li"),meta=el("div",undefined,{class:"meta"}),nums=el("div",undefined,{class:"nums"});
    meta.append(el("span",`${post.date} · ${post.serviceName} · ${CHANNELS[post.channel]?.label||post.channel}`),(()=>{const remove=el("button","삭제",{type:"button",class:"ghost","data-remove":post.id});return remove})());
    item.append(meta,el("div",post.firstLine,{class:"hint"}));
    if(post.experimentId&&post.variant!=="none")item.append(el("div",`실험 ${post.experimentId} · ${post.variant==="baseline"?"A":"B"}${post.change?` · 변경: ${post.change}`:""}`,{class:"hint"}));
    for(const[field,label]of[["views","조회"],["reactions","반응"],["conversions","가입·문의"]]){
      const wrapper=el("label",label+" "),input=el("input",undefined,{type:"number",min:"0","data-post":post.id,"data-field":field});
      input.value=post[field];wrapper.append(input);nums.append(wrapper);
    }
    item.append(nums);list.append(item);
  }
  renderHistorySummary();
}

function renderMedia(){
  const type=$("mediaType").value,list=$("mediaChecklist");list.replaceChildren();
  MEDIA_CHECKLISTS[type].items.forEach((text,index)=>{
    const label=el("label"),box=el("input",undefined,{type:"checkbox","data-media":index});
    const item=el("li");label.append(box,el("span",text));item.append(label);list.append(item);
  });
  updateMediaResult();
}
function updateMediaResult(){
  const boxes=[...document.querySelectorAll("#mediaChecklist input")],done=boxes.filter(box=>box.checked).length;
  $("mediaResult").textContent=done===boxes.length?"모든 항목을 확인했습니다.":`${done}/${boxes.length} 확인했습니다. 남은 항목을 확인한 뒤 올리세요.`;
}

function currentFields(){
  const service=activeService();
  return service?{service:service.name,description:service.description,channel:CHANNELS[state.channel].label,...state.brief}:null;
}

function renderCommunity(){
  $("communityUrl").value=state.communityUrls[state.channel]??CHANNELS[state.channel].home;
  const review=state.ruleReviews[state.channel],source=POLICY_SOURCES[state.channel];
  $("policyUrl").value=review?.url||source?.url||"";$("policyCheckedDate").value=review?.checkedDate||"";$("policyReviewer").value=review?.reviewer||"";$("policyApproved").checked=Boolean(review?.approved);
  renderPolicyReview();
}

function renderPolicyReview(){const result=ruleReviewStatus(state.ruleReviews[state.channel],$("postText").value);$("policyReviewStatus").textContent=`${result.status}: ${result.reason}`;return result}

function renderExperiment(){
  const result=evaluateExperiment(state.posts,state.experiment.id),t=result.totals;
  $("experimentStatus").textContent=t?`${result.status} · A ${t.baseline.conversions}/${t.baseline.views}, B ${t.variant.conversions}/${t.variant.views} · ${result.message}`:`${result.status} · ${result.message}`;
  return result;
}

async function renderIntegrations(){
  const list=$("integrationList");list.replaceChildren(el("li","준비도를 확인하는 중입니다."));
  try{const response=await fetch("/api/integrations",{cache:"no-store"}),result=await response.json();if(!response.ok)throw new Error("status");list.replaceChildren(...result.integrations.map(item=>el("li",item.mode==="unsupported"?`${item.label}: UNSUPPORTED · 공식 자동 게시 경로 없음`:item.mode==="manual"?`${item.label}: MANUAL · 사용자 확인으로 공유`:item.mode==="hold"?`${item.label}: HOLD · 실행 업로더 미구현`:item.invalid?.length?`${item.label}: INVALID_CONFIG · 형식 오류 ${item.invalid.join(", ")}`:item.configured?`${item.label}: LOCAL_CONFIGURED · 계정 동의·심사·live 권한은 HOLD`:`${item.label}: NOT_CONFIGURED · 누락 ${item.missing.join(", ")}`)))}catch{list.replaceChildren(el("li","연동 계약을 읽지 못했습니다. 동기화 검사를 실행하세요."))}
}

function validCommunityUrl(value){try{const url=new URL(value);return url.protocol==="https:"?url:null}catch{return null}}

async function copyPost(){
  const text=$("postText").value;if(!text.trim()){say("복사할 본문이 없습니다.");return false}
  try{await navigator.clipboard.writeText(text);say("본문을 복사했습니다. 올릴 곳에 붙여 넣으세요.");return true}
  catch{$("postText").select();say("자동 복사에 실패했습니다. 선택된 본문을 Ctrl+C로 복사하세요.");return false}
}

async function callAi(path,payload,busyButton){
  if(!confirm("OpenAI 유료 API를 1회 호출합니다. 계속할까요?"))return null;
  busyButton.disabled=true;say("AI가 작업하는 중입니다.");
  try{
    const response=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}),result=await response.json();
    if(!response.ok||!["generated","reviewed"].includes(result.status)){say(ERROR_COPY[result.kind]||ERROR_COPY[result.status]||"요청을 처리하지 못했습니다.");return null}
    return result;
  }catch{say("서버에 연결하지 못했습니다. 실행 창이 켜져 있는지 확인하세요.");return null}
  finally{busyButton.disabled=false}
}

function showReview(result){
  const{review}=result,box=$("aiResult");box.replaceChildren();box.hidden=false;
  box.append(el("h3",`AI 평가 ${review.score}/10`),el("p",`첫 줄: ${review.hook}`),el("p",`설득력: ${review.persuasion}`));
  if(review.risks.length){box.append(el("p","고칠 점:"));const list=el("ul");review.risks.forEach(risk=>list.append(el("li",risk)));box.append(list)}
  box.append(el("p","AI 개선안:"),el("pre",review.rewrite));
  const apply=el("button","개선안을 본문에 적용",{type:"button",class:"ghost",id:"applyRewriteButton"});
  apply.addEventListener("click",()=>{$("postText").value=review.rewrite;onTextChange();say("개선안을 본문에 넣었습니다. 다시 점검해 보세요.")});
  box.append(apply);
  say(`${result.model} · 입력 ${result.usage.input_tokens} / 출력 ${result.usage.output_tokens} 토큰`);
}

function onTextChange(){state.drafts[state.channel]=$("postText").value;save();renderCheck();renderPolicyReview();renderToday()}

function bind(){
  document.querySelectorAll("[data-view-target],[data-go-view]").forEach(button=>button.addEventListener("click",()=>showView(button.dataset.viewTarget||button.dataset.goView)));
  $("serviceSelect").addEventListener("change",()=>{state.activeId=$("serviceSelect").value;save();renderServices();renderCheck()});
  $("saveServiceButton").addEventListener("click",()=>{
    const name=$("serviceName").value.trim(),description=$("serviceDesc").value.trim();
    if(!name||!description){say("서비스 이름과 설명을 모두 입력하세요.");return}
    const service=activeService();
    if(service){service.name=name;service.description=description}
    else{const created={id:uid(),name,description};state.services.push(created);state.activeId=created.id}
    save();renderServices();renderCheck();renderToday();say("서비스를 저장했습니다.");
  });
  $("newServiceButton").addEventListener("click",()=>{state.activeId="";save();renderServices();$("serviceName").focus()});
  $("deleteServiceButton").addEventListener("click",()=>{
    const service=activeService();if(!service||!confirm(`'${service.name}' 서비스를 삭제할까요? 올린 글 기록은 남습니다.`))return;
    state.services=state.services.filter(item=>item.id!==service.id);state.activeId=state.services[0]?.id||"";save();renderServices();renderCheck();
  });
  $("loadStarterButton").addEventListener("click",()=>{
    if(Object.values(state.drafts).some(text=>String(text).trim())&&!confirm("작성 중인 글이 예시 글로 바뀝니다. 계속할까요?"))return;
    let service=state.services.find(item=>item.name===STARTER.service.name);
    if(!service){service={id:uid(),...STARTER.service};state.services.push(service)}
    state.activeId=service.id;state.channel=STARTER.channel;state.brief={...state.brief,...STARTER.brief};state.drafts={...STARTER.drafts};save();
    renderServices();$("channelSelect").value=state.channel;$("postText").value=state.drafts[state.channel];for(const name of ["audience","benefit","proof","cta"])$(name+"Input").value=state.brief[name];$("aiResult").hidden=true;renderCheck();renderCommunity();renderToday();say("대상·가치·신뢰·행동이 포함된 예시 글 6개를 불러왔습니다.");
  });
  $("channelSelect").addEventListener("change",()=>{state.channel=$("channelSelect").value;$("postText").value=state.drafts[state.channel]||"";$("aiResult").hidden=true;save();renderCheck();renderCommunity();renderToday()});
  $("topicInput").addEventListener("input",()=>{state.topic=$("topicInput").value;save()});
  for(const name of ["audience","benefit","proof","cta"])$(name+"Input").addEventListener("input",()=>{state.brief[name]=$(name+"Input").value;save()});
  for(const[id,key]of[["objectiveInput","objective"],["contentPillarInput","content_pillar"],["communityContextInput","community_context"],["conversationQuestionInput","conversation_question"],["evidenceUrlInput","evidence_url"],["successSignalInput","success_signal"]])$(id).addEventListener("input",()=>{state.brief[key]=$(id).value;save()});
  $("postText").addEventListener("input",onTextChange);
  $("draftButton").addEventListener("click",async()=>{
    const fields=currentFields();if(!fields){say("먼저 서비스를 저장하세요.");return}
    const result=await callAi("/api/ai/draft",{...fields,topic:$("topicInput").value},$("draftButton"));
    if(result){$("postText").value=result.text;onTextChange();say(`초안을 넣었습니다. ${result.model} · 입력 ${result.usage.input_tokens} / 출력 ${result.usage.output_tokens} 토큰`)}
  });
  $("reviewButton").addEventListener("click",async()=>{
    const fields=currentFields();if(!fields){say("먼저 서비스를 저장하세요.");return}
    if(!$("postText").value.trim()){say("평가할 본문을 먼저 쓰세요.");return}
    const result=await callAi("/api/ai/review",{...fields,text:$("postText").value},$("reviewButton"));
    if(result)showReview(result);
  });
  $("saveCommunityButton").addEventListener("click",()=>{const url=validCommunityUrl($("communityUrl").value.trim());if(!url){say("https://로 시작하는 커뮤니티 주소를 입력하세요.");return}state.communityUrls[state.channel]=url.href;save();renderCommunity();say(`${CHANNELS[state.channel].label} 게시 주소를 이 브라우저에 저장했습니다.`)});
  $("savePolicyReviewButton").addEventListener("click",()=>{const url=validCommunityUrl($("policyUrl").value.trim()),checkedDate=$("policyCheckedDate").value,reviewer=$("policyReviewer").value.trim(),approved=$("policyApproved").checked;if(!url||!checkedDate||!reviewer||!approved){say("정책 URL·확인일·검수자·승인을 모두 입력하세요.");return}state.ruleReviews[state.channel]={url:url.href,checkedDate,reviewer,approved,textHash:textHash($("postText").value)};save();const result=renderPolicyReview();say(result.reason)});
  for(const[id,key]of[["experimentId","id"],["experimentVariant","variant"],["experimentChange","change"]])$(id).addEventListener("input",()=>{state.experiment[key]=$(id).value;save();renderExperiment()});
  $("copyButton").addEventListener("click",copyPost);
  $("openCommunityButton").addEventListener("click",async()=>{const url=validCommunityUrl($("communityUrl").value.trim());if(!url){say("먼저 유효한 https 커뮤니티 주소를 저장하세요.");return}if(!await copyPost())return;window.open(url.href,"_blank","noopener,noreferrer");say("본문을 복사하고 커뮤니티를 열었습니다. 규칙을 확인한 뒤 붙여 넣으세요.")});
  $("postedButton").addEventListener("click",()=>{
    const text=$("postText").value.trim();if(!text){say("기록할 본문이 없습니다.");return}
    const service=activeService(),result=renderCheck(),policy=renderPolicyReview();
    if(result.verdict==="fix"&&!confirm("수정 필요 항목이 남아 있습니다. 그래도 올린 글로 기록할까요?"))return;
    if(policy.status!=="HUMAN_REVIEW_RECORDED"){say("현재 문안과 연결된 커뮤니티 규칙 검수 증거를 먼저 저장하세요.");return}
    if(state.experiment.variant!=="none"&&!state.experiment.id.trim()){say("A/B 문안을 기록하려면 실험 ID를 입력하세요.");return}
    if(state.experiment.variant==="variant"&&!state.experiment.change.trim()){say("B 문안에서 바꾼 한 가지를 적으세요.");return}
    const today=new Date(),date=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
    state.posts.push({id:uid(),date,serviceName:service?service.name:"(서비스 없음)",channel:state.channel,firstLine:text.split(/\r?\n/)[0].slice(0,80),views:0,reactions:0,conversions:0,experimentId:state.experiment.id.trim(),variant:state.experiment.variant,change:state.experiment.change.trim(),policyUrl:state.ruleReviews[state.channel].url,policyCheckedDate:state.ruleReviews[state.channel].checkedDate});
    save();renderHistory();say("기록했습니다. 반응이 생기면 아래 숫자를 갱신하세요.");
  });
  $("historyList").addEventListener("input",event=>{
    const input=event.target.closest("input[data-post]");if(!input)return;
    const post=state.posts.find(item=>item.id===input.dataset.post),value=Math.max(0,Math.floor(Number(input.value))||0);
    if(post){post[input.dataset.field]=value;save();renderHistorySummary();renderExperiment()}
  });
  $("historyList").addEventListener("click",event=>{
    const button=event.target.closest("button[data-remove]");if(!button||!confirm("이 기록을 삭제할까요?"))return;
    state.posts=state.posts.filter(item=>item.id!==button.dataset.remove);save();renderHistory();
  });
  $("mediaType").addEventListener("change",renderMedia);
  $("mediaChecklist").addEventListener("change",updateMediaResult);
}
function renderHistorySummary(){
  const totals={};
  for(const post of state.posts){const t=totals[post.channel]||(totals[post.channel]={views:0,reactions:0,conversions:0});t.views+=post.views;t.reactions+=post.reactions;t.conversions+=post.conversions}
  const best=Object.entries(totals).sort((a,b)=>b[1].conversions-a[1].conversions||b[1].reactions-a[1].reactions)[0];
  $("historySummary").textContent=best?`지금까지 가장 반응이 좋은 곳: ${CHANNELS[best[0]]?.label||best[0]} (가입·문의 ${best[1].conversions}, 반응 ${best[1].reactions}, 조회 ${best[1].views})`:"올린 글을 기록하면 어느 곳이 반응이 좋은지 여기에 나옵니다.";
}

function init(){
  for(const[key,channel]of Object.entries(CHANNELS))$("channelSelect").append(el("option",channel.label,{value:key}));
  for(const[key,media]of Object.entries(MEDIA_CHECKLISTS))$("mediaType").append(el("option",media.label,{value:key}));
  if(!state.activeId&&state.services[0])state.activeId=state.services[0].id;
  if(!CHANNELS[state.channel])state.channel="threads";
  $("channelSelect").value=state.channel;$("topicInput").value=state.topic;$("postText").value=state.drafts[state.channel]||"";
  for(const name of ["audience","benefit","proof","cta"])$(name+"Input").value=state.brief[name]||"";
  for(const[id,key]of[["objectiveInput","objective"],["contentPillarInput","content_pillar"],["communityContextInput","community_context"],["conversationQuestionInput","conversation_question"],["evidenceUrlInput","evidence_url"],["successSignalInput","success_signal"]])$(id).value=state.brief[key]||"";
  $("experimentId").value=state.experiment.id;$("experimentVariant").value=state.experiment.variant;$("experimentChange").value=state.experiment.change;
  bind();renderServices();renderMedia();renderCheck();renderHistory();renderCommunity();renderExperiment();renderIntegrations();showView(state.activeView||"today");document.body.dataset.ready="1";
}
init();
