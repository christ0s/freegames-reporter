#!/usr/bin/env python3
"""
Free Games Reporter — Matrix Bot
=================================
Fetches free PC game giveaways from the GamerPower API, filters by allowed
platforms, and posts new finds to a Matrix room.  Sent-game IDs are tracked
in a local ``state.json`` which the GitHub Actions workflow commits back to
the repository after each successful run.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import sys

import requests
from nio import AsyncClient, RoomSendResponse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GAMERPOWER_API = "https://www.gamerpower.com/api/giveaways?type=game&platform=pc"
HTTP_TIMEOUT = 30  # seconds

MATRIX_HOMESERVER = os.environ["MATRIX_HOMESERVER"]
MATRIX_USER = os.environ["MATRIX_USER"]
MATRIX_ACCESS_TOKEN = os.environ["MATRIX_ACCESS_TOKEN"]
MATRIX_ROOM_ID = os.environ["MATRIX_ROOM_ID"]

ALLOWED_PLATFORMS = [
    p.strip()
    for p in os.environ.get("ALLOWED_PLATFORMS", "Epic Games Store,Steam,GOG").split(",")
    if p.strip()
]

STATE_FILE = pathlib.Path(os.environ.get("STATE_FILE", "state.json"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# File-based State Persistence
# ---------------------------------------------------------------------------


def load_sent_ids() -> set[int]:
    """Read previously sent IDs from state.json. Returns empty set on first run."""
    if not STATE_FILE.exists():
        log.info("No state file found — first run, starting fresh.")
        return set()
    try:
        data = json.loads(STATE_FILE.read_text())
        log.info("Loaded %d previously sent game IDs from %s.", len(data), STATE_FILE)
        return set(data)
    except (json.JSONDecodeError, TypeError):
        log.warning("Corrupt state file — starting fresh.")
        return set()


def save_sent_ids(ids: set[int]) -> None:
    """Write sent IDs to state.json (sorted for stable diffs)."""
    STATE_FILE.write_text(json.dumps(sorted(ids), indent=2) + "\n")
    log.info("Saved %d sent game IDs to %s.", len(ids), STATE_FILE)


# ---------------------------------------------------------------------------
# GamerPower API
# ---------------------------------------------------------------------------


def fetch_giveaways() -> list[dict]:
    """Fetch the current PC game giveaways from GamerPower."""
    resp = requests.get(GAMERPOWER_API, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    # The API returns a JSON array on success, or a status-message object
    # when there are zero results.
    if isinstance(data, dict) and data.get("status") == 0:
        log.info("GamerPower returned zero active giveaways.")
        return []
    if not isinstance(data, list):
        log.warning("Unexpected GamerPower response: %s", data)
        return []
    return data


def filter_giveaways(
    giveaways: list[dict],
    sent_ids: set[int],
    allowed_platforms: list[str],
) -> list[dict]:
    """Keep only unsent giveaways whose platform matches the allow-list."""
    new = []
    allowed_lower = [p.lower() for p in allowed_platforms]

    for gw in giveaways:
        gw_id = gw.get("id")
        if gw_id in sent_ids:
            continue

        # The "platforms" field may contain comma-separated values like
        # "PC, PlayStation 4".  We check if any token matches the allow-list.
        platforms_raw = gw.get("platforms", "")
        gw_platforms = [p.strip().lower() for p in platforms_raw.split(",")]

        if any(p in allowed_lower for p in gw_platforms):
            new.append(gw)

    return new


# ---------------------------------------------------------------------------
# Matrix Messaging
# ---------------------------------------------------------------------------


def _build_message(gw: dict) -> tuple[str, str]:
    """Return (plain_text, html) for a single game giveaway."""
    title = gw.get("title", "Unknown Game")
    platforms = gw.get("platforms", "N/A")
    link = gw.get("open_giveaway_url") or gw.get("open_giveaway") or gw.get("gamerpower_url", "")
    end_date = gw.get("end_date", "N/A")
    worth = gw.get("worth", "N/A")

    plain = (
        f"\U0001f3ae New Free Game: {title}\n"
        f"\U0001f3e2 Platform: {platforms}\n"
        f"\U0001f4b0 Worth: {worth}\n"
        f"\U0001f517 Claim here: {link}\n"
        f"\u23f3 Expires: {end_date}"
    )
    html = (
        f"<b>\U0001f3ae New Free Game: {title}</b><br/>"
        f"\U0001f3e2 Platform: {platforms}<br/>"
        f"\U0001f4b0 Worth: {worth}<br/>"
        f'\U0001f517 Claim here: <a href="{link}">{link}</a><br/>'
        f"\u23f3 Expires: {end_date}"
    )
    return plain, html


async def send_to_matrix(giveaways: list[dict]) -> list[int]:
    """Send one message per game to the Matrix room. Return IDs that were sent successfully."""
    client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER)
    client.access_token = MATRIX_ACCESS_TOKEN
    client.user_id = MATRIX_USER
    client.device_id = "FREEGAMES_BOT"

    successfully_sent: list[int] = []

    try:
        for gw in giveaways:
            plain, html = _build_message(gw)
            content = {
                "msgtype": "m.text",
                "body": plain,
                "format": "org.matrix.custom.html",
                "formatted_body": html,
            }
            resp = await client.room_send(
                room_id=MATRIX_ROOM_ID,
                message_type="m.room.message",
                content=content,
            )
            if isinstance(resp, RoomSendResponse):
                gw_id = gw["id"]
                log.info("Sent message for '%s' (id=%d).", gw["title"], gw_id)
                successfully_sent.append(gw_id)
            else:
                log.error("Failed to send message for '%s': %s", gw.get("title"), resp)
    finally:
        await client.close()

    return successfully_sent


# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------


async def main() -> int:
    log.info("=== Free Games Reporter starting ===")
    log.info("Homeserver: %s", MATRIX_HOMESERVER)
    log.info("Allowed platforms: %s", ALLOWED_PLATFORMS)

    # 1. Load persisted state
    sent_ids = load_sent_ids()

    # 2. Fetch giveaways
    giveaways = fetch_giveaways()
    log.info("GamerPower returned %d active giveaway(s).", len(giveaways))

    # 3. Filter
    new_giveaways = filter_giveaways(giveaways, sent_ids, ALLOWED_PLATFORMS)
    if not new_giveaways:
        log.info("No new giveaways to report. Done.")
        return 0
    log.info("Found %d new giveaway(s) to report.", len(new_giveaways))

    # 4. Send to Matrix — collect only successfully sent IDs
    sent_now = await send_to_matrix(new_giveaways)
    if not sent_now:
        log.warning("No messages were sent successfully.")
        return 0

    # 5. Update state ONLY with successfully sent IDs (don't corrupt on partial failure)
    sent_ids.update(sent_now)
    save_sent_ids(sent_ids)

    log.info("=== Free Games Reporter finished — %d new game(s) posted ===", len(sent_now))
    return 0


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except Exception:
        log.exception("Critical unhandled error.")
        sys.exit(1)
    sys.exit(rc)
