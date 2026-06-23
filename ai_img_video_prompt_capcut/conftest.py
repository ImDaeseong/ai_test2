"""
main.py 모듈 로드 시 Windows 전용 sys.stdout/stderr 교체 블록을
테스트 환경에서 건너뛰도록 sys.platform을 임시 변경한다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

_orig_platform = sys.platform
sys.platform = "_test"
import main  # noqa: E402
sys.platform = _orig_platform


def pytest_configure(config) -> None:
    # Windows 임시 폴더 권한 문제 우회 (ai_img_video_aiBoygirl과 동일)
    basetemp = Path(__file__).resolve().parent / ".pytest_tmp"
    basetemp.mkdir(exist_ok=True)
    try:
        config.option.basetemp = str(basetemp)
    except AttributeError:
        pass
