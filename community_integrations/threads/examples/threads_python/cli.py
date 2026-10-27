"""Preview Threads requests and execute them only with an explicit flag."""

from __future__ import annotations

import argparse
import json
import os

from threads_client import ThreadsClient, build_container_request


def parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the educational publisher."""
    root = argparse.ArgumentParser(description="Preview or create a Threads media container")
    root.add_argument("kind", choices=("text", "link", "image", "video"))
    root.add_argument("--text", default="")
    root.add_argument("--url")
    root.add_argument("--alt-text")
    root.add_argument("--execute", action="store_true", help="send the request to Threads")
    return root


def main() -> int:
    """Preview a safe request or explicitly send it using environment credentials."""
    args = parser().parse_args()
    user_id = os.getenv("THREADS_USER_ID", "{threads-user-id}")
    fields: dict[str, object] = {"text": args.text or None}
    media_type = args.kind.upper()
    if args.kind == "link":
        media_type = "TEXT"
        fields["link_attachment"] = _required(args.url, "--url")
    elif args.kind == "image":
        fields.update(image_url=_required(args.url, "--url"), alt_text=args.alt_text)
    elif args.kind == "video":
        fields.update(video_url=_required(args.url, "--url"), alt_text=args.alt_text)
    request = build_container_request(user_id, media_type, **fields)
    if not args.execute:
        print(json.dumps(request.safe_dict(), ensure_ascii=False, indent=2))
        return 0
    if user_id == "{threads-user-id}":
        raise SystemExit("THREADS_USER_ID is required with --execute")
    token = os.getenv("THREADS_ACCESS_TOKEN", "")
    print(json.dumps(ThreadsClient(token).execute(request), ensure_ascii=False, indent=2))
    return 0


def _required(value: str | None, flag: str) -> str:
    """Reject a missing value for the selected content type."""
    if not value:
        raise SystemExit(f"{flag} is required for this content type")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
