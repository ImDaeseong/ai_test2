from __future__ import annotations

import threading
import webbrowser

from config import OPENROUTER_API_KEY, STORY_OUTPUT_DIR
from main import story_managed_output_file, story_managed_summary
from web_app_scaffold import PromptRunnerConfig, create_prompt_runner_app

PORT = 5400

app = create_prompt_runner_app(PromptRunnerConfig(
    kind="story",
    port=PORT,
    title="Story Prompt Runner",
    sub_label=f"ai_story/output · all chapter prompts · port {PORT}",
    project_label="Story Projects",
    unit_dirname="chapters",
    unit_label_fmt="ch{:03d}",
    unit_heading="All Chapter Prompts",
    accent_color="#68d391",
    accent_dark_text="#07201a",
    output_dir=STORY_OUTPUT_DIR,
    managed_summary=story_managed_summary,
    managed_output_file=story_managed_output_file,
    openrouter_api_key=OPENROUTER_API_KEY,
))


if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, use_reloader=False)
