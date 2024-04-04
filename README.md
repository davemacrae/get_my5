# Channel 5 (My5) Downloader

An AIO python script to download Channel 5 (My5) content.

## Requirements

* Python 3.6.*
* pip
* ffmpeg (<https://github.com/FFmpeg/FFmpeg>)
* mp4decrypt (<https://github.com/axiomatic-systems/Bento4>)
* yt-dlp (<https://github.com/yt-dlp/yt-dlp>)
* WVD file (<https://github.com/rlaphoenix/pywidevine>)

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Windows
py .\my5-dl.py --download --subtitles --url "https://www.channel5.com/show/secrets-of-our-universe-with-tim-peake/season-1/the-planets"

# Linux
./my5-dl.py --download --subtitles --url "https://www.channel5.com/show/secrets-of-our-universe-with-tim-peake/season-1/the-planets"
```

## Arguments

```bash
-d, --download   Download content.
-s, --subtitles  Download subtitles.
-u, --url        URL of the episode to download.
--season         Include Season in output dir
-ad, --audio-description    Download Audio Description audio track
```

## Config

Config is located in `config.py`

`HMAC_SECRET` - HMAC secret used to generate the authentication key for the content URL  
`AES_KEY` - AES key used to decrypt the data field of the API response  
`BIN_DIR` - Path to where your binaries installed  
`USE_BIN_DIR` - Flag indicating whether to use the binaries in the BIN_DIR path or your system/user path  
`DOWNLOAD_DIR` - Path to your download directory  
`TMP_DIR` - Path to your temp directory  
`WVD_PATH` - Path to your WVD file

All the above config variables can be overridden by creating a `.env` file, a `settings.ini` file. This
is recommended for `HMAC_SECRET` and `AES_KEY` to prevent Git warnings. The programme looks in:
        $HOME/.config/get_my5/.env
        $HOME/.get_my5/.env
        ./.env

As we use pathlib the function is compatible with windows.

In Linux it is also possible to override the values by specifying the value on the command line.

See <https://pypi.org/project/python-decouple/> for full details.

## Retrieving Keys

The `HMAC_SECRET` and `AES_KEY` keys can be retrieved by opening `./keys/retrieve-keys.html` in your browser.

The application hmac-aes-update.py can be used to automatically update these values:

### Example usage

```bash
./hmac-aes-update.py --env .env --keys file://$HOME/src/get_my5/keys/retrieve-keys.html
```

## Disclaimer

1. This script requires a Widevine RSA key pair to retrieve the decryption key from the license server.
2. This script is purely for educational purposes and should not be used to bypass DRM protected content.
