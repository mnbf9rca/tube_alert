import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from fetch.disruption import (
    extract_all_disruptions,
    disruption_id_hash,
)

def test_extract_all_disruptions():
    status_json = [
        {"id": "central", "lineStatuses": [
            {"statusSeverity": 10, "reason": "All good"},
            {"statusSeverity": 9, "reason": "Minor delays", "lineId": "central"},
            {"statusSeverity": 9, "reason": "Minor delays", "lineId": "central"},
            {"statusSeverity": 8, "reason": "Major delays", "lineId": "central"},
        ]},
        {"id": "piccadilly", "lineStatuses": [
            {"statusSeverity": 7, "reason": "Closed", "lineId": "piccadilly"},
        ]},
    ]
    disruptions = extract_all_disruptions(status_json)
    expected = [
        {"statusSeverity": 9, "reason": "Minor delays", "lineId": "central"},
        {"statusSeverity": 8, "reason": "Major delays", "lineId": "central"},
        {"statusSeverity": 7, "reason": "Closed", "lineId": "piccadilly"},
    ]
    assert {(d["lineId"], d["reason"]) for d in disruptions} == {(d["lineId"], d["reason"]) for d in expected}

@pytest.mark.parametrize(
    "disruption1,disruption2,should_match",
    [
        ( {"lineId": "central", "reason": "Minor delays"}, {"lineId": "central", "reason": "Minor delays"}, True ),
        ( {"lineId": "central", "reason": "Minor delays"}, {"lineId": "central", "reason": "Major delays"}, False ),
        ( {"lineId": "central", "reason": "Minor delays"}, {"lineId": "piccadilly", "reason": "Minor delays"}, False ),
        ( {"lineId": "central", "reason": "Minor delays"}, {"lineId": "central"}, False ),
    ]
)
def test_disruption_id_hash(disruption1, disruption2, should_match):
    h1 = disruption_id_hash(disruption1)
    h2 = disruption_id_hash(disruption2)
    assert (h1 == h2) == should_match