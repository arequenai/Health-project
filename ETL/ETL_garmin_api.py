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

def get_mfa():
    """Get MFA code from user input."""
    print("Please enter the MFA code from your Garmin Connect app:")
    mfa_code = input()
    return mfa_code

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
    """Get Garmin data from start_date to today.
    If the existing data file is mostly empty, it will pull all data since March 16, 2024.
    Otherwise, it will pull the last week of data and merge it with existing data."""
    api = garmin_client
    end_date = datetime.date.today()
    data_file = 'Data/Cleaned/Garmin_daily.csv'
    
    # Check existing data
    if os.path.exists(data_file):
        existing_data = pd.read_csv(data_file)
        if len(existing_data) > 0:
            # If we have data, start from the last date minus 7 days
            last_date = pd.to_datetime(existing_data['date'].max()).date()
            start_date = last_date - datetime.timedelta(days=7)
            logger.info(f"Found existing data, pulling from {start_date} onwards")
            
            # Remove the last week of data from existing_data to avoid duplicates
            cutoff_date = start_date.strftime('%Y-%m-%d')
            existing_data = existing_data[existing_data['date'] < cutoff_date]
        else:
            logger.info("Existing data is empty, pulling all data since March 16, 2024")
            start_date = datetime.date(2024, 3, 16)
            existing_data = None
    else:
        logger.info("No existing data found, pulling all data since March 16, 2024")
        start_date = datetime.date(2024, 3, 16)
        existing_data = None
    
    logger.info(f"Getting Garmin data from {start_date} to {end_date}")
    total_days = (end_date - start_date).days + 1
    processed_days = 0
    
    # Initialize empty list to store data
    data_list = []
    
    # Loop through dates
    current_date = start_date
    while current_date <= end_date:
        try:
            # Get data for current date
            stats = api.get_stats(current_date)
            
            # Create dictionary with date and stats data
            data_dict = {'date': current_date.strftime('%Y-%m-%d')}
            data_dict.update(stats)
            
            # Append data to list
            data_list.append(data_dict)
            
            # Update progress
            processed_days += 1
            if processed_days % 10 == 0:  # Log every 10 days
                logger.info(f"Processed {processed_days}/{total_days} days ({(processed_days/total_days)*100:.1f}%)")
            
        except Exception as e:
            logger.warning(f"Failed to get data for {current_date}: {str(e)}")
        
        # Move to next date
        current_date += datetime.timedelta(days=1)
    
    if not data_list:
        logger.warning("No Garmin data found for the specified date range")
        return None
    
    logger.info("Processing daily metrics...")
    
    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(data_list)
    
    # Keep daily metrics
    df = df[['date',
            'averageStressLevel','restStressPercentage', 'lowStressPercentage', 
            'mediumStressPercentage', 'highStressPercentage', 'stressQualifier',
            'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryDuringSleep'
            ]]
    
    logger.info("Getting activities for the same date range...")
    
    # Get activities for the same date range
    activities = api.get_activities_by_date(start_date, end_date)
    
    # Process activities
    activity_data = []
    total_activities = len(activities)
    for i, activity in enumerate(activities, 1):
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
        
        if i % 10 == 0:  # Log every 10 activities
            logger.info(f"Processed {i}/{total_activities} activities ({(i/total_activities)*100:.1f}%)")
    
    logger.info("Processing activity data...")
    
    # Save detailed activity data and merge daily totals
    if activity_data:
        activity_df = pd.DataFrame(activity_data)
        
        # Calculate daily totals
        daily_totals = activity_df.groupby('date').agg({
            'training_load': 'sum',
            'tss': 'sum',
            'duration': 'sum'
        }).reset_index()
        
        # Also keep strength training minutes
        strength_data = activity_df[activity_df['type'] == 'strength_training']
        strength_daily = strength_data.groupby('date')['duration'].sum().reset_index()
        strength_daily['duration'] = strength_daily['duration'] / 60  # Convert to minutes
        strength_daily.rename(columns={'duration': 'strength_minutes'}, inplace=True)
        
        # Merge with daily stats
        df = pd.merge(df, daily_totals, on='date', how='left')
        df = pd.merge(df, strength_daily, on='date', how='left')
    
    # Fill NaN values with 0
    df = df.fillna(0)
    
    # If we have existing data, append the new data
    if existing_data is not None:
        df = pd.concat([existing_data, df], ignore_index=True)
    
    # Convert date to datetime for proper sorting and deduplication
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
    # Convert back to string format
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    logger.info("Completed Garmin data retrieval and processing")
    return df

def get_garmin_activities(garmin_client, start_date=datetime.date(2024, 3, 16)):
    """Get detailed activity data for analysis from start_date to today.
    If the existing data file is mostly empty, it will pull all data since March 16, 2024.
    Otherwise, it will pull the last week of data and merge it with existing data."""
    api = garmin_client
    end_date = datetime.date.today()
    data_file = 'Data/Cleaned/garmin_activities.csv'
    
    # Check existing data
    if os.path.exists(data_file):
        existing_data = pd.read_csv(data_file)
        if len(existing_data) > 0:
            # If we have data, start from the last date minus 7 days
            last_date = pd.to_datetime(existing_data['date'].max()).date()
            start_date = last_date - datetime.timedelta(days=7)
            logger.info(f"Found existing data, pulling from {start_date} onwards")
            
            # Remove the last week of data from existing_data to avoid duplicates
            cutoff_date = start_date.strftime('%Y-%m-%d')
            existing_data = existing_data[existing_data['date'] < cutoff_date]
        else:
            logger.info("Existing data is empty, pulling all data since March 16, 2024")
            start_date = datetime.date(2024, 3, 16)
            existing_data = None
    else:
        logger.info("No existing data found, pulling all data since March 16, 2024")
        start_date = datetime.date(2024, 3, 16)
        existing_data = None
    
    logger.info(f"Getting Garmin activities from {start_date} to {end_date}")
    
    try:
        activities = api.get_activities_by_date(start_date, end_date)
    except Exception as e:
        logger.error(f"Failed to get activities: {str(e)}")
        return None
    
    activity_data = []
    total_activities = len(activities)
    for i, activity in enumerate(activities, 1):
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
        
        if i % 10 == 0:  # Log every 10 activities
            logger.info(f"Processed {i}/{total_activities} activities ({(i/total_activities)*100:.1f}%)")
    
    if not activity_data:
        logger.warning("No activities found for the specified date range")
        return None
    
    df = pd.DataFrame(activity_data)
    
    # If we have existing data, append the new data
    if existing_data is not None:
        df = pd.concat([existing_data, df], ignore_index=True)
    
    # Convert date to datetime for proper sorting and deduplication
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates(subset=['date', 'type', 'duration'], keep='last')
    # Convert back to string format
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    return df

if __name__ == "__main__":
    garmin_client = init_garmin(email, password)
    df = get_garmin_data(garmin_client)
    # Write DataFrame to a temporary CSV file for testing
    df.to_csv('Data/Cleaned/Garmin_daily_new.csv', index=False)
    print('Garmin data saved to temporary CSV file for testing')