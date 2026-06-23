from __future__ import annotations

import base64
from pathlib import Path
from urllib.request import urlopen

from config import IMAGE_MODEL, IMAGE_SIZE, OPENAI_API_KEY


def generate_image_file(prompt: str, output_file: Path) -> Path:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지가 없습니다. `pip install -r requirements.txt`를 먼저 실행하세요.") from exc

    if not OPENAI_API_KEY:
        raise ValueError(".env에 OPENAI_API_KEY가 없습니다.")
    if not prompt.strip():
        raise ValueError("이미지 프롬프트가 비어 있습니다.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
    )
    image = response.data[0]
    image_data = getattr(image, "b64_json", None)
    image_url = getattr(image, "url", None)
    if image_data:
        image_bytes = base64.b64decode(image_data)
    elif image_url:
        with urlopen(image_url) as r:
            image_bytes = r.read()
    else:
        raise ValueError("이미지 생성 응답이 비어 있습니다.")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(image_bytes)
    return output_file
