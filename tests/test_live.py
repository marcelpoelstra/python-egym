import datetime
import os

import pytest

import egym

pytestmark = pytest.mark.skipif(
    not (os.environ.get("EGYM_EMAIL") and os.environ.get("EGYM_PASSWORD")),
    reason="set EGYM_EMAIL and EGYM_PASSWORD to run the live tests",
)

HISTORY_START = datetime.date(2019, 1, 1)
TODAY = datetime.date.today()
YEARS = [
    (datetime.date(year, 1, 1), min(datetime.date(year, 12, 31), TODAY))
    for year in range(HISTORY_START.year, TODAY.year + 1)
]
BODY_TYPES = ["BMI", "BODY_FAT_PERCENTS", "WEIGHT_KG"]
BIO_AGE_TYPES = ["MUSCLE", "METABOLIC", "CARDIO", "FLEXIBILITY"]
CARDIO_METRICS = ["RESTING_HEART_RATE", "VO2MAX", "BLOOD_PRESSURE"]


def has_keys(value, *keys):
    return isinstance(value, dict) and set(keys) <= set(value)


@pytest.fixture(scope="module")
def api():
    client = egym.Api(os.environ["EGYM_EMAIL"], os.environ["EGYM_PASSWORD"])
    yield client
    client.logout()


def test_profile(api):
    profile = api.get_profile()
    assert has_keys(profile, "uuid", "email", "homeClubUuid")
    assert profile["uuid"] == api.exerciser_id
    assert profile["homeClubUuid"] == api.gym_id


def test_gyms(api):
    gyms = api.get_gyms()
    assert gyms and all(has_keys(gym, "uuid", "name", "timezone") for gym in gyms)
    assert api.gym_id in {gym["uuid"] for gym in gyms}


def test_challenges(api):
    assert has_keys(api.get_challenges(), "joined", "unjoined")


def test_workouts_full_history(api):
    workouts = [workout for start, end in YEARS for workout in api.get_workouts(start, end)]
    assert workouts
    for workout in workouts:
        assert has_keys(workout, "completedAt", "timezone", "exercises")
        for exercise in workout["exercises"]:
            assert has_keys(exercise, "id", "label", "activity", "sets")
            for workout_set in exercise["sets"]:
                assert has_keys(workout_set, "setType", "numberOfReps", "weight")


def test_available_plans(api):
    assert all(has_keys(plan, "id", "name") for plan in api.get_available_plans())


def test_favourite_activities(api):
    assert all(has_keys(activity, "activityId") for activity in api.get_favourite_activities())


def test_bio_age(api):
    assert has_keys(
        api.get_bio_age(),
        "totalDetails",
        "metabolicDetails",
        "flexibilityDetails",
        "cardioBioAgeDetails",
        "strengthBioAgeDetails",
    )


@pytest.mark.parametrize("types", [None] + [[bio_age_type] for bio_age_type in BIO_AGE_TYPES])
@pytest.mark.parametrize("period", ["month", "year"])
def test_bio_age_summary(api, period, types):
    current = api.get_bio_age_summary(period, shift=0, types=types)
    previous = api.get_bio_age_summary(period, shift=1, types=types)
    assert has_keys(current, "rangeStart", "rangeEnd", "current")
    assert has_keys(previous, "rangeStart", "rangeEnd", "current")
    assert previous["rangeEnd"] < current["rangeStart"]


def test_latest_body_metrics(api):
    metrics = api.get_latest_body_metrics()
    assert metrics and all(has_keys(metric, "type", "value", "createdAt") for metric in metrics)
    assert {metric["type"] for metric in api.get_latest_body_metrics(BODY_TYPES)} <= set(BODY_TYPES)


@pytest.mark.parametrize("granularity", ["ONE_ITEM_PER_DAY", "ONE_ITEM_PER_MONTH"])
def test_body_metrics_history(api, granularity):
    for body_type in BODY_TYPES:
        items = api.get_body_metrics([body_type], HISTORY_START, TODAY, granularity)
        assert all(has_keys(item, "type", "history") and item["type"] == body_type for item in items)
        assert all(has_keys(point, "date", "value") for item in items for point in item["history"])


def test_body_measurements_full_history(api):
    whole = api.get_body_measurements(BODY_TYPES, HISTORY_START, TODAY)
    per_year = [api.get_body_measurements(BODY_TYPES, start, end) for start, end in YEARS]
    assert whole and len(whole) == sum(map(len, per_year))
    assert all(has_keys(measurement, "id", "createdAt", "metrics") for measurement in whole)


@pytest.mark.parametrize("metric", CARDIO_METRICS)
def test_cardio_full_history(api, metric):
    whole = api.get_cardio_measurements(metric, HISTORY_START, TODAY)["measurements"]
    per_year = [api.get_cardio_measurements(metric, start, end)["measurements"] for start, end in YEARS]
    assert len(whole) == sum(map(len, per_year))
    assert all(has_keys(measurement, "id", "createdAt", "metrics") for measurement in whole)
    if metric == "RESTING_HEART_RATE":
        assert whole


@pytest.mark.parametrize("period", ["month", "year"])
def test_cardio_summary(api, period):
    current = api.get_cardio_summary(period, shift=0)
    previous = api.get_cardio_summary(period, shift=1)
    for summary in (current, previous):
        assert has_keys(
            summary,
            "rangeStart",
            "rangeEnd",
            "restingHeartRateSummary",
            "systolicSummary",
            "diastolicSummary",
            "vo2MaxSummary",
        )
    assert previous["rangeEnd"] < current["rangeStart"]


def test_strength_full_history_and_filters(api):
    whole = api.get_strength_measurements(HISTORY_START, TODAY)["strengthMeasurements"]
    per_year = [api.get_strength_measurements(start, end)["strengthMeasurements"] for start, end in YEARS]
    assert whole and len(whole) == sum(map(len, per_year))
    assert all(has_keys(measurement, "id", "createdAt", "activity", "strength") for measurement in whole)
    activity_ids = sorted({measurement["activity"]["activityId"] for measurement in whole})[:2]
    for activity_id in activity_ids:
        filtered = api.get_strength_measurements(HISTORY_START, TODAY, activity_id=activity_id)["strengthMeasurements"]
        assert filtered and all(measurement["activity"]["activityId"] == activity_id for measurement in filtered)
    latest = api.get_latest_strength_metrics()
    assert latest and all(has_keys(metric, "type", "value", "activityLabel") for metric in latest)
    assert 0 < len(api.get_latest_strength_metrics(activity_ids)) <= len(latest)


def test_muscle_imbalances(api):
    assert has_keys(api.get_muscle_imbalances(), "muscleImbalances")


def test_activity_level(api):
    assert has_keys(api.get_activity_level(), "points", "daysLeft", "level", "goal", "maintainPoints")


def test_ranking(api):
    ranking = api.get_ranking()
    assert has_keys(ranking, "rankOfUser", "leaderBoard")
    assert has_keys(ranking["leaderBoard"], "items")


def test_other_locale_and_measurement_system(api):
    other = egym.Api(
        os.environ["EGYM_EMAIL"], os.environ["EGYM_PASSWORD"], locale="nl-NL", measurement_system="IMPERIAL"
    )
    try:
        start = TODAY - datetime.timedelta(days=30)
        assert len(other.get_workouts(start, TODAY)) == len(api.get_workouts(start, TODAY))
        assert isinstance(other.get_available_plans(), list)
        assert has_keys(other.get_bio_age(), "totalDetails")
        assert has_keys(other.get_ranking(), "rankOfUser", "leaderBoard")
    finally:
        other.logout()
