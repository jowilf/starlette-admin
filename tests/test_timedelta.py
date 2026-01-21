from datetime import timedelta

from starlette_admin.helpers import timedelta_to_components


def test_zero_timedelta():
    td = timedelta()
    expected = {
        "weeks": 0,
        "days": 0,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
        "milliseconds": 0,
        "microseconds": 0,
    }
    result = timedelta_to_components(td)
    assert result == expected


def test_only_days():
    td = timedelta(days=10)
    expected = {
        "weeks": 1,
        "days": 3,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
        "milliseconds": 0,
        "microseconds": 0,
    }
    result = timedelta_to_components(td)
    assert result == expected


def test_complex_timedelta():
    td = timedelta(days=15, seconds=3661, microseconds=123456)
    expected = {
        "weeks": 2,
        "days": 1,
        "hours": 1,
        "minutes": 1,
        "seconds": 1,
        "milliseconds": 123,
        "microseconds": 456,
    }
    result = timedelta_to_components(td)
    assert result == expected


def test_no_microseconds():
    td = timedelta(days=7, seconds=86399)
    expected = {
        "weeks": 1,
        "days": 0,
        "hours": 23,
        "minutes": 59,
        "seconds": 59,
        "milliseconds": 0,
        "microseconds": 0,
    }
    result = timedelta_to_components(td)
    assert result == expected


def test_negative_timedelta():
    td = timedelta(days=-7, seconds=-86399)
    expected = {
        "weeks": -2,
        "days": 6,
        "hours": 0,
        "minutes": 0,
        "seconds": 1,
        "milliseconds": 0,
        "microseconds": 0,
    }
    result = timedelta_to_components(td)
    assert result == expected
