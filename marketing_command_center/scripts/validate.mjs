import{access,readFile}from"node:fs/promises";
import{resolve}from"node:path";
import{fileURLToPath}from"node:url";

const root=resolve(fileURLToPath(new URL("..",import.meta.url)));
const required={
  "index.html":["id=\"bootProblem\"","id=\"loadStarterButton\"","src/boot.js","id=\"serviceSelect\"","id=\"channelSelect\"","id=\"postText\"","id=\"verdict\"","id=\"issueList\"","id=\"draftButton\"","id=\"reviewButton\"","id=\"copyButton\"","id=\"postedButton\"","id=\"historyList\"","id=\"mediaChecklist\""],
  "src/quality.js":["export function checkPost","export const CHANNELS","export const MEDIA_CHECKLISTS"],
  "src/app.js":["localStorage","checkPost","/api/ai/draft","/api/ai/review","OpenAI 유료 API를 1회 호출"],
  "serve.py":["def generate_marketing_draft","def review_marketing_post","/api/health","SO_EXCLUSIVEADDRUSE","\"store\": False"],
  "scripts/browser_e2e.mjs":["Emulation.setDeviceMetricsOverride","browser console errors"],
  "scripts/smoke_launcher.ps1":["$startedPid = [int]$Matches[1]","Wait-Process -Id $startedPid"],
  "README.md":["node --test","localStorage","npm run e2e","사람 검토 HOLD"],
  "PRODUCT_SCOPE.md":["사용 사례","보안 경계","완료 기준","사람 검토 HOLD"]
};
const forbidden={"src/app.js":["OPENAI_API_KEY","sk-"],"index.html":["OPENAI_API_KEY","sk-"]};
let failed=false;
for(const[file,needles]of Object.entries(required)){
  const content=await readFile(resolve(root,file),"utf8"),missing=needles.filter(value=>!content.includes(value)),leaked=(forbidden[file]||[]).filter(value=>content.includes(value));
  if(missing.length||leaked.length){failed=true;console.error(`FAIL ${file}: ${[...missing.map(value=>`missing ${value}`),...leaked.map(value=>`forbidden ${value}`)].join(", ")}`)}else console.log(`PASS ${file}`);
}
// Removed features must not linger in docs or code (guards against stale README/scope text and the old media folder).
const STALE_TERMS=["캘린더","대기열","ZIP","OAuth","PLATFORM_INTEGRATION","model.js","CSV","4173","MARKETING_MEDIA_DIR","media/"];
const CURRENT_FILES=["README.md","PRODUCT_SCOPE.md","index.html","src/app.js","src/boot.js","src/quality.js","src/starter.js","serve.py","scripts/start.ps1","start.bat","start.cmd",".env.example",".gitignore","package.json"];
for(const file of CURRENT_FILES){
  const content=await readFile(resolve(root,file),"utf8"),stale=STALE_TERMS.filter(term=>content.includes(term));
  if(stale.length){failed=true;console.error(`FAIL stale terms in ${file}: ${stale.join(", ")}`)}
}
if(await access(resolve(root,"media")).then(()=>true,()=>false)){failed=true;console.error("FAIL removed media/ folder exists again")}
if(failed)process.exit(1);
console.log("PASS no stale terms or leftover folders");
console.log("PASS marketing_command_center contract");
