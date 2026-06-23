"""
capcut_draft.py — CapCut PC draft 자동 생성 (8.x JSON 포맷)

timeline.json → draft_content.json + draft_meta_info.json
시간 단위: CapCut은 마이크로초(μs) 사용 — ms × 1000
"""

import json
import time
import uuid
from collections import defaultdict
from pathlib import Path

CAPCUT_DRAFT_ROOT = (
    Path.home() / "AppData" / "Local" / "CapCut"
    / "User Data" / "Projects" / "com.lveditor.draft"
)

_APP_VERSION = "8.3.0"
_NEW_VERSION = "163.0.0"
_DEFAULT_CLIP_DUR_MS = 8_000  # clip_durations 측정 실패 시 보수적 기본값 (Kling 클립 일반 길이)
_TRANSITION_EFFECT_ID = "7504513585289219345"  # 사용자 CapCut에 캐시된 디졸브 효과
_TRANSITION_DUR_MS = 500  # 섹션 경계 전환 길이 (ms)


# ─── ID 헬퍼 ────────────────────────────────────────────────────────────────

def _uid() -> str:
    return str(uuid.uuid4()).upper()


def _luid() -> str:
    return str(uuid.uuid4())


def _us(ms: int) -> int:
    """ms → μs"""
    return ms * 1000


def _now_us() -> int:
    return int(time.time() * 1_000_000)


# ─── material 생성 ───────────────────────────────────────────────────────────

def _video_mat(mat_id: str, local_id: str, path: Path, dur_ms: int) -> dict:
    return {
        "aigc_history_id": "", "aigc_item_id": "", "aigc_type": "none",
        "audio_fade": None, "beauty_body_auto_preset": None, "beauty_body_preset_id": "",
        "beauty_face_auto_preset": {"name": "", "preset_id": "", "rate_map": "", "scene": ""},
        "beauty_face_auto_preset_infos": [], "beauty_face_preset_infos": [],
        "cartoon_path": "", "category_id": "", "category_name": "local",
        "check_flag": 62978047, "content_feature_info": None, "corner_pin": None,
        "crop": {
            "lower_left_x": 0.0, "lower_left_y": 1.0,
            "lower_right_x": 1.0, "lower_right_y": 1.0,
            "upper_left_x": 0.0, "upper_left_y": 0.0,
            "upper_right_x": 1.0, "upper_right_y": 0.0,
        },
        "crop_ratio": "free", "crop_scale": 1.0,
        "duration": _us(dur_ms),
        "extra_type_option": 0, "formula_id": "", "freeze": None,
        "has_audio": True, "has_sound_separated": False,
        "height": 1080, "width": 1920,
        "id": mat_id,
        "intensifies_audio_path": "", "intensifies_path": "",
        "is_ai_generate_content": False, "is_copyright": False,
        "is_text_edit_overdub": False, "is_unified_beauty_mode": False,
        "live_photo_cover_path": "", "live_photo_timestamp": -1,
        "local_id": "", "local_material_from": "",
        "local_material_id": local_id,
        "material_id": "", "material_name": path.name, "material_url": "",
        "matting": {
            "custom_matting_id": "", "enable_matting_stroke": False,
            "expansion": 0, "feather": 0, "flag": 0,
            "has_use_quick_brush": False, "has_use_quick_eraser": False,
            "interactiveTime": [], "path": "", "reverse": False, "strokes": [],
        },
        "media_path": "", "multi_camera_info": None, "object_locked": None,
        "origin_material_id": "",
        "path": path.as_posix(),
        "picture_from": "none", "picture_set_category_id": "", "picture_set_category_name": "",
        "request_id": "", "reverse_intensifies_path": "", "reverse_path": "",
        "smart_match_info": None, "smart_motion": None,
        "source": 0, "source_platform": 0,
        "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"duration": 0, "start": 0}},
        "surface_trackings": [], "team_id": "", "type": "video", "unique_id": "",
        "video_algorithm": {
            "ai_background_configs": [], "ai_expression_driven": None,
            "ai_in_painting_config": [], "ai_motion_driven": None,
            "aigc_generate": None, "aigc_generate_list": [], "algorithms": [],
            "complement_frame_config": None, "deflicker": None,
            "gameplay_configs": [], "image_interpretation": None,
            "motion_blur_config": None, "mouth_shape_driver": None,
            "noise_reduction": None, "path": "", "quality_enhance": None,
            "skip_algorithm_index": [], "smart_complement_frame": None,
            "story_video_modify_video_config": {
                "is_overwrite_last_video": False, "task_id": "", "tracker_task_id": "",
            },
            "super_resolution": None, "time_range": None,
        },
        "video_mask_shadow": {
            "alpha": 0.0, "angle": 0.0, "blur": 0.0, "color": "",
            "distance": 0.0, "path": "", "resource_id": "",
        },
        "video_mask_stroke": {
            "alpha": 0.0, "color": "", "distance": 0.0, "horizontal_shift": 0.0,
            "path": "", "resource_id": "", "size": 0.0, "texture": 0.0,
            "type": "", "vertical_shift": 0.0,
        },
    }


def _audio_mat(mat_id: str, local_id: str, path: Path, dur_ms: int) -> dict:
    return {
        "ai_music_enter_from": "", "ai_music_generate_scene": 0, "ai_music_type": 0,
        "aigc_history_id": "", "aigc_item_id": "", "app_id": 0,
        "category_id": "", "category_name": "local", "check_flag": 1,
        "cloned_model_type": "", "copyright_limit_type": "none",
        "duration": _us(dur_ms),
        "effect_id": "", "formula_id": "",
        "id": mat_id,
        "intensifies_path": "",
        "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
        "is_text_edit_overdub": False, "is_ugc": False,
        "local_material_id": local_id,
        "lyric_type": 0, "mock_tone_speaker": "", "moyin_emotion": "",
        "music_id": _luid(), "music_source": "",
        "name": path.name,
        "path": path.as_posix(),
        "pgc_id": "", "pgc_name": "", "query": "", "request_id": "",
        "resource_id": "", "search_id": "",
        "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
        "sound_separate_type": "", "source_from": "", "source_platform": 0,
        "team_id": "", "text_id": "", "third_resource_id": "",
        "tone_category_id": "", "tone_category_name": "",
        "tone_effect_id": "", "tone_effect_name": "",
        "tone_emotion_name_key": "", "tone_emotion_role": "",
        "tone_emotion_scale": 0.0, "tone_emotion_selection": "", "tone_emotion_style": "",
        "tone_platform": "", "tone_second_category_id": "", "tone_second_category_name": "",
        "tone_speaker": "", "tone_type": "",
        "tts_benefit_info": {
            "benefit_amount": -1, "benefit_log_extra": "",
            "benefit_log_id": "", "benefit_type": "none",
        },
        "tts_generate_scene": "", "tts_task_id": "",
        "type": "extract_music", "unique_id": "", "video_id": "", "wave_points": [],
    }


def _speed(sid: str) -> dict:
    return {"curve_speed": None, "id": sid, "mode": 0, "speed": 1.0, "type": "speed"}


def _canvas(cid: str) -> dict:
    return {
        "album_image": "", "blur": 0.0, "color": "", "id": cid,
        "image": "", "image_id": "", "image_name": "",
        "source_platform": 0, "team_id": "", "type": "canvas_color",
    }


def _placeholder(pid: str) -> dict:
    return {
        "error_path": "", "error_text": "", "id": pid,
        "meta_type": "none", "res_path": "", "res_text": "", "type": "placeholder_info",
    }


def _sound_channel(scid: str) -> dict:
    return {"audio_channel_mapping": 0, "id": scid, "is_config_open": False, "type": ""}


def _mat_color(mcid: str) -> dict:
    return {
        "gradient_angle": 90.0, "gradient_colors": [], "gradient_percents": [],
        "height": 0.0, "id": mcid, "is_color_clip": False, "is_gradient": False,
        "solid_color": "", "width": 0.0,
    }


def _text_mat(mat_id: str, text: str, text_size: int = 20) -> dict:
    content = json.dumps({
        "text": text,
        "styles": [{
            "range": [0, len(text)],
            "fill": {"content": {"solid": {"color": [1.0, 1.0, 1.0, 1.0]}}},
            "size": round(text_size / 4.0, 1),
            "font": {"id": "", "path": ""},
            "strokes": [],
            "bold": False,
            "italic": False,
            "underline": False,
        }]
    }, ensure_ascii=False)
    return {
        "add_type": 0, "alignment": 1,
        "background_alpha": 1.0, "background_color": "",
        "background_height": 0.14, "background_horizontal_offset": 0.0,
        "background_round_radius": 0.0, "background_style": 0,
        "background_vertical_offset": 0.0, "background_width": 0.14,
        "base_content": "", "bold_width": 0.0,
        "border_alpha": 1.0, "border_color": "", "border_width": 0.0,
        "caption_template_info": {
            "category_id": "", "category_name": "", "effect_id": "",
            "is_new": False, "path": "", "request_id": "", "resource_id": "",
            "search_id": "", "source_platform": 0, "team_id": "", "title": "",
        },
        "check_flag": 7,
        "combo_info": {"text_templates": []},
        "content": content,
        "fixed_height": -1.0, "fixed_width": -1.0,
        "font_category_id": "", "font_category_name": "",
        "font_id": "", "font_name": "", "font_path": "",
        "font_resource_id": "", "font_size": round(text_size / 4.0, 1),
        "font_source_platform": 0, "font_team_id": "",
        "font_time_range": {"duration": -1, "start": -1},
        "font_title": "", "font_url": "",
        "global_alpha": 1.0, "group_id": "",
        "has_shadow": False, "id": mat_id,
        "initial_scale": 1.0, "inner_padding": -1.0,
        "is_rich_text": False, "italic_degree": 0,
        "ktv_color": "", "language": "",
        "layer_weight": 1, "letter_spacing": 0.0,
        "line_feed": 1, "line_max_width": 0.82, "line_spacing": 0.02,
        "multi_language_current": "none", "name": "",
        "original_size": [], "preset_id": "",
        "recognize_task_id": "", "recognize_type": 0,
        "relevance_segment": [],
        "shadow_alpha": 0.75, "shadow_angle": -45.0, "shadow_color": "",
        "shadow_distance": 8.0, "shadow_point": {"x": 1.0, "y": -1.0},
        "shadow_smoothing": 1.0,
        "shape_clip_x": False, "shape_clip_y": False,
        "style_name": "", "sub_type": 0, "subtype": "",
        "text_alpha": 1.0, "text_color": "#FFFFFF",
        "text_curve": None, "text_preset_resource_id": "",
        "text_size": text_size, "text_to_audio_ids": [],
        "tts_auto_update": False,
        "type": "text", "typesetting": 0,
        "underline": False, "underline_offset": 0.22, "underline_width": 0.05,
        "use_effect_default_color": True,
        "words": {"end_time": [], "start_time": [], "text": []},
    }


def _text_animation(aid: str) -> dict:
    return {
        "animation_id": "", "id": aid,
        "multi_language_current": "none",
        "type": "sticker_animation",
    }


def _text_seg(
    mat_id: str, start_us: int, dur_us: int,
    speed_id: str, ph_id: str, anim_id: str,
    y_pos: float = -0.75,
) -> dict:
    return {
        "caption_info": None, "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": y_pos},
        },
        "color_correct_alg_result": "", "common_keyframes": [],
        "desc": "", "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
        "enable_color_curves": True, "enable_color_match_adjust": False,
        "enable_color_wheels": True, "enable_hsl": False,
        "enable_hsl_curves": True, "enable_lut": True,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": [speed_id, ph_id, anim_id],
        "group_id": "",
        "hdr_settings": None,
        "id": _uid(),
        "intensifies_audio": False, "is_loop": False,
        "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 0.0, "lyric_keyframes": None,
        "material_id": mat_id,
        "raw_segment_id": "", "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": {"start": 0, "duration": dur_us},
        "speed": 1.0, "state": 0,
        "target_timerange": {"start": start_us, "duration": dur_us},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True, "volume": 0.0,
    }


def _vocal_sep(vsid: str) -> dict:
    return {
        "choice": 0, "enter_from": "", "final_algorithm": "", "id": vsid,
        "production_path": "", "removed_sounds": [], "time_range": None,
        "type": "vocal_separation",
    }


def _beats(bid: str) -> dict:
    return {
        "ai_beats": {
            "beat_speed_infos": [], "beats_path": "", "beats_url": "",
            "melody_path": "", "melody_percents": [0.0], "melody_url": "",
        },
        "enable_ai_beats": False, "gear": 404, "gear_count": 0,
        "id": bid, "mode": 404, "type": "beats",
        "user_beats": [], "user_delete_ai_beats": None,
    }


def _sticker_anim(aid: str) -> dict:
    return {
        "id": aid, "type": "sticker_animation",
        "animations": [], "multi_language_current": "none",
    }


def _transition_mat(tid: str, dur_ms: int, path: str) -> dict:
    return {
        "id": tid, "type": "transition",
        "name": "디졸브",
        "effect_id": _TRANSITION_EFFECT_ID,
        "resource_id": _TRANSITION_EFFECT_ID,
        "third_resource_id": "0",
        "source_platform": 1,
        "path": path,
        "duration": _us(dur_ms),
        "is_overlap": True,
        "platform": "all",
        "category_id": "",
        "category_name": "transition",
        "request_id": "",
        "is_ai_transition": False,
        "video_path": "",
        "task_id": "",
    }


def _get_transition_path() -> str:
    """CapCut 로컬 캐시에서 전환 효과 파일 경로를 반환. 없으면 빈 문자열."""
    cache = (
        Path.home() / "AppData" / "Local" / "CapCut" / "User Data" / "Cache"
        / "effect" / _TRANSITION_EFFECT_ID
    )
    if cache.exists():
        files = [f for f in cache.iterdir() if not f.name.endswith("_tmp")]
        if files:
            return files[0].as_posix()
    return ""


# ─── 세그먼트 생성 ────────────────────────────────────────────────────────────

def _video_seg(
    mat_id: str,
    src_dur_us: int, tgt_start_us: int, tgt_dur_us: int,
    speed_id: str, ph_id: str, canvas_id: str,
    sc_id: str, mc_id: str, vs_id: str,
    is_loop: bool,
    transition_id: str = None, anim_id: str = None,
) -> dict:
    if transition_id and anim_id:
        # refs 순서: speed, placeholder, transition, canvas, sticker_anim, sound_channel, material_color, vocal_sep
        extra_refs = [speed_id, ph_id, transition_id, canvas_id, anim_id, sc_id, mc_id, vs_id]
    else:
        # refs 순서: speed, placeholder, canvas, sound_channel, material_color, vocal_sep
        extra_refs = [speed_id, ph_id, canvas_id, sc_id, mc_id, vs_id]
    return {
        "caption_info": None, "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0},
        },
        "color_correct_alg_result": "", "common_keyframes": [],
        "desc": "", "digital_human_template_group_id": "",
        "enable_adjust": True, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
        "enable_color_curves": True, "enable_color_match_adjust": False,
        "enable_color_wheels": True, "enable_hsl": False,
        "enable_hsl_curves": True, "enable_lut": True,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "",
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "id": _uid(),
        "intensifies_audio": False, "is_loop": is_loop,
        "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 0.0, "lyric_keyframes": None,
        "material_id": mat_id,
        "raw_segment_id": "", "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": {"start": 0, "duration": src_dur_us},
        "speed": 1.0, "state": 0,
        "target_timerange": {"start": tgt_start_us, "duration": tgt_dur_us},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 0,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True, "volume": 0.0,
    }


def _audio_seg(
    mat_id: str, dur_us: int,
    speed_id: str, ph_id: str, beats_id: str, sc_id: str, vs_id: str,
) -> dict:
    return {
        "caption_info": None, "cartoon": False, "clip": None,
        "color_correct_alg_result": "", "common_keyframes": [],
        "desc": "", "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False, "enable_color_correct_adjust": False,
        "enable_color_curves": True, "enable_color_match_adjust": False,
        "enable_color_wheels": True, "enable_hsl": False,
        "enable_hsl_curves": True, "enable_lut": False,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False, "enable_video_mask": True,
        # refs 순서: speed, placeholder, beats, sound_channel, vocal_sep
        "extra_material_refs": [speed_id, ph_id, beats_id, sc_id, vs_id],
        "group_id": "", "hdr_settings": None,
        "id": _uid(),
        "intensifies_audio": False, "is_loop": False,
        "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 1.0, "lyric_keyframes": None,
        "material_id": mat_id,
        "raw_segment_id": "", "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": {"start": 0, "duration": dur_us},
        "speed": 1.0, "state": 0,
        "target_timerange": {"start": 0, "duration": dur_us},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": 1,
        "uniform_scale": None,
        "visible": True, "volume": 1.0,
    }


# ─── 드래프트 빌드 ────────────────────────────────────────────────────────────

def build_draft(
    timeline: dict,
    audio_path: Path,
    clips_dir: Path,
    clip_durations: dict,
    srt_entries: list = None,
    srt_entries_en: list = None,
    lyric_video_path: Path = None,
    lyric_video_dur_ms: int = None,
) -> tuple:
    """
    timeline.json → (draft_content, draft_meta_info, draft_id)

    clip_durations: {normalized_stem: duration_ms}  (get_clip_durations() 결과)
    타임라인 전략: 섹션 내 클립들을 균등 분할해 메인 트랙에 순서대로 배치
    """
    draft_id = _uid()
    song_title = timeline["song_title"]
    total_ms = timeline["total_duration_ms"]
    now_us = _now_us()

    # 섹션별 할당된 클립 그룹화 {(start_ms, end_ms): [slot, ...]}
    section_slots: dict = defaultdict(list)
    for clip in timeline["clips"]:
        if clip["source"] == "assigned" and clip["clip_file"]:
            key = (clip["start_ms"], clip["end_ms"])
            section_slots[key].append(clip)

    # 고유 클립 파일 → material 정보
    file_to_mat: dict = {}
    for slots in section_slots.values():
        for slot in slots:
            fname = slot["clip_file"]
            if fname and fname not in file_to_mat:
                abs_path = clips_dir / fname
                stem_key = fname.rsplit(".", 1)[0].lower().replace("-", "_").replace(" ", "_")
                clip_dur = clip_durations.get(stem_key) or _DEFAULT_CLIP_DUR_MS
                file_to_mat[fname] = {
                    "mat_id": _uid(),
                    "local_id": _luid(),
                    "path": abs_path,
                    "dur_ms": clip_dur,
                }

    # materials 컨테이너
    mat_videos, mat_audios = [], []
    mat_speeds, mat_canvases, mat_placeholders = [], [], []
    mat_sound_channels, mat_mat_colors, mat_vocal_seps, mat_beats = [], [], [], []
    mat_texts, mat_text_animations = [], []

    for fname, info in file_to_mat.items():
        mat_videos.append(_video_mat(info["mat_id"], info["local_id"], info["path"], info["dur_ms"]))

    # 가사 영상 material (존재 시)
    lyric_mat_id = None
    lyric_local_id = None
    lv_dur_ms = lyric_video_dur_ms or total_ms
    if lyric_video_path and lyric_video_path.exists():
        lyric_mat_id = _uid()
        lyric_local_id = _luid()
        mat_videos.append(_video_mat(lyric_mat_id, lyric_local_id, lyric_video_path, lv_dur_ms))

    audio_mat_id = _uid()
    audio_local_id = _luid()
    mat_audios.append(_audio_mat(audio_mat_id, audio_local_id, audio_path, total_ms))

    # 비디오 세그먼트 생성 — 클립 자연 길이로 순환 배치
    # 5초짜리 클립을 39초 섹션에 배정하면 검정 화면이 생기므로,
    # 클립 길이 단위로 섹션을 채울 때까지 클립들을 순서대로 돌아가며 배치한다.
    video_segs = []
    mat_transitions = []
    transition_path = _get_transition_path()
    section_keys = sorted(section_slots.keys())
    for sec_idx, (sec_start_ms, sec_end_ms) in enumerate(section_keys):
        slots = section_slots[(sec_start_ms, sec_end_ms)]
        n = len(slots)

        cursor = sec_start_ms
        cycle_idx = 0
        while cursor < sec_end_ms:
            slot = slots[cycle_idx % n]
            fname = slot["clip_file"]
            cycle_idx += 1
            if not fname:
                continue

            info = file_to_mat[fname]
            clip_file_dur_ms = info["dur_ms"]
            remaining_ms = sec_end_ms - cursor
            tgt_dur_ms = min(clip_file_dur_ms, remaining_ms)
            src_dur_ms = tgt_dur_ms  # 실제 재생 분량만 지정 (루프 없음)

            sid, pid, cid, scid, mcid, vsid = _uid(), _uid(), _uid(), _uid(), _uid(), _uid()
            mat_speeds.append(_speed(sid))
            mat_placeholders.append(_placeholder(pid))
            mat_canvases.append(_canvas(cid))
            mat_sound_channels.append(_sound_channel(scid))
            mat_mat_colors.append(_mat_color(mcid))
            mat_vocal_seps.append(_vocal_sep(vsid))

            # 섹션 첫 클립(cycle_idx==1)이고 첫 섹션이 아니면 디졸브 전환 추가
            t_id, a_id = None, None
            if sec_idx > 0 and cycle_idx == 1:
                t_id, a_id = _uid(), _uid()
                mat_transitions.append(_transition_mat(t_id, _TRANSITION_DUR_MS, transition_path))
                mat_text_animations.append(_sticker_anim(a_id))

            video_segs.append(_video_seg(
                mat_id=info["mat_id"],
                src_dur_us=_us(src_dur_ms),
                tgt_start_us=_us(cursor),
                tgt_dur_us=_us(tgt_dur_ms),
                speed_id=sid, ph_id=pid, canvas_id=cid,
                sc_id=scid, mc_id=mcid, vs_id=vsid,
                is_loop=False,
                transition_id=t_id, anim_id=a_id,
            ))
            cursor += tgt_dur_ms

    # 오디오 세그먼트
    a_sid, a_pid, a_bid, a_scid, a_vsid = _uid(), _uid(), _uid(), _uid(), _uid()
    mat_speeds.append(_speed(a_sid))
    mat_placeholders.append(_placeholder(a_pid))
    mat_beats.append(_beats(a_bid))
    mat_sound_channels.append(_sound_channel(a_scid))
    mat_vocal_seps.append(_vocal_sep(a_vsid))

    audio_seg = _audio_seg(
        mat_id=audio_mat_id, dur_us=_us(total_ms),
        speed_id=a_sid, ph_id=a_pid, beats_id=a_bid,
        sc_id=a_scid, vs_id=a_vsid,
    )

    # 가사 영상 트랙 세그먼트 생성 (lyric_video_path 존재 시)
    lyric_segs = []
    if lyric_mat_id:
        lv_sid, lv_pid, lv_cid = _uid(), _uid(), _uid()
        lv_scid, lv_mcid, lv_vsid = _uid(), _uid(), _uid()
        mat_speeds.append(_speed(lv_sid))
        mat_placeholders.append(_placeholder(lv_pid))
        mat_canvases.append(_canvas(lv_cid))
        mat_sound_channels.append(_sound_channel(lv_scid))
        mat_mat_colors.append(_mat_color(lv_mcid))
        mat_vocal_seps.append(_vocal_sep(lv_vsid))
        lyric_segs.append(_video_seg(
            mat_id=lyric_mat_id,
            src_dur_us=_us(lv_dur_ms),
            tgt_start_us=0,
            tgt_dur_us=_us(total_ms),
            speed_id=lv_sid, ph_id=lv_pid, canvas_id=lv_cid,
            sc_id=lv_scid, mc_id=lv_mcid, vs_id=lv_vsid,
            is_loop=False,
        ))

    # 자막 트랙 생성 (SRT 있을 때만)
    def _build_text_segs(entries, text_size, y_pos):
        segs = []
        for entry in (entries or []):
            t_mat_id = _uid()
            t_speed_id, t_ph_id, t_anim_id = _uid(), _uid(), _uid()
            mat_texts.append(_text_mat(t_mat_id, entry["text"], text_size=text_size))
            mat_text_animations.append(_text_animation(t_anim_id))
            mat_speeds.append(_speed(t_speed_id))
            mat_placeholders.append(_placeholder(t_ph_id))
            segs.append(_text_seg(
                mat_id=t_mat_id,
                start_us=_us(entry["start_ms"]),
                dur_us=_us(entry["end_ms"] - entry["start_ms"]),
                speed_id=t_speed_id, ph_id=t_ph_id, anim_id=t_anim_id,
                y_pos=y_pos,
            ))
        return segs

    # 한글: 크기 20, y=-0.75 / 영어: 크기 16, y=-0.88
    text_segs_kr = _build_text_segs(srt_entries, text_size=20, y_pos=-0.75)
    text_segs_en = _build_text_segs(srt_entries_en, text_size=16, y_pos=-0.88)

    # draft_content.json
    draft_content = {
        "canvas_config": {"background": None, "height": 1080, "ratio": "original", "width": 1920},
        "color_space": -1,
        "config": {
            "adjust_max_index": 1, "attachment_info": [], "combination_max_index": 1,
            "export_range": None, "extract_audio_last_index": 1,
            "lyrics_recognition_id": "", "lyrics_sync": True, "lyrics_taskinfo": [],
            "maintrack_adsorb": True, "material_save_mode": 0,
            "multi_language_current": "none", "multi_language_list": [],
            "multi_language_main": "none", "multi_language_mode": "none",
            "original_sound_last_index": 1, "record_audio_last_index": 1,
            "sticker_max_index": 1, "subtitle_keywords_config": None,
            "subtitle_recognition_id": "", "subtitle_sync": True, "subtitle_taskinfo": [],
            "system_font_list": [], "use_float_render": False,
            "video_mute": False, "zoom_info_params": None,
        },
        "cover": None, "create_time": 0, "draft_type": "video",
        "duration": _us(total_ms),
        "extra_info": None, "fps": 30.0, "free_render_index_mode_on": False,
        "id": draft_id, "is_drop_frame_timecode": False,
        "keyframe_graph_list": [],
        "keyframes": {
            "adjusts": [], "audios": [], "effects": [], "filters": [],
            "handwrites": [], "stickers": [], "texts": [], "videos": [],
        },
        "last_modified_platform": {
            "app_id": 359289, "app_source": "cc", "app_version": _APP_VERSION,
            "device_id": "", "hard_disk_id": "", "mac_address": "",
            "os": "windows", "os_version": "10.0.19045",
        },
        "lyrics_effects": [],
        "materials": {
            "ai_translates": [], "audio_balances": [], "audio_effects": [],
            "audio_fades": [], "audio_pannings": [], "audio_pitch_shifts": [],
            "audio_track_indexes": [],
            "audios": mat_audios,
            "beats": mat_beats,
            "canvases": mat_canvases,
            "chromas": [], "color_curves": [], "common_mask": [],
            "digital_human_model_dressing": [], "digital_humans": [],
            "drafts": [], "effects": [], "flowers": [], "green_screens": [],
            "handwrites": [], "hsl": [], "hsl_curves": [], "images": [],
            "log_color_wheels": [], "loudnesses": [],
            "manual_beautys": [], "manual_deformations": [],
            "material_animations": mat_text_animations,
            "material_colors": mat_mat_colors,
            "multi_language_refs": [],
            "placeholder_infos": mat_placeholders,
            "placeholders": [], "plugin_effects": [], "primary_color_wheels": [],
            "realtime_denoises": [], "shapes": [], "smart_crops": [], "smart_relights": [],
            "sound_channel_mappings": mat_sound_channels,
            "speeds": mat_speeds,
            "stickers": [], "tail_leaders": [], "text_templates": [],
            "texts": mat_texts, "time_marks": [], "transitions": mat_transitions,
            "video_effects": [], "video_radius": [], "video_shadows": [],
            "video_strokes": [], "video_trackings": [],
            "videos": mat_videos,
            "vocal_beautifys": [],
            "vocal_separations": mat_vocal_seps,
        },
        "mutable_config": None, "name": "", "new_version": _NEW_VERSION, "path": "",
        "platform": {
            "app_id": 359289, "app_source": "cc", "app_version": _APP_VERSION,
            "device_id": "", "hard_disk_id": "", "mac_address": "",
            "os": "windows", "os_version": "10.0.19045",
        },
        "relationships": [], "render_index_track_mode_on": True,
        "retouch_cover": None, "source": "default", "static_cover_image_path": "",
        "time_marks": None,
        "tracks": [
            {"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
             "name": "", "segments": video_segs, "type": "video"},
            *([{"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": False,
                "name": "Lyric Video", "segments": lyric_segs, "type": "video"}]
              if lyric_segs else []),
            {"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
             "name": "", "segments": [audio_seg], "type": "audio"},
            *([{"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
                "name": "", "segments": text_segs_kr, "type": "text"}]
              if text_segs_kr else []),
            *([{"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
                "name": "", "segments": text_segs_en, "type": "text"}]
              if text_segs_en else []),
        ],
        "update_time": 0, "version": 360000,
    }

    # draft_meta_info.json
    meta_values = []
    for fname, info in file_to_mat.items():
        meta_values.append({
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": _us(info["dur_ms"]), "enter_from": 0,
            "extra_info": fname, "file_Path": info["path"].as_posix(),
            "height": 1080, "id": info["local_id"],
            "import_time": int(time.time()), "import_time_ms": now_us,
            "item_source": 1, "md5": "", "metetype": "video",
            "roughcut_time_range": {"duration": _us(info["dur_ms"]), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0, "width": 1920,
        })
    if lyric_mat_id and lyric_video_path:
        meta_values.append({
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": _us(lv_dur_ms), "enter_from": 0,
            "extra_info": lyric_video_path.name,
            "file_Path": lyric_video_path.as_posix(),
            "height": 1080, "id": lyric_local_id,
            "import_time": int(time.time()), "import_time_ms": now_us,
            "item_source": 1, "md5": "", "metetype": "video",
            "roughcut_time_range": {"duration": _us(lv_dur_ms), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0, "width": 1920,
        })
    meta_values.append({
        "ai_group_type": "", "create_time": int(time.time()),
        "duration": _us(total_ms), "enter_from": 0,
        "extra_info": audio_path.name, "file_Path": audio_path.as_posix(),
        "height": 0, "id": audio_local_id,
        "import_time": int(time.time()), "import_time_ms": now_us,
        "item_source": 1, "md5": "", "metetype": "music",
        "roughcut_time_range": {"duration": _us(total_ms), "start": 0},
        "sub_time_range": {"duration": -1, "start": -1},
        "type": 0, "width": 0,
    })

    draft_meta = {
        "cloud_draft_cover": False, "cloud_draft_sync": False,
        "cloud_package_completed_time": "",
        "draft_cloud_capcut_purchase_info": "", "draft_cloud_last_action_download": False,
        "draft_cloud_package_type": "", "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg", "draft_deeplink_url": "",
        "draft_enterprise_info": {
            "draft_enterprise_extra": "", "draft_enterprise_id": "",
            "draft_enterprise_name": "", "enterprise_material": [],
        },
        "draft_fold_path": "",       # write_draft() 시점에 채움
        "draft_id": draft_id,
        "draft_is_ae_produce": False, "draft_is_ai_packaging_used": False,
        "draft_is_ai_shorts": False, "draft_is_ai_translate": False,
        "draft_is_article_video_draft": False, "draft_is_cloud_temp_draft": False,
        "draft_is_from_deeplink": "false", "draft_is_invisible": False,
        "draft_is_web_article_video": False,
        "draft_materials": [{"type": 0, "value": meta_values}],
        "draft_materials_copied_info": [],
        "draft_name": f"{song_title}_MV",
        "draft_need_rename_folder": False, "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": "",       # write_draft() 시점에 채움
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": 0,
        "draft_type": "", "draft_web_article_video_enter_from": "",
        "tm_draft_cloud_completed": "", "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0, "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1, "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us, "tm_draft_modified": now_us,
        "tm_draft_removed": 0, "tm_duration": _us(total_ms),
    }

    return draft_content, draft_meta, draft_id


def _image_mat(mat_id: str, local_id: str, path: Path, dur_ms: int) -> dict:
    """이미지 파일용 material — video material 기반, has_audio=False, type=photo"""
    mat = _video_mat(mat_id, local_id, path, dur_ms)
    mat["has_audio"] = False
    mat["type"] = "photo"
    mat["picture_from"] = "local"
    return mat


def build_image_lyric_draft(
    image_path: Path,
    audio_path: Path,
    song_title: str,
    total_ms: int,
    caption_entries: list = None,
) -> tuple:
    """
    이미지 + 오디오 + LRC → CapCut 드래프트 직접 생성.
    Python(MoviePy) 렌더링 없이 CapCut에서 편집·내보내기.

    track[0] — 비디오: 이미지 (전체 재생 시간 유지)
    track[1] — 오디오: 원본 음원
    track[2] — 텍스트: LRC 가사 세그먼트 (CapCut에서 스타일 적용)
    """
    draft_id = _uid()
    now_us = _now_us()

    mat_videos, mat_audios = [], []
    mat_speeds, mat_canvases, mat_placeholders = [], [], []
    mat_sound_channels, mat_mat_colors, mat_vocal_seps, mat_beats = [], [], [], []
    mat_texts, mat_text_animations = [], []

    # 이미지 material
    img_mat_id = _uid()
    img_local_id = _luid()
    mat_videos.append(_image_mat(img_mat_id, img_local_id, image_path, total_ms))

    # 오디오 material
    audio_mat_id = _uid()
    audio_local_id = _luid()
    mat_audios.append(_audio_mat(audio_mat_id, audio_local_id, audio_path, total_ms))

    # 이미지 세그먼트 보조 material
    v_sid, v_pid, v_cid = _uid(), _uid(), _uid()
    v_scid, v_mcid, v_vsid = _uid(), _uid(), _uid()
    mat_speeds.append(_speed(v_sid))
    mat_placeholders.append(_placeholder(v_pid))
    mat_canvases.append(_canvas(v_cid))
    mat_sound_channels.append(_sound_channel(v_scid))
    mat_mat_colors.append(_mat_color(v_mcid))
    mat_vocal_seps.append(_vocal_sep(v_vsid))

    image_seg = _video_seg(
        mat_id=img_mat_id,
        src_dur_us=_us(total_ms),
        tgt_start_us=0,
        tgt_dur_us=_us(total_ms),
        speed_id=v_sid, ph_id=v_pid, canvas_id=v_cid,
        sc_id=v_scid, mc_id=v_mcid, vs_id=v_vsid,
        is_loop=False,
    )

    # 오디오 세그먼트 보조 material
    a_sid, a_pid, a_bid, a_scid, a_vsid = _uid(), _uid(), _uid(), _uid(), _uid()
    mat_speeds.append(_speed(a_sid))
    mat_placeholders.append(_placeholder(a_pid))
    mat_beats.append(_beats(a_bid))
    mat_sound_channels.append(_sound_channel(a_scid))
    mat_vocal_seps.append(_vocal_sep(a_vsid))

    audio_seg = _audio_seg(
        mat_id=audio_mat_id, dur_us=_us(total_ms),
        speed_id=a_sid, ph_id=a_pid, beats_id=a_bid,
        sc_id=a_scid, vs_id=a_vsid,
    )

    # 가사 텍스트 세그먼트 (LRC 타이밍 기반)
    text_segs = []
    for entry in (caption_entries or []):
        t_mat_id = _uid()
        t_speed_id, t_ph_id, t_anim_id = _uid(), _uid(), _uid()
        mat_texts.append(_text_mat(t_mat_id, entry["text"], text_size=22))
        mat_text_animations.append(_text_animation(t_anim_id))
        mat_speeds.append(_speed(t_speed_id))
        mat_placeholders.append(_placeholder(t_ph_id))
        text_segs.append(_text_seg(
            mat_id=t_mat_id,
            start_us=_us(entry["start_ms"]),
            dur_us=_us(entry["end_ms"] - entry["start_ms"]),
            speed_id=t_speed_id, ph_id=t_ph_id, anim_id=t_anim_id,
            y_pos=-0.72,
        ))

    draft_content = {
        "canvas_config": {"background": None, "height": 1080, "ratio": "original", "width": 1920},
        "color_space": -1,
        "config": {
            "adjust_max_index": 1, "attachment_info": [], "combination_max_index": 1,
            "export_range": None, "extract_audio_last_index": 1,
            "lyrics_recognition_id": "", "lyrics_sync": True, "lyrics_taskinfo": [],
            "maintrack_adsorb": True, "material_save_mode": 0,
            "multi_language_current": "none", "multi_language_list": [],
            "multi_language_main": "none", "multi_language_mode": "none",
            "original_sound_last_index": 1, "record_audio_last_index": 1,
            "sticker_max_index": 1, "subtitle_keywords_config": None,
            "subtitle_recognition_id": "", "subtitle_sync": True, "subtitle_taskinfo": [],
            "system_font_list": [], "use_float_render": False,
            "video_mute": False, "zoom_info_params": None,
        },
        "cover": None, "create_time": 0, "draft_type": "video",
        "duration": _us(total_ms),
        "extra_info": None, "fps": 30.0, "free_render_index_mode_on": False,
        "id": draft_id, "is_drop_frame_timecode": False,
        "keyframe_graph_list": [],
        "keyframes": {
            "adjusts": [], "audios": [], "effects": [], "filters": [],
            "handwrites": [], "stickers": [], "texts": [], "videos": [],
        },
        "last_modified_platform": {
            "app_id": 359289, "app_source": "cc", "app_version": _APP_VERSION,
            "device_id": "", "hard_disk_id": "", "mac_address": "",
            "os": "windows", "os_version": "10.0.19045",
        },
        "lyrics_effects": [],
        "materials": {
            "ai_translates": [], "audio_balances": [], "audio_effects": [],
            "audio_fades": [], "audio_pannings": [], "audio_pitch_shifts": [],
            "audio_track_indexes": [],
            "audios": mat_audios,
            "beats": mat_beats,
            "canvases": mat_canvases,
            "chromas": [], "color_curves": [], "common_mask": [],
            "digital_human_model_dressing": [], "digital_humans": [],
            "drafts": [], "effects": [], "flowers": [], "green_screens": [],
            "handwrites": [], "hsl": [], "hsl_curves": [], "images": [],
            "log_color_wheels": [], "loudnesses": [],
            "manual_beautys": [], "manual_deformations": [],
            "material_animations": mat_text_animations,
            "material_colors": mat_mat_colors,
            "multi_language_refs": [],
            "placeholder_infos": mat_placeholders,
            "placeholders": [], "plugin_effects": [], "primary_color_wheels": [],
            "realtime_denoises": [], "shapes": [], "smart_crops": [], "smart_relights": [],
            "sound_channel_mappings": mat_sound_channels,
            "speeds": mat_speeds,
            "stickers": [], "tail_leaders": [], "text_templates": [],
            "texts": mat_texts, "time_marks": [], "transitions": [],
            "video_effects": [], "video_radius": [], "video_shadows": [],
            "video_strokes": [], "video_trackings": [],
            "videos": mat_videos,
            "vocal_beautifys": [],
            "vocal_separations": mat_vocal_seps,
        },
        "mutable_config": None, "name": "", "new_version": _NEW_VERSION, "path": "",
        "platform": {
            "app_id": 359289, "app_source": "cc", "app_version": _APP_VERSION,
            "device_id": "", "hard_disk_id": "", "mac_address": "",
            "os": "windows", "os_version": "10.0.19045",
        },
        "relationships": [], "render_index_track_mode_on": True,
        "retouch_cover": None, "source": "default", "static_cover_image_path": "",
        "time_marks": None,
        "tracks": [
            {"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
             "name": "", "segments": [image_seg], "type": "video"},
            {"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
             "name": "", "segments": [audio_seg], "type": "audio"},
            *([{"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": False,
                "name": "가사", "segments": text_segs, "type": "text"}]
              if text_segs else []),
        ],
        "update_time": 0, "version": 360000,
    }

    meta_values = [
        {
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": _us(total_ms), "enter_from": 0,
            "extra_info": image_path.name,
            "file_Path": image_path.as_posix(),
            "height": 1080, "id": img_local_id,
            "import_time": int(time.time()), "import_time_ms": now_us,
            "item_source": 1, "md5": "", "metetype": "photo",
            "roughcut_time_range": {"duration": _us(total_ms), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0, "width": 1920,
        },
        {
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": _us(total_ms), "enter_from": 0,
            "extra_info": audio_path.name,
            "file_Path": audio_path.as_posix(),
            "height": 0, "id": audio_local_id,
            "import_time": int(time.time()), "import_time_ms": now_us,
            "item_source": 1, "md5": "", "metetype": "music",
            "roughcut_time_range": {"duration": _us(total_ms), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0, "width": 0,
        },
    ]

    draft_meta = {
        "cloud_draft_cover": False, "cloud_draft_sync": False,
        "cloud_package_completed_time": "",
        "draft_cloud_capcut_purchase_info": "", "draft_cloud_last_action_download": False,
        "draft_cloud_package_type": "", "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg", "draft_deeplink_url": "",
        "draft_enterprise_info": {
            "draft_enterprise_extra": "", "draft_enterprise_id": "",
            "draft_enterprise_name": "", "enterprise_material": [],
        },
        "draft_fold_path": "",
        "draft_id": draft_id,
        "draft_is_ae_produce": False, "draft_is_ai_packaging_used": False,
        "draft_is_ai_shorts": False, "draft_is_ai_translate": False,
        "draft_is_article_video_draft": False, "draft_is_cloud_temp_draft": False,
        "draft_is_from_deeplink": "false", "draft_is_invisible": False,
        "draft_is_web_article_video": False,
        "draft_materials": [{"type": 0, "value": meta_values}],
        "draft_materials_copied_info": [],
        "draft_name": f"{song_title}_Lyric",
        "draft_need_rename_folder": False, "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": "",
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": 0,
        "draft_type": "", "draft_web_article_video_enter_from": "",
        "tm_draft_cloud_completed": "", "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0, "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1, "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us, "tm_draft_modified": now_us,
        "tm_draft_removed": 0, "tm_duration": _us(total_ms),
    }

    return draft_content, draft_meta, draft_id


def build_lyric_draft(
    lyric_video_path: Path,
    audio_path: Path,
    song_title: str,
    total_ms: int,
    caption_entries: list = None,
) -> tuple:
    """
    완성된 가사 영상 + 오디오 분리 CapCut 드래프트 생성.

    track[0] — 비디오: 가사 영상 (볼륨 0 — 비주얼 전용)
    track[1] — 오디오: 원본 음원 (CapCut Wave·비트 시각화 지원)
    track[2] — 텍스트: LRC 가사 세그먼트 (싱크 수동 조정용, 선택)

    caption_entries: [{"text": str, "start_ms": int, "end_ms": int}, ...]
    CapCut에서 텍스트 세그먼트를 드래그해 싱크를 직접 조정할 수 있습니다.
    """
    draft_id = _uid()
    now_us = _now_us()

    mat_videos, mat_audios = [], []
    mat_speeds, mat_canvases, mat_placeholders = [], [], []
    mat_sound_channels, mat_mat_colors, mat_vocal_seps, mat_beats = [], [], [], []
    mat_texts, mat_text_animations = [], []

    # 가사 영상 material
    lv_mat_id = _uid()
    lv_local_id = _luid()
    mat_videos.append(_video_mat(lv_mat_id, lv_local_id, lyric_video_path, total_ms))

    # 오디오 material
    audio_mat_id = _uid()
    audio_local_id = _luid()
    mat_audios.append(_audio_mat(audio_mat_id, audio_local_id, audio_path, total_ms))

    # 비디오 세그먼트 보조 material
    v_sid, v_pid, v_cid = _uid(), _uid(), _uid()
    v_scid, v_mcid, v_vsid = _uid(), _uid(), _uid()
    mat_speeds.append(_speed(v_sid))
    mat_placeholders.append(_placeholder(v_pid))
    mat_canvases.append(_canvas(v_cid))
    mat_sound_channels.append(_sound_channel(v_scid))
    mat_mat_colors.append(_mat_color(v_mcid))
    mat_vocal_seps.append(_vocal_sep(v_vsid))

    video_seg = _video_seg(
        mat_id=lv_mat_id,
        src_dur_us=_us(total_ms),
        tgt_start_us=0,
        tgt_dur_us=_us(total_ms),
        speed_id=v_sid, ph_id=v_pid, canvas_id=v_cid,
        sc_id=v_scid, mc_id=v_mcid, vs_id=v_vsid,
        is_loop=False,
    )
    video_seg["volume"] = 0.0  # 가사 영상 내장 오디오 음소거 — 오디오 트랙이 담당

    # 오디오 세그먼트 보조 material
    a_sid, a_pid, a_bid, a_scid, a_vsid = _uid(), _uid(), _uid(), _uid(), _uid()
    mat_speeds.append(_speed(a_sid))
    mat_placeholders.append(_placeholder(a_pid))
    mat_beats.append(_beats(a_bid))
    mat_sound_channels.append(_sound_channel(a_scid))
    mat_vocal_seps.append(_vocal_sep(a_vsid))

    audio_seg = _audio_seg(
        mat_id=audio_mat_id, dur_us=_us(total_ms),
        speed_id=a_sid, ph_id=a_pid, beats_id=a_bid,
        sc_id=a_scid, vs_id=a_vsid,
    )

    # 자막 세그먼트 (LRC 가사 — 싱크 수동 조정용)
    text_segs = []
    for entry in (caption_entries or []):
        t_mat_id = _uid()
        t_speed_id, t_ph_id, t_anim_id = _uid(), _uid(), _uid()
        mat_texts.append(_text_mat(t_mat_id, entry["text"], text_size=22))
        mat_text_animations.append(_text_animation(t_anim_id))
        mat_speeds.append(_speed(t_speed_id))
        mat_placeholders.append(_placeholder(t_ph_id))
        text_segs.append(_text_seg(
            mat_id=t_mat_id,
            start_us=_us(entry["start_ms"]),
            dur_us=_us(entry["end_ms"] - entry["start_ms"]),
            speed_id=t_speed_id, ph_id=t_ph_id, anim_id=t_anim_id,
            y_pos=-0.72,  # 화면 하단부 배치
        ))

    draft_content = {
        "canvas_config": {"background": None, "height": 1080, "ratio": "original", "width": 1920},
        "color_space": -1,
        "config": {
            "adjust_max_index": 1, "attachment_info": [], "combination_max_index": 1,
            "export_range": None, "extract_audio_last_index": 1,
            "lyrics_recognition_id": "", "lyrics_sync": True, "lyrics_taskinfo": [],
            "maintrack_adsorb": True, "material_save_mode": 0,
            "multi_language_current": "none", "multi_language_list": [],
            "multi_language_main": "none", "multi_language_mode": "none",
            "original_sound_last_index": 1, "record_audio_last_index": 1,
            "sticker_max_index": 1, "subtitle_keywords_config": None,
            "subtitle_recognition_id": "", "subtitle_sync": True, "subtitle_taskinfo": [],
            "system_font_list": [], "use_float_render": False,
            "video_mute": False, "zoom_info_params": None,
        },
        "cover": None, "create_time": 0, "draft_type": "video",
        "duration": _us(total_ms),
        "extra_info": None, "fps": 30.0, "free_render_index_mode_on": False,
        "id": draft_id, "is_drop_frame_timecode": False,
        "keyframe_graph_list": [],
        "keyframes": {
            "adjusts": [], "audios": [], "effects": [], "filters": [],
            "handwrites": [], "stickers": [], "texts": [], "videos": [],
        },
        "last_modified_platform": {
            "app_id": 359289, "app_source": "cc", "app_version": _APP_VERSION,
            "device_id": "", "hard_disk_id": "", "mac_address": "",
            "os": "windows", "os_version": "10.0.19045",
        },
        "lyrics_effects": [],
        "materials": {
            "ai_translates": [], "audio_balances": [], "audio_effects": [],
            "audio_fades": [], "audio_pannings": [], "audio_pitch_shifts": [],
            "audio_track_indexes": [],
            "audios": mat_audios,
            "beats": mat_beats,
            "canvases": mat_canvases,
            "chromas": [], "color_curves": [], "common_mask": [],
            "digital_human_model_dressing": [], "digital_humans": [],
            "drafts": [], "effects": [], "flowers": [], "green_screens": [],
            "handwrites": [], "hsl": [], "hsl_curves": [], "images": [],
            "log_color_wheels": [], "loudnesses": [],
            "manual_beautys": [], "manual_deformations": [],
            "material_animations": mat_text_animations,
            "material_colors": mat_mat_colors,
            "multi_language_refs": [],
            "placeholder_infos": mat_placeholders,
            "placeholders": [], "plugin_effects": [], "primary_color_wheels": [],
            "realtime_denoises": [], "shapes": [], "smart_crops": [], "smart_relights": [],
            "sound_channel_mappings": mat_sound_channels,
            "speeds": mat_speeds,
            "stickers": [], "tail_leaders": [], "text_templates": [],
            "texts": mat_texts, "time_marks": [], "transitions": [],
            "video_effects": [], "video_radius": [], "video_shadows": [],
            "video_strokes": [], "video_trackings": [],
            "videos": mat_videos,
            "vocal_beautifys": [],
            "vocal_separations": mat_vocal_seps,
        },
        "mutable_config": None, "name": "", "new_version": _NEW_VERSION, "path": "",
        "platform": {
            "app_id": 359289, "app_source": "cc", "app_version": _APP_VERSION,
            "device_id": "", "hard_disk_id": "", "mac_address": "",
            "os": "windows", "os_version": "10.0.19045",
        },
        "relationships": [], "render_index_track_mode_on": True,
        "retouch_cover": None, "source": "default", "static_cover_image_path": "",
        "time_marks": None,
        "tracks": [
            {"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
             "name": "", "segments": [video_seg], "type": "video"},
            {"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": True,
             "name": "", "segments": [audio_seg], "type": "audio"},
            *([{"attribute": 0, "flag": 0, "id": _uid(), "is_default_name": False,
                "name": "가사 싱크", "segments": text_segs, "type": "text"}]
              if text_segs else []),
        ],
        "update_time": 0, "version": 360000,
    }

    meta_values = [
        {
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": _us(total_ms), "enter_from": 0,
            "extra_info": lyric_video_path.name,
            "file_Path": lyric_video_path.as_posix(),
            "height": 1080, "id": lv_local_id,
            "import_time": int(time.time()), "import_time_ms": now_us,
            "item_source": 1, "md5": "", "metetype": "video",
            "roughcut_time_range": {"duration": _us(total_ms), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0, "width": 1920,
        },
        {
            "ai_group_type": "", "create_time": int(time.time()),
            "duration": _us(total_ms), "enter_from": 0,
            "extra_info": audio_path.name,
            "file_Path": audio_path.as_posix(),
            "height": 0, "id": audio_local_id,
            "import_time": int(time.time()), "import_time_ms": now_us,
            "item_source": 1, "md5": "", "metetype": "music",
            "roughcut_time_range": {"duration": _us(total_ms), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0, "width": 0,
        },
    ]

    draft_meta = {
        "cloud_draft_cover": False, "cloud_draft_sync": False,
        "cloud_package_completed_time": "",
        "draft_cloud_capcut_purchase_info": "", "draft_cloud_last_action_download": False,
        "draft_cloud_package_type": "", "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg", "draft_deeplink_url": "",
        "draft_enterprise_info": {
            "draft_enterprise_extra": "", "draft_enterprise_id": "",
            "draft_enterprise_name": "", "enterprise_material": [],
        },
        "draft_fold_path": "",
        "draft_id": draft_id,
        "draft_is_ae_produce": False, "draft_is_ai_packaging_used": False,
        "draft_is_ai_shorts": False, "draft_is_ai_translate": False,
        "draft_is_article_video_draft": False, "draft_is_cloud_temp_draft": False,
        "draft_is_from_deeplink": "false", "draft_is_invisible": False,
        "draft_is_web_article_video": False,
        "draft_materials": [{"type": 0, "value": meta_values}],
        "draft_materials_copied_info": [],
        "draft_name": f"{song_title}_Lyric",
        "draft_need_rename_folder": False, "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": "",
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": 0,
        "draft_type": "", "draft_web_article_video_enter_from": "",
        "tm_draft_cloud_completed": "", "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0, "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1, "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us, "tm_draft_modified": now_us,
        "tm_draft_removed": 0, "tm_duration": _us(total_ms),
    }

    return draft_content, draft_meta, draft_id


def write_draft(
    draft_content: dict,
    draft_meta: dict,
    draft_id: str,
    capcut_root: Path,
) -> Path:
    """드래프트 폴더 생성 및 파일 쓰기. CapCut이 종료된 상태에서 실행 권장."""
    folder = capcut_root / draft_id
    folder.mkdir(parents=True, exist_ok=True)

    draft_meta["draft_fold_path"] = folder.as_posix()
    draft_meta["draft_root_path"] = capcut_root.as_posix()

    (folder / "draft_content.json").write_text(
        json.dumps(draft_content, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (folder / "draft_meta_info.json").write_text(
        json.dumps(draft_meta, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return folder
