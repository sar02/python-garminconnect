#!/usr/bin/env python3
"""
pip3 install garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
import json
import logging
import os
import sys
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

import time
import shutil

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Configure debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
api = None

# Define local Zwift Activity location
user_prof = (os.getenv("USERPROFILE"))
z_location = f'{user_prof}\\Documents\\Zwift\\Activities'
print(z_location)

output_dir="../GarminActivities"

# Example selections and settings
today = datetime.date.today()
startdate = today - datetime.timedelta(days=2)  # Select past week
start = 0
limit = 1
start_badge = 1  # Badge related calls calls start counting at 1
activitytype = ""  # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
activityfile = "MY_ACTIVITY.fit"  # Supported file types are: .fit .gpx .tcx
weight = 89.6
weightunit = 'kg'

def cp_zwift_fits():
    for file in os.listdir(z_location):
        #print(file)
        file_fullpath = os.path.join(z_location, file)
        file_outpath = os.path.join(output_dir, file)
        if file.endswith(".fit") and datetime.date.fromtimestamp(os.path.getctime(file_fullpath)) > startdate:
            print(file)
            shutil.copyfile(file_fullpath, file_outpath)

def display_json(api_call, output):
    """Format API output for better readability."""

    dashed = "-" * 20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-" * len(header)

    print(header)

    if isinstance(output, (int, str, dict, list)):
        print(json.dumps(output, indent=4))
    else:
        print(output)

    print(footer)

def display_text(output):
    """Format API output for better readability."""

    dashed = "-" * 60
    header = f"{dashed}"
    footer = "-" * len(header)

    print(header)
    print(json.dumps(output, indent=4))
    print(footer)


def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        print(
            f"Trying to login to Garmin Connect using token data from '{tokenstore}'...\n"
        )
        garmin = Garmin()
        garmin.login(tokenstore)
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(email, password)
            garmin.login()
            # Save tokens for next login
            garmin.garth.dump(tokenstore)

        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
            logger.error(err)
            return None

    return garmin

def fetch(api):
    # Skip requests if login failed
    if api:
        try:
            # Get activities data from startdate 'YYYY-MM-DD' to enddate 'YYYY-MM-DD', with (optional) activitytype
            # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
            activities = api.get_activities_by_date(startdate.isoformat(), today.isoformat(), activitytype)

            # Download activities
            for activity in activities:
                activity_id = activity["activityId"]
                activity_name = activity["activityName"]
                #display_text(activity)

                print(
                    f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.ORIGINAL)"
                )
                zip_data = api.download_activity(
                    activity_id, dl_fmt=api.ActivityDownloadFormat.ORIGINAL
                )
                output_file = f"{output_dir}/{str(activity_id)}.zip"
                with open(output_file, "wb") as fb:
                    fb.write(zip_data)
                print(f"Activity data downloaded to file {output_file}")
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
            GarthHTTPError
        ) as err:
            logger.error(err)
        except KeyError:
            # Invalid menu option chosen
            pass
    else:
        print("Could not login to Garmin Connect, try again later.")




## Main program loop
# Display header and login
print("\n*** Garmin Connect API Demo by cyberjunky ***\n")

cp_zwift_fits()

# Init API
if not api:
    api = init_api(email, password)

if api:
    fetch(api)
else:
    api = init_api(email, password)