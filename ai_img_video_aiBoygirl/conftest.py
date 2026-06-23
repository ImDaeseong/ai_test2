"""pytest root conftest — main.py를 import 가능하게 경로 추가."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_configure(config) -> None:
    # Windows 임시 폴더 권한 문제 우회: 다른 사용자(pytest-of-sDev 등)가 소유한
    # %TEMP%\pytest-of-* 디렉터리에 접근하면 WinError 5가 발생한다.
    # 프로젝트 로컬 디렉터리를 basetemp로 지정해 회피한다.
    basetemp = Path(__file__).resolve().parent / ".pytest_tmp"
    basetemp.mkdir(exist_ok=True)
    try:
        config.option.basetemp = str(basetemp)
    except AttributeError:
        pass
