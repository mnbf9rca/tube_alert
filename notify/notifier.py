import logging
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Notification filter: users interested in specific lines ---
# For demo: a dict of line_id -> list of user_ids (could be emails, etc.)
USER_LINE_INTERESTS = {
    "piccadilly": ["user1@example.com"],
    "jubilee": ["user2@example.com"],
    "central": ["user2@example.com"],
    # Add more as needed
}
def notify_users(
    disruptions: List[Dict[str, Any]], user_line_interests=USER_LINE_INTERESTS
):
    # Group disruptions by line
    disruptions_by_line = defaultdict(list)
    for d in disruptions:
        line_id = d.get("lineId", "").lower()
        disruptions_by_line[line_id].append(d)
    logger.info(f"lines with disruptions: {list(disruptions_by_line.keys())}")
    # Notify users interested in each line
    for line_id, users in user_line_interests.items():
        normalized_line_id = line_id.lower()
        if normalized_line_id in disruptions_by_line:
            logger.info(f"Notifying users for line: {normalized_line_id}")
            for user in users:
                print(f"Notify {user}: Disruption(s) on {line_id} line!")
                for d in disruptions_by_line[normalized_line_id]:
                    print(f"  Reason: {d.get('reason', 'No reason provided')}")

