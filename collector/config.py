import os
import urllib3

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

FMC_URL = os.getenv(
    "FMC_URL",
    "https://firepower"
)

FMC_USER = os.getenv("FMC_USER")

FMC_PASSWORD = os.getenv("FMC_PASSWORD")

OUTPUT_FILE = os.getenv(
    "OUTPUT_FILE",
    "/data/fmc.json"
)

HTTP_PORT = int(
    os.getenv("HTTP_PORT", "8080")
)

UPDATE_INTERVAL = int(
    os.getenv("UPDATE_INTERVAL", "60")
)