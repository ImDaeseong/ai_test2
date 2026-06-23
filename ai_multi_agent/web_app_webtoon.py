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
    from flask import Flask, jsonify, request, send_file
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "-q"], check=True)
    from flask import Flask, jsonify, request, send_file

from config import IMAGE_MODEL, IMAGE_SIZE, OPENAI_API_KEY, OUTPUT_DIR, WEBTOON_OUTPUT_DIR
from image_generator import generate_image_file

PORT = 5600

app = Flask(__name__)
RUN_LOCK = threading.Lock()


# ── 경로 헬퍼 ─────────────────────────────────────────────────────────────────

def _panel_out_dir(song: str, panel_stem: str) -> Path:
    """ai_multi_agent 결과 저장 경로."""
    return OUTPUT_DIR / "webtoon" / song / "panels" / panel_stem


def _panel_image_file(song: str, panel_stem: str) -> Path:
    return _panel_out_dir(song, panel_stem) / "image.png"


def _panel_status_file(song: str, panel_stem: str) -> Path:
    return _panel_out_dir(song, panel_stem) / "status.json"


def _panel_status(song: str, panel_stem: str) -> dict:
    sf = _panel_status_file(song, panel_stem)
    done = False
    if sf.exists():
        try:
            done = json.loads(sf.read_text(encoding="utf-8")).get("done", False)
        except Exception:
            pass
    image_file = _panel_image_file(song, panel_stem)
    return {
        "done": done,
        "has_image": image_file.exists(),
        "image_url": f"/api/image/{song}/{panel_stem}" if image_file.exists() else None,
    }


def _extract_gpt_prompt(panel_content: str) -> str:
    """패널 파일의 ## GPT Image 블록에서 프롬프트 추출."""
    lines = panel_content.split("\n")
    in_gpt = False
    in_code = False
    result = []
    for line in lines:
        if "## GPT Image" in line:
            in_gpt = True
        elif in_gpt and line.strip() == "```" and not in_code:
            in_code = True
        elif in_gpt and in_code:
            if line.strip() == "```":
                break
            result.append(line)
    return "\n".join(result).strip()


def _extract_timing(content: str) -> dict:
    sec_m = re.search(r"섹션: (.+)", content)
    dur_m = re.search(r"지속 시간: (\d+)초", content)
    num_m = re.search(r"컷 번호: (\d+)/(\d+)", content)
    return {
        "section": sec_m.group(1).strip() if sec_m else "",
        "duration": int(dur_m.group(1)) if dur_m else 0,
        "num": int(num_m.group(1)) if num_m else 0,
        "total": int(num_m.group(2)) if num_m else 0,
    }


def _write_panel_bundle(song: str, panel_stem: str) -> Path:
    """패널 프롬프트를 ai_multi_agent 결과 폴더에 복사하고 경로 반환."""
    source_file = WEBTOON_OUTPUT_DIR / song / "panels" / f"{panel_stem}.md"
    if not source_file.exists():
        raise FileNotFoundError(f"패널 파일이 없습니다: {source_file.name}")
    content = source_file.read_text(encoding="utf-8")
    gpt_prompt = _extract_gpt_prompt(content)
    if not gpt_prompt:
        raise ValueError(f"GPT Image 프롬프트를 찾을 수 없습니다: {panel_stem}")

    out_dir = _panel_out_dir(song, panel_stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "image_prompt.md").write_text(gpt_prompt, encoding="utf-8")

    sf = out_dir / "status.json"
    if not sf.exists():
        sf.write_text(json.dumps({"done": False}), encoding="utf-8")
    return out_dir


def _next_panel_stem(song: str) -> str | None:
    """완료되지 않은 첫 패널 반환. 곡 선택 시에만 호출 (목록에서는 호출 안 함)."""
    panels_dir = WEBTOON_OUTPUT_DIR / song / "panels"
    if not panels_dir.exists():
        return None
    for pf in sorted(panels_dir.glob("panel_*.md")):
        if not _panel_status(song, pf.stem)["done"]:
            return pf.stem
    return None


def _song_done_counts(song: str) -> tuple[int, int]:
    """ai_multi_agent output 폴더에서 완료/이미지 수 집계. 소스 파일 순회 없음."""
    out_panels = OUTPUT_DIR / "webtoon" / song / "panels"
    if not out_panels.exists():
        return 0, 0
    done = imgs = 0
    for panel_dir in out_panels.iterdir():
        if not panel_dir.is_dir():
            continue
        sf = panel_dir / "status.json"
        if sf.exists():
            try:
                if json.loads(sf.read_text(encoding="utf-8")).get("done"):
                    done += 1
            except Exception:
                pass
        if (panel_dir / "image.png").exists():
            imgs += 1
    return done, imgs


def _list_songs() -> list[dict]:
    if not WEBTOON_OUTPUT_DIR.exists():
        return []
    result = []
    for d in sorted(WEBTOON_OUTPUT_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        panels_dir = d / "panels"
        if not panels_dir.exists():
            continue
        # 소스 패널 수만 빠르게 집계 (파일 내용 읽지 않음)
        total = sum(1 for _ in panels_dir.glob("panel_*.md"))
        if total == 0:
            continue
        # 완료/이미지 수는 ai_multi_agent output에서만 확인
        done, imgs = _song_done_counts(d.name)
        result.append({
            "name": d.name,
            "done": done,
            "total": total,
            "has_image": imgs,
        })
    return result


def _get_song_panels(song: str) -> list[dict]:
    panels_dir = WEBTOON_OUTPUT_DIR / song / "panels"
    if not panels_dir.exists():
        return []
    panels = []
    for pf in sorted(panels_dir.glob("panel_*.md")):
        content = pf.read_text(encoding="utf-8")
        timing  = _extract_timing(content)
        gpt_prompt = _extract_gpt_prompt(content)
        status  = _panel_status(song, pf.stem)
        m = re.match(r"panel_(\d+)_(\w+)_(\w+)$", pf.stem)
        panels.append({
            "stem": pf.stem,
            "num": int(m.group(1)) if m else 0,
            "section": m.group(2) if m else "",
            "type": m.group(3) if m else "",
            "section_label": timing["section"],
            "duration": timing["duration"],
            "total": timing["total"],
            "gpt_prompt": gpt_prompt,
            **status,
        })
    return panels


# ── API 라우트 ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return app.response_class(HTML, mimetype="text/html; charset=utf-8")


@app.route("/api/songs")
def api_songs():
    return jsonify({"ok": True, "songs": _list_songs()})


@app.route("/api/song/<path:song>")
def api_song(song: str):
    song_dir = WEBTOON_OUTPUT_DIR / song
    if not song_dir.exists():
        return jsonify({"ok": False, "error": "곡을 찾을 수 없습니다."}), 404
    panels = _get_song_panels(song)
    storyboard = ""
    sp = song_dir / "01_storyboard.md"
    if sp.exists():
        storyboard = sp.read_text(encoding="utf-8")
    return jsonify({
        "ok": True,
        "name": song,
        "panels": panels,
        "storyboard": storyboard,
        "next_panel": _next_panel_stem(song),
        "can_generate": True,
    })


@app.route("/api/generate-next", methods=["POST"])
def api_generate_next():
    data = request.get_json(force=True) or {}
    song  = data.get("name", "")
    force = bool(data.get("force", False))

    if not OPENAI_API_KEY:
        return jsonify({"ok": False, "error": ".env에 OPENAI_API_KEY가 없습니다."}), 400

    panel_stem = _next_panel_stem(song)
    if not panel_stem:
        return jsonify({"ok": False, "error": "생성할 다음 패널이 없습니다."}), 400

    if not RUN_LOCK.acquire(blocking=False):
        return jsonify({"ok": False, "error": "다른 이미지 생성이 진행 중입니다. 완료 후 다시 실행하세요."}), 409

    try:
        out_dir    = _write_panel_bundle(song, panel_stem)
        image_file = out_dir / "image.png"
        if image_file.exists() and not force:
            return jsonify({"ok": False, "error": "이미 생성된 이미지가 있습니다.", "exists": True}), 409

        image_prompt = (out_dir / "image_prompt.md").read_text(encoding="utf-8")
        saved = generate_image_file(image_prompt, image_file)

        manifest = {
            "source": "ai-webtoon",
            "song": song,
            "panel": panel_stem,
            "image_file": saved.name,
            "image_prompt": "image_prompt.md",
            "image_model": IMAGE_MODEL,
            "image_size": IMAGE_SIZE,
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "status.json").write_text(json.dumps({"done": True}), encoding="utf-8")

        return jsonify({
            "ok": True,
            "panel": panel_stem,
            "saved": saved.name,
            "image_url": f"/api/image/{song}/{panel_stem}",
            "output_dir": str(out_dir),
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    finally:
        RUN_LOCK.release()


@app.route("/api/generate-panel", methods=["POST"])
def api_generate_panel():
    data       = request.get_json(force=True) or {}
    song       = data.get("name", "")
    panel_stem = data.get("panel", "")
    force      = bool(data.get("force", False))

    if not OPENAI_API_KEY:
        return jsonify({"ok": False, "error": ".env에 OPENAI_API_KEY가 없습니다."}), 400

    if not (WEBTOON_OUTPUT_DIR / song / "panels" / f"{panel_stem}.md").exists():
        return jsonify({"ok": False, "error": "패널 파일이 없습니다."}), 404

    if not RUN_LOCK.acquire(blocking=False):
        return jsonify({"ok": False, "error": "다른 이미지 생성이 진행 중입니다."}), 409

    try:
        out_dir    = _write_panel_bundle(song, panel_stem)
        image_file = out_dir / "image.png"
        if image_file.exists() and not force:
            return jsonify({"ok": False, "error": "이미 생성된 이미지가 있습니다.", "exists": True}), 409

        image_prompt = (out_dir / "image_prompt.md").read_text(encoding="utf-8")
        saved = generate_image_file(image_prompt, image_file)

        manifest = {
            "source": "ai-webtoon",
            "song": song,
            "panel": panel_stem,
            "image_file": saved.name,
            "image_prompt": "image_prompt.md",
            "image_model": IMAGE_MODEL,
            "image_size": IMAGE_SIZE,
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "status.json").write_text(json.dumps({"done": True}), encoding="utf-8")

        return jsonify({
            "ok": True,
            "panel": panel_stem,
            "saved": saved.name,
            "image_url": f"/api/image/{song}/{panel_stem}",
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    finally:
        RUN_LOCK.release()


@app.route("/api/mark-done", methods=["POST"])
def api_mark_done():
    data       = request.get_json(force=True) or {}
    song       = data.get("name", "")
    panel_stem = data.get("panel", "")
    done       = bool(data.get("done", True))
    sf         = _panel_status_file(song, panel_stem)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps({"done": done}), encoding="utf-8")
    return jsonify({"ok": True, "done": done})


@app.route("/api/image/<path:song>/<panel_stem>")
def api_image(song: str, panel_stem: str):
    image_file = _panel_image_file(song, panel_stem)
    if not image_file.exists():
        return jsonify({"ok": False, "error": "이미지 파일이 없습니다."}), 404
    return send_file(image_file, mimetype="image/png")


# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ai-webtoon MV</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#0a0a0f;color:#e0e0e0}
.sidebar{position:fixed;left:0;top:0;width:260px;height:100vh;overflow-y:auto;background:#12121a;border-right:1px solid #2a2a3a;padding:16px}
.sidebar h1{font-size:13px;color:#ff4db8;margin-bottom:2px;font-weight:700;letter-spacing:1px}
.sidebar small{font-size:10px;color:#555;display:block;margin-bottom:16px}
.song-item{padding:10px 12px;border-radius:8px;cursor:pointer;margin-bottom:6px;border:1px solid transparent}
.song-item:hover{background:#1a1a2e;border-color:#2a2a4a}
.song-item.active{background:#1a0a2e;border-color:#ff4db8}
.song-name{font-size:12px;font-weight:600;word-break:break-all}
.song-prog{font-size:10px;color:#888;margin-top:3px}
.prog-bar{height:3px;background:#222;border-radius:2px;margin-top:5px}
.prog-fill{height:100%;background:#ff4db8;border-radius:2px;transition:width .3s}
.main{margin-left:260px;padding:24px}
.main-header{display:flex;align-items:center;gap:10px;margin-bottom:18px;flex-wrap:wrap}
.main-header h2{font-size:18px;color:#ff4db8;font-weight:700}
.btn{padding:6px 13px;border-radius:6px;border:1px solid #2a2a4a;background:#12121a;color:#aaa;font-size:12px;cursor:pointer}
.btn:hover{border-color:#ff4db8;color:#ff4db8}
.btn.pink{background:#ff4db8;border-color:#ff4db8;color:#fff}
.btn.pink:hover{background:#cc3a93}
.btn.pink:disabled{opacity:.5;cursor:not-allowed}
.panel-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:10px;padding:13px;cursor:pointer;transition:border-color .2s}
.card:hover{border-color:#ff4db8}
.card.done{border-color:#3a6a4a;opacity:.65}
.card.has-img{border-color:#4a8a3a}
.card-num{font-size:10px;color:#ff4db8;font-weight:700}
.card-type{font-size:13px;font-weight:600;margin-top:3px;text-transform:capitalize}
.card-sec{font-size:11px;color:#888;margin-top:2px}
.badge{display:inline-block;font-size:9px;padding:2px 6px;border-radius:8px;margin-top:5px;margin-right:3px}
.badge.done-b{background:#1a3a2a;color:#4db86c}
.badge.img-b{background:#1a3a1a;color:#8fc86c}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:200;overflow-y:auto;padding:28px 14px;align-items:flex-start;justify-content:center}
.overlay.open{display:flex}
.modal{background:#12121a;border:1px solid #2a2a3a;border-radius:12px;padding:22px;max-width:900px;width:100%;position:relative}
.modal-close{position:absolute;top:13px;right:13px;background:none;border:none;color:#666;font-size:18px;cursor:pointer}
.modal-close:hover{color:#ff4db8}
.modal-title{font-size:14px;font-weight:700;color:#ff4db8;margin-bottom:10px}
.info-bar{padding:7px 12px;background:#1a1a2e;border-radius:6px;font-size:11px;color:#888;margin-bottom:10px}
.modal-img{max-width:100%;border-radius:8px;margin-bottom:12px;border:1px solid #2a2a3a}
.pbox{background:#060608;border:1px solid #1e1e2e;border-radius:8px;padding:13px;font-family:monospace;font-size:11px;line-height:1.7;white-space:pre-wrap;word-break:break-word;max-height:280px;overflow-y:auto;color:#b8e0b8}
.err-box{background:#2a0a0a;border:1px solid #6a2a2a;border-radius:6px;padding:10px;font-size:12px;color:#e08080;margin-top:8px;display:none}
.actions{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center}
.spin{display:inline-block;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{color:#555;font-size:14px;padding:60px;text-align:center}
.no-key{background:#1a1a0a;border:1px solid #4a4a1a;padding:10px 14px;border-radius:6px;font-size:12px;color:#aaa;margin-bottom:16px}
</style>
</head>
<body>
<div class="sidebar">
  <h1>🎨 ai-webtoon MV</h1>
  <small>ai_multi_agent · 포트 5600</small>
  <div id="song-list"><div style="color:#555;font-size:11px;padding:16px">로딩 중...</div></div>
</div>
<div class="main" id="main"><div class="empty">← 왼쪽에서 곡을 선택하세요</div></div>

<div class="overlay" id="overlay">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <div class="modal-title" id="mtitle"></div>
    <div class="info-bar" id="minfo"></div>
    <img id="mimg" style="display:none" class="modal-img">
    <div class="pbox" id="mcontent"></div>
    <div class="err-box" id="merr"></div>
    <div class="actions">
      <button class="btn" onclick="copyPrompt()">📋 복사</button>
      <button class="btn pink" id="gen-btn" onclick="generatePanel(false)">▶ 이미지 생성</button>
      <button class="btn pink" id="force-btn" onclick="generatePanel(true)" style="opacity:.6;font-size:11px">↺ 재생성</button>
      <button class="btn" id="done-btn" onclick="toggleDone()">✅ 완료 표시</button>
    </div>
  </div>
</div>

<script>
let song = null, panel = null, allPanels = [], canGen = false;

async function loadSongs() {
  const r = await fetch('/api/songs');
  const d = await r.json();
  const songs = d.songs || [];
  const el = document.getElementById('song-list');
  if (!songs.length) {
    el.innerHTML = '<div style="color:#555;font-size:11px;padding:14px">ai-webtoon/output/ 에 곡이 없습니다.<br>ai-webtoon에서 먼저 create-all 실행하세요.</div>';
    return;
  }
  el.innerHTML = songs.map(s => `
    <div class="song-item" data-name="${esc(s.name)}" onclick="loadSong(this.dataset.name)" id="si-${esc(s.name)}">
      <div class="song-name">${esc(s.name)}</div>
      <div class="song-prog">${s.done}/${s.total} 완료 · 🖼 ${s.has_image}장</div>
      <div class="prog-bar"><div class="prog-fill" style="width:${s.total>0?Math.round(s.done/s.total*100):0}%"></div></div>
    </div>`).join('');
}

async function loadSong(name) {
  song = name;
  document.querySelectorAll('.song-item').forEach(e=>e.classList.remove('active'));
  const si = document.getElementById('si-'+name);
  if(si) si.classList.add('active');
  document.getElementById('main').innerHTML = '<div class="empty">로딩 중...</div>';

  const r = await fetch('/api/song/'+encodeURIComponent(name));
  const d = await r.json();
  if (!d.ok) { document.getElementById('main').innerHTML = '<div class="empty">오류: '+esc(d.error)+'</div>'; return; }

  allPanels = d.panels || [];
  window._sb = d.storyboard || '';

  document.getElementById('main').innerHTML = `
    <div class="main-header">
      <h2>${esc(name)}</h2>
      <button class="btn" onclick="showSb()">📋 스토리보드</button>
      <button class="btn pink" onclick="runNext()">▶ 다음 패널 생성</button>
    </div>
    <div class="panel-grid" id="pgrid"></div>`;
  renderPanels(allPanels);
}

function renderPanels(panels) {
  const g = document.getElementById('pgrid');
  if (!panels.length) { g.innerHTML='<div class="empty">패널 없음</div>'; return; }
  g.innerHTML = panels.map(p=>`
    <div class="card ${p.done?'done':''} ${p.has_image?'has-img':''}" data-stem="${esc(p.stem)}" onclick="openPanel(this.dataset.stem)" id="card-${esc(p.stem)}">
      <div class="card-num">Panel ${String(p.num).padStart(3,'0')}</div>
      <div class="card-type">${esc(p.type)}</div>
      <div class="card-sec">${esc(p.section_label)}${p.duration?' · '+p.duration+'초':''}</div>
      ${p.done?'<span class="badge done-b">✓ 완료</span>':''}
      ${p.has_image?'<span class="badge img-b">🖼 이미지</span>':''}
    </div>`).join('');
}

function openPanel(stem) {
  panel = allPanels.find(p=>p.stem===stem);
  if(!panel) return;
  document.getElementById('mtitle').textContent = `Panel ${String(panel.num).padStart(3,'0')} — ${panel.section_label} / ${panel.type}`;
  document.getElementById('minfo').textContent = `섹션: ${panel.section_label}  |  지속: ${panel.duration}초  |  ${panel.num}/${panel.total}`;
  const mi = document.getElementById('mimg');
  if(panel.image_url){ mi.src=panel.image_url+'?t='+Date.now(); mi.style.display='block'; }
  else mi.style.display='none';
  document.getElementById('mcontent').textContent = panel.gpt_prompt || '(GPT Image 프롬프트 없음)';
  document.getElementById('merr').style.display='none';
  document.getElementById('gen-btn').style.display = 'inline-block';
  document.getElementById('force-btn').style.display = panel.has_image ? 'inline-block' : 'none';
  document.getElementById('done-btn').textContent = panel.done?'↩ 완료 취소':'✅ 완료 표시';
  document.getElementById('overlay').classList.add('open');
}

async function generatePanel(force) {
  if(!panel||!song) return;
  const gb = document.getElementById('gen-btn');
  const fb = document.getElementById('force-btn');
  const eb = document.getElementById('merr');
  gb.disabled=true; fb.disabled=true;
  gb.innerHTML='<span class="spin">⟳</span> 생성 중...';
  eb.style.display='none';

  try {
    const r = await fetch('/api/generate-panel', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({name:song, panel:panel.stem, force}),
    });
    const d = await r.json();
    if(d.ok) {
      panel.has_image=true; panel.done=true;
      panel.image_url=d.image_url;
      const mi=document.getElementById('mimg');
      mi.src=d.image_url+'?t='+Date.now(); mi.style.display='block';
      document.getElementById('done-btn').textContent='↩ 완료 취소';
      document.getElementById('force-btn').style.display='inline-block';
      updateCard(); loadSongs();
    } else {
      eb.textContent='오류: '+(d.error||'알 수 없는 오류');
      eb.style.display='block';
    }
  } catch(e) {
    eb.textContent='요청 실패: '+e; eb.style.display='block';
  } finally {
    gb.disabled=false; fb.disabled=false;
    gb.textContent='▶ 이미지 생성';
  }
}

async function runNext() {
  const r = await fetch('/api/song/'+encodeURIComponent(song));
  const d = await r.json();
  if(d.next_panel) { openPanel(d.next_panel); await generatePanel(false); }
  else alert('모든 패널이 완료되었습니다.');
}

async function toggleDone() {
  if(!panel||!song) return;
  const newDone=!panel.done;
  await fetch('/api/mark-done',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:song,panel:panel.stem,done:newDone})});
  panel.done=newDone;
  document.getElementById('done-btn').textContent=newDone?'↩ 완료 취소':'✅ 완료 표시';
  updateCard(); loadSongs();
}

function updateCard() {
  const c=document.getElementById('card-'+panel.stem);
  if(!c) return;
  c.classList.toggle('done',panel.done);
  c.classList.toggle('has-img',panel.has_image);
  const db=c.querySelector('.badge.done-b'), ib=c.querySelector('.badge.img-b');
  if(panel.done&&!db) c.insertAdjacentHTML('beforeend','<span class="badge done-b">✓ 완료</span>');
  else if(!panel.done&&db) db.remove();
  if(panel.has_image&&!ib) c.insertAdjacentHTML('beforeend','<span class="badge img-b">🖼 이미지</span>');
}

function copyPrompt() {
  navigator.clipboard.writeText(document.getElementById('mcontent').textContent).then(()=>{
    const b=document.querySelector('.actions .btn');
    b.textContent='✓ 복사됨!'; setTimeout(()=>b.textContent='📋 복사',1500);
  });
}

function showSb() {
  document.getElementById('mtitle').textContent='스토리보드';
  document.getElementById('minfo').textContent='';
  document.getElementById('mimg').style.display='none';
  document.getElementById('mcontent').textContent=window._sb||'없음';
  document.getElementById('gen-btn').style.display='none';
  document.getElementById('force-btn').style.display='none';
  document.getElementById('overlay').classList.add('open');
}

function closeModal(){document.getElementById('overlay').classList.remove('open');}
document.getElementById('overlay').addEventListener('click',e=>{if(e.target===e.currentTarget)closeModal();});
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
loadSongs();
</script>
</body>
</html>"""


def _open_browser() -> None:
    import time
    time.sleep(1.0)
    webbrowser.open(f"http://127.0.0.1:{PORT}")


def main() -> None:
    threading.Thread(target=_open_browser, daemon=True).start()
    print(f"ai-webtoon MV (ai_multi_agent) → http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False)


if __name__ == "__main__":
    main()
