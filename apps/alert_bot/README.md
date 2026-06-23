# Telegram Alert Bot Integration Guide

This guide describes how the headless Telegram Alert Bot is structured, where files are saved, and how to run, configure, and test it independently.

---

## 1. File Structure

When adding the Telegram Alert Bot to the surveillance system, the file structure and paths are as follows:

```text
ha_meem_ai_surveillance/
├── .env                          <-- [GIT IGNORED] Bot credentials & API server URLs
├── .env.example                  <-- Template for env configuration
├── .gitignore                    <-- Git rules (ignores state, logs, and sessions)
│
├── apps/
│   └── alert_bot/
│       ├── telegram_bot.py       <-- The Telegram alert bot polling script
│       └── README.md             <-- This guide
│
├── configs/
│   └── cameras.yaml              <-- Camera list mappings (resolves ID -> Name / Location)
│
└── logs/                         <-- [AUTO-CREATED] The logs directory is created on startup
    ├── telegram_bot.log          <-- [AUTO-CREATED] Bot logs (created automatically on first run)
    ├── telegram_state.json       <-- [AUTO-CREATED] [GIT IGNORED] Bot state (created automatically on startup/warmup)
    └── events.jsonl              <-- Real event database containing surveillance logs (written by camera workers)
```

---

## 2. Requirements & Installation

The bot uses lightweight HTTP requests instead of heavy browser engines. Install the following libraries:

```bash
pip install requests PyYAML python-dotenv
```

---

## 3. Configuration (`.env`)

Add the following keys to your `.env` file at the root of the workspace. Do **not** commit this file to git.

```ini
# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_CHAT_ID="your_chat_id_or_channel_id_here"

# API & Polling Configuration
TELEGRAM_API_URL="http://127.0.0.1:8000/events/latest?limit=20"
TELEGRAM_POLL_INTERVAL=2
```

---

## 4. Git Ignore Rules (`.gitignore`)

Add the following entries to your `.gitignore` file to avoid checking in local logs, state files, or credentials:

```text
# Credentials
.env

# Bot Logs & Persistent States
logs/telegram_state.json
logs/telegram_bot.log
```
*(Note: If `/logs/` is already in your `.gitignore`, all files inside the `logs/` directory will be ignored automatically).*

---

## 5. Demo Setup & Mock Files

To check if the bot catches up on events that occurred while it was offline, configure the following:

### A. Demo Location Configuration (`configs/cameras.yaml`)
Create or edit this file to map camera IDs to names and locations:
```yaml
cameras:
  - id: camera_01
    name: Front Entrance
    location: "Packaging Area(3rd Floor)"
    enabled: true
```

### B. Simulating Events in `logs/events.jsonl`
If you are testing offline catch-up, you can simulate events by manually appending logs to `logs/events.jsonl` (the same database file written to by the surveillance workers):
```json
{"timestamp": "2026-06-23T23:40:00.000000", "camera_id": "camera_01", "track_id": 9301, "identity": null, "score": 0.42, "event": "UNKNOWN", "snapshot": "test_snapshot.jpg"}
{"timestamp": "2026-06-23T23:41:00.000000", "camera_id": "camera_01", "track_id": 9302, "identity": "kabir_hossen", "score": 0.95, "event": "AUTHORIZED", "snapshot": "test_snapshot.jpg"}
```

---

## 6. How to Run & Verify Offline Catch-up

Follow this exact sequence to test that the bot detects events added while it was offline:

### Step 1: Start the API Server
In one terminal window, start the FastAPI server (which serves surveillance event log data from `logs/events.jsonl`):
```bash
python -m apps.api_server.main
```

### Step 2: Initialize the Bot State (First Startup Warmup)
In a separate terminal window, start the Telegram bot:
```bash
python -m apps.alert_bot.telegram_bot
```
The bot will perform a warmup, ingest the existing events in `events.jsonl` to establish its baseline timestamp (`23:41:00`), and automatically create `logs/telegram_state.json` and `logs/telegram_bot.log`. It will **not** send duplicate alerts for these existing events.

### Step 3: Stop the Bot (Go Offline)
Stop the bot process using `Ctrl+C`. Keep the API server running!

### Step 4: Append Offline Events
With the bot stopped, append three new mock events to the end of `logs/events.jsonl` (e.g. chronologically after `23:41:00`):
```bash
echo '{"timestamp": "2026-06-23T23:45:00.000000", "camera_id": "camera_01", "track_id": 9401, "identity": null, "score": 0.45, "event": "UNKNOWN", "snapshot": "test_snapshot.jpg"}' >> logs/events.jsonl
echo '{"timestamp": "2026-06-23T23:46:00.000000", "camera_id": "camera_01", "track_id": 9402, "identity": "towhid_islam", "score": 0.90, "event": "AUTHORIZED", "snapshot": "test_snapshot.jpg"}' >> logs/events.jsonl
echo '{"timestamp": "2026-06-23T23:47:00.000000", "camera_id": "camera_01", "track_id": 9403, "identity": null, "score": 0.48, "event": "UNKNOWN", "snapshot": "test_snapshot.jpg"}' >> logs/events.jsonl
```

### Step 5: Restart the Bot
Start the bot again:
```bash
python -m apps.alert_bot.telegram_bot
```
The bot will load `logs/telegram_state.json`, recognize that it was offline since `23:41:00`, fetch all events since that timestamp via `/events?since=23:41:00`, detect the three new events, and dispatch the alerts to your Telegram chat chronologically.
