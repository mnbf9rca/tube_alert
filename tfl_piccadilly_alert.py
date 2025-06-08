import requests
import contextlib
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

MODES = "tube"  # Comma-separated modes, e.g., "tube,overground"
TFL_LINE_MODE_STATUS_URL = (
    f"https://api.tfl.gov.uk/Line/Mode/{MODES}/Status?detail=true"
)


# --- Pure functions ---
def parse_cache_control(headers: Dict[str, str]) -> int:
    """Extracts max-age from Cache-Control header, returns seconds (default 60 if not found)."""
    cache_control = headers.get("Cache-Control", "")
    for part in cache_control.split(","):
        if "max-age" in part:
            with contextlib.suppress(Exception):
                return int(part.split("=")[1].strip())
    # Default to 60 seconds if not found
    return 60




def disruption_hash(disruptions: List[Dict[str, Any]]) -> str:
    """Returns a hash representing the current disruption state for change detection."""
    return hashlib.sha256(str(disruptions).encode()).hexdigest()


# --- Notification filter: users interested in specific lines ---
# For demo: a dict of line_id -> list of user_ids (could be emails, etc.)
USER_LINE_INTERESTS = {
    "piccadilly": ["user1@example.com"],
    "jubilee": ["user2@example.com"],
    "central": ["user2@example.com"],
    # Add more as needed
}


# --- Side-effectful functions ---
def fetch_status_by_mode() -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    resp = requests.get(TFL_LINE_MODE_STATUS_URL)
    resp.raise_for_status()
    # Convert headers to a regular dict of str to str
    return resp.json(), dict(resp.headers)

def dumps_json_to_file(data: List[Dict[str, Any]], filename: str):
    """Dumps the JSON data to a file."""
    with open(filename, "w") as f:
        import json
        json.dump(data, f, indent=2)


def extract_all_disruptions(status_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all unique disruptions from all lines in the status response."""
    disruptions = []
    seen = set()
    for line in status_json:
        for status in line.get("lineStatuses", []):
            if status.get("statusSeverity", "") != 10:
                reason = status.get("reason", "")
                line_id = status.get("lineId", line.get("id", ""))
                unique_key = (line_id, reason)
                if unique_key not in seen:
                    seen.add(unique_key)
                    disruption = status.copy()
                    # Ensure lineId is present
                    disruption["lineId"] = line_id
                    disruptions.append(disruption)
    return disruptions


def disruption_id_hash(disruption: Dict[str, Any]) -> str:
    """Hash for a disruption, using lineId and reason for uniqueness."""
    key = f"{disruption.get('lineId', '')}|{disruption.get('reason', '')}"
    return hashlib.sha256(key.encode()).hexdigest()


def notify_users(
    disruptions: List[Dict[str, Any]], user_line_interests=USER_LINE_INTERESTS
):
    # Group disruptions by line
    disruptions_by_line = defaultdict(list)
    for d in disruptions:
        disruptions_by_line[d.get("lineId", "")].append(d)
    # Notify users interested in each line
    for line_id, users in user_line_interests.items():
        if line_id in disruptions_by_line:
            for user in users:
                print(f"Notify {user}: Disruption(s) on {line_id} line!")
                for d in disruptions_by_line[line_id]:
                    print(f"  Reason: {d.get('reason', 'No reason provided')}")


def sleep_between_cycles(seconds: int):
    print(f"Sleeping for {seconds} seconds before next check.")
    time.sleep(seconds)


# --- Main loop ---
def main_loop():
    last_disruption_hashes = {}  # disruption_id_hash -> hash(disruption)
    while True:
        status_json, headers = fetch_status_by_mode()
        all_disruptions = extract_all_disruptions(status_json)
        cache_timeout = parse_cache_control(headers)
        changed_disruptions = []
        for disruption in all_disruptions:
            d_id = disruption_id_hash(disruption)
            d_hash = disruption_hash([disruption])
            if last_disruption_hashes.get(d_id) != d_hash:
                changed_disruptions.append(disruption)
                last_disruption_hashes[d_id] = d_hash
        if not changed_disruptions:
            print("No new disruptions.")
            sleep_between_cycles(cache_timeout)
            continue
        notify_users(changed_disruptions)
        sleep_between_cycles(cache_timeout)


if __name__ == "__main__":
    main_loop()
