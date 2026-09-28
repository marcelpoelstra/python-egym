# python-egym

An unofficial, read-only Python connector for the member API behind the EGYM Fitness app. It is not affiliated with or endorsed by EGYM.

It supports macOS and Linux, each on amd64 and arm64, with Python 3.10 or newer.

Inspired by a retired version of python-egym by @bitstacker (2017). (original repo seems non-existant)

## Installation

```bash
git clone https://github.com/marcelpoelstra/python-egym.git
cd python-egym
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

To build a source distribution and a wheel:

```bash
pip install build
make
```

## Usage

```python
import datetime

import egym

api = egym.Api(email="user@example.com", password="your-password")

today = datetime.date.today()
for workout in api.get_workouts(today - datetime.timedelta(days=6), today):
    print(workout["completedAt"], len(workout["exercises"]))

print(api.get_bio_age())
api.logout()
```

The connector finds your gym from your email address, logs in, and renews the session and the access token by itself. Every method except `logout()` returns the API's JSON as plain Python lists and dictionaries.

### Options

| Argument | Default | Meaning |
| --- | --- | --- |
| `base_url` | found from the email address | Your gym's Netpulse address, for example `https://yourgym.netpulse.com` |
| `app_version`, `app_build` | `3.91`, `1190` | EGYM Fitness app release the connector identifies as |
| `locale` | `en-GB` | Locale sent to the API as `locale` and `Accept-Language`; the ranking gets its language part (`en`) as `languageCode` |
| `zone` | the time zone returned at login (your gym's) | IANA time zone used for dates, for example `Europe/Amsterdam` |
| `measurement_system` | `METRIC` | `METRIC` or `IMPERIAL` |
| `timeout` | `30` | Seconds per request |

### Methods

`start` and `end` accept a `datetime.date` or a `datetime.datetime`. `types` and `metric` take the API's own values, for example `WEIGHT_KG`, `BMI`, `BODY_FAT_PERCENTS`, `RESTING_HEART_RATE`, `VO2MAX` and `BLOOD_PRESSURE`. `period` is `"month"` or `"year"`; `shift` counts periods back, 0 being the current one. A `types` list of more than 40 values is sent in batches of 40, and the results are joined.

| Method | Returns |
| --- | --- |
| `get_profile()` | Member profile |
| `get_gyms()` | Gyms of your gym brand |
| `get_challenges()` | Challenges, grouped into joined and unjoined |
| `get_workouts(start, end)` | Workouts with their exercises and sets, `end` included; long ranges are fetched in 30-day windows |
| `get_available_plans()` | Training plans available at your gym |
| `get_favourite_activities()` | Favourite activities |
| `get_bio_age()` | Current bio age and its parts |
| `get_bio_age_summary(period, shift=0, types=None)` | Bio age per month or year; `types` from `MUSCLE`, `METABOLIC`, `CARDIO`, `FLEXIBILITY`, all four by default |
| `get_latest_body_metrics(types=None)` | Latest body metrics |
| `get_body_metrics(types, start, end, granularity="ONE_ITEM_PER_DAY")` | Body metric history; `granularity` is `ONE_ITEM_PER_DAY` or `ONE_ITEM_PER_MONTH` |
| `get_body_measurements(types, start, end)` | Body measurements, grouped per measurement |
| `get_cardio_measurements(metric, start, end)` | Resting heart rate, VO2max or blood pressure history |
| `get_cardio_summary(period, shift=0)` | Cardio summary per month or year |
| `get_strength_measurements(start, end, activity_id=None)` | Strength measurements; each item's `activity.activityId` is the id to filter on |
| `get_latest_strength_metrics(activity_ids=None)` | Latest strength results per activity, optionally for the given activity ids |
| `get_muscle_imbalances()` | Muscle imbalance analysis |
| `get_activity_level()` | Activity level, points and goal |
| `get_ranking(size=20)` | Your ranking and the leaderboard |
| `logout()` | Ends the session |

The attributes `base_url`, `exerciser_id` and `gym_id` show what the connector found at login.

### Errors

| Exception | Raised when |
| --- | --- |
| `egym.EgymError` | Base class of the exceptions below |
| `egym.DiscoveryError` | Your gym could not be found from the email address; pass `base_url` instead |
| `egym.AuthenticationError` | Login was refused, or a request stayed refused after a new login; `status_code` holds the HTTP status |
| `egym.ApiError` | The API answered with an error; `status_code`, `url` and `text` describe it |

Network errors and timeouts come from `requests` unchanged. An unknown `zone` raises `zoneinfo.ZoneInfoNotFoundError` and an unknown `period` raises `ValueError`, both before any request is sent.

## Tests

```bash
pip install -e ".[test]"
pytest
```

The live test in `tests/test_live.py` talks to the real API with your account. It runs only when `EGYM_EMAIL` and `EGYM_PASSWORD` are set:

```bash
export EGYM_EMAIL=user@example.com
read -s EGYM_PASSWORD && export EGYM_PASSWORD
pytest tests/test_live.py
```

`read -s` asks for the password without showing it or storing it in the shell history.

## API sources

EGYM does not document this API for members. The calls in this connector are based on:

- Traffic of the EGYM Fitness iOS app, version 3.91, captured in September 2026 while logging in and using the app.
- The OpenAPI specification that the mwa-api service publishes itself. It covers the workout, analysis and measurement calls, without descriptions.
- [thegymgroup-api](https://github.com/luke0x90/thegymgroup-api), a third-party description of the Netpulse API behind white-label gym apps, for the Netpulse login and session.
- Read-only tests against the live API, which also found that long date ranges need 30-day windows and long `types` lists need batches.

## Migrating from 1.x

Version 1.x talked to an API that no longer exists. Version 2.0 is a rewrite:

- Methods return plain JSON (lists and dictionaries). The `Session`, `Exercise` and `Set` classes are gone.
- Method names are snake_case.
- `egym.Api(email, password)` still logs in; the gym is found from the email address.

| 1.x | 2.0 |
| --- | --- |
| `Api(email, password)` with `GetUserLogin` | `Api(email, password)` |
| `GetUserSessions`, `GetSessionData` | `get_workouts(start, end)` |
| `GetUserProfile` | `get_profile()` |
| `GetBioAge` | `get_bio_age()` |
| `GetBodyData` | `get_latest_body_metrics()`, `get_body_metrics(...)` |
| `GetMuscleAnalysis` | `get_muscle_imbalances()` |
| `GetMaxForce` | `get_strength_measurements(...)`, `get_latest_strength_metrics()` |
| `GetRanking` | `get_ranking()` |
| `GetUserDashboard`, `GetFriends` | no replacement |

The fields of the removed classes map to keys in each item returned by `get_workouts`:

| 1.x | 2.0 |
| --- | --- |
| `Session` | workout item |
| `Session.sessionDate`, `Session.sessionIsoDate` | `completedAt`, with `timezone` |
| `Session.exercises` | `exercises` |
| `Session.points` | no workout-level key; `points` per exercise |
| `Exercise` | item in `exercises` |
| `Exercise.sets`, `Exercise.points` | `sets`, `points` |
| `Exercise.duration`, `Exercise.distance` | `duration` and `distance` per set, and `summary` |
| `Set` | item in `sets` |
| `Set.setType`, `Set.numberOfReps`, `Set.weight` | `setType`, `numberOfReps`, `weight` |

Other 1.x fields have no confirmed equivalent.
