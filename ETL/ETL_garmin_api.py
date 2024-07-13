from dotenv import load_dotenv
load_dotenv("Credentials.env")

import datetime
import pandas as pd
import json
import logging
import os
import sys
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

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
email = os.getenv("USERNAME_G")
password = os.getenv("PASSWORD_G")

def init_garmin(email, password):
    """Initialize Garmin API with your credentials."""
    tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
    tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"

    try:
        # Using Oauth1 and OAuth2 token files from directory
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

            garmin = Garmin(email=email, password=password, is_cn=False, prompt_mfa=get_mfa)
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
            logger.error(err)
            return None

    return garmin

def get_mfa():
   
    return input("MFA code: ")

def get_garmin_data(garmin_client, start_date=datetime.date(2024, 3, 16)):
    api = garmin_client

    # Initialize empty list to store data
    data_list = []

    # Define start date and today's date
    end_date = datetime.date.today()

    # Loop through dates
    current_date = start_date
    while current_date <= end_date:
        # Get data for current date
        stats = api.get_stats(current_date)
        
        # Create dictionary with date and stats data
        data_dict = {'date': current_date}
        data_dict.update(stats)

        # Append data to list
        data_list.append(data_dict)
        
        # Move to next date
        current_date += datetime.timedelta(days=1)

    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(data_list)

    # Keep only relevant columns
    df = df[['date',
            'averageStressLevel','restStressPercentage', 'lowStressPercentage', 'mediumStressPercentage', 'highStressPercentage', 'stressQualifier',
            'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryDuringSleep'
                ]]

    # Now get Strength training data
    s_list = api.get_activities_by_date(start_date, datetime.date.today())

    # Initialize the DataFrame with empty values if the list is empty
    if not s_list:
        df_s = pd.DataFrame({
            'date': [datetime.date.today()],
            'strength_minutes': [0]
        })
    else:
        df_s = pd.DataFrame(s_list)
        df_s['typeKey'] = df_s['activityType'].apply(lambda x: x['typeKey'] if 'typeKey' in x else None)
        df_s = df_s[df_s['typeKey'] == 'strength_training']
        df_s['date'] = df_s['startTimeLocal'].apply(lambda x: x.split('T')[0])
        df_s['date'] = pd.to_datetime(df_s['date']).dt.date
        df_s = df_s[['date', 'duration']]
        df_s['duration'] = df_s['duration'] / 60
        df_s.rename(columns={'duration': 'strength_minutes'}, inplace=True)

    # Merge strength training data with main DataFrame
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = pd.merge(df, df_s, on='date', how='left')
    df['strength_minutes'] = df['strength_minutes'].fillna(0)

    return df

if __name__ == "__main__":
    garmin_client = init_garmin(email, password)
    df = get_garmin_data(garmin_client)
    # Write DataFrame to CSV file
    df.to_csv('Data/Cleaned/Garmin_daily.csv', index=False)
    print('Garmin data saved to CSV file')