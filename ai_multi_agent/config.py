import os
from pathlib import Path

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:
    find_dotenv = None
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# Search .env from the current working directory upward.
if find_dotenv and load_dotenv:
    load_dotenv(find_dotenv(usecwd=True, raise_error_if_not_found=False))

load_env_file(WORKSPACE_ROOT / ".env")
load_env_file(PROJECT_ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1536x1024")

def workspace_path(env_name: str, default_relative: str) -> Path:
    configured = os.getenv(env_name, "").strip()
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else (WORKSPACE_ROOT / path).resolve()
    return WORKSPACE_ROOT / default_relative


HERMES_ROOT = workspace_path("HERMES_ROOT", "ai_img_video_prompt")
INPUT_DIR = HERMES_ROOT / "input"
REFERENCE_DIR = HERMES_ROOT / "reference"
HERMES_OUTPUT_DIR = HERMES_ROOT / "output"

STORY_ROOT = workspace_path("STORY_ROOT", "ai_story")
STORY_OUTPUT_DIR = STORY_ROOT / "output"

SCENARIO_ROOT = workspace_path("SCENARIO_ROOT", "ai_Scenario")
SCENARIO_OUTPUT_DIR = SCENARIO_ROOT / "output"

ANIME_ROOT = workspace_path("ANIME_ROOT", "ai_anime")
ANIME_OUTPUT_DIR = ANIME_ROOT / "output"

WEBTOON_ROOT = workspace_path("WEBTOON_ROOT", "ai-webtoon")
WEBTOON_OUTPUT_DIR = WEBTOON_ROOT / "output"
WEBTOON_REFERENCE_DIR = WEBTOON_ROOT / "reference"
