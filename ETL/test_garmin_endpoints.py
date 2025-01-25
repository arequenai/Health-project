from dotenv import load_dotenv
load_dotenv("Credentials.env")

import datetime
import pandas as pd
import json
import logging
import os
from getpass import getpass

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = os.getenv("USERNAME_G")
password = os.getenv("PASSWORD_G")

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
            garmin = Garmin(email=email, password=password, is_cn=False, prompt_mfa=get_mfa)
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError) as err:
            logger.error(err)
            return None

    return garmin

def process_vo2max(all_data):
    """Post-process VO2max data:
    - If no VO2max data or no run for a day, use previous day's VO2max
    - If there's a run and VO2max data, use that value
    """
    prev_vo2max = None
    dates = sorted(all_data.keys())
    
    for date in dates:
        current_vo2max = all_data[date]['vo2max']
        has_run = all_data[date]['distance'] > 0
        
        if has_run and current_vo2max is not None:
            # If there's a run and VO2max data, use it
            prev_vo2max = current_vo2max
        elif prev_vo2max is not None:
            # If no run or no VO2max data, use previous value
            all_data[date]['vo2max'] = prev_vo2max
            
    return all_data

def test_endpoints():
    """Test various Garmin Connect endpoints for six months of data."""
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=180)  # approximately 6 months
    logger.info(f"Testing endpoints from {start_date} to {end_date}")
    
    # Initialize Garmin client
    api = init_garmin(email, password)
    if api is None:
        logger.error("Failed to initialize Garmin client")
        return
    
    try:
        # Test race predictions (daily)
        logger.info("\nTesting race predictions...")
        try:
            race_predictions = api.get_race_predictions(
                startdate=start_date,
                enddate=end_date,
                _type='daily'
            )
            logger.info(f"Race predictions: {json.dumps(race_predictions, indent=2)}")
            
            # Store predictions by date
            daily_predictions = {}
            for prediction in race_predictions:
                date = prediction.get('calendarDate')
                if date:
                    daily_predictions[date] = {
                        'predicted_5k': prediction.get('time5K', 0),
                        'predicted_10k': prediction.get('time10K', 0),
                        'predicted_half': prediction.get('timeHalfMarathon', 0),
                        'predicted_marathon': prediction.get('timeMarathon', 0)
                    }
        except Exception as e:
            logger.warning(f"Could not get race predictions: {str(e)}")
            daily_predictions = {}
        
        # Test max metrics for VO2max (daily)
        logger.info("\nTesting max metrics for VO2max...")
        vo2max_data = []
        current_date = start_date
        while current_date <= end_date:
            try:
                max_metrics = api.get_max_metrics(current_date.strftime('%Y-%m-%d'))
                if max_metrics and max_metrics[0].get('generic', {}).get('vo2MaxValue'):
                    vo2max_data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'vo2max': max_metrics[0]['generic']['vo2MaxValue']
                    })
            except Exception as e:
                logger.warning(f"Could not get max metrics for {current_date}: {str(e)}")
            current_date += datetime.timedelta(days=1)
        
        logger.info(f"VO2max data collected for {len(vo2max_data)} days:")
        for data in vo2max_data:
            logger.info(f"Date: {data['date']}, VO2max: {data['vo2max']}")
        
        # Test activities for running metrics (daily totals)
        logger.info("\nTesting activities...")
        activities = api.get_activities_by_date(start_date, end_date)
        running_data = []
        
        for activity in activities:
            if activity.get('activityType', {}).get('typeKey') == 'running':
                activity_date = datetime.datetime.strptime(
                    activity['startTimeLocal'].split()[0], 
                    '%Y-%m-%d'
                ).date()
                
                running_data.append({
                    'date': activity_date.strftime('%Y-%m-%d'),
                    'distance': activity.get('distance', 0),
                    'elevation_gain': activity.get('elevationGain', 0)
                })
        
        # Group running data by date
        daily_running = {}
        for activity in running_data:
            date = activity['date']
            if date not in daily_running:
                daily_running[date] = {
                    'distance': 0,
                    'elevation_gain': 0
                }
            daily_running[date]['distance'] += activity['distance']
            daily_running[date]['elevation_gain'] += activity['elevation_gain']
        
        logger.info(f"\nRunning data collected for {len(daily_running)} days:")
        for date, metrics in sorted(daily_running.items()):
            logger.info(
                f"Date: {date}, "
                f"Total Distance: {metrics['distance']:.1f}m, "
                f"Total Elevation: {metrics['elevation_gain']:.1f}m"
            )
        
        # Write all data to CSV
        all_data = {}
        
        # Update the data combination section
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            predictions = daily_predictions.get(date_str, {})
            all_data[date_str] = {
                'date': date_str,
                'predicted_5k': predictions.get('predicted_5k', 0),
                'predicted_10k': predictions.get('predicted_10k', 0),
                'predicted_half': predictions.get('predicted_half', 0),
                'predicted_marathon': predictions.get('predicted_marathon', 0),
                'vo2max': next((d['vo2max'] for d in vo2max_data if d['date'] == date_str), None),
                'distance': daily_running.get(date_str, {}).get('distance', 0),
                'elevation_gain': daily_running.get(date_str, {}).get('elevation_gain', 0)
            }
            current_date += datetime.timedelta(days=1)
        
        # Apply VO2max post-processing
        all_data = process_vo2max(all_data)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(all_data.values())
        df.to_csv('Data/Cleaned/garmin_test_results.csv', index=False)
        logger.info("\nData saved to Data/Cleaned/garmin_test_results.csv")
    
    except Exception as e:
        logger.error(f"Error testing endpoints: {str(e)}")

if __name__ == "__main__":
    test_endpoints() 