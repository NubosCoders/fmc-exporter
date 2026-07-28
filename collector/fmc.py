import requests
import time


session = requests.Session()

from .config import *

def login():

    url = (
        FMC_URL +
        "/api/fmc_platform/v1/auth/generatetoken"
    )

    response = session.post(
        url,
        auth=(FMC_USER, FMC_PASSWORD),
        verify=True
    )

    if response.status_code != 204:
        raise Exception(
            f"Login failed {response.status_code}"
        )

    token = {
        "access": response.headers["X-auth-access-token"],
        "refresh": response.headers["X-auth-refresh-token"]
    }

    print("FMC login successful", flush=True)

    return token


def refresh_token(token):

    url = (
        FMC_URL +
        "/api/fmc_platform/v1/auth/refreshtoken"
    )


    headers = {
        "X-auth-access-token": token["access"],
        "X-auth-refresh-token": token["refresh"]
    }


    response = session.post(
        url,
        headers=headers,
        verify=True
    )


    print(
        "Refresh status:",
        response.status_code,
        flush=True
    )


    if response.status_code != 204:

        raise Exception(
            f"Refresh token failed {response.status_code}: {response.text}"
        )

    new_token = {
        "access": response.headers["X-auth-access-token"],
        "refresh": response.headers["X-auth-refresh-token"]
        }


    print(
        "FMC token refreshed",
        flush=True
    )


    return new_token

def api_get(path, token):

    url = FMC_URL + path

    headers = {
        "X-auth-access-token": token["access"],
        "Accept": "application/json"
    }

    response = session.get(
        url,
        headers=headers,
        verify=True
    )


    if response.status_code == 401:

        print(
            "Access token expired, refreshing...",
            flush=True
        )

        new_token = refresh_token(token)

        token["access"] = new_token["access"]
        token["refresh"] = new_token["refresh"]


        headers["X-auth-access-token"] = token["access"]


        response = session.get(
            url,
            headers=headers,
            verify=True
        )


    if response.status_code != 200:

        raise Exception(
            f"GET {path} failed HTTP {response.status_code}"
        )


    return response.json()


def get_domain(token):

    data = api_get(
        "/api/fmc_platform/v1/info/domain",
        token
    )


    if not data.get("items"):
        raise Exception(
            "No FMC domains found"
        )


    domain = data["items"][0]["uuid"]

    print(
        f"FMC domain: {domain}",
        flush=True
    )

    return domain





