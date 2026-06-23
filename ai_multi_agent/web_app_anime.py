from __future__ import annotations

import os
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

from agents.base import call_agent
from config import ANIME_OUTPUT_DIR, OPENROUTER_API_KEY, OUTPUT_DIR

PORT = 5500
app = Flask(__name__)
RUN_LOCK = threading.Lock()

GROUPS = [
    ("reference", "Reference / Workflow"),
    ("image", "Image Prompts"),
    ("video", "Video Scene Prompts"),
    ("clip", "Video Clip Prompts"),
]


def _iter_md_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return [
        Path(entry.path)
        for entry in os.scandir(folder)
        if entry.is_file() and entry.name.lower().endswith(".md")
    ]


def _projects() -> list[Path]:
    if not ANIME_OUTPUT_DIR.exists():
        return []
    projects = []
    for entry in sorted(os.scandir(ANIME_OUTPUT_DIR), key=lambda e: e.name.lower()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        project = Path(entry.path)
        if any(_prompt_files(project, group_key) for group_key, _ in GROUPS):
            projects.append(project)
    return projects


def _prompt_files(project: Path, group: str | None = None) -> list[Path]:
    files: list[Path] = []

    if group in (None, "reference"):
        for name in ("00_prompt_to_video_workflow.md", "character_reference_prompt.md"):
            path = project / name
            if path.exists():
                files.append(path)
        sheet = project / "image_prompts" / "00_character_turnaround_model_sheet.md"
        if sheet.exists():
            files.append(sheet)

    if group in (None, "image"):
        files.extend(
            path for path in _iter_md_files(project / "image_prompts")
            if not path.name.startswith("00_")
        )

    if group in (None, "video"):
        files.extend(_iter_md_files(project / "video_prompts"))

    if group in (None, "clip"):
        files.extend(
            path for path in _iter_md_files(project / "video_clip_prompts")
            if path.name != "timeline_plan.md"
        )

    return sorted(files, key=lambda p: p.relative_to(project).as_posix().lower())


def _managed_project_dir(project: Path) -> Path:
    return OUTPUT_DIR / "anime" / project.name


def _managed_output_file(project: Path, prompt_file: Path) -> Path:
    rel = prompt_file.relative_to(project)
    return _managed_project_dir(project) / rel.parent / f"{prompt_file.stem}_result.md"


def _group_summary(project: Path, group: str) -> dict:
    prompts = _prompt_files(project, group)
    done = sum(1 for prompt in prompts if _managed_output_file(project, prompt).exists())
    next_file = next((prompt for prompt in prompts if not _managed_output_file(project, prompt).exists()), None)
    label = next(label for key, label in GROUPS if key == group)
    return {
        "key": group,
        "label": label,
        "current": done,
        "total": len(prompts),
        "has_next": next_file is not None,
        "next_label": next_file.relative_to(project).as_posix() if next_file else None,
    }


def _summary(project: Path) -> dict:
    groups = [_group_summary(project, key) for key, _ in GROUPS]
    current = sum(group["current"] for group in groups)
    total = sum(group["total"] for group in groups)
    next_group = next((group for group in groups if group["has_next"]), None)
    return {
        "name": project.name,
        "title": project.name,
        "current": current,
        "total": total,
        "has_next": next_group is not None,
        "next_group": next_group["key"] if next_group else None,
        "groups": groups,
    }


def _outputs(project: Path, group: str | None = None) -> list[dict]:
    items = []
    for prompt_file in _prompt_files(project, group):
        output_file = _managed_output_file(project, prompt_file)
        if output_file.exists():
            items.append({
                "label": prompt_file.relative_to(project).as_posix(),
                "file": output_file.relative_to(_managed_project_dir(project)).as_posix(),
                "content": output_file.read_text(encoding="utf-8", errors="replace"),
            })
    return items


def _prompt_entries(project: Path, group: str | None = None) -> list[dict]:
    entries = []
    for prompt_file in _prompt_files(project, group):
        output_file = _managed_output_file(project, prompt_file)
        rel = prompt_file.relative_to(project).as_posix()
        entries.append({
            "rel": rel,
            "label": rel,
            "done": output_file.exists(),
            "output_file": output_file.relative_to(_managed_project_dir(project)).as_posix() if output_file.exists() else None,
        })
    return entries


def _find_project(name: str) -> Path | None:
    direct = ANIME_OUTPUT_DIR / name
    if direct.exists() and direct.is_dir():
        return direct
    lowered = name.lower()
    return next((project for project in _projects() if lowered in project.name.lower()), None)


def _find_prompt(project: Path, rel_path: str) -> Path | None:
    normalized = rel_path.replace("\\", "/")
    return next(
        (prompt for prompt in _prompt_files(project, None) if prompt.relative_to(project).as_posix() == normalized),
        None,
    )


def _next_prompt(project: Path, group: str | None = None) -> Path | None:
    groups = [group] if group else [key for key, _ in GROUPS]
    for group_key in groups:
        for prompt in _prompt_files(project, group_key):
            if not _managed_output_file(project, prompt).exists():
                return prompt
    return None


def _run_prompt(prompt_file: Path, output_file: Path, force: bool, max_tokens: int) -> Path:
    if output_file.exists() and not force:
        raise FileExistsError(f"이미 결과 파일이 있습니다: {output_file.name}")
    prompt = prompt_file.read_text(encoding="utf-8", errors="replace")
    system = (
        "You are an expert production assistant for an animated music video workflow. "
        "Execute the user's prompt exactly and return only the requested result."
    )
    result = call_agent(system, prompt, max_tokens=max_tokens)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(result, encoding="utf-8", newline="\n")
    return output_file


@app.route("/")
def index():
    return INDEX_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/projects")
def api_projects():
    return jsonify({"ok": True, "projects": [_summary(project) for project in _projects()]})


@app.route("/api/detail/<path:name>")
def api_detail(name: str):
    group = request.args.get("group") or None
    project = _find_project(name)
    if not project:
        return jsonify({"ok": False, "error": "프로젝트를 찾을 수 없습니다."}), 404
    summary = _summary(project)
    next_file = _next_prompt(project, group)
    return jsonify({
        "ok": True,
        **summary,
        "selected_group": group,
        "next_label": next_file.relative_to(project).as_posix() if next_file else None,
        "next_prompt": next_file.read_text(encoding="utf-8", errors="replace") if next_file else None,
        "prompts": _prompt_entries(project, group),
        "outputs": _outputs(project, group),
    })


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True) or {}
    name = data.get("name", "")
    group = data.get("group") or None
    rel_path = data.get("rel") or None
    force = bool(data.get("force", False))
    max_tokens = int(data.get("max_tokens", 4096))

    if not OPENROUTER_API_KEY:
        return jsonify({"ok": False, "error": ".env에 OPENROUTER_API_KEY가 없습니다."}), 400

    project = _find_project(name)
    if not project:
        return jsonify({"ok": False, "error": "프로젝트를 찾을 수 없습니다."}), 404

    next_file = _find_prompt(project, rel_path) if rel_path else _next_prompt(project, group)
    if not next_file:
        return jsonify({"ok": False, "error": "실행할 다음 프롬프트가 없습니다."}), 400

    output_file = _managed_output_file(project, next_file)
    try:
        if not RUN_LOCK.acquire(blocking=False):
            return jsonify({"ok": False, "error": "다른 API 실행이 진행 중입니다."}), 409
        try:
            saved = _run_prompt(next_file, output_file, force=force, max_tokens=max_tokens)
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
<title>Anime Prompt Runner</title>
<style>
:root{--bg:#111318;--panel:#1a1d24;--panel2:#222733;--line:#333947;--text:#eef1f7;--muted:#9aa3b5;--accent:#f2c96d;--ok:#4fc07a;--warn:#f0aa4f;--bad:#ef5f6b;--font:"Malgun Gothic","Apple SD Gothic Neo",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);height:100vh;display:flex;flex-direction:column}
header{height:52px;display:flex;align-items:center;gap:12px;padding:0 22px;border-bottom:1px solid var(--line);background:var(--panel);flex-shrink:0}header h1{font-size:15px;margin:0}.sub{color:var(--muted);font-size:12px}
.layout{display:flex;flex:1;overflow:hidden}.sidebar{width:280px;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column}.sidebar-hd{padding:10px 14px;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;border-bottom:1px solid var(--line)}.sidebar-body{overflow-y:auto;flex:1}
.proj-item{padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--line)}.proj-item:hover,.proj-item.active{background:var(--panel2)}.proj-item.active{border-left:2px solid var(--accent)}.proj-title{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.proj-sub{font-size:11px;color:var(--muted);margin-top:4px}
.content{flex:1;overflow-y:auto;padding:24px}.empty-state{display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);font-size:14px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:20px 22px;margin-bottom:16px}.panel h2{font-size:14px;margin:0 0 14px;color:var(--accent)}
.groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin:14px 0}.group{border:1px solid var(--line);border-radius:8px;background:var(--panel2);padding:10px;cursor:pointer}.group.active{border-color:var(--accent)}.group-name{font-size:12px;font-weight:700}.group-meta{font-size:11px;color:var(--muted);margin-top:4px}
.info-row{display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap}.info-item{font-size:13px;color:var(--muted)}.info-item strong{color:var(--text)}
.prompt-box{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:14px;font-size:12px;font-family:Consolas,"Malgun Gothic",monospace;white-space:pre-wrap;max-height:340px;overflow-y:auto;line-height:1.55;color:var(--text)}
.btn-row{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}button{font-family:var(--font);border:1px solid var(--line);border-radius:8px;padding:9px 16px;font-size:13px;font-weight:700;cursor:pointer;background:var(--panel2);color:var(--text)}button.primary{background:var(--accent);color:#211702;border-color:var(--accent)}button.warn{background:var(--warn);color:#201204;border-color:var(--warn)}button:disabled{opacity:.45;cursor:not-allowed}.status{margin-top:12px;font-size:13px;color:var(--muted);white-space:pre-wrap;line-height:1.6}.status.ok{color:var(--ok)}.status.err{color:var(--bad)}.result-panel{border-color:var(--ok)}.result-panel h2{color:var(--ok)}.spinner{display:inline-block;width:14px;height:14px;margin-right:6px;border:2px solid var(--muted);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle}@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<header><h1>Anime Prompt Runner</h1><span class="sub">ai_anime/output · reference, image, video, clip groups · port 5500</span></header>
<div class="layout"><aside class="sidebar"><div class="sidebar-hd">Anime Projects</div><div class="sidebar-body" id="proj-list"><div style="padding:14px;color:var(--muted);font-size:12px">Loading...</div></div></aside><main class="content" id="content"><div class="empty-state">Select a project.</div></main></div>
<script>
let cur=null, group=null;
async function loadList(){const r=await fetch('/api/projects');const d=await r.json();renderList(d.projects||[])}
function renderList(projects){const el=document.getElementById('proj-list');if(!projects.length){el.innerHTML='<div style="padding:14px;color:var(--muted);font-size:12px">No projects</div>';return}el.innerHTML=projects.map(p=>`<div class="proj-item${cur===p.name?' active':''}" onclick="sel('${esc(p.name)}',null)"><div class="proj-title" title="${esc(p.title)}">${esc(p.title)}</div><div class="proj-sub">${p.current}/${p.total} · ${p.has_next?'next '+esc(p.next_group||''):'done'}</div></div>`).join('')}
async function sel(name,nextGroup){cur=name;group=nextGroup;loadList();const c=document.getElementById('content');c.innerHTML='<div class="empty-state"><span class="spinner"></span>Loading...</div>';const url='/api/detail/'+encodeURIComponent(name)+(group?'?group='+encodeURIComponent(group):'');const r=await fetch(url);const d=await r.json();if(!d.ok){c.innerHTML='<div class="empty-state" style="color:var(--bad)">Error: '+esc(d.error)+'</div>';return}renderDetail(d)}
function renderDetail(d){
  const hasNext=d.next_prompt!=null;
  const outputs=d.outputs||[];
  const prompts=d.prompts||[];
  document.getElementById('content').innerHTML=`
    <div class="panel">
      <h2>${esc(d.title)}</h2>
      <div class="info-row">
        <div class="info-item">Progress: <strong>${d.current} / ${d.total}</strong></div>
        <div class="info-item">Selected: <strong>${esc(d.selected_group||'all')}</strong></div>
        <div class="info-item">Next: <strong>${esc(d.next_label||'none')}</strong></div>
      </div>
      <div class="groups">${d.groups.map(g=>`
        <div class="group ${(d.selected_group||'')===g.key?'active':''}" onclick="sel('${esc(d.name)}','${g.key}')">
          <div class="group-name">${esc(g.label)}</div>
          <div class="group-meta">${g.current}/${g.total} · ${g.has_next?'next':'done'}</div>
        </div>`).join('')}</div>
      ${hasNext?`
        <label style="font-size:12px;color:var(--muted);font-weight:700;display:block;margin-bottom:6px">${esc(d.next_label)}</label>
        <div class="prompt-box">${esc(d.next_prompt)}</div>
        <div class="btn-row"><button class="primary" onclick="run('${esc(d.name)}')">Run Next</button></div>
      `:`<div class="status ok">No remaining prompts in this selection.</div>`}
      <div id="run-status" class="status"></div>
    </div>
    <div class="panel">
      <h2>Prompt List</h2>
      <div class="groups">${prompts.map(p=>`
        <div class="group">
          <div class="group-name">${esc(p.label)}</div>
          <div class="group-meta">${p.done?'done':'pending'}</div>
          <div class="btn-row">
            <button onclick="run('${esc(d.name)}',false,'${esc(p.rel)}')">Run</button>
            <button class="warn" onclick="run('${esc(d.name)}',true,'${esc(p.rel)}')">Force</button>
          </div>
        </div>`).join('')}</div>
    </div>
    ${outputs.length?`<div class="panel result-panel"><h2>Saved Results</h2>${outputs.map(o=>`
      <label style="font-size:12px;color:var(--muted);font-weight:700;display:block;margin:12px 0 6px">${esc(o.label)} · ${esc(o.file)}</label>
      <div class="prompt-box">${esc(o.content)}</div>`).join('')}</div>`:''}`;
}
async function run(name,force=false,rel=null){
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  const st=document.getElementById('run-status');
  if(st){st.className='status';st.innerHTML='<span class="spinner"></span>Running API...';}
  try{
    const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,group,rel,force,max_tokens:4096})});
    const d=await r.json();
    if(d.ok){
      if(st){st.className='status ok';st.textContent=d.saved+' saved';}
      await loadList(); await sel(name,group);
    }else if(d.exists){
      if(st){st.className='status err';st.textContent='Result file already exists. Use force rerun.';}
    }else{
      if(st){st.className='status err';st.textContent='Error: '+d.error;}
    }
  }catch(e){
    if(st){st.className='status err';st.textContent='Network error: '+e.message;}
  }
  document.querySelectorAll('button').forEach(b=>b.disabled=false);
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
loadList();
</script>
</body>
</html>"""


if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, use_reloader=False)
