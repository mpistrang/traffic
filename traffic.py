import argparse
import collections
from datetime import datetime
import json
import os
import sys

import dropbox
from selenium.webdriver import Chrome, ChromeOptions

CHROME_EXECUTABLE_PATH = "chromedriver75"

Screenshot = collections.namedtuple("Screenshot", "filename, label, bytes")


def get_screenshots(direction_urls, save_to_disk=False):
    """Yield a generator of Screenshot namedtuples for each provided direction urls"""
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
    with open("direction_urls.json") as f:
        direction_urls = json.load(f)

    return direction_urls


def save_screenshots(screenshots, save_to_disk=False, upload_to_dropbox=False):

    dbx = None
    if upload_to_dropbox:
        try:
            DROPBOX_ACCESS_TOKEN = os.environ["DROPBOX_ACCESS_TOKEN"]
        except KeyError:
            print("No DROPBOX_ACCESS_TOKEN found in environment variables!  Skipping the upload to Dropbox.")
            upload_to_dropbox = False
        else:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

    for screenshot in screenshots:
        if save_to_disk:
            filename = f"./traffic/{screenshot.filename}"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            try:
                with open(filename, 'wb') as f:
                    f.write(screenshot.bytes)
            except IOError as e:
                print(f"Could not write {screenshot.filename} due to {e}.")

        if upload_to_dropbox:
            try:
                dbx.files_upload(screenshot.bytes, f"/traffic/{screenshot.label}/{screenshot.filename}")
            except Exception as e:
                print(f"Could not write {screenshot.filename} due to {e}.")



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Screenshot traffic conditions.')
    parser.add_argument('-s', '--save_to_disk', action='store_true', help="Save screenshot files to disk.")
    parser.add_argument('-u', '--upload_to_dropbox', action='store_true', help="Upload screenshot files to Dropbox.")

    args = parser.parse_args()

    if not args.save_to_disk and not args.upload_to_dropbox:
        print("Save to disk or upload to dropbox required.  Otherwise what's the point?")
        sys.exit(1)


    direction_urls = get_direction_urls()

    screenshots = get_screenshots(direction_urls)

    save_screenshots(screenshots, save_to_disk=args.save_to_disk, upload_to_dropbox=args.upload_to_dropbox)
