from __future__ import annotations

import json
from pathlib import Path

from app.core import EvaluationReport


class JsonReportWriter:
    def write(self, report: EvaluationReport, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "analysis_report.json"
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
