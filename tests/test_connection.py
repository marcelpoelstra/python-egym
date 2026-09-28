import plistlib
import re

import pytest
import requests
import responses
from responses import matchers

from egym.connection import Connection
from egym.exceptions import ApiError, AuthenticationError, DiscoveryError
from fakes import (
    BASE_URL,
    BRANDING_URL,
    CONFIG_BODY,
    CONFIG_URL,
    EMAIL,
    EXERCISER_ID,
    GYM_ID,
    IDENTITY,
    LOGIN_BODY,
    LOGIN_URL,
    MOBILE_API_URL,
    MWA_API_URL,
    PASSWORD,
    TOKEN_URL,
    USERS_BODY,
    USERS_URL,
    add_discovery,
    add_login,
    add_token,
    make_connection,
)


def test_login_sends_identity_and_form_and_stores_ids(mocked):
    mocked.add(
        responses.POST,
        LOGIN_URL,
        json=LOGIN_BODY,
        match=[
            matchers.header_matcher(IDENTITY),
            matchers.urlencoded_params_matcher({"username": EMAIL, "password": PASSWORD}),
        ],
    )
    connection = make_connection()
    assert (connection.exerciser_id, connection.gym_id, connection.timezone) == (
        EXERCISER_ID,
        GYM_ID,
        "Europe/Amsterdam",
    )


def test_app_version_and_build_are_configurable(mocked):
    mocked.add(
        responses.POST,
        LOGIN_URL,
        json=LOGIN_BODY,
        match=[
            matchers.header_matcher(
                {
                    "X-NP-APP-Version": "4.0",
                    "X-NP-User-Agent": re.compile(r".*applicationVersion=4\.0; applicationVersionCode=2000;"),
                    "User-Agent": re.compile(r"NetpulseFitness/4\.0 \(com\.netpulse\.netpulsefitness; build:2000;"),
                }
            )
        ],
    )
    Connection(EMAIL, PASSWORD, base_url=BASE_URL, app_version="4.0", app_build="2000", locale="en-GB", timeout=30)


@pytest.mark.parametrize("status", [400, 401, 403])
def test_login_refused_raises_authentication_error(mocked, status):
    mocked.add(responses.POST, LOGIN_URL, json={"message": "Bad credentials"}, status=status)
    with pytest.raises(AuthenticationError) as error:
        make_connection()
    assert error.value.status_code == status


def test_base_url_skips_discovery(mocked):
    add_login(mocked)
    make_connection()
    assert [call.request.url for call in mocked.calls] == [LOGIN_URL]


def test_discovery_finds_base_url(mocked):
    add_discovery(mocked)
    add_login(mocked)
    assert make_connection(base_url=None).base_url == BASE_URL


def test_unknown_email_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, json={**USERS_BODY, "containerData": None})
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_failed_user_lookup_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, json={"message": "Not found"}, status=404)
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_config_without_branding_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, json=USERS_BODY)
    mocked.add(responses.GET, CONFIG_URL, json={**CONFIG_BODY, "resources": []})
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_branding_without_backend_address_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, json=USERS_BODY)
    mocked.add(responses.GET, CONFIG_URL, json=CONFIG_BODY)
    mocked.add(responses.GET, BRANDING_URL, body=plistlib.dumps({"Settings": {}}))
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_logout(mocked):
    add_login(mocked)
    mocked.add(responses.POST, f"{BASE_URL}/np/logout", body="")
    assert make_connection().logout() is None


def test_netpulse_get_sends_cookie_and_identity(mocked):
    add_login(mocked)
    connection = make_connection()
    mocked.add(
        responses.GET,
        f"{BASE_URL}/np/thing",
        json={"a": 1},
        match=[
            matchers.query_param_matcher({"x": "1"}),
            matchers.header_matcher({**IDENTITY, "Cookie": "JSESSIONID=session-1"}),
        ],
    )
    assert connection.get("netpulse", "/np/thing", {"x": "1"}) == {"a": 1}


def test_mobile_api_get_sends_session_cookie(mocked):
    add_login(mocked)
    connection = make_connection()
    mocked.add(
        responses.GET,
        f"{MOBILE_API_URL}/analysis/api/thing",
        json={"a": 1},
        match=[matchers.header_matcher({**IDENTITY, "Cookie": "JSESSIONID=session-1"})],
    )
    assert connection.get("mobile-api", "/analysis/api/thing") == {"a": 1}


def test_mobile_api_cookie_after_discovery(mocked):
    add_discovery(mocked)
    add_login(mocked)
    connection = make_connection(base_url=None)
    mocked.add(
        responses.GET,
        f"{MOBILE_API_URL}/analysis/api/thing",
        json={},
        match=[matchers.header_matcher({"Cookie": "JSESSIONID=session-1"})],
    )
    connection.get("mobile-api", "/analysis/api/thing")


def test_mwa_get_sends_bearer_without_identity(mocked):
    add_login(mocked)
    connection = make_connection()
    add_token(mocked)
    mocked.add(
        responses.GET,
        f"{MWA_API_URL}/thing",
        json=[1],
        match=[matchers.header_matcher({"Authorization": "Bearer token-1"})],
    )
    assert connection.get("mwa-api", "/thing") == [1]
    assert "X-NP-User-Agent" not in mocked.calls[-1].request.headers


def test_token_reused_while_valid(mocked):
    add_login(mocked)
    connection = make_connection()
    add_token(mocked)
    mocked.add(responses.GET, f"{MWA_API_URL}/thing", json={})
    connection.get("mwa-api", "/thing")
    connection.get("mwa-api", "/thing")
    assert [call.request.url for call in mocked.calls].count(TOKEN_URL) == 1


def test_token_renewed_after_expiry(mocked):
    add_login(mocked)
    connection = make_connection()
    add_token(mocked, token="token-1", expires_at="2000-01-01T00:00:00")
    add_token(mocked, token="token-2")
    mocked.add(
        responses.GET, f"{MWA_API_URL}/thing", json={}, match=[matchers.header_matcher({"Authorization": "Bearer token-1"})]
    )
    mocked.add(
        responses.GET, f"{MWA_API_URL}/thing", json={}, match=[matchers.header_matcher({"Authorization": "Bearer token-2"})]
    )
    connection.get("mwa-api", "/thing")
    connection.get("mwa-api", "/thing")
    assert [call.request.url for call in mocked.calls].count(TOKEN_URL) == 2


def test_netpulse_403_logs_in_again_and_retries(mocked):
    add_login(mocked, session_id="session-1")
    connection = make_connection()
    add_login(mocked, session_id="session-2")
    mocked.add(responses.GET, f"{BASE_URL}/np/thing", json={"message": "Access is denied"}, status=403)
    mocked.add(
        responses.GET,
        f"{BASE_URL}/np/thing",
        json={"a": 1},
        match=[matchers.header_matcher({"Cookie": "JSESSIONID=session-2"})],
    )
    assert connection.get("netpulse", "/np/thing") == {"a": 1}


def test_mwa_401_fetches_new_token_and_retries(mocked):
    add_login(mocked)
    connection = make_connection()
    add_token(mocked, token="token-1")
    add_token(mocked, token="token-2")
    mocked.add(
        responses.GET,
        f"{MWA_API_URL}/thing",
        status=401,
        match=[matchers.header_matcher({"Authorization": "Bearer token-1"})],
    )
    mocked.add(
        responses.GET,
        f"{MWA_API_URL}/thing",
        json={"a": 1},
        match=[matchers.header_matcher({"Authorization": "Bearer token-2"})],
    )
    assert connection.get("mwa-api", "/thing") == {"a": 1}


def test_token_call_403_logs_in_again(mocked):
    add_login(mocked, session_id="session-1")
    connection = make_connection()
    add_login(mocked, session_id="session-2")
    mocked.add(responses.GET, TOKEN_URL, json={"message": "Access is denied"}, status=403)
    add_token(mocked)
    mocked.add(
        responses.GET, f"{MWA_API_URL}/thing", json={}, match=[matchers.header_matcher({"Authorization": "Bearer token-1"})]
    )
    connection.get("mwa-api", "/thing")
    assert [call.request.url for call in mocked.calls].count(LOGIN_URL) == 2


def test_second_403_raises_authentication_error(mocked):
    add_login(mocked, session_id="session-1")
    connection = make_connection()
    add_login(mocked, session_id="session-2")
    mocked.add(responses.GET, f"{BASE_URL}/np/thing", json={"message": "Access is denied"}, status=403)
    with pytest.raises(AuthenticationError) as error:
        connection.get("netpulse", "/np/thing")
    assert error.value.status_code == 403


def test_second_401_raises_authentication_error(mocked):
    add_login(mocked)
    connection = make_connection()
    add_token(mocked)
    mocked.add(responses.GET, f"{MWA_API_URL}/thing", status=401)
    with pytest.raises(AuthenticationError) as error:
        connection.get("mwa-api", "/thing")
    assert error.value.status_code == 401


def test_other_status_raises_api_error(mocked):
    add_login(mocked)
    connection = make_connection()
    mocked.add(responses.GET, f"{BASE_URL}/np/thing", body="boom", status=500)
    with pytest.raises(ApiError) as error:
        connection.get("netpulse", "/np/thing")
    assert (error.value.status_code, error.value.url, error.value.text) == (500, f"{BASE_URL}/np/thing", "boom")


def test_non_json_success_propagates_requests_error(mocked):
    add_login(mocked)
    connection = make_connection()
    mocked.add(responses.GET, f"{BASE_URL}/np/thing", body="<html></html>")
    with pytest.raises(requests.exceptions.JSONDecodeError):
        connection.get("netpulse", "/np/thing")


def test_unknown_server_raises_value_error(mocked):
    add_login(mocked)
    connection = make_connection()
    with pytest.raises(ValueError):
        connection.get("elsewhere", "/thing")


def test_base_url_trailing_slash_is_ignored(mocked):
    add_login(mocked)
    assert make_connection(base_url=f"{BASE_URL}/").base_url == BASE_URL


def test_mobile_api_403_logs_in_again_with_new_cookie(mocked):
    add_login(mocked, session_id="session-1")
    connection = make_connection()
    add_login(mocked, session_id="session-2")
    mocked.add(
        responses.GET,
        f"{MOBILE_API_URL}/analysis/api/thing",
        json={"message": "Access is denied"},
        status=403,
        match=[matchers.header_matcher({"Cookie": "JSESSIONID=session-1"})],
    )
    mocked.add(
        responses.GET,
        f"{MOBILE_API_URL}/analysis/api/thing",
        json={"a": 1},
        match=[matchers.header_matcher({"Cookie": "JSESSIONID=session-2"})],
    )
    assert connection.get("mobile-api", "/analysis/api/thing") == {"a": 1}


def test_failed_brand_configuration_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, json=USERS_BODY)
    mocked.add(responses.GET, CONFIG_URL, json={"message": "error"}, status=500)
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_failed_branding_download_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, json=USERS_BODY)
    mocked.add(responses.GET, CONFIG_URL, json=CONFIG_BODY)
    mocked.add(responses.GET, BRANDING_URL, status=404)
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_discovery_non_json_raises_discovery_error(mocked):
    mocked.add(responses.GET, USERS_URL, body="<html></html>")
    with pytest.raises(DiscoveryError):
        make_connection(base_url=None)


def test_call_after_logout_logs_in_again(mocked):
    add_login(mocked, session_id="session-1")
    connection = make_connection()
    mocked.add(responses.POST, f"{BASE_URL}/np/logout", body="")
    connection.logout()
    add_login(mocked, session_id="session-2")
    mocked.add(
        responses.GET,
        f"{BASE_URL}/np/thing",
        json={"message": "Access is denied"},
        status=403,
        match=[matchers.header_matcher({"Cookie": "JSESSIONID=session-1"})],
    )
    mocked.add(
        responses.GET,
        f"{BASE_URL}/np/thing",
        json={"a": 1},
        match=[matchers.header_matcher({"Cookie": "JSESSIONID=session-2"})],
    )
    assert connection.get("netpulse", "/np/thing") == {"a": 1}
