import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from fetch.common import (
    parse_cache_control,
    hash_dictionary
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
        ({"Cache-Control": "max-age=0"}, 0),
    ],
)
def test_parse_cache_control(headers, expected):
    assert parse_cache_control(headers) == expected


def test_disruption_hash_changes():
    d1 = [{"lineId": "central", "reason": "Minor delays"}]
    d2 = [{"lineId": "central", "reason": "Good Service"}]
    d3 = [{"reason": "Minor delays", "lineId": "central"}]
    # Different disruptions should have different hashes
    assert hash_dictionary(d1) != hash_dictionary(d2)
    # Identical disruptions (even as new dicts) should have the same hash
    assert hash_dictionary(d1) == hash_dictionary([{**d1[0]}])
    # Hash should be consistent regardless of order
    assert hash_dictionary(d1) == hash_dictionary(d3)

def test_disruption_hash_empty_list():
    # disruption_hash should handle empty list
    assert isinstance(hash_dictionary([]), str)
    # Hash of empty list should be consistent
    assert hash_dictionary([]) == hash_dictionary([])

def test_disruption_hash_multiple_disruptions():
    d1 = [
        {"lineId": "central", "reason": "Minor delays"},
        {"lineId": "district", "reason": "Major delays"},
    ]
    d2 = [
        {"lineId": "central", "reason": "Minor delays"},
        {"lineId": "district", "reason": "Major delays"},
    ]
    d3 = [
        {"lineId": "central", "reason": "Minor delays"},
        {"lineId": "district", "reason": "Good Service"},
    ]
    # Hash should be the same for identical lists
    assert hash_dictionary(d1) == hash_dictionary(d2)
    # Hash should differ if any disruption changes
    assert hash_dictionary(d1) != hash_dictionary(d3)