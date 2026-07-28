import os

FMC_URL = os.getenv(
    "FMC_URL",
    "https://fmc.example.local"
).rstrip("/")

FMC_USER = os.getenv("FMC_USER")

FMC_PASSWORD = os.getenv("FMC_PASSWORD")

# Empty by default: HTTP is the primary output. Set this for an optional snapshot.
OUTPUT_FILE = os.getenv("OUTPUT_FILE") or None

FMC_CA_BUNDLE = os.getenv("FMC_CA_BUNDLE")
FMC_TLS_VERIFY = os.getenv("FMC_TLS_VERIFY", "true").lower() not in {
    "0", "false", "no"
}
FMC_TLS_VERIFY_HOSTNAME = os.getenv(
    "FMC_TLS_VERIFY_HOSTNAME",
    "true",
).lower() not in {"0", "false", "no"}
FMC_TRUST_ENV = os.getenv("FMC_TRUST_ENV", "false").lower() in {
    "1", "true", "yes"
}

CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "5"))
READ_TIMEOUT = float(os.getenv("READ_TIMEOUT", "30"))
REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

HTTP_PORT = int(
    os.getenv("HTTP_PORT", "8080")
)

UPDATE_INTERVAL = int(
    os.getenv("UPDATE_INTERVAL", "60")
)
