from ETL.ETL_garmin_api import init_garmin, get_garmin_data, get_garmin_activities
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials
email = os.getenv("USERNAME_G")
password = os.getenv("PASSWORD_G")

# Initialize Garmin client
logger.info("Initializing Garmin connection...")
garmin_client = init_garmin(email, password)

if garmin_client:
    logger.info("Getting Garmin daily data...")
    df_garmin = get_garmin_data(garmin_client)
    if df_garmin is not None and not df_garmin.empty:
        df_garmin.to_csv('Data/Cleaned/Garmin_daily.csv', index=False)
        logger.info("Data/Cleaned/Garmin_daily.csv: Data obtained and saved")
    else:
        logger.info("No new Garmin daily data to update")
    
    logger.info("Getting Garmin activities...")
    df_activities = get_garmin_activities(garmin_client)
    if df_activities is not None and not df_activities.empty:
        df_activities.to_csv('Data/Cleaned/garmin_activities.csv', index=False)
        logger.info("Data/Cleaned/garmin_activities.csv: Data obtained and saved")
    else:
        logger.info("No new Garmin activities to update")
else:
    logger.error("Failed to initialize Garmin client") 