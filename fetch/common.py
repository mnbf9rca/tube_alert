import contextlib
import logging
from typing import Dict, Any, List
import json
from hashlib import sha256


logger = logging.getLogger(__name__)

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

def hash_dictionary(dict_to_hash: List[Dict[str, Any]]) -> str:
    """Returns a hash representing the current disruption state for change detection."""
    return sha256(json.dumps(dict_to_hash, sort_keys=True).encode()).hexdigest()