import time
import logging
from typing import Any, Dict, List, Callable
from fetch.disruption import fetch_disruptions_with_timeout

from notify import notifier  # Importing the notifier module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def dumps_json_to_file(data: List[Dict[str, Any]], filename: str):
    """Dumps the JSON data to a file."""
    with open(filename, "w") as f:
        import json

        json.dump(data, f, indent=2)

def sleep_between_cycles(seconds: int):
    logger.info(f"Sleeping for {seconds} seconds before next check.")
    time.sleep(seconds)


# --- Main loop ---
def main_loop():
    last_disruption_hashes = {}  # disruption_id_hash -> hash(disruption)
    while True:
        cache_timeout, changed_disruptions = fetch_disruptions_with_timeout(last_disruption_hashes)
        notify_on_disruption_change(changed_disruptions, notifier.notify_users)
        sleep_between_cycles(cache_timeout)


def notify_on_disruption_change(
    changed_disruptions: List[Dict[str, Any]],
    notify_func: Callable[[List[Dict[str, Any]]], None]
) -> None:
    """Notify users about changes in disruptions."""
    if changed_disruptions:
        logger.info(f"Detected {len(changed_disruptions)} changed disruptions.")
        notify_func(changed_disruptions)
    else:
        logger.info("No changes in disruptions detected.")


if __name__ == "__main__":
    main_loop()
