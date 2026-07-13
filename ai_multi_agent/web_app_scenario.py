from __future__ import annotations

import threading
import webbrowser

from config import OPENROUTER_API_KEY, SCENARIO_OUTPUT_DIR
from main import scenario_managed_output_file, scenario_managed_summary
from web_app_scaffold import PromptRunnerConfig, create_prompt_runner_app

PORT = 5300

app = create_prompt_runner_app(PromptRunnerConfig(
    kind="scenario",
    port=PORT,
    title="Scenario Prompt Runner",
    sub_label=f"ai_Scenario/output · all scene prompts · port {PORT}",
    project_label="Scenario Projects",
    unit_dirname="scenes",
    unit_label_fmt="씬{:03d}",
    unit_heading="All Scene Prompts",
    accent_color="#4ea1ff",
    accent_dark_text="#07101d",
    output_dir=SCENARIO_OUTPUT_DIR,
    managed_summary=scenario_managed_summary,
    managed_output_file=scenario_managed_output_file,
    openrouter_api_key=OPENROUTER_API_KEY,
))


if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, use_reloader=False)
