#!/bin/bash
set -e

# Set the state file path
STATE_FILE="${STATE_FILE:-/app/storage/state.json}"

# Ensure the directory exists
mkdir -p "$(dirname "$STATE_FILE")"

# Ensure the state.json file exists
if [ ! -f "$STATE_FILE" ]; then
  echo "{}" > "$STATE_FILE"
  echo "Created new state file at $STATE_FILE"
else
  echo "ℹ️ State file already exists at $STATE_FILE"
fi

# Handle signals
trap 'echo \"Caught signal, exiting...\"; exit 1' SIGINT SIGTERM

while true; do
  echo \"Running free_games_bot.py...\"
  python free_games_bot.py
  echo \"Finished running free_games_bot.py. Sleeping for 86400 seconds...\"
  sleep 86400  # Check for new games every day
done

