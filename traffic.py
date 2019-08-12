import argparse
import collections
from datetime import datetime
import json
import logging
import os
import sys

import dropbox
from selenium.webdriver import Chrome, ChromeOptions

CHROME_EXECUTABLE_PATH = "/usr/local/bin/chromedriver75"
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler(filename=f"{PROJECT_DIR}/logs/traffic.log")
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

log.addHandler(fh)


Screenshot = collections.namedtuple("Screenshot", "filename, label, bytes")

def get_screenshots(direction_urls):
    """Yield a generator of Screenshot namedtuples for each provided direction urls"""

    log.info(f"Taking screenshots of {len(direction_urls)} directions.")

    now = datetime.now()

    chrome_options = ChromeOptions()
    chrome_options.headless = True
    chrome_options.add_argument("--window-size=1440x900")

    with Chrome(executable_path=CHROME_EXECUTABLE_PATH, options=chrome_options) as driver:
        driver.maximize_window()

        for label, url in direction_urls.items():
            driver.get(url)

            yield Screenshot(
                filename=f"{label}/{label}_{now:%Y-%m-%dT%H:%M:%S.%f}.png",
                label=label,
                bytes=driver.get_screenshot_as_png(),
                )

def get_direction_urls():
    log.info("Parsing direction urls json.")

    with open(f"{PROJECT_DIR}/direction_urls.json") as f:
        direction_urls = json.load(f)

    return direction_urls


def save_screenshots(screenshots, save_to_disk=False, upload_to_dropbox=False):
    dbx = None
    if upload_to_dropbox:
        try:
            DROPBOX_ACCESS_TOKEN="l6v_IxP-c50AAAAAAAAnSQAI1XAhux9-X4szoFZiBg1qA34lE05Fx9J0PIU2Baci"
            #DROPBOX_ACCESS_TOKEN = os.environ["DROPBOX_ACCESS_TOKEN"]
        except KeyError:
            logging.error("No DROPBOX_ACCESS_TOKEN found in environment variables!  Skipping the upload to Dropbox.")
            upload_to_dropbox = False
        else:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

    for i, screenshot in enumerate(screenshots):
        log.info(f"Saving screenshot {i} to disk.")
        if save_to_disk:
            filename = f"{PROJECT_DIR}/traffic/{screenshot.filename}"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            try:
                with open(filename, 'wb') as f:
                    f.write(screenshot.bytes)
            except IOError as e:
                logging.error(f"Could not write {screenshot.filename} due to {e}.")

        if upload_to_dropbox:
            log.info(f"Saving screenshot {i} to Dropbox.")
            try:
                dbx.files_upload(screenshot.bytes, f"/traffic/{screenshot.filename}")
            except Exception as e:
                logging.error(f"Could not write {screenshot.filename} due to {e}.")



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Screenshot traffic conditions.')
    parser.add_argument('-s', '--save_to_disk', action='store_true', help="Save screenshot files to disk.")
    parser.add_argument('-u', '--upload_to_dropbox', action='store_true', help="Upload screenshot files to Dropbox.")

    args = parser.parse_args()

    log.info(f"Traffic.py called with args {args.__dict__}")

    if not args.save_to_disk and not args.upload_to_dropbox:
        logging.error("Save to disk or upload to dropbox required.  Otherwise what's the point?")
        sys.exit(1)

    direction_urls = get_direction_urls()

    screenshots = get_screenshots(direction_urls)

    save_screenshots(screenshots, save_to_disk=args.save_to_disk, upload_to_dropbox=args.upload_to_dropbox)

    log.info("Done saving screenshots of trafic.")
