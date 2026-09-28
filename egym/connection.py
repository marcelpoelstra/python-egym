import datetime
import plistlib
import uuid
from urllib.parse import urlsplit

import requests

from .exceptions import ApiError, AuthenticationError, DiscoveryError

DISCOVERY_URL = "https://one.netpulse.com"
MOBILE_API_URL = "https://mobile-api.int.api.egym.com"
MWA_API_URL = "https://mwa-api.int.api.egym.com/mwa/api"
NP_API_VERSION = "1.5"
IOS_VERSION = "27.0.0"
ALAMOFIRE_VERSION = "5.9.1"
CFNETWORK_VERSION = "3896.100.1.2.1"
DARWIN_VERSION = "27.0.0"


def _is_success(response):
    return 200 <= response.status_code < 300


class Connection:
    """Session with the EGYM Fitness servers: discovery, login, mwa token and renewal."""

    def __init__(self, email, password, *, base_url, app_version, app_build, locale, timeout):
        self._email = email
        self._password = password
        self._timeout = timeout
        self._http = requests.Session()
        device_uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, email)).upper()
        self._identity = {
            "Accept": "application/json,text/plain",
            "Accept-Encoding": "br;q=1.0, gzip;q=0.9, deflate;q=0.8",
            "Accept-Language": locale,
            "X-NP-API-Version": NP_API_VERSION,
            "X-NP-APP-Version": app_version,
            "X-NP-User-Agent": (
                f"clientType=MOBILE_DEVICE; devicePlatform=IOS; deviceUid={device_uid}; "
                f"applicationName=EGYM Fitness; applicationVersion={app_version}; "
                f"applicationVersionCode={app_build}; containerName=NetpulseFitness;"
            ),
            "User-Agent": (
                f"NetpulseFitness/{app_version} (com.netpulse.netpulsefitness; "
                f"build:{app_build}; iOS {IOS_VERSION}) Alamofire/{ALAMOFIRE_VERSION}"
            ),
        }
        self._mwa_identity = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": locale,
            "User-Agent": f"EGYM%20Fitness/{app_build} CFNetwork/{CFNETWORK_VERSION} Darwin/{DARWIN_VERSION}",
        }
        self._token = None
        self._token_expires_at = None
        self.exerciser_id = None
        self.gym_id = None
        self.timezone = None
        self.base_url = (base_url or self._discover()).rstrip("/")
        self.login()

    def _send(self, method, url, **kwargs):
        return self._http.request(method, url, timeout=self._timeout, **kwargs)

    def _discover(self):
        users = self._send(
            "GET", f"{DISCOVERY_URL}/np/egym/v1.0/users", headers=self._identity, params={"email": self._email}
        )
        container = self._discovery_json(users, "User lookup").get("containerData") or {}
        brand = container.get("brandIdentifier")
        resource_type = container.get("resourceType")
        if not brand or not resource_type:
            raise DiscoveryError("No gym brand found for this email address")
        config = self._send(
            "GET",
            f"{DISCOVERY_URL}/np/nfa/config",
            headers=self._identity,
            params={"brandIdentifier": brand, "resourceType": resource_type},
        )
        resources = self._discovery_json(config, "Brand configuration").get("resources") or []
        branding_url = next((item.get("url") for item in resources if item.get("key") == "Branding.plist"), None)
        if not branding_url:
            raise DiscoveryError("Brand configuration lists no Branding.plist")
        branding = self._send("GET", branding_url, headers=self._mwa_identity)
        if not _is_success(branding):
            raise DiscoveryError(f"Branding.plist download failed with status {branding.status_code}")
        try:
            return plistlib.loads(branding.content)["NetworkSettings"]["NGBackendAddressKey"]
        except (ValueError, KeyError, TypeError) as error:
            raise DiscoveryError("Branding.plist holds no NGBackendAddressKey") from error

    @staticmethod
    def _discovery_json(response, step):
        if not _is_success(response):
            raise DiscoveryError(f"{step} failed with status {response.status_code}")
        try:
            body = response.json()
        except ValueError as error:
            raise DiscoveryError(f"{step} returned no JSON") from error
        if not isinstance(body, dict):
            raise DiscoveryError(f"{step} returned unexpected JSON")
        return body

    def login(self):
        response = self._send(
            "POST",
            f"{self.base_url}/np/exerciser/login",
            headers={**self._identity, "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
            data={"username": self._email, "password": self._password},
        )
        if not _is_success(response):
            raise AuthenticationError(f"Login failed with status {response.status_code}", response.status_code)
        body = response.json()
        self.exerciser_id = body["uuid"]
        self.gym_id = body["homeClubUuid"]
        self.timezone = body["timezone"]
        self._token = None

    def logout(self):
        response = self._send("POST", f"{self.base_url}/np/logout", headers=self._identity)
        if not _is_success(response):
            raise ApiError(response.status_code, response.url, response.text)
        self._token = None

    def get(self, server, path, params=None):
        if server == "mwa-api":
            return self._mwa_get(path, params).json()
        if server == "netpulse":
            url = f"{self.base_url}{path}"
        elif server == "mobile-api":
            url = f"{MOBILE_API_URL}{path}"
        else:
            raise ValueError(f"Unknown server: {server!r}")
        return self._session_get(url, params).json()

    def _session_get(self, url, params=None):
        response = self._send_with_session(url, params)
        if response.status_code == 403:
            self.login()
            response = self._send_with_session(url, params)
            if response.status_code in (401, 403):
                raise AuthenticationError(f"Still refused after a new login: {response.url}", response.status_code)
        if not _is_success(response):
            raise ApiError(response.status_code, response.url, response.text)
        return response

    def _send_with_session(self, url, params):
        headers = dict(self._identity)
        if url.startswith(MOBILE_API_URL):
            session_id = self._http.cookies.get("JSESSIONID", domain=urlsplit(self.base_url).hostname)
            headers["Cookie"] = f"JSESSIONID={session_id}"
        return self._send("GET", url, headers=headers, params=params)

    def _mwa_get(self, path, params):
        url = f"{MWA_API_URL}{path}"
        response = self._send("GET", url, headers=self._mwa_headers(), params=params)
        if response.status_code == 401:
            self._token = None
            response = self._send("GET", url, headers=self._mwa_headers(), params=params)
            if response.status_code in (401, 403):
                raise AuthenticationError(f"Still refused with a new token: {response.url}", response.status_code)
        if not _is_success(response):
            raise ApiError(response.status_code, response.url, response.text)
        return response

    def _mwa_headers(self):
        return {**self._mwa_identity, **self._bearer()}

    def _bearer(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        if self._token is None or now >= self._token_expires_at:
            body = self._session_get(
                f"{self.base_url}/np/micro-web-app/v1.0/exercisers/{self.exerciser_id}/tokens/FLS"
            ).json()
            self._token = body["accessToken"]
            self._token_expires_at = datetime.datetime.fromisoformat(body["accessTokenExpiresAt"]).replace(
                tzinfo=datetime.timezone.utc
            )
        return {"Authorization": f"Bearer {self._token}"}
