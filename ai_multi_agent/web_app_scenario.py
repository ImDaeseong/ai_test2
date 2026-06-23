from __future__ import annotations

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

from config import OPENROUTER_API_KEY, SCENARIO_OUTPUT_DIR
from main import find_project, project_dirs, run_prompt_once, scenario_managed_output_file, scenario_managed_summary

PORT = 5300
app = Flask(__name__)
RUN_LOCK = threading.Lock()


def _prompt_file(project: Path, scene_num: int) -> Path:
    return project / "scenes" / f"씬{scene_num:03d}_GPT_프롬프트.md"


def _prompt_items(project: Path) -> list[dict]:
    summary = scenario_managed_summary(project)
    items = []
    for scene_num in range(1, int(summary["total"] or 0) + 1):
        prompt_file = _prompt_file(project, scene_num)
        output_file = scenario_managed_output_file(project, scene_num)
        items.append({
            "num": scene_num,
            "label": f"씬{scene_num:03d}",
            "prompt_file": prompt_file.name,
            "has_prompt": prompt_file.exists(),
            "done": output_file.exists(),
            "output_file": output_file.name if output_file.exists() else None,
        })
    return items


def _output_items(project: Path) -> list[dict]:
    items = []
    for item in _prompt_items(project):
        if item["done"]:
            output_file = scenario_managed_output_file(project, item["num"])
            items.append({
                "label": item["label"],
                "file": output_file.name,
                "content": output_file.read_text(encoding="utf-8", errors="replace"),
            })
    return items


def _list() -> list[dict]:
    result = []
    for project in project_dirs(SCENARIO_OUTPUT_DIR):
        summary = scenario_managed_summary(project)
        result.append({
            "name": project.name,
            "title": summary["title"],
            "current": summary["current"],
            "total": summary["total"],
            "has_next": summary["next_file"] is not None,
        })
    return result


def _detail(name: str) -> dict | None:
    project = find_project(SCENARIO_OUTPUT_DIR, name)
    if not project:
        return None
    summary = scenario_managed_summary(project)
    next_file = summary["next_file"]
    return {
        "name": project.name,
        "title": summary["title"],
        "current": summary["current"],
        "total": summary["total"],
        "next_num": summary["next_num"],
        "next_label": f"씬{summary['next_num']:03d}" if summary["next_num"] else None,
        "next_prompt": next_file.read_text(encoding="utf-8", errors="replace") if next_file else None,
        "prompts": _prompt_items(project),
        "outputs": _output_items(project),
        "has_settings": (project / "설정집.md").exists(),
    }


def _run_scene(project: Path, scene_num: int, force: bool, max_tokens: int) -> Path:
    prompt_file = _prompt_file(project, scene_num)
    if not prompt_file.exists():
        raise FileNotFoundError(f"프롬프트 파일이 없습니다: {prompt_file.name}")
    output_file = scenario_managed_output_file(project, scene_num)
    return run_prompt_once(prompt_file, output_file, "scenario", force=force, max_tokens=max_tokens)


@app.route("/")
def index():
    return INDEX_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/projects")
def api_projects():
    return jsonify({"ok": True, "projects": _list()})


@app.route("/api/detail/<path:name>")
def api_detail(name: str):
    detail = _detail(name)
    if not detail:
        return jsonify({"ok": False, "error": "프로젝트를 찾을 수 없습니다."}), 404
    return jsonify({"ok": True, **detail})


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True) or {}
    name = data.get("name", "")
    force = bool(data.get("force", False))
    max_tokens = int(data.get("max_tokens", 4096))
    scene_num = data.get("num")

    if not OPENROUTER_API_KEY:
        return jsonify({"ok": False, "error": ".env에 OPENROUTER_API_KEY가 없습니다."}), 400

    project = find_project(SCENARIO_OUTPUT_DIR, name)
    if not project:
        return jsonify({"ok": False, "error": "프로젝트를 찾을 수 없습니다."}), 404

    if scene_num is None:
        summary = scenario_managed_summary(project)
        scene_num = summary["next_num"]
    if not scene_num:
        return jsonify({"ok": False, "error": "실행할 프롬프트가 없습니다."}), 400

    try:
        if not RUN_LOCK.acquire(blocking=False):
            return jsonify({"ok": False, "error": "다른 API 실행이 진행 중입니다."}), 409
        try:
            saved = _run_scene(project, int(scene_num), force=force, max_tokens=max_tokens)
        finally:
            RUN_LOCK.release()
        return jsonify({"ok": True, "saved": saved.name, "result": saved.read_text(encoding="utf-8", errors="replace")})
    except FileExistsError as exc:
        return jsonify({"ok": False, "error": str(exc), "exists": True}), 409
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scenario Prompt Runner</title>
<style>
:root{--bg:#111318;--panel:#1a1d24;--panel2:#222733;--line:#333947;--text:#eef1f7;--muted:#9aa3b5;--accent:#4ea1ff;--ok:#4fc07a;--warn:#f0aa4f;--bad:#ef5f6b;--font:"Malgun Gothic","Apple SD Gothic Neo",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);height:100vh;display:flex;flex-direction:column}
header{height:52px;display:flex;align-items:center;gap:12px;padding:0 22px;border-bottom:1px solid var(--line);background:var(--panel);flex-shrink:0}header h1{font-size:15px;margin:0}.sub{color:var(--muted);font-size:12px}
.layout{display:flex;flex:1;overflow:hidden}.sidebar{width:260px;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column}.sidebar-hd{padding:10px 14px;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;border-bottom:1px solid var(--line)}.sidebar-body{overflow-y:auto;flex:1}
.proj-item{padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--line)}.proj-item:hover,.proj-item.active{background:var(--panel2)}.proj-item.active{border-left:2px solid var(--accent)}.proj-title{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.proj-sub{font-size:11px;color:var(--muted);margin-top:4px}
.content{flex:1;overflow-y:auto;padding:24px}.empty-state{display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);font-size:14px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:20px 22px;margin-bottom:16px}.panel h2{font-size:14px;margin:0 0 14px;color:var(--accent)}
.info-row{display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap}.info-item{font-size:13px;color:var(--muted)}.info-item strong{color:var(--text)}
.prompt-box{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:14px;font-size:12px;font-family:Consolas,"Malgun Gothic",monospace;white-space:pre-wrap;max-height:300px;overflow-y:auto;line-height:1.55}
.prompt-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}.prompt-item{border:1px solid var(--line);background:var(--panel2);border-radius:8px;padding:10px}.prompt-title{font-size:12px;font-weight:700}.prompt-meta{font-size:11px;color:var(--muted);margin:5px 0 8px}.done{color:var(--ok)}.missing{color:var(--bad)}
.btn-row{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}button{font-family:var(--font);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:12px;font-weight:700;cursor:pointer;background:var(--panel2);color:var(--text)}button.primary{background:var(--accent);color:#07101d;border-color:var(--accent)}button.warn{background:var(--warn);color:#201204;border-color:var(--warn)}button:disabled{opacity:.45}.status{margin-top:12px;font-size:13px;color:var(--muted);white-space:pre-wrap}.status.ok{color:var(--ok)}.status.err{color:var(--bad)}.result-panel{border-color:var(--ok)}.spinner{display:inline-block;width:14px;height:14px;margin-right:6px;border:2px solid var(--muted);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle}@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<header><h1>Scenario Prompt Runner</h1><span class="sub">ai_Scenario/output · all scene prompts · port 5300</span></header>
<div class="layout"><aside class="sidebar"><div class="sidebar-hd">Scenario Projects</div><div class="sidebar-body" id="proj-list">Loading...</div></aside><main class="content" id="content"><div class="empty-state">Select a project.</div></main></div>
<script>
let cur=null;
async function loadList(){const r=await fetch('/api/projects');const d=await r.json();renderList(d.projects||[])}
function renderList(projects){const el=document.getElementById('proj-list');if(!projects.length){el.innerHTML='<div style="padding:14px;color:var(--muted);font-size:12px">No projects</div>';return}el.innerHTML=projects.map(p=>`<div class="proj-item${cur===p.name?' active':''}" onclick="sel('${esc(p.name)}')"><div class="proj-title">${esc(p.title)}</div><div class="proj-sub">${p.current}/${p.total} · ${p.has_next?'pending':'done'}</div></div>`).join('')}
async function sel(name){cur=name;loadList();const c=document.getElementById('content');c.innerHTML='<div class="empty-state"><span class="spinner"></span>Loading...</div>';const r=await fetch('/api/detail/'+encodeURIComponent(name));const d=await r.json();if(!d.ok){c.innerHTML='<div class="empty-state" style="color:var(--bad)">Error: '+esc(d.error)+'</div>';return}renderDetail(d)}
function renderDetail(d){const outputs=d.outputs||[];document.getElementById('content').innerHTML=`<div class="panel"><h2>${esc(d.title)}</h2><div class="info-row"><div class="info-item">Progress: <strong>${d.current}/${d.total}</strong></div><div class="info-item">Next: <strong>${esc(d.next_label||'none')}</strong></div><div class="info-item">Settings: <strong>${d.has_settings?'yes':'no'}</strong></div></div>${d.next_prompt?`<label style="font-size:12px;color:var(--muted);font-weight:700">${esc(d.next_label)} preview</label><div class="prompt-box">${esc(d.next_prompt)}</div><div class="btn-row"><button class="primary" onclick="run('${esc(d.name)}')">Run Next</button></div>`:''}<div id="run-status" class="status"></div></div><div class="panel"><h2>All Scene Prompts</h2><div class="prompt-grid">${d.prompts.map(p=>promptCard(d.name,p)).join('')}</div></div>${outputs.length?`<div class="panel result-panel"><h2>Saved Results</h2>${outputs.map(o=>`<label style="font-size:12px;color:var(--muted);font-weight:700;display:block;margin:12px 0 6px">${esc(o.label)} · ${esc(o.file)}</label><div class="prompt-box">${esc(o.content)}</div>`).join('')}</div>`:''}`}
function promptCard(name,p){return `<div class="prompt-item"><div class="prompt-title">${esc(p.label)}</div><div class="prompt-meta ${p.done?'done':p.has_prompt?'':'missing'}">${p.done?'done':p.has_prompt?'pending':'missing prompt'}</div><button onclick="run('${esc(name)}',${p.num},false)" ${!p.has_prompt?'disabled':''}>Run</button> <button class="warn" onclick="run('${esc(name)}',${p.num},true)" ${!p.has_prompt?'disabled':''}>Force</button></div>`}
async function run(name,num=null,force=false){document.querySelectorAll('button').forEach(b=>b.disabled=true);const st=document.getElementById('run-status');if(st){st.className='status';st.innerHTML='<span class="spinner"></span>Running API...'}try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,num,force,max_tokens:4096})});const d=await r.json();if(d.ok){if(st){st.className='status ok';st.textContent=d.saved+' saved'}await loadList();await sel(name)}else{if(st){st.className='status err';st.textContent='Error: '+d.error}else alert(d.error)}}catch(e){if(st){st.className='status err';st.textContent='Network error: '+e.message}}document.querySelectorAll('button').forEach(b=>b.disabled=false)}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
loadList();
</script>
</body>
</html>"""


if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, use_reloader=False)
