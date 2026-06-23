import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def pytest_configure(config) -> None:
    basetemp = Path(__file__).resolve().parent / ".pytest_tmp"
    basetemp.mkdir(exist_ok=True)
    try:
        config.option.basetemp = str(basetemp)
    except AttributeError:
        pass
