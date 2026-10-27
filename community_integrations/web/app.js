const state={catalog:[],platform:null,file:null};
const $=id=>document.getElementById(id);
const labels={text:'글',image:'그림',video:'영상',audio:'음악/오디오',file:'문서'};

async function loadCatalog(){
  try{const response=await fetch('/api/capabilities');if(!response.ok)throw new Error('기능 정보를 불러오지 못했습니다.');const data=await response.json();state.catalog=data.platforms;renderPlatforms();selectPlatform('threads');}
  catch(error){$('notice').className='notice hold';$('notice').textContent=error.message;}
}

function renderPlatforms(){
  $('platformList').replaceChildren(...state.catalog.map(item=>{const button=document.createElement('button');button.type='button';button.className='platform-button';button.dataset.platform=item.id;button.innerHTML=`<span class="platform-icon">${item.label.slice(0,1)}</span><span class="platform-copy"><strong>${item.label}</strong><small>${item.configured?'설정됨':'설정 필요'}</small></span>`;button.addEventListener('click',()=>selectPlatform(item.id));return button;}));
}

function selectPlatform(id){
  state.platform=state.catalog.find(item=>item.id===id);document.querySelectorAll('.platform-button').forEach(button=>button.classList.toggle('active',button.dataset.platform===id));
  $('previewPlatform').textContent=state.platform.label;$('previewAvatar').textContent=state.platform.label.slice(0,1);$('confirmationText').placeholder=id;$('configBadge').textContent=state.platform.configured?'연결 설정됨':'환경 변수 필요';$('configBadge').className=`status-badge ${state.platform.configured?'':'hold'}`;
  $('capabilityChips').replaceChildren(...Object.entries(labels).map(([key,label])=>{const span=document.createElement('span');const value=state.platform.capabilities[key];span.className=`chip ${String(value).startsWith('NO')?'no':''}`;span.textContent=`${label} · ${value}`;return span;}));
  const missing=state.platform.missing.length?`필요 설정: ${state.platform.missing.join(', ')}`:'계정 환경 변수가 준비되었습니다.';$('notice').className=`notice ${state.platform.configured?'good':''}`;$('notice').textContent=missing;updatePreview();
}

function payload(){return{platform:state.platform?.id,title:$('title').value,text:$('text').value,media_type:$('mediaType').value,media_url:$('mediaUrl').value,media_id:$('mediaId').value,alt_text:$('altText').value,privacy_level:$('privacy').value,local_file_name:state.file?.name||'',confirmed:$('confirmed').checked,confirmation_text:$('confirmationText').value};}

function updatePreview(){
  $('textCount').textContent=$('text').value.length;$('previewTitle').textContent=$('title').value;$('previewText').textContent=$('text').value||'작성한 내용이 이곳에 표시됩니다.';$('previewText').classList.toggle('placeholder',!$('text').value);
  const box=$('mediaPreview');box.replaceChildren();box.classList.add('hidden');const url=state.file?URL.createObjectURL(state.file):$('mediaUrl').value;if(!url)return;box.classList.remove('hidden');const type=state.file?.type||$('mediaType').value.toLowerCase();let child;if(type.startsWith('image')||type==='image'||type==='photo'){child=document.createElement('img');child.alt=$('altText').value||'선택한 이미지 미리보기';child.src=url;}else if(type.startsWith('video')||type==='video'||type==='reels'||type==='stories'){child=document.createElement('video');child.controls=true;child.src=url;}else{child=document.createElement('div');child.className='media-file';child.textContent=state.file?.name||$('mediaUrl').value;}box.append(child);
}

async function submit(endpoint){
  if(!state.platform)return;const button=endpoint==='preview' ? $('previewButton') : $('publishButton');button.disabled=true;$('result').textContent='처리 중…';try{const response=await fetch(`/api/${endpoint}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});const data=await response.json();$('result').textContent=JSON.stringify(data,null,2);$('notice').className=`notice ${response.ok?'good':'hold'}`;$('notice').textContent=response.ok?(endpoint==='preview'?'네트워크 전송 없이 요청 구조를 확인했습니다.':'게시 요청이 완료되었습니다.'):data.message||'요청을 확인해 주세요.';}catch(error){$('notice').className='notice hold';$('notice').textContent=error.message;$('result').textContent='서버 연결 실패';}finally{button.disabled=false;}
}

document.querySelectorAll('#composerForm input,#composerForm textarea,#composerForm select').forEach(element=>element.addEventListener('input',updatePreview));
$('localFile').addEventListener('change',event=>{state.file=event.target.files[0]||null;$('fileHint').textContent=state.file?`${state.file.name} · 로컬 미리보기 전용 (자동 게시 HOLD)`:'그림·영상·음악·문서의 미리보기만 지원합니다.';updatePreview();});
$('previewButton').addEventListener('click',()=>submit('preview'));
$('publishButton').addEventListener('click',()=>submit('publish'));
$('resetButton').addEventListener('click',()=>{document.getElementById('composerForm').reset();state.file=null;$('result').textContent='요청 정보가 여기에 표시됩니다.';$('fileHint').textContent='그림·영상·음악·문서의 미리보기만 지원합니다.';updatePreview();});
loadCatalog();
