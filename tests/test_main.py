import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from unittest.mock import patch

from main import notify_on_disruption_change

def test_notify_on_disruption_change():
    disruptions = [
        {"lineId": "piccadilly", "reason": "Closed for maintenance"},
        {"lineId": "central", "reason": "Minor delays"},
    ]
    
    # Mock the notifier to capture output
    mock_notify = patch('notify.notifier.notify_users').start()
    mock_notify.return_value = None  # Mock the return value
    # Call the function with mocked notifier
    notify_on_disruption_change(disruptions, mock_notify)
    # Assert that the notifier was called with the disruptions
    assert mock_notify.called
    assert mock_notify.call_count == 1
    assert mock_notify.call_args[0][0] == disruptions

