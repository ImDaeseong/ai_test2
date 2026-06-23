from __future__ import annotations

import json
import re
import sys
import threading
import webbrowser
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from flask import Flask, jsonify, request
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "-q"], check=True)
    from flask import Flask, jsonify, request

OUTPUT_DIR = Path(__file__).parent / "output"
PORT = 5100

PARTS = [
    ("01_vocal",  "03_vocal_image_prompt.md",  "보컬"),
    ("02_guitar", "04_guitar_image_prompt.md",  "기타"),
    ("03_bass",   "05_bass_image_prompt.md",    "베이스"),
    ("04_drum",   "06_drum_image_prompt.md",    "드럼"),
    ("05_stage",  "07_stage_image_prompt.md",   "전체 무대"),
    ("06_crowd",  "08_crowd_image_prompt.md",   "관객"),
]

VIDEO_SECTION_MAP = {
    "01_vocal":  "보컬 영상",
    "02_guitar": "기타 영상",
    "03_bass":   "베이스 영상",
    "04_drum":   "드럼 영상",
    "05_stage":  "전체 무대 영상",
    "06_crowd":  "군중 영상",
}

app = Flask(__name__)


def extract_video_section(video_file: Path, section_title: str) -> str:
    if not video_file.exists():
        return ""
    content = video_file.read_text(encoding="utf-8")
    m = re.search(rf"## {re.escape(section_title)}\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    return m.group(1).strip() if m else ""


def part_status(song_dir: Path, part_key: str) -> dict:
    part_dir = song_dir / "parts" / part_key
    bundled = (part_dir / "image_prompt.md").exists()
    done = False
    sf = part_dir / "status.json"
    if sf.exists():
        try:
            done = json.loads(sf.read_text(encoding="utf-8")).get("done", False)
        except Exception:
            pass
    return {"bundled": bundled, "done": done}


def list_songs() -> list[dict]:
    if not OUTPUT_DIR.exists():
        return []
    result = []
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        if not any(d.glob("0[1-9]_*.md")):
            continue
        statuses = [part_status(d, pk) for pk, _, _ in PARTS]
        done = sum(1 for s in statuses if s["done"])
        result.append({"name": d.name, "done": done, "total": len(PARTS)})
    return result


def get_song_detail(name: str) -> dict | None:
    song_dir = OUTPUT_DIR / name
    if not song_dir.exists():
        return None
    video_file = song_dir / "09_video_motion_prompts.md"
    parts = []
    for part_key, img_file, label in PARTS:
        img_path = song_dir / img_file
        img_content = img_path.read_text(encoding="utf-8") if img_path.exists() else ""
        video_content = extract_video_section(video_file, VIDEO_SECTION_MAP[part_key])
        status = part_status(song_dir, part_key)
        parts.append({"key": part_key, "label": label,
                      "image_prompt": img_content, "video_prompt": video_content, **status})
    return {"name": name, "parts": parts}


@app.route("/")
def index():
    return INDEX_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/songs")
def api_songs():
    return jsonify({"ok": True, "songs": list_songs()})


@app.route("/api/song/<path:name>")
def api_song(name: str):
    detail = get_song_detail(name)
    if not detail:
        return jsonify({"ok": False, "error": "곡을 찾을 수 없습니다."}), 404
    return jsonify({"ok": True, **detail})


@app.route("/api/bundle", methods=["POST"])
def api_bundle():
    data = request.get_json(force=True) or {}
    name = data.get("name", "")
    song_dir = OUTPUT_DIR / name
    if not song_dir.exists():
        return jsonify({"ok": False, "error": "곡 폴더가 없습니다."}), 404
    video_file = song_dir / "09_video_motion_prompts.md"
    for part_key, img_file, _ in PARTS:
        part_dir = song_dir / "parts" / part_key
        part_dir.mkdir(parents=True, exist_ok=True)
        img_path = song_dir / img_file
        if img_path.exists():
            (part_dir / "image_prompt.md").write_text(
                img_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        video_content = extract_video_section(video_file, VIDEO_SECTION_MAP[part_key])
        if video_content:
            (part_dir / "video_prompt.md").write_text(
                video_content, encoding="utf-8", newline="\n")
        sf = part_dir / "status.json"
        if not sf.exists():
            sf.write_text(json.dumps({"done": False}, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True})


@app.route("/api/mark-done", methods=["POST"])
def api_mark_done():
    data = request.get_json(force=True) or {}
    name = data.get("name", "")
    part_key = data.get("part", "")
    done = bool(data.get("done", True))
    part_dir = OUTPUT_DIR / name / "parts" / part_key
    if not part_dir.exists():
        return jsonify({"ok": False, "error": "파트 폴더가 없습니다."}), 404
    (part_dir / "status.json").write_text(
        json.dumps({"done": done}, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True})


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MV 프롬프트 관리</title>
<style>
:root {
  --bg:#111318; --panel:#1a1d24; --panel2:#222733; --line:#333947;
  --text:#eef1f7; --muted:#9aa3b5; --accent:#b48aff;
  --ok:#4fc07a; --warn:#f0aa4f; --bad:#ef5f6b; --radius:8px;
  --font:"Malgun Gothic","Apple SD Gothic Neo",sans-serif;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);height:100vh;display:flex;flex-direction:column;}
header{height:52px;display:flex;align-items:center;gap:12px;padding:0 22px;border-bottom:1px solid var(--line);background:var(--panel);flex-shrink:0;}
header h1{font-size:15px;margin:0;}
header .sub{color:var(--muted);font-size:12px;}
.layout{display:flex;flex:1;overflow:hidden;}
.sidebar{width:230px;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column;flex-shrink:0;}
.sidebar-hd{padding:10px 14px;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--line);}
.sidebar-body{overflow-y:auto;flex:1;}
.song-item{padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--line);transition:background .1s;}
.song-item:hover{background:var(--panel2);}
.song-item.active{background:var(--panel2);border-left:2px solid var(--accent);}
.song-item .sname{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.prog-row{display:flex;align-items:center;gap:6px;margin-top:4px;}
.prog-bar{flex:1;height:3px;background:var(--line);border-radius:2px;}
.prog-fill{height:100%;background:var(--accent);border-radius:2px;transition:width .3s;}
.prog-txt{font-size:11px;color:var(--muted);white-space:nowrap;}
.content{flex:1;overflow-y:auto;padding:22px;}
.empty-state{display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);font-size:14px;}
.detail-hd{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:18px;gap:10px;flex-wrap:wrap;}
.detail-hd h2{font-size:18px;font-weight:700;margin:0;}
.detail-hd .meta{font-size:12px;color:var(--muted);margin-top:4px;}
button{font-family:var(--font);border:1px solid var(--line);border-radius:var(--radius);padding:9px 16px;font-size:13px;font-weight:700;cursor:pointer;background:var(--panel2);color:var(--text);}
button.primary{background:var(--accent);color:#100820;border-color:var(--accent);font-size:14px;padding:10px 22px;}
button:hover{filter:brightness(1.1);}
button:disabled{opacity:.45;cursor:not-allowed;filter:none;}
.hint{font-size:12px;color:var(--muted);margin-bottom:16px;padding:10px 14px;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);line-height:1.6;}
.parts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;}
.part-card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;}
.part-card.done{border-color:var(--ok);}
.part-card-hd{padding:10px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);}
.part-label{font-size:13px;font-weight:700;color:var(--accent);}
.done-label{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--muted);cursor:pointer;}
.part-body{padding:8px;display:flex;flex-direction:column;gap:6px;}
.psec{border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;}
.ptoggle{padding:7px 10px;background:var(--panel2);display:flex;justify-content:space-between;align-items:center;cursor:pointer;font-size:12px;font-weight:700;color:var(--muted);user-select:none;}
.ptoggle:hover{filter:brightness(1.1);}
.pbody{display:none;padding:10px;font-size:11px;font-family:Consolas,"Malgun Gothic",monospace;white-space:pre-wrap;max-height:200px;overflow-y:auto;border-top:1px solid var(--line);background:var(--bg);line-height:1.5;}
.pbody.open{display:block;}
.cbtn{font-size:10px;padding:2px 7px;font-weight:700;}
.spinner{display:inline-block;width:14px;height:14px;margin-right:6px;border:2px solid var(--muted);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;}
@keyframes spin{to{transform:rotate(360deg);}}
</style>
</head>
<body>
<header>
  <h1>MV 프롬프트 관리</h1>
  <span class="sub">ai_img_video_prompt · port 5100</span>
</header>
<div class="layout">
  <div class="sidebar">
    <div class="sidebar-hd">곡 목록</div>
    <div class="sidebar-body" id="song-list">
      <div style="padding:14px;color:var(--muted);font-size:12px">로딩 중...</div>
    </div>
  </div>
  <div class="content" id="content">
    <div class="empty-state">← 왼쪽에서 곡을 선택하세요</div>
  </div>
</div>
<script>
let songs=[], cur=null;

async function load(){
  const r=await fetch('/api/songs');
  const d=await r.json();
  songs=d.songs||[];
  renderList();
}

function renderList(){
  const el=document.getElementById('song-list');
  if(!songs.length){el.innerHTML='<div style="padding:14px;color:var(--muted);font-size:12px">폴더 없음</div>';return;}
  el.innerHTML=songs.map(s=>`
    <div class="song-item${cur===s.name?' active':''}" onclick="sel('${esc(s.name)}')">
      <div class="sname" title="${esc(s.name)}">${esc(s.name)}</div>
      <div class="prog-row">
        <div class="prog-bar"><div class="prog-fill" style="width:${s.done/s.total*100}%"></div></div>
        <div class="prog-txt">${s.done}/${s.total}</div>
      </div>
    </div>`).join('');
}

async function sel(name){
  cur=name; renderList();
  const c=document.getElementById('content');
  c.innerHTML='<div class="empty-state"><span class="spinner"></span>로딩 중...</div>';
  const r=await fetch('/api/song/'+encodeURIComponent(name));
  const d=await r.json();
  if(!d.ok){c.innerHTML='<div class="empty-state" style="color:var(--bad)">오류: '+esc(d.error)+'</div>';return;}
  renderDetail(d);
}

function renderDetail(song){
  const allBundled=song.parts.every(p=>p.bundled);
  const doneN=song.parts.filter(p=>p.done).length;
  document.getElementById('content').innerHTML=`
    <div class="detail-hd">
      <div><h2>${esc(song.name)}</h2><div class="meta">${doneN}/${song.parts.length} 파트 완료</div></div>
      <button class="primary" onclick="bundle('${esc(song.name)}')" ${allBundled?'disabled':''}>
        ${allBundled?'✓ 번들 생성됨':'파트 번들 생성'}</button>
    </div>
    ${!allBundled?'<div class="hint">파트 번들 생성 시 각 파트 폴더에 image_prompt.md와 video_prompt.md가 저장됩니다. 이미지 생성 후 완료 체크로 진행 상태를 관리하세요.</div>':''}
    <div class="parts-grid">${song.parts.map(p=>partCard(song.name,p)).join('')}</div>`;
}

function partCard(sn,p){
  return `<div class="part-card${p.done?' done':''}" id="card-${p.key}">
    <div class="part-card-hd">
      <span class="part-label">${esc(p.label)}</span>
      <label class="done-label">
        <input type="checkbox"${p.done?' checked':''} onchange="markDone('${esc(sn)}','${p.key}',this.checked)"> 완료
      </label>
    </div>
    <div class="part-body">
      <div class="psec">
        <div class="ptoggle" onclick="tog(this)">
          이미지 프롬프트
          <span style="display:flex;gap:5px;align-items:center">
            <button class="cbtn" onclick="event.stopPropagation();cp('img-${p.key}')">복사</button>
            <span class="arr">▼</span>
          </span>
        </div>
        <div class="pbody" id="img-${p.key}">${esc(p.image_prompt)}</div>
      </div>
      <div class="psec">
        <div class="ptoggle" onclick="tog(this)">
          영상 프롬프트
          <span style="display:flex;gap:5px;align-items:center">
            <button class="cbtn" onclick="event.stopPropagation();cp('vid-${p.key}')">복사</button>
            <span class="arr">▼</span>
          </span>
        </div>
        <div class="pbody" id="vid-${p.key}">${esc(p.video_prompt)}</div>
      </div>
    </div>
  </div>`;
}

function tog(el){
  const b=el.nextElementSibling;
  b.classList.toggle('open');
  const a=el.querySelector('.arr');
  if(a) a.textContent=b.classList.contains('open')?'▲':'▼';
}

async function bundle(name){
  const btn=event.target;
  btn.disabled=true; btn.innerHTML='<span class="spinner"></span>생성 중...';
  const r=await fetch('/api/bundle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  const d=await r.json();
  if(d.ok){sel(name);load();}
  else{alert('오류: '+d.error);btn.disabled=false;btn.textContent='파트 번들 생성';}
}

async function markDone(sn,pk,done){
  const r=await fetch('/api/mark-done',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:sn,part:pk,done})});
  const d=await r.json();
  if(d.ok){document.getElementById('card-'+pk)?.classList.toggle('done',done);await load();}
}

function cp(id){const el=document.getElementById(id);if(el)navigator.clipboard.writeText(el.textContent);}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

load();
</script>
</body>
</html>"""


if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, use_reloader=False)
