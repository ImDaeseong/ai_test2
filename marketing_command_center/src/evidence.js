/** Evidence contracts for human rule review and non-causal response experiments. */

export const POLICY_SOURCES={
  threads:{label:"Threads",url:"https://www.facebook.com/help/477434105621119?locale=ko_KR"},
  instagram:{label:"Instagram",url:"https://www.facebook.com/help/477434105621119?locale=ko_KR"},
  x:{label:"X",url:"https://help.x.com/en/rules-and-policies/authenticity"},
  linkedin:{label:"LinkedIn",url:"https://www.linkedin.com/legal/professional-community-policies"},
  naver_blog:{label:"네이버 블로그·카페",url:"https://policy.naver.com/policy/service_group.html"},
  community:{label:"커뮤니티 게시판",url:""}
};

/** Hash text locally so a review becomes stale when its approved copy changes. */
export function textHash(text=""){
  let hash=2166136261;
  for(const char of String(text)){hash^=char.codePointAt(0);hash=Math.imul(hash,16777619)}
  return(hash>>>0).toString(16).padStart(8,"0");
}

/** Validate human rule-review evidence against the exact post text. */
export function ruleReviewStatus(review,text,today=new Date().toISOString().slice(0,10)){
  if(!review)return{status:"HOLD_RULES_UNVERIFIED",reason:"규칙 검수 기록이 없습니다."};
  let url;
  try{url=new URL(review.url)}catch{return{status:"HOLD_RULES_UNVERIFIED",reason:"정책 URL이 올바르지 않습니다."}}
  if(url.protocol!=="https:"||!review.reviewer||!review.checkedDate||!review.approved)return{status:"HOLD_RULES_UNVERIFIED",reason:"URL·확인일·검수자·승인을 모두 기록하세요."};
  if(review.checkedDate>today)return{status:"HOLD_RULES_UNVERIFIED",reason:"확인일은 미래일 수 없습니다."};
  if(review.textHash!==textHash(text))return{status:"HOLD_RULES_UNVERIFIED",reason:"검수 뒤 문안이 바뀌었습니다. 다시 확인하세요."};
  return{status:"HUMAN_REVIEW_RECORDED",reason:"현재 문안과 규칙 검수 증거가 연결됐습니다."};
}

/** Summarize raw A/B observations without claiming statistical causality. */
export function evaluateExperiment(posts,experimentId){
  if(!experimentId)return{status:"NOT_RUN",message:"실험 ID를 입력하면 A/B 관찰을 비교합니다."};
  const selected=posts.filter(post=>post.experimentId===experimentId&&["baseline","variant"].includes(post.variant));
  const totals={baseline:{views:0,conversions:0,count:0},variant:{views:0,conversions:0,count:0}};
  for(const post of selected){const item=totals[post.variant];item.views+=Number(post.views)||0;item.conversions+=Number(post.conversions)||0;item.count++}
  if(!totals.baseline.count||!totals.variant.count)return{status:"HOLD_INSUFFICIENT_EXPOSURE",message:"A와 B 게시 기록이 모두 필요합니다.",totals};
  if(!totals.baseline.views||!totals.variant.views)return{status:"HOLD_INSUFFICIENT_EXPOSURE",message:"A와 B의 실제 조회 분모를 모두 입력하세요.",totals};
  const rates={baseline:totals.baseline.conversions/totals.baseline.views,variant:totals.variant.conversions/totals.variant.views};
  const status=rates.variant>rates.baseline?"OBSERVED_LIFT":"NO_LIFT_OBSERVED";
  return{status,message:status==="OBSERVED_LIFT"?"B의 관찰 전환율이 높습니다. 통계적 인과 증명은 아닙니다.":"B의 관찰 전환율 상승이 보이지 않습니다.",totals,rates};
}
