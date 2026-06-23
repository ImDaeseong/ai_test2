from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from agents import run_script, run_image, run_video, run_reviewer
from agents.base import call_agent, sanitize_text
from config import HERMES_OUTPUT_DIR, INPUT_DIR, OUTPUT_DIR, SCENARIO_OUTPUT_DIR, STORY_OUTPUT_DIR, WORKSPACE_ROOT


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(errors="replace")
            except (OSError, ValueError):
                pass


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def song_slug(title: str) -> str:
    forbidden = '<>:"/\\|?*'
    slug = "".join("_" if c in forbidden else c for c in title).strip().strip(".")
    if not slug:
        raise ValueError("폴더 이름으로 사용할 수 없는 곡 제목입니다.")
    return slug


def safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT.resolve()))
    except ValueError:
        return str(path)
    except OSError:
        return str(path)


def project_dirs(output_dir: Path) -> list[Path]:
    if not output_dir.exists():
        return []
    return sorted([p for p in output_dir.iterdir() if p.is_dir()], key=lambda p: p.name)


def find_project(output_dir: Path, name: str | None) -> Path | None:
    projects = project_dirs(output_dir)
    if not projects:
        return None
    if not name:
        return max(projects, key=lambda p: p.stat().st_mtime)

    direct = output_dir / name
    if direct.exists() and direct.is_dir():
        return direct

    normalized = name.replace(" ", "_")
    for project in projects:
        state = safe_read_json(project / "state.json")
        title = str(state.get("title", ""))
        if project.name == normalized or title == name or normalized in project.name or name in title:
            return project
    return None


def story_summary(project_dir: Path) -> dict:
    state = safe_read_json(project_dir / "state.json")
    chapters_dir = project_dir / "chapters"
    prompt_files = sorted(chapters_dir.glob("ch*_GPT_프롬프트.md")) if chapters_dir.exists() else []
    gpt_outputs = sorted(chapters_dir.glob("ch*_GPT_출력.md")) if chapters_dir.exists() else []
    final_outputs = sorted(chapters_dir.glob("ch*_완성.md")) if chapters_dir.exists() else []
    total = int(state.get("total_chapters") or len(prompt_files) or 0)
    current = int(state.get("current_chapter") or 0)
    next_num = current + 1 if current < total else None
    next_file = chapters_dir / f"ch{next_num:03d}_GPT_프롬프트.md" if next_num else None
    return {
        "mode": "story",
        "project_dir": project_dir,
        "title": state.get("title", project_dir.name),
        "total": total,
        "current": current,
        "settings": (project_dir / "설정집.md").exists(),
        "prompts": len(prompt_files),
        "gpt_outputs": len(gpt_outputs),
        "final_outputs": len(final_outputs),
        "next_num": next_num,
        "next_file": next_file if next_file and next_file.exists() else None,
    }


def scenario_summary(project_dir: Path) -> dict:
    state = safe_read_json(project_dir / "state.json")
    scenes_dir = project_dir / "scenes"
    prompt_files = sorted(scenes_dir.glob("씬*_GPT_프롬프트.md")) if scenes_dir.exists() else []
    gpt_outputs = sorted(scenes_dir.glob("씬*_GPT_출력.md")) if scenes_dir.exists() else []
    final_outputs = sorted(scenes_dir.glob("씬*_완성.md")) if scenes_dir.exists() else []
    total = int(state.get("total_scenes") or len(prompt_files) or 0)
    current = int(state.get("current_scene") or 0)
    next_num = current + 1 if current < total else None
    next_file = scenes_dir / f"씬{next_num:03d}_GPT_프롬프트.md" if next_num else None
    return {
        "mode": "scenario",
        "project_dir": project_dir,
        "title": state.get("title", project_dir.name),
        "total": total,
        "current": current,
        "settings": (project_dir / "설정집.md").exists(),
        "prompts": len(prompt_files),
        "gpt_outputs": len(gpt_outputs),
        "final_outputs": len(final_outputs),
        "next_num": next_num,
        "next_file": next_file if next_file and next_file.exists() else None,
    }


def story_managed_output_file(project_dir: Path, chapter_num: int) -> Path:
    return OUTPUT_DIR / "story" / project_dir.name / "chapters" / f"ch{chapter_num:03d}_GPT_출력.md"


def scenario_managed_output_file(project_dir: Path, scene_num: int) -> Path:
    return OUTPUT_DIR / "scenario" / project_dir.name / "scenes" / f"씬{scene_num:03d}_GPT_출력.md"


# ─────────────────────────────────────────
# 롤링 요약 치환 (story/scenario 원본 프롬프트 파일 업데이트)
# ─────────────────────────────────────────

ROLLING_PLACEHOLDER = "%%ROLLING_SUMMARY%%"
LAST_SENTENCE_PLACEHOLDER = "%%LAST_SENTENCE%%"
LAST_LINE_PLACEHOLDER = "%%LAST_LINE%%"


def _apply_rolling_story(prompt_file: Path, summaries: list[dict], last_sentence: str) -> bool:
    if not prompt_file.exists():
        return False
    content = prompt_file.read_text(encoding="utf-8")
    if ROLLING_PLACEHOLDER not in content and LAST_SENTENCE_PLACEHOLDER not in content:
        return False
    recent = summaries[-3:]
    rolling = "\n".join(f"ch{s['chapter']:02d} 요약: {s['summary']}" for s in recent) + "\n"
    content = content.replace(ROLLING_PLACEHOLDER, rolling)
    content = content.replace(LAST_SENTENCE_PLACEHOLDER, f'"{last_sentence}"')
    write_file(prompt_file, content)
    return True


def _apply_rolling_scenario(prompt_file: Path, summaries: list[dict], last_line: str) -> bool:
    if not prompt_file.exists():
        return False
    content = prompt_file.read_text(encoding="utf-8")
    if ROLLING_PLACEHOLDER not in content and LAST_LINE_PLACEHOLDER not in content:
        return False
    recent = summaries[-3:]
    rolling = "\n".join(f"씬{s['scene']:03d} 요약: {s['summary']}" for s in recent) + "\n"
    content = content.replace(ROLLING_PLACEHOLDER, rolling)
    content = content.replace(LAST_LINE_PLACEHOLDER, f'"{last_line}"')
    write_file(prompt_file, content)
    return True


def _ask_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def story_managed_summary(project_dir: Path) -> dict:
    summary = story_summary(project_dir)
    total = int(summary["total"] or 0)
    current = 0
    next_num = None
    next_file = None

    for chapter_num in range(1, total + 1):
        prompt_file = project_dir / "chapters" / f"ch{chapter_num:03d}_GPT_프롬프트.md"
        if story_managed_output_file(project_dir, chapter_num).exists():
            current += 1
            continue
        if next_num is None and prompt_file.exists():
            next_num = chapter_num
            next_file = prompt_file

    return {
        **summary,
        "current": current,
        "gpt_outputs": current,
        "next_num": next_num,
        "next_file": next_file,
        "managed_output_dir": OUTPUT_DIR / "story" / project_dir.name,
    }


def scenario_managed_summary(project_dir: Path) -> dict:
    summary = scenario_summary(project_dir)
    total = int(summary["total"] or 0)
    current = 0
    next_num = None
    next_file = None

    for scene_num in range(1, total + 1):
        prompt_file = project_dir / "scenes" / f"씬{scene_num:03d}_GPT_프롬프트.md"
        if scenario_managed_output_file(project_dir, scene_num).exists():
            current += 1
            continue
        if next_num is None and prompt_file.exists():
            next_num = scene_num
            next_file = prompt_file

    return {
        **summary,
        "current": current,
        "gpt_outputs": current,
        "next_num": next_num,
        "next_file": next_file,
        "managed_output_dir": OUTPUT_DIR / "scenario" / project_dir.name,
    }


def print_project_summary(summary: dict) -> None:
    unit = "챕터" if summary["mode"] == "story" else "씬"
    print(f"제목: {summary['title']}")
    print(f"위치: {display_path(summary['project_dir'])}")
    print(f"진행: {summary['current']}/{summary['total']} {unit}")
    print(f"설정집: {'있음' if summary['settings'] else '없음'}")
    print(f"GPT 프롬프트: {summary['prompts']}/{summary['total']}")
    print(f"GPT 출력: {summary['gpt_outputs']}개")
    print(f"완성본: {summary['final_outputs']}개")
    next_file = summary["next_file"]
    print(f"다음 작업: {display_path(next_file) if next_file else '없음'}")


def command_story_list(args: argparse.Namespace) -> int:
    projects = project_dirs(Path(args.output_dir))
    if not projects:
        print("ai_story output 프로젝트가 없습니다.")
        return 1
    for index, project in enumerate(projects, 1):
        summary = story_managed_summary(project)
        print(f"{index}. {summary['title']}  ch{summary['current']:02d}/{summary['total']:02d}  ({project.name})")
    return 0


def command_story_status(args: argparse.Namespace) -> int:
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_story 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    print_project_summary(story_managed_summary(project))
    return 0


def command_story_next(args: argparse.Namespace) -> int:
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_story 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    summary = story_managed_summary(project)
    next_file = summary["next_file"]
    if not next_file:
        print("다음 챕터 프롬프트가 없습니다.")
        return 1
    print_project_summary(summary)
    if args.show:
        print("\n" + next_file.read_text(encoding="utf-8"))
    return 0


def run_prompt_once(prompt_file: Path, output_file: Path, mode: str, force: bool, max_tokens: int) -> Path:
    if output_file.exists() and not force:
        raise FileExistsError(f"이미 GPT 출력 파일이 있습니다: {display_path(output_file)}")
    prompt = prompt_file.read_text(encoding="utf-8")
    system = (
        "당신은 전문 작가 AI입니다. 사용자가 제공한 프롬프트의 지시를 정확히 따라 "
        "요구된 출력 형식으로만 작성하세요."
        if mode == "story"
        else "당신은 전문 시나리오 작가 AI입니다. 사용자가 제공한 프롬프트의 지시를 정확히 따라 "
        "요구된 출력 형식으로만 작성하세요."
    )
    result = call_agent(system, prompt, max_tokens=max_tokens)
    write_file(output_file, result)
    return output_file


def command_story_run(args: argparse.Namespace) -> int:
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_story 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    summary = story_managed_summary(project)
    next_file = summary["next_file"]
    next_num = summary["next_num"]
    if not next_file or not next_num:
        print("실행할 다음 챕터 프롬프트가 없습니다.")
        return 1
    output_file = story_managed_output_file(project, next_num)
    print_project_summary(summary)
    print(f"\nGPT 실행 대상: {display_path(next_file)}")
    print(f"저장 예정: {display_path(output_file)}")
    if args.dry_run:
        print("dry-run: API 호출 없이 종료합니다.")
        return 0
    try:
        saved = run_prompt_once(next_file, output_file, "story", args.force, args.max_tokens)
    except Exception as exc:
        print(f"GPT 실행 실패: {exc}", file=sys.stderr)
        return 1
    print(f"GPT 출력 저장 완료: {display_path(saved)}")
    print(f"다음 단계: ai_story에서 `python story.py finish {next_num}` 실행")
    return 0


def command_scenario_list(args: argparse.Namespace) -> int:
    projects = project_dirs(Path(args.output_dir))
    if not projects:
        print("ai_Scenario output 프로젝트가 없습니다.")
        return 1
    for index, project in enumerate(projects, 1):
        summary = scenario_managed_summary(project)
        print(f"{index}. {summary['title']}  씬{summary['current']:03d}/{summary['total']:03d}  ({project.name})")
    return 0


def command_scenario_status(args: argparse.Namespace) -> int:
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_Scenario 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    print_project_summary(scenario_managed_summary(project))
    return 0


def command_scenario_next(args: argparse.Namespace) -> int:
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_Scenario 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    summary = scenario_managed_summary(project)
    next_file = summary["next_file"]
    if not next_file:
        print("다음 씬 프롬프트가 없습니다.")
        return 1
    print_project_summary(summary)
    if args.show:
        print("\n" + next_file.read_text(encoding="utf-8"))
    return 0


def command_story_save_output(args: argparse.Namespace) -> int:
    """GPT 출력 저장 후 ai_story 원본 state.json에 롤링 요약 반영."""
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_story 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    summary = story_managed_summary(project)

    # 가장 최근에 완료된 챕터 번호 확인
    last_done = None
    for n in range(1, int(summary["total"] or 0) + 1):
        if story_managed_output_file(project, n).exists():
            last_done = n

    if args.chapter:
        target_num = args.chapter
    elif last_done:
        target_num = last_done
    else:
        print("저장된 GPT 출력 파일이 없습니다.", file=sys.stderr)
        return 1

    output_file = story_managed_output_file(project, target_num)
    if not output_file.exists():
        print(f"GPT 출력 파일이 없습니다: {display_path(output_file)}", file=sys.stderr)
        return 1

    state = safe_read_json(project / "state.json")
    total = int(state.get("total_chapters") or summary["total"] or 0)

    print(f"\n{'━'*50}")
    print(f"  {state.get('title', project.name)} — ch{target_num:03d} 저장")
    print(f"{'━'*50}")
    print(f"GPT 출력 파일: {display_path(output_file)}")
    print()

    # 요약과 마지막 문장 입력
    summary_text = _ask_input(f"ch{target_num:03d} 요약 (3줄 이내): ")
    if not summary_text:
        print("요약을 입력해야 합니다.", file=sys.stderr)
        return 1
    last_sentence = _ask_input("다음 프롬프트에 넣을 마지막 문장 (정확히): ")
    if not last_sentence:
        print("마지막 문장을 입력해야 합니다.", file=sys.stderr)
        return 1

    # state.json 업데이트
    summaries = [s for s in state.get("rolling_summaries", []) if s.get("chapter") != target_num]
    summaries.append({"chapter": target_num, "summary": summary_text})
    summaries.sort(key=lambda s: s["chapter"])
    state["rolling_summaries"] = summaries
    state["last_sentence"] = last_sentence
    state["current_chapter"] = max(int(state.get("current_chapter") or 0), target_num)
    write_file(project / "state.json",
               json.dumps(state, ensure_ascii=False, indent=2))

    # 다음 챕터 프롬프트에 롤링 요약 반영
    next_n = target_num + 1
    if next_n <= total:
        next_prompt = project / "chapters" / f"ch{next_n:03d}_GPT_프롬프트.md"
        if _apply_rolling_story(next_prompt, summaries, last_sentence):
            print(f"✓ ch{next_n:03d}_GPT_프롬프트.md 롤링 요약 반영 완료")
        else:
            print(f"  ch{next_n:03d}_GPT_프롬프트.md: placeholder 없음 (이미 반영됐거나 없음)")

    print(f"✓ ch{target_num:03d} 저장 완료 (ai_story state.json 갱신)")
    if next_n <= total:
        print(f"  다음: python main.py story run \"{state.get('title', project.name)}\"")
    else:
        print(f"  전체 {total}챕터 완성!")
    return 0


def command_scenario_save_output(args: argparse.Namespace) -> int:
    """GPT 출력 저장 후 ai_Scenario 원본 state.json에 롤링 요약 반영."""
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_Scenario 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    sc_summary = scenario_managed_summary(project)

    last_done = None
    for n in range(1, int(sc_summary["total"] or 0) + 1):
        if scenario_managed_output_file(project, n).exists():
            last_done = n

    if args.scene:
        target_num = args.scene
    elif last_done:
        target_num = last_done
    else:
        print("저장된 GPT 출력 파일이 없습니다.", file=sys.stderr)
        return 1

    output_file = scenario_managed_output_file(project, target_num)
    if not output_file.exists():
        print(f"GPT 출력 파일이 없습니다: {display_path(output_file)}", file=sys.stderr)
        return 1

    state = safe_read_json(project / "state.json")
    total = int(state.get("total_scenes") or sc_summary["total"] or 0)

    print(f"\n{'━'*50}")
    print(f"  {state.get('title', project.name)} — 씬{target_num:03d} 저장")
    print(f"{'━'*50}")
    print(f"GPT 출력 파일: {display_path(output_file)}")
    print()

    summary_text = _ask_input(f"씬{target_num:03d} 요약 (2줄 이내): ")
    if not summary_text:
        print("요약을 입력해야 합니다.", file=sys.stderr)
        return 1
    last_line = _ask_input("완성본 마지막 라인 (정확히): ")
    if not last_line:
        print("마지막 라인을 입력해야 합니다.", file=sys.stderr)
        return 1

    summaries = [s for s in state.get("rolling_summaries", []) if s.get("scene") != target_num]
    summaries.append({"scene": target_num, "summary": summary_text})
    summaries.sort(key=lambda s: s["scene"])
    state["rolling_summaries"] = summaries
    state["last_line"] = last_line
    state["current_scene"] = max(int(state.get("current_scene") or 0), target_num)
    write_file(project / "state.json",
               json.dumps(state, ensure_ascii=False, indent=2))

    next_n = target_num + 1
    if next_n <= total:
        next_prompt = project / "scenes" / f"씬{next_n:03d}_GPT_프롬프트.md"
        if _apply_rolling_scenario(next_prompt, summaries, last_line):
            print(f"✓ 씬{next_n:03d}_GPT_프롬프트.md 롤링 요약 반영 완료")
        else:
            print(f"  씬{next_n:03d}_GPT_프롬프트.md: placeholder 없음")

    print(f"✓ 씬{target_num:03d} 저장 완료 (ai_Scenario state.json 갱신)")
    if next_n <= total:
        print(f"  다음: python main.py scenario run \"{state.get('title', project.name)}\"")
    else:
        print(f"  전체 {total}씬 완성!")
    return 0


def command_scenario_run(args: argparse.Namespace) -> int:
    project = find_project(Path(args.output_dir), args.name)
    if not project:
        print("ai_Scenario 프로젝트를 찾을 수 없습니다.", file=sys.stderr)
        return 1
    summary = scenario_managed_summary(project)
    next_file = summary["next_file"]
    next_num = summary["next_num"]
    if not next_file or not next_num:
        print("실행할 다음 씬 프롬프트가 없습니다.")
        return 1
    output_file = scenario_managed_output_file(project, next_num)
    print_project_summary(summary)
    print(f"\nGPT 실행 대상: {display_path(next_file)}")
    print(f"저장 예정: {display_path(output_file)}")
    if args.dry_run:
        print("dry-run: API 호출 없이 종료합니다.")
        return 0
    try:
        saved = run_prompt_once(next_file, output_file, "scenario", args.force, args.max_tokens)
    except Exception as exc:
        print(f"GPT 실행 실패: {exc}", file=sys.stderr)
        return 1
    print(f"GPT 출력 저장 완료: {display_path(saved)}")
    print(f"다음 단계: ai_Scenario에서 `python scenario.py finish {next_num}` 실행")
    return 0


# ─────────────────────────────────────────
# MV CLI — 곡별 파트 진행 관리
# ─────────────────────────────────────────

MV_PARTS = [
    ("01_vocal",  "03_vocal_image_prompt.md",  "보컬",    "보컬 영상"),
    ("02_guitar", "04_guitar_image_prompt.md",  "기타",    "기타 영상"),
    ("03_bass",   "05_bass_image_prompt.md",    "베이스",  "베이스 영상"),
    ("04_drum",   "06_drum_image_prompt.md",    "드럼",    "드럼 영상"),
    ("05_stage",  "07_stage_image_prompt.md",   "전체 무대", "전체 무대 영상"),
    ("06_crowd",  "08_crowd_image_prompt.md",   "관객",    "군중 영상"),
]


def _mv_song_dir(name: str) -> Path:
    return HERMES_OUTPUT_DIR / name


def _mv_output_dir(name: str) -> Path:
    return OUTPUT_DIR / "mv" / name


def _mv_part_dir(name: str, part_key: str) -> Path:
    return _mv_output_dir(name) / "parts" / part_key


def _mv_part_status(name: str, part_key: str) -> dict:
    part_dir = _mv_part_dir(name, part_key)
    bundled = (part_dir / "image_prompt.md").exists()
    has_image = (part_dir / "image.png").exists()
    done = False
    sf = part_dir / "status.json"
    if sf.exists():
        try:
            done = safe_read_json(sf).get("done", False)
        except Exception:
            pass
    return {"bundled": bundled, "has_image": has_image, "done": done, "part_dir": part_dir}


def _mv_extract_video_section(video_file: Path, section: str) -> str:
    import re
    if not video_file.exists():
        return ""
    content = video_file.read_text(encoding="utf-8")
    m = re.search(rf"## {re.escape(section)}\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    return m.group(1).strip() if m else ""


def _mv_prepare_part(name: str, part_key: str) -> Path:
    song_dir = _mv_song_dir(name)
    part = next((p for p in MV_PARTS if p[0] == part_key), None)
    if not part:
        raise ValueError(f"알 수 없는 파트: {part_key}")
    _, img_file, _, video_section = part
    part_dir = _mv_part_dir(name, part_key)
    part_dir.mkdir(parents=True, exist_ok=True)

    img_path = song_dir / img_file
    if img_path.exists():
        (part_dir / "image_prompt.md").write_text(
            img_path.read_text(encoding="utf-8"), encoding="utf-8")

    video_file = song_dir / "09_video_motion_prompts.md"
    video_content = _mv_extract_video_section(video_file, video_section)
    if video_content:
        (part_dir / "video_prompt.md").write_text(video_content, encoding="utf-8")

    sf = part_dir / "status.json"
    if not sf.exists():
        sf.write_text(json.dumps({"done": False}, ensure_ascii=False), encoding="utf-8")
    return part_dir


def command_mv_songs(args: argparse.Namespace) -> int:
    """ai_img_video_prompt/output 곡 목록 표시."""
    if not HERMES_OUTPUT_DIR.exists():
        print(f"Hermes output 폴더가 없습니다: {HERMES_OUTPUT_DIR}", file=sys.stderr)
        return 1
    songs = sorted([d for d in HERMES_OUTPUT_DIR.iterdir() if d.is_dir()])
    if not songs:
        print("처리된 곡이 없습니다.")
        return 1
    print(f"\n{'━'*50}")
    print(f"  MV 곡 목록 ({len(songs)}곡)")
    print(f"{'━'*50}")
    for i, song in enumerate(songs, 1):
        parts_done = sum(
            1 for p in MV_PARTS
            if _mv_part_status(song.name, p[0])["has_image"]
        )
        print(f"  {i:2d}. {song.name}  [{parts_done}/{len(MV_PARTS)} 파트 이미지 완료]")
    return 0


def command_mv_prepare(args: argparse.Namespace) -> int:
    """선택한 곡의 파트별 작업 폴더와 프롬프트 파일을 생성한다."""
    name = args.song
    song_dir = _mv_song_dir(name)
    if not song_dir.exists():
        print(f"곡 폴더가 없습니다: {song_dir}", file=sys.stderr)
        return 1
    print(f"\n{name} — 파트 폴더 준비 중...")
    for part_key, _, label, _ in MV_PARTS:
        part_dir = _mv_prepare_part(name, part_key)
        status = _mv_part_status(name, part_key)
        img_mark = "✓" if status["has_image"] else "○"
        prompt_mark = "✓" if status["bundled"] else "✗"
        print(f"  [{img_mark}이미지] [{prompt_mark}프롬프트] {part_key} ({label})  → {display_path(part_dir)}")
    print(f"\n✓ 준비 완료. 다음: python main.py mv next {name}")
    return 0


def command_mv_next(args: argparse.Namespace) -> int:
    """다음 미완료 파트의 이미지 프롬프트를 출력한다."""
    name = args.song
    song_dir = _mv_song_dir(name)
    if not song_dir.exists():
        print(f"곡 폴더가 없습니다: {song_dir}", file=sys.stderr)
        return 1
    for part_key, _, label, _ in MV_PARTS:
        status = _mv_part_status(name, part_key)
        if status["has_image"]:
            continue
        part_dir = _mv_part_dir(name, part_key)
        prompt_file = part_dir / "image_prompt.md"
        if not prompt_file.exists():
            _mv_prepare_part(name, part_key)
        print(f"\n다음 작업: {part_key} ({label})")
        print(f"이미지 프롬프트: {display_path(prompt_file)}")
        if args.show and prompt_file.exists():
            print("\n" + prompt_file.read_text(encoding="utf-8"))
        print(f"\n완료 후: python main.py mv attach {name} {part_key} <image.png 경로>")
        return 0
    print(f"✓ {name} — 전체 {len(MV_PARTS)}개 파트 이미지 완료")
    return 0


def command_mv_attach(args: argparse.Namespace) -> int:
    """생성된 이미지를 파트 폴더에 등록하고 상태를 갱신한다."""
    import shutil
    name = args.song
    part_key = args.part
    image_src = Path(args.image)
    if not image_src.exists():
        print(f"이미지 파일이 없습니다: {image_src}", file=sys.stderr)
        return 1
    part_dir = _mv_part_dir(name, part_key)
    part_dir.mkdir(parents=True, exist_ok=True)
    dest = part_dir / "image.png"
    shutil.copy2(image_src, dest)
    sf = part_dir / "status.json"
    sf.write_text(json.dumps({"done": True}, ensure_ascii=False), encoding="utf-8")
    print(f"✓ 이미지 등록: {display_path(dest)}")
    status = _mv_part_status(name, part_key)
    video_prompt = part_dir / "video_prompt.md"
    if video_prompt.exists():
        print(f"  비디오 프롬프트: {display_path(video_prompt)}")
    print(f"\n다음: python main.py mv next {name}")
    return 0


def command_mv_status(args: argparse.Namespace) -> int:
    """MV 파트별 진행률을 표시한다."""
    name = args.song
    song_dir = _mv_song_dir(name)
    if not song_dir.exists():
        print(f"곡 폴더가 없습니다: {song_dir}", file=sys.stderr)
        return 1
    print(f"\n{'━'*50}")
    print(f"  {name}")
    print(f"{'━'*50}")
    done_count = 0
    for part_key, _, label, _ in MV_PARTS:
        status = _mv_part_status(name, part_key)
        img = "✓" if status["has_image"] else "○"
        prm = "✓" if status["bundled"] else "✗"
        vid = "✓" if (status["part_dir"] / "video_prompt.md").exists() else "✗"
        if status["has_image"]:
            done_count += 1
        print(f"  {part_key} ({label:<8})  이미지:{img}  프롬프트:{prm}  비디오:{vid}")
    print(f"\n  진행: {done_count}/{len(MV_PARTS)} 파트 이미지 완료")
    return 0


def run_pipeline(song_path: Path, output_dir: Path, force: bool = False) -> tuple[bool, str]:
    song_text = sanitize_text(song_path.read_text(encoding="utf-8-sig"))
    title = song_path.stem

    dest = output_dir / song_slug(title)
    if dest.exists() and not force:
        return False, f"폴더가 이미 존재합니다: {dest}. --force 옵션을 사용하세요."

    dest.mkdir(parents=True, exist_ok=True)

    print("  [1/4] ScriptAgent — 장면 구성 중...")
    script_result = run_script(song_text)
    write_file(dest / "01_script.json", script_result)

    print("  [2/4] ImageAgent — 이미지 프롬프트 생성 중...")
    image_result = run_image(script_result)
    write_file(dest / "02_image_prompts.md", image_result)

    print("  [3/4] VideoAgent — 영상 모션 프롬프트 생성 중...")
    video_result = run_video(script_result, image_result)
    write_file(dest / "03_video_prompts.md", video_result)

    print("  [4/4] ReviewerAgent — 검수 중...")
    review_result = run_reviewer(script_result, image_result, video_result)
    write_file(dest / "04_review.md", review_result)

    return True, str(dest)


def command_create(args: argparse.Namespace) -> int:
    song_path = Path(args.input)
    if not song_path.exists():
        print(f"파일이 없습니다: {song_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    print(f"\n{song_path.name} 처리 시작...")
    try:
        success, message = run_pipeline(song_path, output_dir, args.force)
        print(f"\n{'완료' if success else '건너뜀'}: {message}")
        return 0 if success else 1
    except Exception as exc:
        print(f"\n오류: {exc}", file=sys.stderr)
        return 1


def command_create_all(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"입력 폴더가 없습니다: {input_dir}", file=sys.stderr)
        return 1

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print(f"처리할 txt 파일이 없습니다: {input_dir}")
        return 1

    output_dir = Path(args.output_dir)
    total = len(files)
    failed: list[tuple[str, str]] = []

    print(f"입력 파일 {total}개 처리 시작: {input_dir}\n")
    for index, song_path in enumerate(files, start=1):
        print(f"[{index}/{total}] {song_path.name}")
        try:
            success, message = run_pipeline(song_path, output_dir, args.force)
            if success:
                print(f"  완료: {message}\n")
            else:
                print(f"  건너뜀: {message}\n")
                failed.append((song_path.name, message))
        except Exception as exc:
            print(f"  오류: {exc}\n")
            failed.append((song_path.name, str(exc)))

    print(f"\n처리 완료: 성공 {total - len(failed)}개, 실패 {len(failed)}개")
    if failed:
        print("실패 목록:")
        for name, reason in failed:
            print(f"  - {name}: {reason}")
        return 1
    return 0


REQUIRED_OUTPUT_FILES = [
    "01_script.json",
    "02_image_prompts.md",
    "03_video_prompts.md",
    "04_review.md",
]


PLACEHOLDER_CHECK_FILES = ["01_script.json", "02_image_prompts.md", "03_video_prompts.md"]
MANAGED_OUTPUT_DIR_NAMES = {"mv", "story", "scenario"}


def validate_output(folder: Path) -> tuple[bool, list[str]]:
    missing = [f for f in REQUIRED_OUTPUT_FILES if not (folder / f).exists()]
    placeholder_hits: list[str] = []
    for fname in PLACEHOLDER_CHECK_FILES:
        fpath = folder / fname
        if fpath.exists():
            text = fpath.read_text(encoding="utf-8", errors="replace")
            if any(p in text for p in ("{title}", "{prompt}", "{section_label}")):
                placeholder_hits.append(fname)
    issues = [f"누락: {f}" for f in missing] + [f"placeholder 잔여: {f}" for f in placeholder_hits]
    return len(issues) == 0, issues


def command_validate(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    folders = (
        sorted([d for d in output_dir.iterdir() if d.is_dir() and d.name not in MANAGED_OUTPUT_DIR_NAMES])
        if args.folder is None
        else [Path(args.folder)]
    )

    if not folders:
        print("검증할 output 폴더가 없습니다.")
        return 1

    total, passed, failed_list = len(folders), 0, []
    for folder in folders:
        ok, issues = validate_output(folder)
        if ok:
            passed += 1
            print(f"  PASS  {folder.name}")
        else:
            failed_list.append(folder.name)
            print(f"  CHECK {folder.name}")
            for issue in issues:
                print(f"       -> {issue}")

    print(f"\n검증 완료: {passed}/{total} PASS")
    return 0 if not failed_list else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ai_multi_agent 작업 진행 관리자")
    sub = parser.add_subparsers(dest="command", required=True)

    mv = sub.add_parser("mv", help="MV 파트별 이미지/비디오 작업 관리")
    mv_sub = mv.add_subparsers(dest="mv_command", required=True)

    mv_songs = mv_sub.add_parser("songs", help="처리된 곡 목록 표시")
    mv_songs.set_defaults(func=command_mv_songs)

    mv_prepare = mv_sub.add_parser("prepare", help="곡의 파트별 작업 폴더 및 프롬프트 생성")
    mv_prepare.add_argument("song", help="곡 폴더명")
    mv_prepare.set_defaults(func=command_mv_prepare)

    mv_next = mv_sub.add_parser("next", help="다음 미완료 파트 이미지 프롬프트 확인")
    mv_next.add_argument("song", help="곡 폴더명")
    mv_next.add_argument("--show", action="store_true", help="이미지 프롬프트 본문 출력")
    mv_next.set_defaults(func=command_mv_next)

    mv_attach = mv_sub.add_parser("attach", help="생성된 이미지를 파트에 등록")
    mv_attach.add_argument("song", help="곡 폴더명")
    mv_attach.add_argument("part", help="파트 키 (예: 01_vocal)")
    mv_attach.add_argument("image", help="등록할 이미지 파일 경로")
    mv_attach.set_defaults(func=command_mv_attach)

    mv_status = mv_sub.add_parser("status", help="MV 파트별 진행 상태 표시")
    mv_status.add_argument("song", help="곡 폴더명")
    mv_status.set_defaults(func=command_mv_status)

    create = sub.add_parser("create", help="단일 곡 처리")
    create.add_argument("--input", required=True, help="곡 txt 파일 경로")
    create.add_argument("--output-dir", default=str(OUTPUT_DIR), help="출력 폴더")
    create.add_argument("--force", action="store_true", help="기존 폴더 덮어쓰기")
    create.set_defaults(func=command_create)

    create_all = sub.add_parser("create-all", help="전체 곡 일괄 처리")
    create_all.add_argument("--input-dir", default=str(INPUT_DIR), help="곡 txt 폴더")
    create_all.add_argument("--output-dir", default=str(OUTPUT_DIR), help="출력 폴더")
    create_all.add_argument("--force", action="store_true", help="기존 폴더 덮어쓰기")
    create_all.set_defaults(func=command_create_all)

    validate = sub.add_parser("validate", help="output 폴더 검증 (필수 파일 + placeholder 확인)")
    validate.add_argument("--folder", default=None, help="검증할 특정 곡 폴더 (미지정 시 전체)")
    validate.add_argument("--output-dir", default=str(OUTPUT_DIR), help="output 루트 폴더")
    validate.set_defaults(func=command_validate)

    story = sub.add_parser("story", help="ai_story 결과 읽기")
    story_sub = story.add_subparsers(dest="story_command", required=True)

    story_list = story_sub.add_parser("list", help="소설 프로젝트 목록")
    story_list.add_argument("--output-dir", default=str(STORY_OUTPUT_DIR), help="ai_story output 폴더")
    story_list.set_defaults(func=command_story_list)

    story_status = story_sub.add_parser("status", help="소설 프로젝트 상태 확인")
    story_status.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    story_status.add_argument("--output-dir", default=str(STORY_OUTPUT_DIR), help="ai_story output 폴더")
    story_status.set_defaults(func=command_story_status)

    story_next = story_sub.add_parser("next", help="다음 챕터 프롬프트 확인")
    story_next.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    story_next.add_argument("--output-dir", default=str(STORY_OUTPUT_DIR), help="ai_story output 폴더")
    story_next.add_argument("--show", action="store_true", help="프롬프트 본문까지 출력")
    story_next.set_defaults(func=command_story_next)

    story_run = story_sub.add_parser("run", help="다음 챕터 프롬프트 1개를 GPT로 실행")
    story_run.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    story_run.add_argument("--output-dir", default=str(STORY_OUTPUT_DIR), help="ai_story output 폴더")
    story_run.add_argument("--force", action="store_true", help="기존 GPT 출력 파일 덮어쓰기")
    story_run.add_argument("--dry-run", action="store_true", help="API 호출 없이 실행 대상만 확인")
    story_run.add_argument("--max-tokens", type=int, default=4096, help="GPT 응답 최대 토큰")
    story_run.set_defaults(func=command_story_run)

    story_save = story_sub.add_parser("save-output", help="GPT 출력 저장 후 ai_story state.json 갱신")
    story_save.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    story_save.add_argument("--chapter", type=int, default=None, help="저장할 챕터 번호 (미지정 시 최근 완료)")
    story_save.add_argument("--output-dir", default=str(STORY_OUTPUT_DIR), help="ai_story output 폴더")
    story_save.set_defaults(func=command_story_save_output)

    scenario = sub.add_parser("scenario", help="ai_Scenario 결과 읽기")
    scenario_sub = scenario.add_subparsers(dest="scenario_command", required=True)

    scenario_list = scenario_sub.add_parser("list", help="시나리오 프로젝트 목록")
    scenario_list.add_argument("--output-dir", default=str(SCENARIO_OUTPUT_DIR), help="ai_Scenario output 폴더")
    scenario_list.set_defaults(func=command_scenario_list)

    scenario_status = scenario_sub.add_parser("status", help="시나리오 프로젝트 상태 확인")
    scenario_status.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    scenario_status.add_argument("--output-dir", default=str(SCENARIO_OUTPUT_DIR), help="ai_Scenario output 폴더")
    scenario_status.set_defaults(func=command_scenario_status)

    scenario_next = scenario_sub.add_parser("next", help="다음 씬 프롬프트 확인")
    scenario_next.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    scenario_next.add_argument("--output-dir", default=str(SCENARIO_OUTPUT_DIR), help="ai_Scenario output 폴더")
    scenario_next.add_argument("--show", action="store_true", help="프롬프트 본문까지 출력")
    scenario_next.set_defaults(func=command_scenario_next)

    scenario_run = scenario_sub.add_parser("run", help="다음 씬 프롬프트 1개를 GPT로 실행")
    scenario_run.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    scenario_run.add_argument("--output-dir", default=str(SCENARIO_OUTPUT_DIR), help="ai_Scenario output 폴더")
    scenario_run.add_argument("--force", action="store_true", help="기존 GPT 출력 파일 덮어쓰기")
    scenario_run.add_argument("--dry-run", action="store_true", help="API 호출 없이 실행 대상만 확인")
    scenario_run.add_argument("--max-tokens", type=int, default=4096, help="GPT 응답 최대 토큰")
    scenario_run.set_defaults(func=command_scenario_run)

    scenario_save = scenario_sub.add_parser("save-output", help="GPT 출력 저장 후 ai_Scenario state.json 갱신")
    scenario_save.add_argument("name", nargs="?", default=None, help="프로젝트 폴더명 또는 작품 제목")
    scenario_save.add_argument("--scene", type=int, default=None, help="저장할 씬 번호 (미지정 시 최근 완료)")
    scenario_save.add_argument("--output-dir", default=str(SCENARIO_OUTPUT_DIR), help="ai_Scenario output 폴더")
    scenario_save.set_defaults(func=command_scenario_save_output)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_output()
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n중단됨.")
        return 130
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
