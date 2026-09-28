import plistlib
import re

import responses
from responses import matchers

from egym.connection import Connection

EMAIL = "user@example.com"
PASSWORD = "secret"
BASE_URL = "https://gym.netpulse.com"
DISCOVERY_URL = "https://one.netpulse.com"
MOBILE_API_URL = "https://mobile-api.int.api.egym.com"
MWA_API_URL = "https://mwa-api.int.api.egym.com/mwa/api"
USERS_URL = f"{DISCOVERY_URL}/np/egym/v1.0/users"
CONFIG_URL = f"{DISCOVERY_URL}/np/nfa/config"
BRANDING_URL = "https://galaxy-eca.cdn.egym.com/brand/Branding.plist"
EXERCISER_ID = "11111111-2222-3333-4444-555555555555"
GYM_ID = "66666666-7777-8888-9999-000000000000"
LOGIN_URL = f"{BASE_URL}/np/exerciser/login"
TOKEN_URL = f"{BASE_URL}/np/micro-web-app/v1.0/exercisers/{EXERCISER_ID}/tokens/FLS"

USERS_BODY = {
    "termsAccepted": True,
    "passwordSet": True,
    "containerData": {"brandIdentifier": "GymBrand", "resourceType": "prod"},
    "gymLocationData": None,
}
CONFIG_BODY = {
    "brandIdentifier": "GymBrand",
    "devicePlatform": "IOS",
    "resources": [{"key": "Branding.plist", "url": BRANDING_URL, "hash": "0", "size": 1}],
}
LOGIN_BODY = {
    "uuid": EXERCISER_ID,
    "homeClubUuid": GYM_ID,
    "timezone": "Europe/Amsterdam",
    "egymAccountId": "account-1",
}
IDENTITY = {
    "Accept": "application/json",
    "Accept-Language": "en-GB",
    "X-NP-API-Version": "1.5",
    "X-NP-APP-Version": "3.91",
    "X-NP-User-Agent": re.compile(
        r"clientType=MOBILE_DEVICE; devicePlatform=IOS; "
        r"deviceUid=[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}; "
        r"applicationName=EGYM Fitness; applicationVersion=3\.91; applicationVersionCode=1190; "
        r"containerName=NetpulseFitness;$"
    ),
    "User-Agent": "NetpulseFitness/3.91 (com.netpulse.netpulsefitness; build:1190; iOS 27.0.0) Alamofire/5.9.1",
}


def make_connection(base_url=BASE_URL):
    return Connection(
        EMAIL, PASSWORD, base_url=base_url, app_version="3.91", app_build="1190", locale="en-GB", timeout=30
    )


def add_discovery(mocked):
    mocked.add(
        responses.GET,
        USERS_URL,
        json=USERS_BODY,
        headers={"Set-Cookie": "JSESSIONID=discovery-session; Path=/; Secure; HttpOnly"},
        match=[matchers.query_param_matcher({"email": EMAIL}), matchers.header_matcher(IDENTITY)],
    )
    mocked.add(
        responses.GET,
        CONFIG_URL,
        json=CONFIG_BODY,
        match=[
            matchers.query_param_matcher({"brandIdentifier": "GymBrand", "resourceType": "prod"}),
            matchers.header_matcher(IDENTITY),
        ],
    )
    mocked.add(
        responses.GET,
        BRANDING_URL,
        body=plistlib.dumps({"NetworkSettings": {"NGBackendAddressKey": BASE_URL}, "Settings": {}}),
    )


def add_login(mocked, session_id="session-1"):
    mocked.add(
        responses.POST,
        LOGIN_URL,
        json=LOGIN_BODY,
        headers={"Set-Cookie": f"JSESSIONID={session_id}; Path=/; Secure; HttpOnly"},
        match=[matchers.urlencoded_params_matcher({"username": EMAIL, "password": PASSWORD})],
    )


def add_token(mocked, token="token-1", expires_at="2999-01-01T00:00:00"):
    mocked.add(
        responses.GET,
        TOKEN_URL,
        json={"provider": "FLS", "partner": "FLS", "accessToken": token, "accessTokenExpiresAt": expires_at},
    )
