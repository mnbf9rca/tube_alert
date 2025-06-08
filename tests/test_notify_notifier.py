import sys
import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.notify.notifier import notify_users

def test_notify_users(capsys):
    disruptions = [
        {"lineId": "piccadilly", "reason": "Closed for maintenance"},
        {"lineId": "central", "reason": "Minor delays"},
    ]
    user_line_interests = {
        "piccadilly": ["alice@example.com"],
        "central": ["bob@example.com", "carol@example.com"],
        "jubilee": ["nobody@example.com"],
    }
    notify_users(disruptions, user_line_interests)
    out = capsys.readouterr().out
    assert "Notify alice@example.com: Disruption(s) on piccadilly line!" in out
    assert "Notify bob@example.com: Disruption(s) on central line!" in out
    assert "Notify carol@example.com: Disruption(s) on central line!" in out
    assert "Closed for maintenance" in out
    assert "Minor delays" in out
    assert "jubilee" not in out