''' This file contains configuration options '''
# pylint: disable=line-too-long

# Configurable
from decouple import config

HMAC_SECRET = config('HMAC_SECRET', default="")
AES_KEY = config('AES_KEY', default="")
WVD_PATH = config('WVD_PATH', default="")

DOWNLOAD_DIR = config('DOWNLOAD_DIR', default="./downloads")
TMP_DIR = config('TMP_DIR', default="./tmp")
BIN_DIR = config('BIN_DIR', default="./bin")
USE_BIN_DIR = config('USE_BIN_DIR', default=False, cast=bool)

# Don't touch
APP_NAME = "my5desktopng"
BASE_URL_MEDIA = "https://cassie.channel5.com/api/v2/media"
BASE_URL_SHOWS = "https://corona.channel5.com/shows"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
DEFAULT_HEADERS = {
    "Accept": "*/*",
    "User-Agent": USER_AGENT,
}
DEFAULT_JSON_HEADERS = {
    "Content-type": "application/json",
    "Accept": "*/*",
    "User-Agent": USER_AGENT,
}
