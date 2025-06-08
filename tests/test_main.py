import pytest
from main import (
    parse_cache_control,
    disruption_hash,
    extract_all_disruptions,
    disruption_id_hash,
    notify_users,
)

@pytest.mark.parametrize(
    "headers,expected",
    [
        ({"Cache-Control": "public, must-revalidate, max-age=30, s-maxage=60"}, 30),
        ({"Cache-Control": "max-age=120"}, 120),
        ({"Cache-Control": "no-cache"}, 60),
        ({}, 60),
        ({"Cache-Control": "max-age=notanint"}, 60),
        ({"Cache-Control": "public, max-age=45, foo=bar"}, 45),
        ({"Cache-Control": "public, s-maxage=60"}, 60),
    ],
)
def test_parse_cache_control(headers, expected):
    assert parse_cache_control(headers) == expected

def test_disruption_hash_changes():
    d1 = [{"lineId": "central", "reason": "Minor delays"}]
    d2 = [{"lineId": "central", "reason": "Good Service"}]
    assert disruption_hash(d1) != disruption_hash(d2)
    assert disruption_hash(d1) == disruption_hash([{**d1[0]}])

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
