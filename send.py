#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from board_renderer import render_market_board
from market_data import build_snapshot


def load_webhook_url() -> str | None:
    env_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if env_url:
        return env_url

    file_env = os.environ.get("DISCORD_WEBHOOK_FILE", "").strip()
    if file_env:
        path = Path(file_env).expanduser()
        if path.exists():
            return path.read_text(encoding="utf-8").strip()

    for candidate in (
        Path.home() / "btc-tools" / "webhook" / "MarketBoard",
        Path.home() / "btc-tools" / "webhook" / "market-board",
    ):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    return None


def upload_to_discord(webhook_url: str, screenshot_path: Path, content: str) -> None:
    payload = json.dumps({"content": content}, ensure_ascii=False)
    subprocess.run(
        [
            "curl",
            "-fsS",
            "-F",
            f"file=@{screenshot_path}",
            "--form-string",
            f"payload_json={payload}",
            webhook_url,
        ],
        check=True,
    )


def build_content(snapshot: dict) -> str:
    timestamp = snapshot["timestamp"]
    market_count = len(snapshot["markets"])
    index_price = snapshot["indexPrice"]
    net_cvd = snapshot["summary"]["netCvd5mUsd"]
    return (
        f"market-board | markets={market_count} | index={index_price:.1f} | "
        f"net_cvd_5m={net_cvd:,.0f} | ts={timestamp}"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render market-board and send to Discord")
    parser.add_argument("--output", default="/tmp/market-board.png", help="PNG output path")
    parser.add_argument("--no-discord", action="store_true", help="skip Discord upload")
    args = parser.parse_args(argv)

    snapshot = build_snapshot()
    screenshot_path = Path(args.output).expanduser()
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    render_market_board(snapshot, screenshot_path)

    content = build_content(snapshot)
    webhook_url = load_webhook_url()
    if args.no_discord or not webhook_url:
        print(screenshot_path)
        if not webhook_url and not args.no_discord:
            print("discord webhook not configured; screenshot only", file=sys.stderr)
        return 0

    upload_to_discord(webhook_url, screenshot_path, content)
    print(screenshot_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
