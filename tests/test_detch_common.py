import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from fetch.common import (
    parse_cache_control,
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