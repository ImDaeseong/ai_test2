import test from"node:test";
import assert from"node:assert/strict";
import{evaluateExperiment,ruleReviewStatus,textHash}from"../src/evidence.js";

test("human rule review is bound to the exact approved text",()=>{
  const text="Hermes를 직접 써 보고 의견을 댓글로 알려 주세요.";
  const review={url:"https://community.example/rules",checkedDate:"2026-10-22",reviewer:"검수자",approved:true,textHash:textHash(text)};
  assert.equal(ruleReviewStatus(review,text,"2026-10-22").status,"HUMAN_REVIEW_RECORDED");
  assert.equal(ruleReviewStatus(review,text+" 변경","2026-10-22").status,"HOLD_RULES_UNVERIFIED");
  assert.equal(ruleReviewStatus({...review,checkedDate:"2026-10-23"},text,"2026-10-22").status,"HOLD_RULES_UNVERIFIED");
});

test("experiments keep missing evidence distinct from observed lift",()=>{
  const a={experimentId:"hook-1",variant:"baseline",views:100,conversions:2};
  assert.equal(evaluateExperiment([a],"hook-1").status,"HOLD_INSUFFICIENT_EXPOSURE");
  const b={experimentId:"hook-1",variant:"variant",views:80,conversions:4};
  const result=evaluateExperiment([a,b],"hook-1");
  assert.equal(result.status,"OBSERVED_LIFT");
  assert.deepEqual(result.totals.variant,{views:80,conversions:4,count:1});
  assert.match(result.message,/인과 증명은 아닙니다/);
});

test("zero exposure is not flattened into a zero percent result",()=>{
  const posts=[{experimentId:"x",variant:"baseline",views:10,conversions:0},{experimentId:"x",variant:"variant",views:0,conversions:0}];
  assert.equal(evaluateExperiment(posts,"x").status,"HOLD_INSUFFICIENT_EXPOSURE");
});
