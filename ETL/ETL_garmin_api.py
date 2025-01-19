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

def get_credentials():
    email = input("Enter your Garmin Connect email: ")
    password = getpass("Enter your Garmin Connect password: ")
    return email, password


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
        data_dict = {'date': current_date.strftime('%Y-%m-%d')}  # Convert date to string format
        data_dict.update(stats)

        # Append data to list
        data_list.append(data_dict)
        
        # Move to next date
        current_date += datetime.timedelta(days=1)

    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(data_list)

    # Keep daily metrics
    df = df[['date',
            'averageStressLevel','restStressPercentage', 'lowStressPercentage', 
            'mediumStressPercentage', 'highStressPercentage', 'stressQualifier',
            'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryDuringSleep'
            ]]

    # Get all activities
    activities = api.get_activities_by_date(start_date, end_date)
    
    # Process activities
    activity_data = []
    for activity in activities:
        activity_date = pd.to_datetime(activity['startTimeLocal']).date().strftime('%Y-%m-%d')  # Convert to string format
        
        activity_dict = {
            'date': activity_date,
            'type': activity.get('activityType', {}).get('typeKey', 'unknown'),
            'duration': activity.get('duration', 0),
            'training_load': activity.get('activityTrainingLoad', 0),
            'aerobic_te': activity.get('aerobicTrainingEffect', 0),
            'anaerobic_te': activity.get('anaerobicTrainingEffect', 0),
            'avg_hr': activity.get('averageHR', 0),
            'max_hr': activity.get('maxHR', 0),
            'avg_power': activity.get('avgPower', 0),
            'norm_power': activity.get('normPower', 0),
            'intensity_factor': activity.get('intensityFactor', 0),
            'tss': activity.get('trainingStressScore', 0)
        }
        activity_data.append(activity_dict)

    # Save detailed activity data for analysis
    if activity_data:
        activity_df = pd.DataFrame(activity_data)
        activity_df.to_csv('Data/Cleaned/garmin_activities.csv', index=False)
        
        # Calculate daily totals
        daily_totals = activity_df.groupby('date').agg({
            'training_load': 'sum',
            'tss': 'sum',
            'duration': 'sum'
        }).reset_index()
        
        # Also keep strength training minutes as before
        strength_data = activity_df[activity_df['type'] == 'strength_training']
        strength_daily = strength_data.groupby('date')['duration'].sum().reset_index()
        strength_daily['duration'] = strength_daily['duration'] / 60  # Convert to minutes
        strength_daily.rename(columns={'duration': 'strength_minutes'}, inplace=True)
        
        # Merge with daily stats
        df = pd.merge(df, daily_totals, on='date', how='left')
        df = pd.merge(df, strength_daily, on='date', how='left')
    
    # Fill NaN values with 0
    df = df.fillna(0)
    
    return df

def get_garmin_activities(garmin_client, start_date=datetime.date(2024, 3, 16)):
    """Separate function to get detailed activity data for analysis."""
    api = garmin_client
    end_date = datetime.date.today()
    
    activities = api.get_activities_by_date(start_date, end_date)
    
    activity_data = []
    for activity in activities:
        activity_date = pd.to_datetime(activity['startTimeLocal']).date().strftime('%Y-%m-%d')
        
        activity_dict = {
            'date': activity_date,
            'type': activity.get('activityType', {}).get('typeKey', 'unknown'),
            'duration': activity.get('duration', 0),
            'training_load': activity.get('activityTrainingLoad', 0),
            'aerobic_te': activity.get('aerobicTrainingEffect', 0),
            'anaerobic_te': activity.get('anaerobicTrainingEffect', 0),
            'avg_hr': activity.get('averageHR', 0),
            'max_hr': activity.get('maxHR', 0),
            'avg_power': activity.get('avgPower', 0),
            'norm_power': activity.get('normPower', 0),
            'intensity_factor': activity.get('intensityFactor', 0),
            'tss': activity.get('trainingStressScore', 0)
        }
        activity_data.append(activity_dict)
    
    return pd.DataFrame(activity_data) if activity_data else None

if __name__ == "__main__":
    garmin_client = init_garmin(email, password)
    df = get_garmin_data(garmin_client)
    # Write DataFrame to a temporary CSV file for testing
    df.to_csv('Data/Cleaned/Garmin_daily_new.csv', index=False)
    print('Garmin data saved to temporary CSV file for testing')