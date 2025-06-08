import sys
import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.fetch.disruption import (
    extract_all_disruptions,
    disruption_id_hash,
    identify_changed_disruption_items
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

def make_disruption(line_id, reason, extra=None):
    d = {"lineId": line_id, "reason": reason}
    if extra:
        d.update(extra)
    return d

def fake_hash_dictionary(disruptions):
    # Simple deterministic hash for testing
    return str(sorted((d["lineId"], d["reason"]) for d in disruptions))

@pytest.mark.parametrize(
    "last_hashes,all_disruptions,expected",
    [
        # New disruption (not in last_hashes)
        ({}, [make_disruption("central", "Signal failure")], [make_disruption("central", "Signal failure")]),
        # Unchanged disruption (hash matches)
        (
            {disruption_id_hash(make_disruption("central", "Signal failure")): fake_hash_dictionary([make_disruption("central", "Signal failure")])},
            [make_disruption("central", "Signal failure")],
            []
        ),
        # Changed disruption (hash differs)
        (
            {disruption_id_hash(make_disruption("central", "Signal failure")): "oldhash"},
            [make_disruption("central", "Signal failure")],
            [make_disruption("central", "Signal failure")]
        ),
        # Multiple disruptions, one new, one unchanged
        (
            {disruption_id_hash(make_disruption("central", "Signal failure")): fake_hash_dictionary([make_disruption("central", "Signal failure")])},
            [make_disruption("central", "Signal failure"), make_disruption("piccadilly", "Track obstruction")],
            [make_disruption("piccadilly", "Track obstruction")]
        ),
    ]
)
def test_identify_changed_disruption_items(monkeypatch, last_hashes, all_disruptions, expected):
    # Patch hash_dictionary to our fake for deterministic results
    monkeypatch.setattr("app.fetch.disruption.hash_dictionary", fake_hash_dictionary)
    # Copy last_hashes to avoid mutation between tests
    last_hashes = dict(last_hashes)
    result = identify_changed_disruption_items(last_hashes, all_disruptions)
    # Compare by lineId and reason only for simplicity
    def key(d):
        return (d["lineId"], d["reason"])
    assert sorted(map(key, result)) == sorted(map(key, expected))

def test_identify_changed_disruption_items_updates_last_hashes(monkeypatch):
    monkeypatch.setattr("app.fetch.disruption.hash_dictionary", fake_hash_dictionary)
    d = make_disruption("central", "Signal failure")
    last_hashes = {}
    identify_changed_disruption_items(last_hashes, [d])
    assert disruption_id_hash(d) in last_hashes

