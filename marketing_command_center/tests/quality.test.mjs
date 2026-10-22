import test from"node:test";
import assert from"node:assert/strict";
import{checkPost,CHANNELS,MEDIA_CHECKLISTS}from"../src/quality.js";
import{STARTER}from"../src/starter.js";

test("starter massage-practice posts pass the rules in every channel they ship for",()=>{
  assert.deepEqual(Object.keys(STARTER.drafts).sort(),Object.keys(CHANNELS).sort(),"every channel needs its own starter post");
  for(const[channel,text]of Object.entries(STARTER.drafts)){
    assert.ok(CHANNELS[channel],channel);
    const result=checkPost({text,channel,serviceName:STARTER.service.name});
    assert.equal(result.verdict,"ready",`${channel}: ${JSON.stringify(result.issues)}`);
    assert.doesNotMatch(text,/치료를 해|완치|효과 보장|통증이 사라/,`${channel} must not make health claims`);
    assert.match(text,/피드백/,`${channel} must state the feedback condition`);
    assert.match(text,/임신/,`${channel} must mention a safety precaution`);
  }
});

const GOOD="매주 월요일마다 광고 성과를 엑셀로 옮기느라 한 시간씩 쓰시나요?\nHermes 대시보드는 채널별 숫자를 한 화면에 모아 줍니다. 직접 써 보고 불편한 점을 댓글로 알려 주세요.";
const ids=result=>result.issues.map(issue=>issue.id);

test("a concrete, honest post passes with no blocking issue",()=>{
  const result=checkPost({text:GOOD,channel:"threads",serviceName:"Hermes"});
  assert.equal(result.verdict,"ready");
  assert.deepEqual(result.issues.filter(issue=>issue.level==="fix"),[]);
});

test("empty or tiny text blocks posting",()=>{
  assert.equal(checkPost({text:"",channel:"threads",serviceName:"Hermes"}).verdict,"fix");
  assert.ok(ids(checkPost({text:"좋아요",channel:"threads",serviceName:"Hermes"})).includes("too_short"));
});

test("guarantee and hype wording is flagged with the offending word",()=>{
  const guarantee=checkPost({text:"Hermes는 100% 무조건 성과를 보장합니다. 지금 써 보세요.",channel:"threads",serviceName:"Hermes"});
  assert.equal(guarantee.verdict,"fix");
  assert.ok(guarantee.issues.some(issue=>issue.id==="guarantee"&&issue.message.includes("100%")));
  const hype=checkPost({text:"역대급 대박 서비스 Hermes를 써 보세요. 댓글로 의견 주세요.",channel:"threads",serviceName:"Hermes"});
  assert.ok(ids(hype).includes("hype"));
});

test("numeric claims ask for evidence, exclamations and emoji are capped",()=>{
  assert.ok(ids(checkPost({text:"Hermes로 매출이 3배 늘었어요. 써 보세요.",channel:"threads",serviceName:"Hermes"})).includes("unsourced_number"));
  assert.ok(ids(checkPost({text:"Hermes 소개! 지금! 바로! 써 보세요!",channel:"threads",serviceName:"Hermes"})).includes("exclamations"));
  assert.ok(ids(checkPost({text:"Hermes 소개 🔥🔥🔥🔥🔥🔥 써 보세요",channel:"threads",serviceName:"Hermes"})).includes("emoji"));
});

test("weak openings and a missing call to action are flagged",()=>{
  assert.ok(ids(checkPost({text:"안녕하세요 Hermes입니다. 저희는 대시보드를 만듭니다.",channel:"threads",serviceName:"Hermes"})).includes("greeting_opening"));
  assert.ok(ids(checkPost({text:"Hermes는 광고 성과를 한 화면에 모아 보여 주는 도구입니다.",channel:"threads",serviceName:"Hermes"})).includes("no_cta"));
  assert.ok(ids(checkPost({text:"가".repeat(70)+"\n나머지 설명입니다. 댓글로 알려 주세요. Hermes",channel:"threads",serviceName:"Hermes"})).includes("long_hook"));
});

test("a post that names no reader value is sent back for review",()=>{
  const result=checkPost({text:"Hermes를 소개합니다. 자세한 내용은 댓글로 문의해 주세요.",channel:"threads",serviceName:"Hermes"});
  assert.ok(result.issues.some(item=>item.id==="unclear_value"));
});

test("length is judged per channel and links are limited",()=>{
  const long="Hermes "+"설명".repeat(200)+" 댓글 주세요";
  assert.ok(ids(checkPost({text:long,channel:"x",serviceName:"Hermes"})).includes("too_long"));
  assert.ok(!ids(checkPost({text:long,channel:"linkedin",serviceName:"Hermes"})).includes("too_long"));
  assert.ok(ids(checkPost({text:GOOD+" https://a.example https://b.example",channel:"threads",serviceName:"Hermes"})).includes("many_links"));
  assert.ok(ids(checkPost({text:GOOD+" https://a.example",channel:"community",serviceName:"Hermes"})).includes("community_link"));
});

test("the service name must appear but not dominate",()=>{
  assert.ok(ids(checkPost({text:"광고 성과를 한 화면에 모으는 방법이 궁금하시면 댓글 주세요.",channel:"threads",serviceName:"Hermes"})).includes("no_service_name"));
  assert.ok(ids(checkPost({text:"Hermes Hermes Hermes Hermes 댓글 주세요 Hermes 입니다 좋은 도구",channel:"community",serviceName:"Hermes"})).includes("name_repeated"));
});

test("every channel has a label and a recommended length, and media has checklists",()=>{
  for(const channel of Object.values(CHANNELS)){assert.ok(channel.label);assert.ok(channel.maxLength>0)}
  for(const type of["image","video","music"])assert.ok(MEDIA_CHECKLISTS[type].items.length>=4);
});
