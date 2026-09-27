import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
import responses
from responses import matchers

import egym
from egym.api import _day, _utc_moment
from fakes import (
    BASE_URL,
    EMAIL,
    EXERCISER_ID,
    GYM_ID,
    MOBILE_API_URL,
    MWA_API_URL,
    PASSWORD,
    add_discovery,
    add_login,
    add_token,
)

AMSTERDAM = ZoneInfo("Europe/Amsterdam")
ZONE = "Europe/Amsterdam"
START = datetime.date(2026, 9, 21)
END = datetime.date(2026, 9, 27)
DATES = {"startDate": "2026-09-21", "endDate": "2026-09-27", "zoneId": ZONE}
TYPES = ["BMI", "WEIGHT_KG"]

SESSION_CASES = [
    (lambda api: api.get_profile(), f"{BASE_URL}/np/exerciser/{EXERCISER_ID}/profile", {}),
    (lambda api: api.get_gyms(), f"{BASE_URL}/np/company/children", {"responseType": "detail"}),
    (
        lambda api: api.get_challenges(),
        f"{BASE_URL}/np/exerciser/{EXERCISER_ID}/challenges",
        {"grouping": "joinStatus"},
    ),
    (
        lambda api: api.get_ranking(),
        f"{MOBILE_API_URL}/analysis/api/v1.0/exercisers/{EXERCISER_ID}/rankingwithleaderboard",
        {"languageCode": "en", "size": 20},
    ),
]

MWA_CASES = [
    (
        lambda api: api.get_workouts(START, END),
        "/workouts/v1.0/workouts",
        {
            "completedAfter": "2026-09-20T22:00:00Z",
            "completedBefore": "2026-09-27T22:00:00Z",
            "gymLocationId": GYM_ID,
            "measurementSystem": "METRIC",
            "locale": "en-GB",
        },
    ),
    (
        lambda api: api.get_available_plans(),
        "/workouts/v1.1/available-plans",
        {"gymLocationId": GYM_ID, "measurementSystem": "METRIC", "locale": "en-GB"},
    ),
    (lambda api: api.get_favourite_activities(), "/workouts/v2.0/favourite-activities", {"gymLocationId": GYM_ID}),
    (lambda api: api.get_bio_age(), "/analysis/v1.0/bio-age", {"locale": "en-GB"}),
    (
        lambda api: api.get_bio_age_summary("month"),
        "/analysis/v1.0/bio-age-monthly-summary",
        {"types": ["MUSCLE", "METABOLIC", "CARDIO", "FLEXIBILITY"], "shift": 0},
    ),
    (
        lambda api: api.get_bio_age_summary("year", shift=1, types=["CARDIO"]),
        "/analysis/v1.0/bio-age-yearly-summary",
        {"types": "CARDIO", "shift": 1},
    ),
    (lambda api: api.get_latest_body_metrics(), "/measurements/v1.0/latest-body-metrics", {}),
    (lambda api: api.get_latest_body_metrics(TYPES), "/measurements/v1.0/latest-body-metrics", {"types": TYPES}),
    (
        lambda api: api.get_body_metrics(TYPES, START, END),
        "/measurements/v1.0/body-metrics",
        {"types": TYPES, "granularity": "ONE_ITEM_PER_DAY", **DATES},
    ),
    (
        lambda api: api.get_body_measurements(TYPES, START, END),
        "/measurements/v1.0/body-measurements-grouped",
        {"types": TYPES, **DATES},
    ),
    (
        lambda api: api.get_cardio_measurements("VO2MAX", START, END),
        "/measurements/v1.0/cardio",
        {"metricType": "VO2MAX", **DATES},
    ),
    (
        lambda api: api.get_cardio_summary("month"),
        "/measurements/v1.0/cardio-measurements-monthly-summary",
        {"shift": 0, "zoneId": ZONE},
    ),
    (
        lambda api: api.get_cardio_summary("year", shift=2),
        "/measurements/v1.0/cardio-measurements-yearly-summary",
        {"shift": 2, "zoneId": ZONE},
    ),
    (lambda api: api.get_strength_measurements(START, END), "/measurements/v1.0/strength", DATES),
    (
        lambda api: api.get_strength_measurements(START, END, activity_id=7),
        "/measurements/v1.0/strength",
        {**DATES, "activityId": 7},
    ),
    (lambda api: api.get_latest_strength_metrics(), "/measurements/v1.0/strength/latest-metrics", {"zoneId": ZONE}),
    (
        lambda api: api.get_latest_strength_metrics([1, 2]),
        "/measurements/v1.0/strength/latest-metrics",
        {"zoneId": ZONE, "activityIds": ["1", "2"]},
    ),
    (lambda api: api.get_muscle_imbalances(), "/analysis/v1.0/muscle-imbalances", {"zoneId": ZONE}),
    (lambda api: api.get_activity_level(), "/analysis/v1.0/activity-levels", {}),
]


@pytest.mark.parametrize("call, url, params", SESSION_CASES)
def test_session_methods(api, mocked, call, url, params):
    mocked.add(
        responses.GET,
        url,
        json={"ok": True},
        match=[
            matchers.query_param_matcher(params),
            matchers.header_matcher({"Cookie": "JSESSIONID=session-1", "X-NP-API-Version": "1.5"}),
        ],
    )
    assert call(api) == {"ok": True}


@pytest.mark.parametrize("call, path, params", MWA_CASES)
def test_mwa_methods(api, mocked, call, path, params):
    add_token(mocked)
    mocked.add(
        responses.GET,
        f"{MWA_API_URL}{path}",
        json=[{"ok": True}],
        match=[
            matchers.query_param_matcher(params),
            matchers.header_matcher({"Authorization": "Bearer token-1"}),
        ],
    )
    assert call(api) == [{"ok": True}]


def test_attributes(api):
    assert (api.base_url, api.exerciser_id, api.gym_id) == (BASE_URL, EXERCISER_ID, GYM_ID)


def test_discovery_used_without_base_url(mocked):
    add_discovery(mocked)
    add_login(mocked)
    assert egym.Api(EMAIL, PASSWORD).base_url == BASE_URL


def test_explicit_zone_overrides_login_timezone(mocked):
    add_login(mocked)
    api = egym.Api(EMAIL, PASSWORD, base_url=BASE_URL, zone="Europe/London")
    add_token(mocked)
    mocked.add(
        responses.GET,
        f"{MWA_API_URL}/analysis/v1.0/muscle-imbalances",
        json={},
        match=[matchers.query_param_matcher({"zoneId": "Europe/London"})],
    )
    api.get_muscle_imbalances()


def test_invalid_zone_fails_before_login(mocked):
    with pytest.raises(ZoneInfoNotFoundError):
        egym.Api(EMAIL, PASSWORD, base_url=BASE_URL, zone="Nowhere/Invalid")
    assert len(mocked.calls) == 0


@pytest.mark.parametrize("period", ["week", "Month", ""])
def test_unknown_period_raises_value_error(api, period):
    with pytest.raises(ValueError):
        api.get_bio_age_summary(period)
    with pytest.raises(ValueError):
        api.get_cardio_summary(period)


def test_logout_returns_none(api, mocked):
    mocked.add(responses.POST, f"{BASE_URL}/np/logout", body="")
    assert api.logout() is None


def test_package_exports():
    assert egym.__all__ == ["Api", "ApiError", "AuthenticationError", "DiscoveryError", "EgymError"]


@pytest.mark.parametrize(
    "value, end, expected",
    [
        (datetime.date(2026, 9, 21), False, "2026-09-20T22:00:00Z"),
        (datetime.date(2026, 9, 27), True, "2026-09-27T22:00:00Z"),
        (datetime.datetime(2026, 9, 21, 8, 30), False, "2026-09-21T06:30:00Z"),
        (datetime.datetime(2026, 9, 21, 8, 30), True, "2026-09-21T06:30:00Z"),
        (datetime.datetime(2026, 9, 21, 8, 30, tzinfo=datetime.timezone.utc), False, "2026-09-21T08:30:00Z"),
        (datetime.date(2026, 10, 25), False, "2026-10-24T22:00:00Z"),
        (datetime.date(2026, 10, 25), True, "2026-10-25T23:00:00Z"),
    ],
)
def test_utc_moment(value, end, expected):
    assert _utc_moment(value, AMSTERDAM, end=end).strftime("%Y-%m-%dT%H:%M:%SZ") == expected


def test_workouts_split_into_30_day_windows(api, mocked):
    add_token(mocked)
    windows = [
        ("2025-12-31T23:00:00Z", "2026-01-30T23:00:00Z"),
        ("2026-01-30T23:00:00Z", "2026-03-01T23:00:00Z"),
        ("2026-03-01T23:00:00Z", "2026-03-15T23:00:00Z"),
    ]
    for number, (after, before) in enumerate(windows, start=1):
        mocked.add(
            responses.GET,
            f"{MWA_API_URL}/workouts/v1.0/workouts",
            json=[{"window": number}],
            match=[
                matchers.query_param_matcher(
                    {
                        "completedAfter": after,
                        "completedBefore": before,
                        "gymLocationId": GYM_ID,
                        "measurementSystem": "METRIC",
                        "locale": "en-GB",
                    }
                )
            ],
        )
    workouts = api.get_workouts(datetime.date(2026, 1, 1), datetime.date(2026, 3, 15))
    assert workouts == [{"window": 1}, {"window": 2}, {"window": 3}]


def test_workouts_empty_range_makes_no_call(api, mocked):
    assert api.get_workouts(datetime.date(2026, 3, 15), datetime.date(2026, 3, 1)) == []
    assert [call.request.url for call in mocked.calls] == [f"{BASE_URL}/np/exerciser/login"]


@pytest.mark.parametrize(
    "value, expected",
    [
        (datetime.date(2026, 9, 21), "2026-09-21"),
        (datetime.datetime(2026, 9, 21, 23, 30), "2026-09-21"),
        (datetime.datetime(2026, 9, 21, 23, 30, tzinfo=datetime.timezone.utc), "2026-09-22"),
    ],
)
def test_day(value, expected):
    assert _day(value, AMSTERDAM) == expected


LONG_TYPES = [f"TYPE_{number}" for number in range(45)]


def add_batch(mocked, path, batch, extra, body):
    mocked.add(
        responses.GET,
        f"{MWA_API_URL}{path}",
        json=body,
        match=[matchers.query_param_matcher({"types": batch, **extra})],
    )


def test_latest_body_metrics_split_into_batches(api, mocked):
    add_token(mocked)
    add_batch(mocked, "/measurements/v1.0/latest-body-metrics", LONG_TYPES[:40], {}, [{"type": "TYPE_0"}])
    add_batch(mocked, "/measurements/v1.0/latest-body-metrics", LONG_TYPES[40:], {}, [{"type": "TYPE_40"}])
    assert api.get_latest_body_metrics(LONG_TYPES) == [{"type": "TYPE_0"}, {"type": "TYPE_40"}]


def test_body_metrics_split_into_batches(api, mocked):
    add_token(mocked)
    extra = {"granularity": "ONE_ITEM_PER_DAY", **DATES}
    add_batch(mocked, "/measurements/v1.0/body-metrics", LONG_TYPES[:40], extra, [{"type": "TYPE_0", "history": []}])
    add_batch(mocked, "/measurements/v1.0/body-metrics", LONG_TYPES[40:], extra, [{"type": "TYPE_40", "history": []}])
    assert api.get_body_metrics(LONG_TYPES, START, END) == [
        {"type": "TYPE_0", "history": []},
        {"type": "TYPE_40", "history": []},
    ]


def test_body_measurements_batches_merged_by_id(api, mocked):
    add_token(mocked)
    path = "/measurements/v1.0/body-measurements-grouped"
    add_batch(
        mocked,
        path,
        LONG_TYPES[:40],
        DATES,
        [
            {"id": 1, "createdAt": "2026-09-02", "metrics": [{"type": "TYPE_0", "value": 1}]},
            {"id": 2, "createdAt": "2026-09-01", "metrics": [{"type": "TYPE_1", "value": 2}]},
        ],
    )
    add_batch(
        mocked,
        path,
        LONG_TYPES[40:],
        DATES,
        [
            {"id": 2, "createdAt": "2026-09-01", "metrics": [{"type": "TYPE_40", "value": 3}]},
            {"id": 3, "createdAt": "2026-08-31", "metrics": [{"type": "TYPE_41", "value": 4}]},
        ],
    )
    assert api.get_body_measurements(LONG_TYPES, START, END) == [
        {"id": 1, "createdAt": "2026-09-02", "metrics": [{"type": "TYPE_0", "value": 1}]},
        {"id": 2, "createdAt": "2026-09-01", "metrics": [{"type": "TYPE_1", "value": 2}, {"type": "TYPE_40", "value": 3}]},
        {"id": 3, "createdAt": "2026-08-31", "metrics": [{"type": "TYPE_41", "value": 4}]},
    ]


def test_single_type_string_is_one_value(api, mocked):
    add_token(mocked)
    add_batch(mocked, "/measurements/v1.0/latest-body-metrics", "BMI", {}, [{"type": "BMI"}])
    assert api.get_latest_body_metrics("BMI") == [{"type": "BMI"}]
