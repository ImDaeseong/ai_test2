/** Rule-based post quality checks that run instantly and cost nothing; AI review adds judgment on top. */

export const CHANNELS={
  threads:{label:"Threads",maxLength:500,home:"https://www.threads.net/"},
  x:{label:"X",maxLength:280,home:"https://x.com/compose/post"},
  linkedin:{label:"LinkedIn",maxLength:3000,home:"https://www.linkedin.com/feed/"},
  naver_blog:{label:"네이버 블로그·카페",maxLength:5000,home:"https://section.blog.naver.com/"},
  community:{label:"커뮤니티 게시판",maxLength:2000,home:""},
  instagram:{label:"Instagram 캡션",maxLength:2200,home:"https://www.instagram.com/"}
};

export const MEDIA_CHECKLISTS={
  image:{label:"그림",items:["첫눈에 무엇을 하는 서비스인지 3초 안에 보인다","모바일 크기에서도 글자가 읽힌다","실제 화면이나 실제 결과물이다(합성·과장 아님)","저작권·초상권 문제가 없는 소재다","올릴 커뮤니티의 이미지·광고 표기 규칙을 지켰다"]},
  video:{label:"영상",items:["첫 3초 안에 문제나 결과가 나온다","소리 없이 자막만으로도 이해된다","길이가 너무 길지 않고 한 가지 메시지만 전한다","실제 사용 장면이다(연출·과장 아님)","음원·영상 소재의 사용 권리가 있다","광고·협찬 표기가 필요한 곳이면 표기했다"]},
  music:{label:"음악",items:["첫 10초 안에 분위기와 서비스 메시지가 전달된다","음량이 일정하고 잡음이 없다","저작권이 있는 음원을 쓰지 않았다","AI 생성물 표기가 필요한 곳이면 표기했다","서비스 이미지와 어울리고 반복해 들어도 거슬리지 않는다"]}
};

const GUARANTEE=/100\s*%|무조건|보장|반드시\s*성공|확실히\s*(?:늘|오르|벌)/g;
const HYPE=/역대급|대박|최고|최강|혁명|압도적|완벽|기적|놀라운|미쳤/g;
const CTA=/댓글|써\s?보|해\s?보|사용해|확인해|신청|가입|문의|알려\s?주|공유|링크|클릭|체험|참여|의견/;
const URL=/https?:\/\/\S+/g;
const VALUE=/무료|절약|줄(?:이|여)|빠르|간편|직접|받아|얻|배우|확인|비교|피드백|도움/;

const unique=matches=>[...new Set(matches)];
const issue=(id,level,message)=>({id,level,message});

/** Check one post against the rules and return issues plus an overall verdict (ready, review, fix). */
export function checkPost({text="",channel="threads",serviceName=""}){
  const issues=[],body=String(text).trim(),channelInfo=CHANNELS[channel]||CHANNELS.threads;
  if(body.length<30)issues.push(issue("too_short","fix","너무 짧습니다. 독자가 이유를 알 만큼 구체적으로 쓰세요."));
  if(body.length>channelInfo.maxLength)issues.push(issue("too_long","warn",`${channelInfo.label} 권장 길이 ${channelInfo.maxLength}자를 넘었습니다(현재 ${body.length}자).`));
  const guarantee=unique(body.match(GUARANTEE)||[]);
  if(guarantee.length)issues.push(issue("guarantee","fix",`결과를 보장하는 표현은 신뢰를 잃고 규칙 위반이 되기 쉽습니다: ${guarantee.join(", ")}`));
  const hype=unique(body.match(HYPE)||[]);
  if(hype.length)issues.push(issue("hype","warn",`과장 표현을 구체적인 사실로 바꾸세요: ${hype.join(", ")}`));
  if(/\d+(?:\.\d+)?\s*(?:%|배|퍼센트)/.test(body))issues.push(issue("unsourced_number","warn","수치 주장에는 근거(기간, 측정 방법)를 함께 적으세요."));
  if((body.match(/!/g)||[]).length>2)issues.push(issue("exclamations","warn","느낌표가 많으면 광고처럼 보입니다. 2개 이하로 줄이세요."));
  if((body.match(/\p{Extended_Pictographic}/gu)||[]).length>5)issues.push(issue("emoji","warn","이모지가 많습니다. 5개 이하로 줄이세요."));
  const firstLine=body.split(/\r?\n/)[0]||"";
  if(/^(안녕|반갑|저희는|저는)/.test(firstLine))issues.push(issue("greeting_opening","warn","인사나 자기소개로 시작하면 읽히지 않습니다. 독자의 문제나 결과로 시작하세요."));
  if(firstLine.length>60)issues.push(issue("long_hook","warn",`첫 줄이 깁니다(${firstLine.length}자). 60자 이내로 줄여 핵심을 먼저 보여 주세요.`));
  if(body.length>=30&&!VALUE.test(body))issues.push(issue("unclear_value","warn","독자가 무엇을 얻는지 구체적으로 보이지 않습니다. 시간·비용·경험 중 실제 가치를 적으세요."));
  if(body.length>=30&&!CTA.test(body))issues.push(issue("no_cta","warn","독자가 다음에 할 행동(써 보기, 댓글, 문의)이 없습니다. 한 가지만 제시하세요."));
  const urls=body.match(URL)||[];
  if(urls.length>1)issues.push(issue("many_links","warn","링크가 여러 개면 스팸처럼 보입니다. 하나만 남기세요."));
  if(channel==="community"&&urls.length)issues.push(issue("community_link","warn","커뮤니티는 링크가 든 홍보글을 제한하는 곳이 많습니다. 게시판 규칙을 먼저 확인하세요."));
  const name=String(serviceName).trim();
  if(name){
    const count=body.toLowerCase().split(name.toLowerCase()).length-1;
    if(count===0)issues.push(issue("no_service_name","warn","서비스 이름이 글에 없습니다. 독자가 무엇을 찾아야 할지 모릅니다."));
    else if(count>3)issues.push(issue("name_repeated","warn",`서비스 이름이 ${count}번 나옵니다. 3번 이하로 줄여 광고 느낌을 낮추세요.`));
  }
  const verdict=issues.some(item=>item.level==="fix")?"fix":issues.length>=3?"review":"ready";
  return{issues,verdict};
}
