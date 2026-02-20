# Free Games Reporter

A Matrix bot that automatically finds free PC game giveaways and posts them to your Element/Matrix room. Runs every 3 days via GitHub Actions.

## How it works

1. Fetches active PC game giveaways from the [GamerPower API](https://www.gamerpower.com/api-doc)
2. Filters by your allowed platforms (e.g. Steam, Epic Games Store, GOG)
3. Sends a formatted message to your Matrix room for each new game
4. Commits a `state.json` file back to the repo so games are never posted twice

## Example message

```
🎮 New Free Game: Some Awesome Game
🏢 Platform: Steam
💰 Worth: $19.99
🔗 Claim here: https://store.steampowered.com/...
⏳ Expires: 2026-03-01
```

## Setup

### 1. Create a Matrix bot account

Register a dedicated account on your Matrix homeserver (e.g. `@freegamesbot:matrix.org`) and join it to the target room.

Obtain an access token — the easiest way is via `curl`:

```bash
curl -X POST "https://YOUR_HOMESERVER/_matrix/client/v3/login" \
  -H "Content-Type: application/json" \
  -d '{"type":"m.login.password","user":"freegamesbot","password":"YOUR_PASSWORD"}'
```

Copy the `access_token` from the response.

### 2. Configure GitHub repository secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository.

#### Secrets (sensitive values)

| Name | Example | Description |
|---|---|---|
| `MATRIX_HOMESERVER` | `https://matrix.org` | Your Matrix server URL |
| `MATRIX_USER` | `@freegamesbot:matrix.org` | Bot's full Matrix user ID |
| `MATRIX_ACCESS_TOKEN` | `syt_...` | Access token from step 1 |
| `MATRIX_ROOM_ID` | `#myroom:matrix.org` | Room alias or internal ID (`!abc:matrix.org`) |

> **Tip:** The room alias (e.g. `#myroom:matrix.org`) is the easiest to use. You can find it in Element under Room Settings → General. The internal ID (`!...`) from Room Settings → Advanced also works.

#### Variables (non-sensitive values)

| Name | Example | Description |
|---|---|---|
| `ALLOWED_PLATFORMS` | `Epic Games Store,Steam,GOG` | Comma-separated list of platforms to track |

### 3. Schedule

The workflow is preconfigured to run **every 3 days at 10:00 UTC**. To change the schedule, edit the `cron` expression in [`.github/workflows/free-games.yml`](.github/workflows/free-games.yml):

```yaml
on:
  schedule:
    - cron: "0 10 */3 * *"  # Every 3 days at 10:00 UTC
```

You can also trigger it manually from the **Actions** tab → **Free Games Reporter** → **Run workflow**.

## Running locally

```bash
pip install -r requirements.txt

export MATRIX_HOMESERVER="https://yourMatrixHomeServer.org"
export MATRIX_USER="@freegamesbot:yourMatrixHomeServer.org"
export MATRIX_ACCESS_TOKEN="syt_..."
export MATRIX_ROOM_ID="!abcdefg:yourMatrixHomeServer.org"
export ALLOWED_PLATFORMS="Epic Games Store,Steam,GOG"

python free_games_bot.py
```

State is saved to `state.json` in the working directory.

## Docker Installation

### Prerequisites

- Docker installed on your machine.
- Access to a terminal or command prompt.

### Steps to Run with Docker

1. **Clone the repository and create an `.env` file:**

   Copy the .env.example to .env and set your variables


2. **Build the Docker Image:**

   ```bash
   docker build -t free-games-bot .
   ```

3. **Run the Docker Container:**

   ```bash
   docker run \
   --name free_games_bot_docker \
      --env-file .env \
      -v ./storage:/app/storage \
      -d \
      free-games-bot
   ```

4. **Verify the Bot is Running:**

   Ensure that the Docker container is running with:

   ```bash
   docker ps
   ```

5. **Inspect Logs (Optional):**

   If you encounter any issues, check the logs to troubleshoot:

   ```bash
   docker logs -f <container_id>
   ```

### Steps to Run with Docker Compose

1. **Clone the repository and create an `.env` file:**

   Rename the ".env.example" to ".env" and set your variables


2. **Build and Run the Docker Compose Stack:**

   ```bash
   docker-compose up --build -d
   ```

3. **Verify the Bot is Running:**

   Ensure that the Docker container is running with:

   ```bash
   docker ps
   ```

4. **Inspect Logs (Optional):**

   If you encounter any issues, check the logs to troubleshoot:

   ```bash
   docker-compose logs -f
   ```

### Notes

- Docker installation uses a volume (./storage:/app/storage) to persist the state.json file across container restarts. The STATE_FILE environment variable is set to /app/storage/state.json to ensure the file is stored in the correct location inside the container.
- Docker is configured to check for free PC games every day. If you need to change the frequency you can edit the entrypoint.sh and set sleep to your liking. (in seconds)

## Project structure

```
.
├── .env.example                    # Example environment variables file (for Docker)
├── .github/                        # GitHub Actions and other GitHub-related files
│   └── workflows/                  # GitHub Actions workflows
│       └── free-games.yml          # Workflow file for running the bot every 3 days
├── Dockerfile                      # Docker configuration file
├── README.md                       # This file — instructions and documentation
├── free_games_bot.py               # Main Python script for the bot
├── entrypoint.sh                   # Script to run the bot inside the Docker container
├── requirements.txt                # Python dependencies for the bot
├── state.json                      # Auto-generated file storing sent-game IDs
└── docker-compose.yml              # Docker Compose configuration (optional, for easier Docker setup)
```

## License

See [LICENSE](LICENSE).
