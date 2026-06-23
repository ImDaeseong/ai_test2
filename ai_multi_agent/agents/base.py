from __future__ import annotations

import time

from config import MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL

_MAX_RETRIES = 3
_RETRY_DELAY = 5  # seconds


def strip_code_fence(text: str) -> str:
    """Claude가 JSON 앞뒤에 붙이는 마크다운 코드 블록을 제거한다."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        end = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), None)
        if end is not None:
            return "\n".join(lines[1:end]).strip()
    return stripped


def sanitize_text(text: str) -> str:
    """단독 서로게이트 문자를 제거해 JSON 직렬화 오류를 방지한다."""
    return text.encode("utf-8", errors="replace").decode("utf-8")


def call_agent(system: str, user_content: str, max_tokens: int = 4096) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지가 없습니다. `pip install -r requirements.txt`를 먼저 실행하세요.") from exc

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=max_tokens,
                timeout=60,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError(f"모델 응답이 비어 있습니다. 모델: {MODEL}")
            return content
        except ValueError:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
    raise RuntimeError(f"API 호출 {_MAX_RETRIES}회 모두 실패: {last_exc}") from last_exc
