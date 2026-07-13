"""
Shared Flask app factory for the single-kind "prompt runner" web UIs
(web_app_story.py, web_app_scenario.py). Each of those files only differs
in labels, folder/format conventions, and which main.py helpers it wires
in - this module holds the one copy of the actual routes/logic.
"""
from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

try:
    from flask import Flask, jsonify, request
except ImportError:
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "-q"], check=True)
    from flask import Flask, jsonify, request

from main import find_project, project_dirs, run_prompt_once


@dataclass(frozen=True)
class PromptRunnerConfig:
    """Everything that differs between the story and scenario runners."""

    kind: str  # passed to run_prompt_once's `mode` arg: "story" / "scenario"
    port: int
    title: str  # e.g. "Story Prompt Runner"
    sub_label: str  # header subtitle, e.g. "ai_story/output · all chapter prompts · port 5400"
    project_label: str  # sidebar heading, e.g. "Story Projects"
    unit_dirname: str  # subfolder under each project: "chapters" / "scenes"
    unit_label_fmt: str  # e.g. "ch{:03d}" / "씬{:03d}"
    unit_heading: str  # e.g. "All Chapter Prompts" / "All Scene Prompts"
    accent_color: str
    accent_dark_text: str  # text color on the accent-colored primary button
    output_dir: Path
    managed_summary: Callable[[Path], dict]
    managed_output_file: Callable[[Path, int], Path]
    openrouter_api_key: str | None


def create_prompt_runner_app(cfg: PromptRunnerConfig) -> Flask:
    app = Flask(cfg.kind)
    run_lock = threading.Lock()

    def _label(num: int) -> str:
        return cfg.unit_label_fmt.format(num)

    def _prompt_file(project: Path, num: int) -> Path:
        return project / cfg.unit_dirname / f"{_label(num)}_GPT_프롬프트.md"

    def _prompt_items(project: Path) -> list[dict]:
        summary = cfg.managed_summary(project)
        items = []
        for num in range(1, int(summary["total"] or 0) + 1):
            prompt_file = _prompt_file(project, num)
            output_file = cfg.managed_output_file(project, num)
            items.append({
                "num": num,
                "label": _label(num),
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
                output_file = cfg.managed_output_file(project, item["num"])
                items.append({
                    "label": item["label"],
                    "file": output_file.name,
                    "content": output_file.read_text(encoding="utf-8", errors="replace"),
                })
        return items

    def _list() -> list[dict]:
        result = []
        for project in project_dirs(cfg.output_dir):
            summary = cfg.managed_summary(project)
            result.append({
                "name": project.name,
                "title": summary["title"],
                "current": summary["current"],
                "total": summary["total"],
                "has_next": summary["next_file"] is not None,
            })
        return result

    def _detail(name: str) -> dict | None:
        project = find_project(cfg.output_dir, name)
        if not project:
            return None
        summary = cfg.managed_summary(project)
        next_file = summary["next_file"]
        return {
            "name": project.name,
            "title": summary["title"],
            "current": summary["current"],
            "total": summary["total"],
            "next_num": summary["next_num"],
            "next_label": _label(summary["next_num"]) if summary["next_num"] else None,
            "next_prompt": next_file.read_text(encoding="utf-8", errors="replace") if next_file else None,
            "prompts": _prompt_items(project),
            "outputs": _output_items(project),
            "has_settings": (project / "설정집.md").exists(),
        }

    def _run_unit(project: Path, num: int, force: bool, max_tokens: int) -> Path:
        prompt_file = _prompt_file(project, num)
        if not prompt_file.exists():
            raise FileNotFoundError(f"프롬프트 파일이 없습니다: {prompt_file.name}")
        output_file = cfg.managed_output_file(project, num)
        return run_prompt_once(prompt_file, output_file, cfg.kind, force=force, max_tokens=max_tokens)

    @app.route("/")
    def index():
        return _render_index_html(cfg), 200, {"Content-Type": "text/html; charset=utf-8"}

    @app.route("/api/projects")
    def api_projects():
        output_dir_exists = cfg.output_dir.exists()
        payload = {"ok": True, "projects": _list(), "output_dir_exists": output_dir_exists}
        if not output_dir_exists:
            payload["warning"] = f"설정된 폴더가 없습니다: {cfg.output_dir} (.env의 프로젝트 경로 설정을 확인하세요)"
        return jsonify(payload)

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
        num = data.get("num")

        if not cfg.openrouter_api_key:
            return jsonify({"ok": False, "error": ".env에 OPENROUTER_API_KEY가 없습니다."}), 400

        project = find_project(cfg.output_dir, name)
        if not project:
            return jsonify({"ok": False, "error": "프로젝트를 찾을 수 없습니다."}), 404

        if num is None:
            summary = cfg.managed_summary(project)
            num = summary["next_num"]
        if not num:
            return jsonify({"ok": False, "error": "실행할 프롬프트가 없습니다."}), 400

        try:
            if not run_lock.acquire(blocking=False):
                return jsonify({"ok": False, "error": "다른 API 실행이 진행 중입니다."}), 409
            try:
                saved = _run_unit(project, int(num), force=force, max_tokens=max_tokens)
            finally:
                run_lock.release()
            return jsonify({"ok": True, "saved": saved.name, "result": saved.read_text(encoding="utf-8", errors="replace")})
        except FileExistsError as exc:
            return jsonify({"ok": False, "error": str(exc), "exists": True}), 409
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

    return app


def _render_index_html(cfg: PromptRunnerConfig) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{cfg.title}</title>
<style>
:root{{--bg:#111318;--panel:#1a1d24;--panel2:#222733;--line:#333947;--text:#eef1f7;--muted:#9aa3b5;--accent:{cfg.accent_color};--ok:#4fc07a;--warn:#f0aa4f;--bad:#ef5f6b;--font:"Malgun Gothic","Apple SD Gothic Neo",sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--font);height:100vh;display:flex;flex-direction:column}}
header{{height:52px;display:flex;align-items:center;gap:12px;padding:0 22px;border-bottom:1px solid var(--line);background:var(--panel);flex-shrink:0}}header h1{{font-size:15px;margin:0}}.sub{{color:var(--muted);font-size:12px}}
.layout{{display:flex;flex:1;overflow:hidden}}.sidebar{{width:260px;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column}}.sidebar-hd{{padding:10px 14px;font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;border-bottom:1px solid var(--line)}}.sidebar-body{{overflow-y:auto;flex:1}}
.proj-item{{padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--line)}}.proj-item:hover,.proj-item.active{{background:var(--panel2)}}.proj-item.active{{border-left:2px solid var(--accent)}}.proj-title{{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.proj-sub{{font-size:11px;color:var(--muted);margin-top:4px}}
.content{{flex:1;overflow-y:auto;padding:24px}}.empty-state{{display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);font-size:14px}}.panel{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:20px 22px;margin-bottom:16px}}.panel h2{{font-size:14px;margin:0 0 14px;color:var(--accent)}}
.info-row{{display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap}}.info-item{{font-size:13px;color:var(--muted)}}.info-item strong{{color:var(--text)}}
.prompt-box{{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:14px;font-size:12px;font-family:Consolas,"Malgun Gothic",monospace;white-space:pre-wrap;max-height:300px;overflow-y:auto;line-height:1.55}}
.prompt-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}}.prompt-item{{border:1px solid var(--line);background:var(--panel2);border-radius:8px;padding:10px}}.prompt-title{{font-size:12px;font-weight:700}}.prompt-meta{{font-size:11px;color:var(--muted);margin:5px 0 8px}}.done{{color:var(--ok)}}.missing{{color:var(--bad)}}
.btn-row{{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}}button{{font-family:var(--font);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:12px;font-weight:700;cursor:pointer;background:var(--panel2);color:var(--text)}}button.primary{{background:var(--accent);color:{cfg.accent_dark_text};border-color:var(--accent)}}button.warn{{background:var(--warn);color:#201204;border-color:var(--warn)}}button:disabled{{opacity:.45}}.status{{margin-top:12px;font-size:13px;color:var(--muted);white-space:pre-wrap}}.status.ok{{color:var(--ok)}}.status.err{{color:var(--bad)}}.result-panel{{border-color:var(--ok)}}.spinner{{display:inline-block;width:14px;height:14px;margin-right:6px;border:2px solid var(--muted);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle}}@keyframes spin{{to{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
<header><h1>{cfg.title}</h1><span class="sub">{cfg.sub_label}</span></header>
<div class="layout"><aside class="sidebar"><div class="sidebar-hd">{cfg.project_label}</div><div class="sidebar-body" id="proj-list">Loading...</div></aside><main class="content" id="content"><div class="empty-state">Select a project.</div></main></div>
<script>
let cur=null;
async function loadList(){{const r=await fetch('/api/projects');const d=await r.json();renderList(d.projects||[],d.warning)}}
function renderList(projects,warning){{const el=document.getElementById('proj-list');if(!projects.length){{el.innerHTML=warning?'<div style="padding:14px;color:var(--bad);font-size:12px">'+esc(warning)+'</div>':'<div style="padding:14px;color:var(--muted);font-size:12px">No projects</div>';return}}el.innerHTML=projects.map(p=>`<div class="proj-item${{cur===p.name?' active':''}}" onclick="sel('${{esc(p.name)}}')"><div class="proj-title">${{esc(p.title)}}</div><div class="proj-sub">${{p.current}}/${{p.total}} · ${{p.has_next?'pending':'done'}}</div></div>`).join('')}}
async function sel(name){{cur=name;loadList();const c=document.getElementById('content');c.innerHTML='<div class="empty-state"><span class="spinner"></span>Loading...</div>';const r=await fetch('/api/detail/'+encodeURIComponent(name));const d=await r.json();if(!d.ok){{c.innerHTML='<div class="empty-state" style="color:var(--bad)">Error: '+esc(d.error)+'</div>';return}}renderDetail(d)}}
function renderDetail(d){{const outputs=d.outputs||[];document.getElementById('content').innerHTML=`<div class="panel"><h2>${{esc(d.title)}}</h2><div class="info-row"><div class="info-item">Progress: <strong>${{d.current}}/${{d.total}}</strong></div><div class="info-item">Next: <strong>${{esc(d.next_label||'none')}}</strong></div><div class="info-item">Settings: <strong>${{d.has_settings?'yes':'no'}}</strong></div></div>${{d.next_prompt?`<label style="font-size:12px;color:var(--muted);font-weight:700">${{esc(d.next_label)}} preview</label><div class="prompt-box">${{esc(d.next_prompt)}}</div><div class="btn-row"><button class="primary" onclick="run('${{esc(d.name)}}')">Run Next</button></div>`:''}}<div id="run-status" class="status"></div></div><div class="panel"><h2>{cfg.unit_heading}</h2><div class="prompt-grid">${{d.prompts.map(p=>promptCard(d.name,p)).join('')}}</div></div>${{outputs.length?`<div class="panel result-panel"><h2>Saved Results</h2>${{outputs.map(o=>`<label style="font-size:12px;color:var(--muted);font-weight:700;display:block;margin:12px 0 6px">${{esc(o.label)}} · ${{esc(o.file)}}</label><div class="prompt-box">${{esc(o.content)}}</div>`).join('')}}</div>`:''}}`}}
function promptCard(name,p){{return `<div class="prompt-item"><div class="prompt-title">${{esc(p.label)}}</div><div class="prompt-meta ${{p.done?'done':p.has_prompt?'':'missing'}}">${{p.done?'done':p.has_prompt?'pending':'missing prompt'}}</div><button onclick="run('${{esc(name)}}',${{p.num}},false)" ${{!p.has_prompt?'disabled':''}}>Run</button> <button class="warn" onclick="run('${{esc(name)}}',${{p.num}},true)" ${{!p.has_prompt?'disabled':''}}>Force</button></div>`}}
async function run(name,num=null,force=false){{document.querySelectorAll('button').forEach(b=>b.disabled=true);const st=document.getElementById('run-status');if(st){{st.className='status';st.innerHTML='<span class="spinner"></span>Running API...'}}try{{const r=await fetch('/api/run',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name,num,force,max_tokens:4096}})}});const d=await r.json();if(d.ok){{if(st){{st.className='status ok';st.textContent=d.saved+' saved'}}await loadList();await sel(name)}}else{{if(st){{st.className='status err';st.textContent='Error: '+d.error}}else alert(d.error)}}}}catch(e){{if(st){{st.className='status err';st.textContent='Network error: '+e.message}}}}document.querySelectorAll('button').forEach(b=>b.disabled=false)}}
function esc(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}
loadList();
</script>
</body>
</html>"""
