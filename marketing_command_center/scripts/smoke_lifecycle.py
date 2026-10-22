"""Exercise startup, health, security headers, POST validation, port conflict, and clean shutdown."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    """Reserve an unused loopback port for the smoke run."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def post_status(url: str, payload: object) -> tuple[int, dict[str, object]]:
    """POST JSON and return the status and decoded body, including error statuses."""
    request = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode())
        except json.JSONDecodeError:
            return error.code, {}


def main() -> int:
    """Run a bounded end-to-end lifecycle verification."""
    port = free_port()
    command = [sys.executable, "serve.py", "--host", "127.0.0.1", "--port", str(port)]
    environment = os.environ.copy()
    environment.pop("OPENAI_API_KEY", None)
    first = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
    second = None
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(30):
            try:
                with urlopen(f"{base}/api/health", timeout=3) as response:
                    if response.status == 200 and json.loads(response.read().decode()).get("status") == "ok":
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("health endpoint did not become ready")
        with urlopen(f"{base}/", timeout=3) as response:
            page = response.read().decode()
            assert response.status == 200 and "Hermes Marketing Studio" in page
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Content-Security-Policy"]
            assert "no-cache" in response.headers["Cache-Control"], "stale cached pages break after an update"
        with urlopen(f"{base}/src/app.js", timeout=3) as response:
            assert response.headers["Content-Type"].startswith("text/javascript")
            assert "no-cache" in response.headers["Cache-Control"]
        with urlopen(f"{base}/api/health", timeout=3) as response:
            assert isinstance(json.loads(response.read().decode()).get("code_version"), int), "launcher needs code_version to detect a stale server"
        for private in ("/serve.py", "/logs/server.err.log", "/.env.example", "/README.md", "/scripts/start.ps1", "/tests/test_server.py", "/..%2fserve.py"):
            for method in ("GET", "HEAD"):
                try:
                    urlopen(Request(f"{base}{private}", method=method), timeout=3)
                    raise AssertionError(f"{method} {private} must not be served")
                except HTTPError as error:
                    assert error.code == 404, f"{method} {private} -> {error.code}"
        for public in ("/", "/index.html", "/styles.css", "/src/app.js", "/src/quality.js", "/assets/favicon.svg"):
            with urlopen(f"{base}{public}", timeout=3) as response:
                assert response.status == 200, public
        second = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
        assert second.wait(timeout=3) != 0, "second server unexpectedly acquired the same port"
        good = {"service": "Hermes", "description": "설명", "channel": "Threads", "text": "본문"}
        assert post_status(f"{base}/api/ai/draft", good)[0] == 503, "missing key must not call the network"
        assert post_status(f"{base}/api/ai/review", good)[0] == 503
        assert post_status(f"{base}/api/media", good)[0] == 404, "removed upload route must stay removed"
        print("PASS lifecycle: startup, health, headers, port conflict, key-less AI routes, shutdown")
        return 0
    finally:
        if second and second.poll() is None:
            second.terminate()
        first.terminate()
        try:
            first.wait(timeout=5)
        except subprocess.TimeoutExpired:
            first.kill()


if __name__ == "__main__":
    raise SystemExit(main())
