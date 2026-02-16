#!/bin/bash
set -e

STATE_FILE="${STATE_FILE:-/app/storage/state.json}"
mkdir -p "$(dirname "$STATE_FILE")"

while true; do
  python free_games_bot.py
  sleep 86400  # Check for new games every day
done
