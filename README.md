# ai-tools

AI-assisted tools for music video production, storytelling, and content research.  
Five independent Python projects — from prompt generation to video editing automation.

---

## Projects

| Project | What it does | Python | API |
|---------|-------------|--------|-----|
| [ai_anime](./ai_anime/) | Per-song anime character + scene prompt generator (7 genre profiles, 6 image platforms) | 3.9+ | None |
| [ai_img_video_aiBoygirl](./ai_img_video_aiBoygirl/) | Fixed AI Boy/AI Girl robot character MV prompt builder (32 genre profiles, 22 reference PNGs) | 3.9+ | None |
| [ai_img_video_prompt_capcut](./ai_img_video_prompt_capcut/) | Auto-generates CapCut editing timeline from Suno LRC + Kling video clips | 3.9+ | None |
| [ai_multi_agent](./ai_multi_agent/) | Prompt runner with 5 web UIs — story, scenario, MV, anime, webtoon | 3.8+ | OpenRouter (required) / OpenAI (optional) |
| [youtube_research](./youtube_research/) | YouTube AI music channel benchmarking — metadata collection, AI-only filtering, markdown reports | 3.8+ | yt-dlp (free) |

---

## How These Tools Connect

Three of the tools form a music video production pipeline:

```
ai_img_video_aiBoygirl
  └─ 09_video_motion_prompts.md  (CapCut Editing Map)
        │
        ▼
ai_img_video_prompt_capcut
  + Suno audio (.wav)
  + Suno lyrics (.lrc)
  + Kling-generated clips (.mp4)
        │
        ▼
  timeline.json + shot_list.md
        │
        ▼
  CapCut PC — auto-created draft project

ai_anime  ──→  anime scene + character prompts
              (can be run through ai_multi_agent web UI)

youtube_research  ──→  benchmark competitor channels independently
```

---

## Quick Start

### No API key needed (3 projects)

```bash
# Anime MV prompts — unique character per song
cd ai_anime
python main.py create-all --force

# AI Boy/AI Girl MV prompts — fixed robot characters, 32 genres
cd ../ai_img_video_aiBoygirl
python main.py create-all --input-dir input --force

# YouTube AI channel benchmarking
cd ../youtube_research
pip install yt-dlp
python run.py search 30       # collect → filter → thumbnail → report
# open output/reports/report_날짜.md
```

### CapCut automation (after generating video clips in Kling AI)

```bash
cd ai_img_video_prompt_capcut
pip install click mutagen
# place audio + LRC + clips in input/{song}/
python main.py inspect --song MySong   # check inputs
python main.py build   --song MySong   # generate timeline.json
python main.py export-draft --song MySong   # create CapCut project
```

### ai_multi_agent (OpenRouter API key required)

```bash
cd ai_multi_agent
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set OPENROUTER_API_KEY=sk-or-...
python web_app_mv.py       # http://127.0.0.1:5200  MV prompts
python web_app_anime.py    # http://127.0.0.1:5500  Anime prompts
```

Get a free OpenRouter API key at https://openrouter.ai/keys

---

## Requirements

- Python 3.9+ (3.8+ for `ai_multi_agent` and `youtube_research`)
- Each project folder contains its own `requirements.txt` or install instructions

---

## Running Tests

```bash
cd ai_anime                    && python -m pytest tests_unit.py -q
cd ../ai_img_video_aiBoygirl   && python -m pytest -q
cd ../ai_img_video_prompt_capcut && python -m pytest tests_unit.py -q
cd ../ai_multi_agent           && python -m pytest tests_unit.py -q
cd ../youtube_research         && python -m pytest tests_unit.py -q
```

---

## License

MIT
