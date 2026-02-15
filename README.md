# Free Games Reporter

A Matrix bot that automatically finds free PC game giveaways and posts them to your Element/Matrix room. Runs weekly via GitHub Actions.

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

Register a dedicated account on your Matrix homeserver (e.g. `@freegamesbot:pcriot.org`) and join it to the target room.

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
| `MATRIX_HOMESERVER` | `https://pcriot.org` | Your Matrix server URL |
| `MATRIX_USER` | `@freegamesbot:pcriot.org` | Bot's full Matrix user ID |
| `MATRIX_ACCESS_TOKEN` | `syt_...` | Access token from step 1 |
| `MATRIX_ROOM_ID` | `!abcdefg:pcriot.org` | Internal room ID (not the alias) |

> **Tip:** To find the room ID in Element, go to Room Settings → Advanced → Internal room ID.

#### Variables (non-sensitive values)

| Name | Example | Description |
|---|---|---|
| `ALLOWED_PLATFORMS` | `Epic Games Store,Steam,GOG` | Comma-separated list of platforms to track |

### 3. Schedule

The workflow is preconfigured to run **every Monday at 10:00 UTC**. To change the schedule, edit the `cron` expression in [`.github/workflows/free-games.yml`](.github/workflows/free-games.yml):

```yaml
on:
  schedule:
    - cron: "0 10 * * 1"  # Mon 10:00 UTC
```

You can also trigger it manually from the **Actions** tab → **Free Games Reporter** → **Run workflow**.

## Running locally

```bash
pip install -r requirements.txt

export MATRIX_HOMESERVER="https://pcriot.org"
export MATRIX_USER="@freegamesbot:pcriot.org"
export MATRIX_ACCESS_TOKEN="syt_..."
export MATRIX_ROOM_ID="!abcdefg:pcriot.org"
export ALLOWED_PLATFORMS="Epic Games Store,Steam,GOG"

python free_games_bot.py
```

State is saved to `state.json` in the working directory.

## Project structure

```
├── .github/workflows/free-games.yml   # GitHub Actions workflow
├── free_games_bot.py                  # Main bot script
├── requirements.txt                   # Python dependencies
├── state.json                         # Auto-generated sent-game IDs (do not edit)
└── README.md
```

## License

See [LICENSE](LICENSE).
