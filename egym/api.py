import datetime
from zoneinfo import ZoneInfo

from .connection import Connection

BIO_AGE_TYPES = ["MUSCLE", "METABOLIC", "CARDIO", "FLEXIBILITY"]
PERIODS = {"month": "monthly", "year": "yearly"}
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
WORKOUT_WINDOW = datetime.timedelta(days=30)
TYPES_BATCH = 40


def _type_batches(types):
    values = [types] if isinstance(types, str) else list(types)
    return [values[index:index + TYPES_BATCH] for index in range(0, len(values), TYPES_BATCH)]


def _utc_moment(value, zone, *, end=False):
    if isinstance(value, datetime.datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=zone)
    else:
        day = value + datetime.timedelta(days=1) if end else value
        moment = datetime.datetime.combine(day, datetime.time(), tzinfo=zone)
    return moment.astimezone(datetime.timezone.utc)


def _day(value, zone):
    if isinstance(value, datetime.datetime):
        if value.tzinfo:
            value = value.astimezone(zone)
        return value.date().isoformat()
    return value.isoformat()


def _period(period):
    if period not in PERIODS:
        raise ValueError(f"period must be 'month' or 'year', not {period!r}")
    return PERIODS[period]


class Api:
    """Read-only client for the member API behind the EGYM Fitness app."""

    def __init__(
        self,
        email: str,
        password: str,
        *,
        base_url: str | None = None,
        app_version: str = "3.91",
        app_build: str = "1190",
        locale: str = "en-GB",
        zone: str | None = None,
        measurement_system: str = "METRIC",
        timeout: float = 30,
    ):
        zone_info = ZoneInfo(zone) if zone else None
        self._connection = Connection(
            email,
            password,
            base_url=base_url,
            app_version=app_version,
            app_build=app_build,
            locale=locale,
            timeout=timeout,
        )
        self._locale = locale
        self._language = locale.split("-")[0]
        self._zone = zone_info or ZoneInfo(self._connection.timezone)
        self._measurement_system = measurement_system

    @property
    def base_url(self) -> str:
        return self._connection.base_url

    @property
    def exerciser_id(self) -> str:
        return self._connection.exerciser_id

    @property
    def gym_id(self) -> str:
        return self._connection.gym_id

    def _mwa(self, path, params=None):
        return self._connection.get("mwa-api", path, params)

    def _between(self, start, end):
        return {"startDate": _day(start, self._zone), "endDate": _day(end, self._zone), "zoneId": self._zone.key}

    def get_profile(self) -> dict:
        return self._connection.get("netpulse", f"/np/exerciser/{self.exerciser_id}/profile")

    def get_gyms(self) -> list:
        return self._connection.get("netpulse", "/np/company/children", {"responseType": "detail"})

    def get_challenges(self) -> dict:
        return self._connection.get(
            "netpulse", f"/np/exerciser/{self.exerciser_id}/challenges", {"grouping": "joinStatus"}
        )

    def get_workouts(self, start: datetime.date, end: datetime.date) -> list:
        after = _utc_moment(start, self._zone)
        before = _utc_moment(end, self._zone, end=True)
        workouts = []
        while after < before:
            window_end = min(after + WORKOUT_WINDOW, before)
            workouts += self._mwa(
                "/workouts/v1.0/workouts",
                {
                    "completedAfter": after.strftime(UTC_FORMAT),
                    "completedBefore": window_end.strftime(UTC_FORMAT),
                    "gymLocationId": self.gym_id,
                    "measurementSystem": self._measurement_system,
                    "locale": self._locale,
                },
            )
            after = window_end
        return workouts

    def get_available_plans(self) -> list:
        return self._mwa(
            "/workouts/v1.1/available-plans",
            {"gymLocationId": self.gym_id, "measurementSystem": self._measurement_system, "locale": self._locale},
        )

    def get_favourite_activities(self) -> list:
        return self._mwa("/workouts/v2.0/favourite-activities", {"gymLocationId": self.gym_id})

    def get_bio_age(self) -> dict:
        return self._mwa("/analysis/v1.0/bio-age", {"locale": self._locale})

    def get_bio_age_summary(self, period: str, shift: int = 0, types: list[str] | None = None) -> dict:
        return self._mwa(
            f"/analysis/v1.0/bio-age-{_period(period)}-summary",
            {"types": types if types is not None else BIO_AGE_TYPES, "shift": shift},
        )

    def get_latest_body_metrics(self, types: list[str] | None = None) -> list:
        path = "/measurements/v1.0/latest-body-metrics"
        if types is None:
            return self._mwa(path)
        return [metric for batch in _type_batches(types) for metric in self._mwa(path, {"types": batch})]

    def get_body_metrics(
        self, types: list[str], start: datetime.date, end: datetime.date, granularity: str = "ONE_ITEM_PER_DAY"
    ) -> list:
        params = {"granularity": granularity, **self._between(start, end)}
        return [
            item
            for batch in _type_batches(types)
            for item in self._mwa("/measurements/v1.0/body-metrics", {"types": batch, **params})
        ]

    def get_body_measurements(self, types: list[str], start: datetime.date, end: datetime.date) -> list:
        results = [
            self._mwa("/measurements/v1.0/body-measurements-grouped", {"types": batch, **self._between(start, end)})
            for batch in _type_batches(types)
        ]
        if len(results) == 1:
            return results[0]
        merged = {}
        for entries in results:
            for entry in entries:
                if entry["id"] in merged:
                    merged[entry["id"]]["metrics"] += entry["metrics"]
                else:
                    merged[entry["id"]] = {**entry, "metrics": list(entry["metrics"])}
        return list(merged.values())

    def get_cardio_measurements(self, metric: str, start: datetime.date, end: datetime.date) -> dict:
        return self._mwa("/measurements/v1.0/cardio", {"metricType": metric, **self._between(start, end)})

    def get_cardio_summary(self, period: str, shift: int = 0) -> dict:
        return self._mwa(
            f"/measurements/v1.0/cardio-measurements-{_period(period)}-summary",
            {"shift": shift, "zoneId": self._zone.key},
        )

    def get_strength_measurements(
        self, start: datetime.date, end: datetime.date, activity_id: int | None = None
    ) -> dict:
        params = self._between(start, end)
        if activity_id is not None:
            params["activityId"] = activity_id
        return self._mwa("/measurements/v1.0/strength", params)

    def get_latest_strength_metrics(self, activity_ids: list[int] | None = None) -> list:
        params = {"zoneId": self._zone.key}
        if activity_ids is not None:
            params["activityIds"] = activity_ids
        return self._mwa("/measurements/v1.0/strength/latest-metrics", params)

    def get_muscle_imbalances(self) -> dict:
        return self._mwa("/analysis/v1.0/muscle-imbalances", {"zoneId": self._zone.key})

    def get_activity_level(self) -> dict:
        return self._mwa("/analysis/v1.0/activity-levels")

    def get_ranking(self, size: int = 20) -> dict:
        return self._connection.get(
            "mobile-api",
            f"/analysis/api/v1.0/exercisers/{self.exerciser_id}/rankingwithleaderboard",
            {"languageCode": self._language, "size": size},
        )

    def logout(self) -> None:
        self._connection.logout()
