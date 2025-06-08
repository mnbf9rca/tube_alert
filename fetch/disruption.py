import json
from hashlib import sha256
import logging
import requests
from .common import parse_cache_control
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODES = "tube"  # Comma-separated modes, e.g., "tube,overground"
TFL_LINE_MODE_STATUS_URL = (
    f"https://api.tfl.gov.uk/Line/Mode/{MODES}/Status?detail=true"
)

def disruption_hash(disruptions: List[Dict[str, Any]]) -> str:
    """Returns a hash representing the current disruption state for change detection."""
    return sha256(json.dumps(disruptions, sort_keys=True).encode()).hexdigest()


def fetch_disruptions_with_timeout(last_disruption_hashes: dict) -> Tuple[int, List[Dict[str, Any]]]:
    all_disruptions, cache_timeout = get_disruptions_with_timeout(last_disruption_hashes)
    changed_disruption = process_changed_disruptions(last_disruption_hashes, all_disruptions)
    return cache_timeout, changed_disruption

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

def fetch_status_by_mode() -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Fetches the status of all lines for the specified mode from TFL API."""
    resp = requests.get(TFL_LINE_MODE_STATUS_URL, timeout=10)
    resp.raise_for_status()
    # Convert headers to a regular dict of str to str
    return resp.json(), dict(resp.headers)

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
    return sha256(key.encode()).hexdigest()

def process_changed_disruptions(last_disruption_hashes: dict, all_disruptions: list) -> List[Dict[str, Any]]:
    """Compares current disruptions with last known state and returns changed disruptions."""
    changed_disruptions = []
    for disruption in all_disruptions:
        d_id = disruption_id_hash(disruption)
        d_hash = disruption_hash([disruption])
        if last_disruption_hashes.get(d_id) != d_hash:
            changed_disruptions.append(disruption)
            last_disruption_hashes[d_id] = d_hash
    return changed_disruptions