import requests
import contextlib
import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from notify import notifier  # Importing the notifier module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODES = "tube"  # Comma-separated modes, e.g., "tube,overground"
TFL_LINE_MODE_STATUS_URL = (
    f"https://api.tfl.gov.uk/Line/Mode/{MODES}/Status?detail=true"
)


# --- Pure functions ---
def parse_cache_control(headers: Dict[str, str]) -> int:
    """Extracts max-age from Cache-Control header, returns seconds (default 60 if not found)."""
    cache_control = headers.get("Cache-Control", "")
    for part in cache_control.split(","):
        part = part.strip()
        if "max-age" in part:
            with contextlib.suppress(Exception):
                return int(part.split("=")[1].strip())
    # Default to 60 seconds if not found
    logger.debug("No max-age found in Cache-Control, defaulting to 60 seconds.")
    return 60


def disruption_hash(disruptions: List[Dict[str, Any]]) -> str:
    """Returns a hash representing the current disruption state for change detection."""
    return hashlib.sha256(json.dumps(disruptions, sort_keys=True).encode()).hexdigest()




# --- Side-effectful functions ---
def fetch_status_by_mode() -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Fetches the status of all lines for the specified mode from TFL API."""
    resp = requests.get(TFL_LINE_MODE_STATUS_URL, timeout=10)
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



def sleep_between_cycles(seconds: int):
    logger.info(f"Sleeping for {seconds} seconds before next check.")
    time.sleep(seconds)


def run_cycle_return_timeout(last_disruption_hashes: dict) -> int:
    all_disruptions, cache_timeout = get_disruptions_with_timeout(last_disruption_hashes)
    process_changed_disruptions(last_disruption_hashes, all_disruptions)
    return cache_timeout

def process_changed_disruptions(last_disruption_hashes: dict, all_disruptions: list) -> None:
    """Compares current disruptions with last known state and notifies users of changes."""
    changed_disruptions = []
    for disruption in all_disruptions:
        d_id = disruption_id_hash(disruption)
        d_hash = disruption_hash([disruption])
        if last_disruption_hashes.get(d_id) != d_hash:
            changed_disruptions.append(disruption)
            last_disruption_hashes[d_id] = d_hash
    if changed_disruptions:
        logger.info(f"Detected {len(changed_disruptions)} changed disruptions.")
        notifier.notify_users(changed_disruptions)
    else:
        logger.info("No changes in disruptions detected.")


def get_disruptions_with_timeout(last_disruption_hashes: dict) -> Tuple[List[Dict[str, Any]], int]:
    """Fetches disruptions and returns them along with cache timeout."""
    status_json, headers = fetch_status_by_mode()
    all_disruptions = extract_all_disruptions(status_json)
    logger.info(f"Fetched {len(all_disruptions)} disruptions.")

    # Purge entries for disruptions no longer present to prevent unbounded state growth
    current_ids = {disruption_id_hash(d) for d in all_disruptions}
    to_remove = [k for k in last_disruption_hashes if k not in current_ids]
    for k in to_remove:
        del last_disruption_hashes[k]
    logger.info(f"Removed {len(to_remove)} old disruptions from tracking.")
    cache_timeout = parse_cache_control(headers)
    return all_disruptions, cache_timeout


# --- Main loop ---
def main_loop():
    last_disruption_hashes = {}  # disruption_id_hash -> hash(disruption)
    while True:
        cache_timeout = run_cycle_return_timeout(last_disruption_hashes)
        sleep_between_cycles(cache_timeout)


if __name__ == "__main__":
    main_loop()
