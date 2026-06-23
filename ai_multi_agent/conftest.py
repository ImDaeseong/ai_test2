"""
pytest 설정 — ai_multi_agent 단위 테스트 환경 초기화.
ai_multi_agent 디렉토리를 sys.path에 추가하여 내부 모듈을 import할 수 있도록 한다.

실행 방법 (반드시 프로젝트 디렉토리 안에서 실행):
    cd ai_multi_agent && python -m pytest tests_unit.py
루트 디렉토리에서 일괄 실행 시 다른 프로젝트의 main.py와 충돌할 수 있음.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def pytest_configure(config) -> None:
    # Windows 임시 폴더 권한 문제 우회 (pytest-of-sDev WinError 5)
    basetemp = Path(__file__).resolve().parent / ".pytest_tmp"
    basetemp.mkdir(exist_ok=True)
    try:
        config.option.basetemp = str(basetemp)
    except AttributeError:
        pass
