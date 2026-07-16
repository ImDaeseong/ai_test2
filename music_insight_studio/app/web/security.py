from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.analyzers import AudioAnalyzer


@dataclass(frozen=True)
class UploadSecurityPolicy:
    max_upload_bytes: int = 100 * 1024 * 1024
    allowed_extensions: frozenset[str] = frozenset(AudioAnalyzer.SUPPORTED_EXTENSIONS)
    require_known_signature: bool = True


SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".wav": (b"RIFF",),
    ".flac": (b"fLaC",),
    ".mp3": (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"),
    ".ogg": (b"OggS",),
    ".aiff": (b"FORM",),
    ".aif": (b"FORM",),
    ".aifc": (b"FORM",),
    ".caf": (b"caff",),
}


def validate_content_length(length: int, policy: UploadSecurityPolicy = UploadSecurityPolicy()) -> None:
    if length <= 0:
        raise ValueError("Upload body is empty.")
    if length > policy.max_upload_bytes:
        mb = policy.max_upload_bytes // (1024 * 1024)
        raise ValueError(f"Audio upload is too large. Maximum size is {mb} MB for the local web MVP.")


def validate_audio_payload(filename: str, payload: bytes, policy: UploadSecurityPolicy = UploadSecurityPolicy()) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in policy.allowed_extensions:
        supported = ", ".join(sorted(ext.upper().lstrip(".") for ext in policy.allowed_extensions))
        raise ValueError(f"Supported audio files: {supported}. Received: {extension or 'unknown'}")
    if not payload:
        raise ValueError("Audio file is empty.")
    if len(payload) > policy.max_upload_bytes:
        mb = policy.max_upload_bytes // (1024 * 1024)
        raise ValueError(f"Audio file is too large. Maximum size is {mb} MB for the local web MVP.")
    if policy.require_known_signature and not has_expected_audio_signature(extension, payload):
        raise ValueError("Audio file signature does not match its extension. Convert the file to a supported WAV, MP3, FLAC, OGG, AIFF, or CAF file and try again.")


def has_expected_audio_signature(extension: str, payload: bytes) -> bool:
    signatures = SIGNATURES.get(extension.lower())
    if not signatures:
        return False
    head = payload[:16]
    if extension.lower() in {".aiff", ".aif", ".aifc"}:
        return head.startswith(b"FORM") and (b"AIFF" in head or b"AIFC" in head)
    if extension.lower() == ".wav":
        return head.startswith(b"RIFF") and b"WAVE" in head
    return any(head.startswith(signature) for signature in signatures)
