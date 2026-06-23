import os
import time
import logging
import sys
import requests
import yaml
import json
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Robust path resolution relative to workspace root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOGS_DIR, "telegram_bot.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger("telegram_bot")

# Config loading
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_URL = os.getenv("TELEGRAM_API_URL", "http://127.0.0.1:8000/events/latest?limit=1")
POLL_INTERVAL = int(os.getenv("TELEGRAM_POLL_INTERVAL", 2))
STATE_FILE = os.path.join(LOGS_DIR, "telegram_state.json")

class TelegramAlertBot:
    def __init__(self):
        if not TOKEN or not CHAT_ID:
            log.critical("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment!")
            sys.exit(1)
        
        # Load persisted state
        self.last_timestamp, self.processed_ids = self.load_state()
        
        # Load human-readable camera metadata (name and location)
        self.camera_names = {}
        self.camera_locations = {}
        try:
            cameras_yaml_path = os.path.join(WORKSPACE_ROOT, "configs/cameras.yaml")
            with open(cameras_yaml_path, "r") as f:
                cam_cfg = yaml.safe_load(f) or {}
                for cam in cam_cfg.get("cameras", []):
                    self.camera_names[cam["id"]] = cam.get("name", cam["id"])
                    self.camera_locations[cam["id"]] = cam.get("location", "Packaging Area(3rd Floor)")
            log.info(f"Loaded {len(self.camera_names)} camera config entries.")
        except Exception as e:
            log.warning(f"Could not load camera config: {e}")
            
        log.info("Telegram Alert Bot initialized successfully.")

    def load_state(self) -> tuple[str | None, set]:
        if not os.path.exists(STATE_FILE):
            return None, set()
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                return state.get("last_timestamp"), set(state.get("processed_ids", []))
        except Exception as e:
            log.warning(f"Could not load state file: {e}")
            return None, set()

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            # Keep only the last 100 processed IDs to limit state file size
            ids_list = list(self.processed_ids)
            if len(ids_list) > 100:
                ids_list = ids_list[-100:]
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "last_timestamp": self.last_timestamp,
                    "processed_ids": ids_list
                }, f)
        except Exception as e:
            log.warning(f"Could not save state file: {e}")

    def _build_message(self, event: dict) -> str:
        identity = event.get("identity")
        camera_id = event.get("camera_id", "unknown")
        timestamp = event.get("timestamp", "")
        score = event.get("score", 0.0)
        t = timestamp[11:19] if len(timestamp) >= 19 else timestamp

        # Resolve location metadata (fallback to default)
        location = self.camera_locations.get(camera_id, "Packaging Area(3rd Floor)")

        # HTML character escaper
        def esc(val):
            if val is None:
                return ""
            return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Clean name format: e.g. "kabir_hossen" -> "Kabir Hossen"
        def format_name(raw_id):
            if not raw_id:
                return "An Unauthorized person"
            return " ".join([word.capitalize() for word in raw_id.split("_")])

        clean_location = esc(location)
        clean_camera = esc(camera_id)
        
        if identity:
            clean_identity = format_name(identity)
            headline = "✅ <b>ENTRY DETECTED</b>"
            description = f"<b>{esc(clean_identity)}</b> entered from <b>{clean_camera}</b> door in the <b>{clean_location}</b>"
            return (
                f"{headline}\n"
                f"{description}\n\n"
                f"<b>Camera:</b> {clean_camera}\n"
                f"<b>Time:</b> {esc(t)}\n"
                f"<b>Confidence:</b> {score:.2f}"
            )
        else:
            headline = "🚨 <b>UNKNOWN PERSON DETECTED</b>"
            description = f"An Unauthorized person entered from <b>{clean_camera}</b> door in the <b>{clean_location}</b>"
            return (
                f"{headline}\n"
                f"{description}\n\n"
                f"<b>Camera:</b> {clean_camera}\n"
                f"<b>Time:</b> {esc(t)}\n"
                f"<b>Confidence:</b> {score:.2f}"
            )

    def _send_alert(self, event: dict):
        message = self._build_message(event)
        snapshot = event.get("snapshot")

        # Telegram API endpoints
        text_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

        # Resolve snapshot absolute path
        snapshot_path = None
        if snapshot:
            if os.path.isabs(snapshot):
                snapshot_path = snapshot
            else:
                snapshot_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, snapshot))

        # Check if snapshot exists
        if snapshot_path and os.path.exists(snapshot_path):
            log.info(f"Sending photo alert with snapshot: {snapshot_path}")
            try:
                with open(snapshot_path, "rb") as photo_file:
                    payload = {
                        "chat_id": CHAT_ID,
                        "caption": message,
                        "parse_mode": "HTML"
                    }
                    files = {"photo": photo_file}
                    r = requests.post(photo_url, data=payload, files=files, timeout=10)
                    if r.status_code == 200:
                        log.info("Photo alert sent successfully.")
                        return
                    else:
                        log.error(f"Failed to send photo alert: Status {r.status_code}, Response: {r.text}")
            except Exception as e:
                log.error(f"Exception during photo alert dispatch: {e}")

        # Fallback to text message if photo fails or snapshot does not exist
        log.info("Sending text-only alert fallback...")
        try:
            payload = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            r = requests.post(text_url, json=payload, timeout=5)
            if r.status_code == 200:
                log.info("Text-only alert sent successfully.")
            else:
                log.error(f"Failed to send text alert: Status {r.status_code}, Response: {r.text}")
        except Exception as e:
            log.error(f"Exception during text alert dispatch: {e}")

    def poll(self):
        log.info("Polling API server started.")
        is_startup = (self.last_timestamp is None)
        
        # Parse base URL from TELEGRAM_API_URL configuration
        parsed = urlparse(API_URL)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        while True:
            try:
                # If we have a last_timestamp, query all events since that timestamp to catch up on offline events
                if self.last_timestamp:
                    url = f"{base_url}/events?since={self.last_timestamp}"
                else:
                    url = f"{base_url}/events/latest?limit=20"

                r = requests.get(url, timeout=5)
                if r.status_code != 200:
                    time.sleep(POLL_INTERVAL)
                    continue

                data = r.json()
                events = data if isinstance(data, list) else [data]
                events = [e for e in events if e]

                state_changed = False
                for event in events:
                    event_time = event.get("timestamp")
                    event_id = f"{event_time}_{event.get('track_id')}"

                    if event_id not in self.processed_ids:
                        self.processed_ids.add(event_id)
                        state_changed = True
                        
                        # Only dispatch alerts for new events
                        if not is_startup:
                            log.info(f"New event detected: {event_id}. Dispatching alert...")
                            self._send_alert(event)
                            # Add a tiny delay to ensure chronological message delivery
                            time.sleep(0.5)
                        else:
                            log.debug(f"Startup warmup - skipped past event: {event_id}")

                if is_startup:
                    log.info(f"First-time startup warmup complete. Ingested {len(self.processed_ids)} historical events.")
                    is_startup = False
                    state_changed = True

                if events:
                    # Sort events to ensure self.last_timestamp represents the chronologically latest event
                    events.sort(key=lambda x: x.get("timestamp", ""))
                    new_ts = events[-1].get("timestamp")
                    if new_ts != self.last_timestamp:
                        self.last_timestamp = new_ts
                        state_changed = True

                if state_changed:
                    self.save_state()

            except requests.exceptions.ConnectionError:
                log.warning("FastAPI Server unreachable. Retrying in background...")
            except Exception as e:
                log.error(f"Polling loop error: {e}")

            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    bot = TelegramAlertBot()
    bot.poll()

