import os
import ssl

import requests
from requests.adapters import HTTPAdapter

from .config import (
    FMC_CA_BUNDLE,
    FMC_PASSWORD,
    FMC_TLS_VERIFY,
    FMC_TLS_VERIFY_HOSTNAME,
    FMC_TRUST_ENV,
    FMC_URL,
    FMC_USER,
    REQUEST_TIMEOUT,
)


class FmcError(RuntimeError):
    """Base error returned by FMC operations."""


class FmcAuthenticationError(FmcError):
    """Authentication failed or an FMC token cannot be renewed."""


class NoHostnameVerificationAdapter(HTTPAdapter):
    """Verify the certificate chain but allow a legacy certificate without SAN."""

    def init_poolmanager(
        self,
        connections,
        maxsize,
        block=False,
        **pool_kwargs,
    ):
        pool_kwargs["assert_hostname"] = False
        return super().init_poolmanager(
            connections,
            maxsize,
            block=block,
            **pool_kwargs,
        )


session = requests.Session()
# Docker may inject HTTP(S)_PROXY variables. FMC is normally an internal
# appliance, so do not route its credentials or TLS connection through an
# ambient proxy unless this is explicitly enabled.
session.trust_env = FMC_TRUST_ENV
if not FMC_TLS_VERIFY:
    print(
        "WARNING: FMC TLS certificate verification is fully disabled",
        flush=True,
    )
elif not FMC_TLS_VERIFY_HOSTNAME:
    session.mount("https://", NoHostnameVerificationAdapter())
    print(
        "WARNING: FMC TLS hostname verification is disabled; "
        "certificate chain verification remains enabled",
        flush=True,
    )
SYSTEM_CA_BUNDLE = ssl.get_default_verify_paths().cafile


def tls_verify():
    if FMC_CA_BUNDLE:
        return FMC_CA_BUNDLE
    if not FMC_TLS_VERIFY:
        return False
    if SYSTEM_CA_BUNDLE and os.path.isfile(SYSTEM_CA_BUNDLE):
        return SYSTEM_CA_BUNDLE
    return True


def request(method, url, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    kwargs.setdefault("verify", tls_verify())
    try:
        return session.request(method, url, **kwargs)
    except requests.exceptions.SSLError as error:
        raise FmcError(
            "FMC TLS verification failed. Install the CA in the system trust "
            "store or set FMC_CA_BUNDLE to the mounted CA file. "
            f"OpenSSL reason: {error}"
        ) from error
    except requests.Timeout as error:
        raise FmcError(f"FMC request timed out: {url}") from error
    except requests.RequestException as error:
        raise FmcError(f"FMC request failed: {url}: {error}") from error


def token_from_headers(response):
    access = response.headers.get("X-auth-access-token")
    refresh = response.headers.get("X-auth-refresh-token")
    if not access or not refresh:
        raise FmcAuthenticationError(
            "FMC response did not contain both authentication tokens"
        )
    return {"access": access, "refresh": refresh}


def login():
    if not FMC_USER or not FMC_PASSWORD:
        raise FmcAuthenticationError("FMC_USER and FMC_PASSWORD are required")

    response = request(
        "POST",
        FMC_URL + "/api/fmc_platform/v1/auth/generatetoken",
        auth=(FMC_USER, FMC_PASSWORD),
    )
    if response.status_code != 204:
        raise FmcAuthenticationError(f"Login failed HTTP {response.status_code}")

    print("FMC login successful", flush=True)
    return token_from_headers(response)


def refresh_token(token):
    response = request(
        "POST",
        FMC_URL + "/api/fmc_platform/v1/auth/refreshtoken",
        headers={
            "X-auth-access-token": token["access"],
            "X-auth-refresh-token": token["refresh"],
        },
    )
    if response.status_code != 204:
        raise FmcAuthenticationError(
            f"Refresh token failed HTTP {response.status_code}"
        )

    print("FMC token refreshed", flush=True)
    return token_from_headers(response)


def api_get(path, token):
    url = FMC_URL + path
    headers = {
        "X-auth-access-token": token["access"],
        "Accept": "application/json",
    }
    response = request("GET", url, headers=headers)

    if response.status_code == 401:
        new_token = refresh_token(token)
        token.update(new_token)
        headers["X-auth-access-token"] = token["access"]
        response = request("GET", url, headers=headers)

    if response.status_code == 401:
        raise FmcAuthenticationError(f"GET {path} failed HTTP 401")
    if response.status_code != 200:
        raise FmcError(f"GET {path} failed HTTP {response.status_code}")

    try:
        return response.json()
    except ValueError as error:
        raise FmcError(f"GET {path} returned invalid JSON") from error


def get_domain(token):
    data = api_get("/api/fmc_platform/v1/info/domain", token)
    items = data.get("items") or []
    if not items or not items[0].get("uuid"):
        raise FmcError("No FMC domains found")

    domain = items[0]["uuid"]
    print(f"FMC domain: {domain}", flush=True)
    return domain
