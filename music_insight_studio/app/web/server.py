from __future__ import annotations

import argparse
import html
import posixpath
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

from app.analyzers import AudioAnalyzer
from app.core import AnalysisMode, TrackInput, Verdict
from app.services import AnalysisService
from app.web.security import UploadSecurityPolicy, validate_audio_payload, validate_content_length


ALLOWED_EXTENSIONS = AudioAnalyzer.SUPPORTED_EXTENSIONS
SUPPORTED_AUDIO_LABEL = ", ".join(sorted(ext.upper().lstrip(".") for ext in ALLOWED_EXTENSIONS))
UNSUPPORTED_AUDIO_MESSAGE = (
    f"Supported audio files: {SUPPORTED_AUDIO_LABEL}. "
    "M4A/AAC are not supported by the current local decoder; convert them to WAV, MP3, or FLAC first."
)
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {
    "/static/vendor/opensheetmusicdisplay.min.js": (
        STATIC_DIR / "vendor" / "opensheetmusicdisplay.min.js",
        "application/javascript; charset=utf-8",
    ),
}
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SECURITY_POLICY = UploadSecurityPolicy()
REPORT_FILENAMES = {"analysis_report.md", "analysis_report.ko.md", "analysis_report.json", "analysis_lead_sheet.musicxml"}
VERDICT_LABELS = {
    Verdict.PASS: "진행 가능",
    Verdict.REVISE: "수정 권장",
    Verdict.HOLD: "보류",
    Verdict.NOT_APPLICABLE: "해당 없음",
}


@dataclass(frozen=True)
class WebPaths:
    uploads_dir: Path = Path("uploads")
    outputs_dir: Path = Path("outputs") / "web"


@dataclass(frozen=True)
class UploadedAudio:
    filename: str
    content: bytes


@dataclass(frozen=True)
class UploadForm:
    audio: UploadedAudio
    mode: AnalysisMode
    target: str
    lyrics: str = ""
    prompt: str = ""


def is_allowed_audio(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def safe_filename(filename: str) -> str:
    name = Path(filename.replace("\\", "/")).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name or "audio"


def parse_upload(content_type: str, body: bytes) -> UploadForm:
    if "multipart/form-data" not in content_type:
        raise ValueError("Expected multipart form data.")

    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: " + content_type.encode("utf-8") + b"\r\n\r\n" + body
    )

    audio: UploadedAudio | None = None
    mode = AnalysisMode.GENERAL
    target = "general"
    lyrics = ""
    prompt = ""
    valid_modes = {item.value for item in AnalysisMode}

    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        name = part.get_param("name", header="content-disposition")
        if name == "audio":
            filename = safe_filename(part.get_filename() or "")
            payload = part.get_payload(decode=True) or b""
            if not filename or not payload:
                raise ValueError("Audio file is required.")
            if not is_allowed_audio(filename):
                extension = Path(filename).suffix.lower() or "unknown"
                raise ValueError(f"{UNSUPPORTED_AUDIO_MESSAGE} Received: {extension}")
            validate_audio_payload(filename, payload, SECURITY_POLICY)
            audio = UploadedAudio(filename, payload)
        elif name == "mode":
            value = part.get_content().strip()
            mode = AnalysisMode(value) if value in valid_modes else AnalysisMode.GENERAL
        elif name == "target":
            target = part.get_content().strip() or "general"
        elif name == "lyrics":
            lyrics = part.get_content().strip()
        elif name == "prompt":
            prompt = part.get_content().strip()

    if audio is None:
        raise ValueError("Audio file is required.")
    return UploadForm(audio, mode, target, lyrics, prompt)


def analyze_upload(
    audio: UploadedAudio,
    mode: AnalysisMode,
    target: str,
    paths: WebPaths,
    lyrics: str = "",
    prompt: str = "",
) -> tuple[dict[str, str], Verdict, float | None, str]:
    request_id = uuid4().hex[:12]
    upload_dir = paths.uploads_dir / request_id
    out_dir = paths.outputs_dir / request_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    audio_path = upload_dir / audio.filename
    audio_path.write_bytes(audio.content)

    service = AnalysisService()
    report = service.analyze(
        TrackInput(audio_path=audio_path, mode=mode, lyrics=lyrics, prompt=prompt, target_platform=target)
    )
    written = service.write_reports(report, out_dir)
    written_names = {path.name for path in written}
    for expected in ("analysis_report.md", "analysis_report.ko.md", "analysis_report.json", "analysis_lead_sheet.musicxml"):
        if expected not in written_names:
            raise RuntimeError(f"Missing generated report: {expected}")

    links = {
        "markdown": f"/reports/{request_id}/analysis_report.md",
        "korean_markdown": f"/reports/{request_id}/analysis_report.ko.md",
        "json": f"/reports/{request_id}/analysis_report.json",
        "musicxml": f"/reports/{request_id}/analysis_lead_sheet.musicxml",
    }
    korean_report = (out_dir / "analysis_report.ko.md").read_text(encoding="utf-8")
    return links, report.overall_verdict, report.overall_score, korean_report


_INLINE_CODE = re.compile(r"`([^`]+)`")
_INLINE_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def render_inline_markdown(text: str) -> str:
    """Escape HTML, then convert inline `code` spans and **bold** spans.

    The rest of render_markdown_preview only understands block-level markdown
    (headings, list items, plain paragraphs); it passed line content straight
    through html.escape, so literal backticks/asterisks from the report
    (e.g. Suno style tags in `code`, score/verdict in **bold**) leaked into
    the rendered page unconverted.
    """
    escaped = html.escape(text)
    escaped = _INLINE_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = _INLINE_BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    return escaped


def render_markdown_preview(markdown: str) -> str:
    html_lines = []
    in_list = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{render_inline_markdown(line[2:])}</h2>")
        elif line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{render_inline_markdown(line[3:])}</h3>")
        elif line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h4>{render_inline_markdown(line[4:])}</h4>")
        elif line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{render_inline_markdown(line[2:])}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{render_inline_markdown(line)}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def render_result(links: dict[str, str], verdict: Verdict, score: float | None, korean_report: str) -> str:
    return render_user_result(links, verdict, score, korean_report)


def render_legacy_result(links: dict[str, str], verdict: Verdict, score: float | None, korean_report: str) -> str:
    score_label = "N/A" if score is None else f"{score:.1f}/100"
    return f"""<section class="result">
      <div class="result-head">
        <div>
          <h2>분석 결과</h2>
          <p><strong>판정:</strong> {html.escape(verdict.value)} / <strong>점수:</strong> {html.escape(score_label)}</p>
        </div>
        <div class="links">
          <a href="{html.escape(links["korean_markdown"])}">Korean Markdown</a>
          <a href="{html.escape(links["markdown"])}">Markdown</a>
          <a href="{html.escape(links["json"])}">JSON</a>
        </div>
      </div>
      <article class="report-body">
        {render_markdown_preview(korean_report)}
      </article>
    </section>"""


def render_user_result(links: dict[str, str], verdict: Verdict, score: float | None, korean_report: str) -> str:
    score_label = "N/A" if score is None else f"{score:.1f}/100"
    verdict_label = VERDICT_LABELS.get(verdict, verdict.value)
    musicxml_link = links.get("musicxml")
    musicxml_html = ""
    if musicxml_link:
        score_page_url = "/score?src=" + urllib.parse.quote(musicxml_link, safe="")
        musicxml_html = f'<a href="{html.escape(score_page_url)}" target="_blank" rel="noopener">악보 MusicXML</a>'
    return f"""<section class="result">
      <div class="result-head">
        <div>
          <h2>분석 결과</h2>
          <p><strong>판단:</strong> {html.escape(verdict_label)} / <strong>점수:</strong> {html.escape(score_label)}</p>
        </div>
        <div class="links">
          <a href="{html.escape(links["json"])}" target="_blank" rel="noopener">JSON</a>
          {musicxml_html}
        </div>
      </div>
      <article class="report-body">
        {render_markdown_preview(korean_report)}
      </article>
    </section>"""


def parse_report_path(request_path: str) -> tuple[str, str] | None:
    parts = [part for part in posixpath.normpath(request_path).split("/") if part]
    if len(parts) != 3 or parts[0] != "reports":
        return None
    _, request_id, filename = parts
    if not re.fullmatch(r"[a-f0-9]{12}", request_id) or filename not in REPORT_FILENAMES:
        return None
    return request_id, filename


def render_score_page(musicxml_url: str) -> bytes:
    escaped_url = html.escape(musicxml_url)
    page = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>악보 MusicXML</title>
  <style>
    :root {{ color-scheme: light; --ink:#202124; --muted:#5f6368; --line:#dadce0; --bg:#f8fafc; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, "Malgun Gothic", sans-serif; color: var(--ink); background: var(--bg); }}
    main {{ max-width: 960px; margin: 0 auto; padding: 24px 16px 44px; }}
    h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .score-note {{ color: var(--muted); margin: 0 0 16px; }}
    .score-view {{ padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--muted); }}
    .score-notation {{ overflow-x: auto; min-height: 24px; }}
    .score-view h4 {{ margin: 16px 0 6px; font-size: 14px; }}
    .score-xml {{ margin: 0; max-height: 420px; overflow: auto; background: var(--bg); border: 1px solid var(--line); border-radius: 6px; padding: 10px; font-size: 12px; line-height: 1.4; white-space: pre-wrap; word-break: break-all; }}
  </style>
</head>
<body>
  <main>
    <h1>악보 MusicXML</h1>
    <p class="score-note">악보는 분석 메타데이터 기반 구간 차트입니다(멜로디 채보 아님).</p>
    <div class="score-view" data-musicxml-url="{escaped_url}">
      <div class="score-notation">악보 불러오는 중...</div>
      <h4>MusicXML 원문</h4>
      <pre class="score-xml"></pre>
    </div>
  </main>
  <script src="/static/vendor/opensheetmusicdisplay.min.js"></script>
  <script>
    (function () {{
      var scoreEl = document.querySelector('.score-view');
      var notationEl = scoreEl.querySelector('.score-notation');
      var xmlEl = scoreEl.querySelector('.score-xml');
      var url = scoreEl.getAttribute('data-musicxml-url');
      if (typeof opensheetmusicdisplay === 'undefined') {{
        notationEl.textContent = '악보 렌더러를 불러오지 못했습니다.';
        return;
      }}
      fetch(url)
        .then(function (response) {{ return response.text(); }})
        .then(function (xml) {{
          xmlEl.textContent = xml;
          notationEl.textContent = '';
          var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(notationEl, {{ backend: 'svg' }});
          return osmd.load(xml).then(function () {{
            osmd.EngravingRules.RenderXMeasuresPerLineAkaSystem = 2;
            osmd.render();
          }});
        }})
        .catch(function () {{
          notationEl.textContent = '악보를 표시하지 못했습니다. 아래 MusicXML 원문을 참고해 주세요.';
        }});
    }})();
  </script>
</body>
</html>"""
    return page.encode("utf-8")


def render_home(error: str = "", result: str = "") -> bytes:
    error_html = f'<div class="alert">{html.escape(error)}</div>' if error else ""
    modes = "".join(f'<option value="{mode.value}">{html.escape(mode.value)}</option>' for mode in AnalysisMode)
    page = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>음악 분석</title>
  <style>
    :root {{ color-scheme: light; --ink:#202124; --muted:#5f6368; --line:#dadce0; --accent:#0b57d0; --warn:#b3261e; --bg:#f8fafc; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, "Malgun Gothic", sans-serif; color: var(--ink); background: var(--bg); }}
    header {{ padding: 24px clamp(16px, 4vw, 44px); background: #fff; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0 0 8px; font-size: clamp(26px, 4vw, 38px); letter-spacing: 0; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 28px 16px 44px; }}
    form, .result {{ background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 20px; }}
    label {{ display: block; font-weight: 700; margin: 0 0 8px; }}
    input, select {{ width: 100%; min-height: 42px; border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; font: inherit; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 220px; gap: 16px; margin-top: 16px; align-items: end; }}
    button {{ margin-top: 18px; min-height: 44px; border: 0; border-radius: 6px; padding: 0 16px; background: var(--accent); color: #fff; font: inherit; font-weight: 700; cursor: pointer; }}
    .hint {{ color: var(--muted); margin: 0; }}
    .alert {{ margin-bottom: 16px; padding: 12px; border: 1px solid #f2b8b5; background: #fceeee; color: var(--warn); border-radius: 6px; }}
    .result {{ margin-top: 18px; }}
    .result-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 18px; }}
    .result-head h2 {{ margin: 0 0 6px; font-size: 24px; }}
    .result-head p {{ margin: 0; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 4px; }}
    .links a {{ color: var(--accent); font-weight: 700; }}
    .report-body {{ max-width: 820px; }}
    .report-body h2 {{ font-size: 22px; margin: 0 0 14px; }}
    .report-body h3 {{ font-size: 18px; margin: 24px 0 8px; }}
    .report-body h4 {{ font-size: 16px; margin: 18px 0 8px; }}
    .report-body ul {{ margin: 0 0 12px; padding-left: 20px; }}
    .report-body li {{ margin: 6px 0; line-height: 1.5; }}
    .progress {{ margin-top: 18px; padding: 20px; border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--muted); }}
    button:disabled {{ opacity: 0.6; cursor: default; }}
    @media (max-width: 680px) {{ .grid, .result-head {{ grid-template-columns: 1fr; display: grid; }} }}
  </style>
</head>
<body>
  <header>
    <h1>음악 분석</h1>
    <p class="hint">음원 파일을 올리면 분석 결과를 보여줍니다.</p>
  </header>
  <main>
    <form id="analyze-form" method="post" action="/analyze" enctype="multipart/form-data">
      <label for="audio">음원 파일</label>
      <input id="audio" name="audio" type="file" accept=".wav,.flac,.mp3,.ogg,.aiff,.aif,.aifc,.caf,audio/wav,audio/flac,audio/mpeg,audio/ogg,audio/aiff,audio/x-aiff" required>
      <div class="grid">
        <div>
          <label for="mode">분석 모드</label>
          <select id="mode" name="mode">{modes}</select>
        </div>
        <div>
          <button id="analyze-button" type="submit">분석하기</button>
        </div>
      </div>
    </form>
    <div id="result-container">{error_html}{result}</div>
  </main>
  <script>
    (function () {{
      var form = document.getElementById('analyze-form');
      var button = document.getElementById('analyze-button');
      var container = document.getElementById('result-container');
      var originalLabel = button.textContent;

      form.addEventListener('submit', function (event) {{
        event.preventDefault();
        button.disabled = true;
        button.textContent = '분석 중...';
        container.innerHTML = '<div class="progress">분석 중입니다. 파일 길이에 따라 시간이 걸릴 수 있습니다...</div>';
        fetch('/analyze', {{ method: 'POST', body: new FormData(form) }})
          .then(function (response) {{
            return response.text();
          }})
          .then(function (text) {{
            container.innerHTML = text;
          }})
          .catch(function () {{
            container.innerHTML = '<div class="alert">네트워크 오류로 분석에 실패했습니다. 다시 시도해 주세요.</div>';
          }})
          .then(function () {{
            button.disabled = false;
            button.textContent = originalLabel;
          }});
      }});
    }})();
  </script>
</body>
</html>"""
    return page.encode("utf-8")


class MusicInsightHandler(BaseHTTPRequestHandler):
    paths = WebPaths()

    def do_GET(self) -> None:
        parts = self.path.split("?", 1)
        request_path = parts[0]
        if request_path == "/":
            self._send_html(render_home())
            return
        if request_path == "/healthz":
            self._send_text(b"ok", content_type="text/plain; charset=utf-8")
            return
        if request_path.startswith("/reports/"):
            self._send_report(request_path)
            return
        if request_path == "/score":
            self._send_score_page(parts[1] if len(parts) > 1 else "")
            return
        if request_path in STATIC_FILES:
            self._send_static(request_path)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            validate_content_length(length, SECURITY_POLICY)
            body = self.rfile.read(length)
            form = parse_upload(self.headers.get("Content-Type", ""), body)
            links, verdict, score, korean_report = analyze_upload(
                form.audio,
                form.mode,
                form.target,
                self.paths,
                lyrics=form.lyrics,
                prompt=form.prompt,
            )
            fragment = render_user_result(links, verdict, score, korean_report)
            self._send_html(fragment.encode("utf-8"))
        except Exception as exc:
            error_fragment = f'<div class="alert">{html.escape(str(exc))}</div>'
            self._send_html(error_fragment.encode("utf-8"), status=HTTPStatus.BAD_REQUEST)

    def _send_html(self, body: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send_text(body, status=status, content_type="text/html; charset=utf-8")

    def _send_text(self, body: bytes, status: HTTPStatus = HTTPStatus.OK, content_type: str = "text/plain; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def _send_static(self, request_path: str) -> None:
        file_path, content_type = STATIC_FILES[request_path]
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        with file_path.open("rb") as source:
            shutil.copyfileobj(source, self.wfile)

    def _send_score_page(self, query_string: str) -> None:
        query = urllib.parse.parse_qs(query_string)
        src = (query.get("src") or [""])[0]
        parsed = parse_report_path(src)
        if not parsed or parsed[1] != "analysis_lead_sheet.musicxml":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send_html(render_score_page(src))

    def _send_report(self, request_path: str) -> None:
        parsed = parse_report_path(request_path)
        if not parsed:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        request_id, filename = parsed
        report_path = self.paths.outputs_dir / request_id / filename
        if not report_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if filename.endswith(".json"):
            content_type = "application/json; charset=utf-8"
        elif filename.endswith(".musicxml"):
            content_type = "application/xml; charset=utf-8"
        else:
            content_type = "text/markdown; charset=utf-8"
        body = report_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        with report_path.open("rb") as source:
            shutil.copyfileobj(source, self.wfile)

    def log_message(self, format: str, *args: object) -> None:
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="music-insight-web", description="Run the local Music Insight Studio web UI.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--uploads", type=Path, default=Path("uploads"))
    parser.add_argument("--outputs", type=Path, default=Path("outputs") / "web")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    MusicInsightHandler.paths = WebPaths(args.uploads, args.outputs)
    server = ThreadingHTTPServer((args.host, args.port), MusicInsightHandler)
    print(f"Music Insight Studio web UI: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web UI.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())




