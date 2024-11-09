import platform
import sys
import time
import time as t
import warnings
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union

import ntplib
from requests import Response, request

from . import __version__
from .config import config
from .errors import InvalidEnvironmentError, SettradeError
from .logger import log_wrapper
from .util import (
    create_sha256_with_ecdsa_signature,
    get_current_milli_timestamp_str,
    truncate_timestamp,
)


@dataclass
class Option:
    method: str
    endpoint: str
    payload: Union[dict, list] = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)

    @property
    def rate_limit_id(self):
        """
        rate limit is identify by http method, but POST and PATCH is count along together
        """
        if self.method == "GET":
            return f"1"
        if self.method == "POST":
            return f"2"
        if self.method == "PATCH":
            return f"2"
        return f"0"


@dataclass
class RateLimit:
    """Rate limit manager
    ntp_time_diff   : time difference (ms) between local and stratum server
    last_request_at : timestamp when latest request was sent, this will auto update when call update()
    rate_per_x      : how many time api can call per second/minute, this will auto update when call update()
    remaining_per_x : how many time left api can call in current block second/minute, this will auto update when call update()
    """

    ntp_time_diff: int = 0
    last_request_at: Optional[int] = None
    rate_per_second: int = 5
    rate_per_minute: int = 60
    remaining_per_second: int = 5
    remaining_per_minute: int = 60

    def now(self) -> int:
        """
        time.time() in local may have a little bit different compare to settrade open api server
        and these difference can break block counting

        so this function adjust that difference with ntp_time_diff
        """
        return int(time.time() * 1000) + self.ntp_time_diff

    def time_until_next_block(self, d: int) -> int:
        """
        rate limit is reset in every second and minute
        ex for second block -> 0.8s, 0.9s, 1.0s (rate limit reset), 1.1s, 1.2s
        ex for minute block -> 0.58m,0.59m,1.00m (rate limit reset), 1.01m, 1.02m

        so this function truncates timestamp back to start point in each block,
        then add up with block_duration to calculate next block time
        """
        if self.last_request_at == None:
            return 0
        next_block_at = truncate_timestamp(self.last_request_at, d) + d
        return max(next_block_at - self.now(), 0)

    def is_difference_block(self, d: int) -> bool:
        if self.last_request_at == None:
            return True
        if self.now() - self.last_request_at > d:
            return True
        return False

    def wait(self):
        """
        if rate_limit_remaining is exceed :
            if latest_request and current_request is in difference block :
                no sleep and reset remaining
            else :
                sleep until next block
        """
        if self.remaining_per_minute <= 0:
            block_duration = 60 * 1000

            if self.is_difference_block(block_duration):
                self.reset_remaining()
            else:
                time.sleep(self.time_until_next_block(block_duration) * 0.001)

        if self.remaining_per_second <= 0:
            block_duration = 1 * 1000

            if self.is_difference_block(block_duration):
                self.reset_remaining()
            else:
                time.sleep(self.time_until_next_block(block_duration) * 0.001)

    def update(self, response: Optional[Response]):
        """
        update last_request_at and remaining from headers
        """
        self.last_request_at = self.now()

        if response == None:
            return self.reset_remaining()

        try:
            headers = response.headers
            self.remaining_per_second = int(headers["X-RateLimit-Remaining-second"])
            self.remaining_per_minute = int(headers["X-RateLimit-Remaining-minute"])
            self.rate_per_second = int(headers["X-RateLimit-Limit-second"])
            self.rate_per_minute = int(headers["X-RateLimit-Limit-minute"])
        except KeyError:
            self.reset_remaining()

    def reset_remaining(self):
        self.remaining_per_second = self.rate_per_second
        self.remaining_per_minute = self.rate_per_minute


class Context:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        app_code: str,
        broker_id: str,
        is_auto_queue: bool = False,
    ):
        self.app_id: str = app_id
        self.app_secret: str = app_secret
        self.app_code: str = app_code
        self.broker_id: str = broker_id

        if config["environment"] == "prod":
            self.base_url = "https://open-api.settrade.com"
        elif config["environment"] == "uat":
            self.base_url = "https://open-api-test.settrade.com"
        else:
            raise InvalidEnvironmentError()

        self.token_type: Optional[str] = None
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None

        self.is_auto_queue: bool = is_auto_queue
        self.rate_limit: dict[str, RateLimit] = {}

        self.ntp_time_diff_ms: int = self.sync_ntp_time_diff()
        self.expired_at: int = 0
        self.refresh_token_before_exp: int = 100

        self._check_version()

    @property
    def login_path(self):
        return f"{self.base_url}/api/oam/v1/{self.broker_id}/broker-apps/{self.app_code}/login"

    @property
    def refresh_token_path(self):
        return f"{self.base_url}/api/oam/v1/{self.broker_id}/broker-apps/{self.app_code}/refresh-token"

    @property
    def user_agent(self) -> str:
        ver = platform.python_version()
        bit = "x" + platform.architecture()[0].replace("bit", "")
        return f"SettradeOpenApiSdkV2Python{ver}_{bit}/{__version__}"

    @log_wrapper
    def login(self):
        params = config["param"]
        ts = get_current_milli_timestamp_str()
        content = f"{self.app_id}.{params}.{ts}"
        sig = create_sha256_with_ecdsa_signature(self.app_secret, content)
        res = self.request(
            "POST",
            self.login_path,
            json={
                "apiKey": self.app_id,
                "params": params,
                "signature": sig,
                "timestamp": ts,
            },
        )
        if not res.ok:
            raise SettradeError(
                code=res.json()["code"],
                status_code=res.status_code,
                message=res.json()["message"],
            )
        self.token_type = res.json()["token_type"]
        self.token = res.json()["access_token"]
        self.refresh_token = res.json()["refresh_token"]
        self.expired_at = int(t.time()) + res.json()["expires_in"]

    @log_wrapper
    def refresh(self):
        res = self.request(
            "POST",
            self.refresh_token_path,
            json={"apiKey": self.app_id, "refreshToken": self.refresh_token},
        )
        if not res.ok:
            return
        self.token = res.json()["access_token"]
        self.refresh_token = res.json()["refresh_token"]
        self.expired_at = int(t.time()) + res.json()["expires_in"]

    def sync_ntp_time_diff(self):
        try:
            current_stratum = int(
                ntplib.NTPClient().request("2.asia.pool.ntp.org").tx_time * 1000
            )
            current_local = int(time.time() * 1000)
            return current_stratum - current_local
        except:
            return 0

    def wrap_auth_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        out = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
        }
        if self.token_type and self.token:
            out["Authorization"] = f"{self.token_type} {self.token}"

        if headers is not None:
            out.update(headers)

        return out

    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        return request(
            method=method,
            url=endpoint,
            headers=self.wrap_auth_headers(headers),
            **kwargs,
        )

    def get_rate_limit(self, option: Option):
        if option.rate_limit_id not in self.rate_limit:
            self.rate_limit[option.rate_limit_id] = RateLimit(self.ntp_time_diff_ms)
        return self.rate_limit[option.rate_limit_id]

    def send_request(self, option: Option):
        if self._should_refresh():
            self.refresh()

        if not option.method in ["GET", "POST", "PATCH"]:
            raise ValueError("Invalid method")

        return self.request(
            method=option.method,
            endpoint=option.endpoint,
            headers=option.headers,
            params=option.params,
            json=option.payload,
        )

    def dispatch(self, option: Option):
        if self.is_auto_queue:
            r = self.get_rate_limit(option)
            r.wait()
            data = self.send_request(option)
            r.update(data)
            return data
        else:
            return self.send_request(option)

    def _should_refresh(self):
        return self.expired_at - int(t.time()) <= self.refresh_token_before_exp

    """
    Version
    """

    def _check_version(self):
        app_version = __version__
        current_version, min_version = self._get_version()

        if app_version < min_version:
            raise ValueError(
                f"Your sdk version [{app_version}] is obsolete. Please update your sdk version to {current_version}."
            )
        elif app_version < current_version:
            warnings.warn(
                f"Please update your sdk version {app_version} to {current_version}.",
                DeprecationWarning,
            )

    def _get_version(self) -> Tuple[str, str]:
        """Get version of the https://open-api.settrade.com/sdk-open-api/sdk-version.json

        Returns
        -------
        str
            version ex. "1.0.0"

        Raises
        ------
        ValueError
            Version not found for platform {plt} and os {os}
        """
        endpoint = f"{self.base_url}/sdk-open-api/sdk-version.json"

        response = self.request(method="GET", endpoint=endpoint)
        response.raise_for_status()
        version_list = response.json()

        plt = "python_x64" if sys.maxsize > 2**32 else "python_x86"

        if sys.platform == "win32":
            os = "windows_amd64" if platform.machine() == "AMD64" else "windows_386"
        else:
            os = f"{sys.platform}_amd64"

        for i in version_list:
            key = i["key"]
            if key["platform"] == plt and key["os"] == os:
                return i["currentVersion"], i["minimumVersion"]

        raise ValueError(f"Version not found for platform {plt} and os {os}")
