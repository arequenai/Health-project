#!/usr/bin/env python3

# Import necessary modules and functions
import os, datetime
import pandas as pd
import logging
import sys
from ETL.ETL_general import update_incremental, update_incremental_api, get_most_recent_date, export_to_gsheets, get_incremental_data_api
from ETL.ETL_garmin_api import init_garmin, get_garmin_data, get_garmin_activities
from ETL.ETL_whoop import init_whoop, get_sleep_recovery_data, get_journal_data
from ETL.ETL_mfp_api import init_mfp, get_meal_data, get_meal_daily
from ETL.ETL_libreview import get_glucose_daily, get_glucose_time
from ETL.ETL_tss_calculation import get_tss_data
from ETL.ETL_fitbit import init_fitbit, get_body_measurements
from ETL.ETL_journal import get_journal_data

# Configure logging with a more visible format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def update_clean_files():
    """Update data of intermediate clean files"""
    
    logger.info("Starting to update clean files...")
    
    # Load environment variables
    email_g = os.getenv("USERNAME_G")
    password_g = os.getenv("PASSWORD_G")
    
    # Weight data update from Fitbit
    weight_file = 'Data/Cleaned/Weight.csv'
    try:
        logger.info("Initializing Fitbit connection...")
        tokens = init_fitbit()
        df_weight = get_body_measurements(tokens)
        if not df_weight.empty:
            df_weight.to_csv(weight_file, index=False)
            logger.info(f"{weight_file}: Data obtained from Fitbit and saved")
        else:
            logger.warning("No Fitbit weight data found")
    except Exception as e:
        logger.error(f"Error getting Fitbit weight data: {str(e)}")

    # MyFitnessPal API update
    logger.info("Starting MyFitnessPal update...")
    meals_file = 'Data/Cleaned/MFP meals scrapped.csv'
    meals_daily_file = 'Data/Cleaned/MFP per day scrapped.csv'
    try:
        mfp_client = init_mfp()
        get_meal_data(mfp_client, meals_file)
        get_meal_daily(mfp_client, meals_daily_file)
    except Exception as e:
        logger.error(f"Error in MyFitnessPal update: {str(e)}")

    # Garmin update
    logger.info("Starting Garmin update...")
    logger.info("Initializing Garmin connection...")
    garmin_client = init_garmin(email_g, password_g)
    
    if garmin_client:
        logger.info("Getting Garmin daily data...")
        df_garmin = get_incremental_data_api(garmin_client, 'Data/Cleaned/Garmin_daily.csv', get_garmin_data)
        if df_garmin is not None and not df_garmin.empty:
            df_garmin.to_csv('Data/Cleaned/Garmin_daily.csv', index=False)
            logger.info("Data/Cleaned/Garmin_daily.csv: Data obtained and saved")
        else:
            logger.info("No new Garmin daily data to update")
        
        logger.info("Getting Garmin activities...")
        df_activities = get_incremental_data_api(garmin_client, 'Data/Cleaned/garmin_activities.csv', get_garmin_activities)
        if df_activities is not None and not df_activities.empty:
            df_activities.to_csv('Data/Cleaned/garmin_activities.csv', index=False)
            logger.info("Data/Cleaned/garmin_activities.csv: Data obtained and saved")
            
            # Calculate TSS metrics only if we have new activities
            logger.info("Calculating TSS metrics...")
            df_tss = get_tss_data(df_activities)
            if df_tss is not None and not df_tss.empty:
                df_tss.to_csv('Data/Cleaned/TSS metrics.csv', index=False)
                logger.info("Data/Cleaned/TSS metrics.csv: TSS metrics calculated from Garmin data")
        else:
            logger.info("No new Garmin activities to update")

    # Glucose update
    logger.info("Starting Glucose update...")
    try:
        libreview_file_raw = 'Data/LibreLink/AlbertoRequena Izard_glucose.csv'
        glucose_daily_file = 'Data/Cleaned/Glucose_daily.csv'
        glucose_time_file = 'Data/Cleaned/Glucose.csv'
        glucose_time_raw = 'Data/LibreLink/AlbertoRequena Izard_glucose.csv'
        update_incremental(libreview_file_raw, glucose_daily_file, get_glucose_daily)
        get_glucose_time(glucose_time_raw).to_csv(glucose_time_file, index=False)
    except Exception as e:
        logger.error(f"Error in Glucose update: {str(e)}")

    # Replace Whoop journal update with Google Form journal update
    logger.info("Starting Journal update...")
    try:
        JOURNAL_SPREADSHEET_ID = '1E0pWgt9Zifdx3S3iqpyAjTHijn-xZcXYLRXvqwgo-tg'  # Form responses spreadsheet
        df_journal = get_journal_data(JOURNAL_SPREADSHEET_ID)
        if df_journal is not None:
            journal_file = 'Data/Cleaned/Journal.csv'
            df_journal.to_csv(journal_file, index=False)
            logger.info(f"{journal_file}: Journal data obtained and saved")
        else:
            logger.warning("No new journal data found")
    except Exception as e:
        logger.error(f"Error in Journal update: {str(e)}")

    logger.info('Clean data files update completed')

def integrate_data():
    """Integrate all data sources into a single file and upload to Google Sheets"""
    
    # Get all key dfs from Cleaned Data
    df_t = pd.read_csv('Data/Cleaned/TSS metrics.csv')
    df_s = pd.read_csv('Data/Cleaned/Sleep_and_recovery.csv')
    df_f = pd.read_csv('Data/Cleaned/MFP per day scrapped.csv')
    df_g = pd.read_csv('Data/Cleaned/Glucose_daily.csv')
    df_gar = pd.read_csv('Data/Cleaned/Garmin_daily.csv')
    df_j = pd.read_csv('Data/Cleaned/Journal.csv')
    df_w = pd.read_csv('Data/Cleaned/Weight.csv')

    # Filter out today from MFP per day scrapped
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    df_f = df_f[df_f['date']!=today]

    # Filter out TSS metrics from before we are reading Garmin data
    df_t = df_t[df_t['date']>=df_gar['date'].min()]

    # Print the min and the max date of each df
    print('\nData ranges:')
    print('TSS metrics: ', df_t['date'].min(),' to ',df_t['date'].max())
    print('Sleep and recovery: ',df_s['date'].min(),' to ',df_s['date'].max())
    print('MFP per day scrapped: ',df_f['date'].min(),' to ',df_f['date'].max())
    print('Glucose daily: ',df_g['date'].min(),' to ',df_g['date'].max())
    print('Garmin daily: ',df_gar['date'].min(),' to ',df_gar['date'].max())
    print('Journal: ',df_j['date'].min(),' to ',df_j['date'].max())
    print('Weight: ',df_w['date'].min(),' to ',df_w['date'].max())

    # Perform an outer join on all dfs
    df = df_t.merge(df_s, on='date', how='outer')
    df = df.merge(df_f, on='date', how='outer')
    df = df.merge(df_g, on='date', how='outer')
    df = df.merge(df_gar, on='date', how='outer')
    df = df.merge(df_j, on='date', how='outer')
    df = df.merge(df_w, on='date', how='outer')

    # Save to CSV
    df.to_csv('Data/Cleaned/Integrated_data.csv', index=False)
    print('\nIntegrated data file created: ',df['date'].min(),' to ',df['date'].max())

    # Export DataFrame to Google Sheets
    print('\nUploading to Google Sheets...')
    sheet_name = 'Integrated_data'
    if export_to_gsheets(df, sheet_name):
        print(f'Successfully uploaded to Google Sheets sheet: {sheet_name}')
    else:
        print('Failed to upload to Google Sheets. Check the logs for details.')
        print('Data is still saved locally in Data/Cleaned/Integrated_data.csv')

if __name__ == "__main__":
    # Load environment variables from Credentials.env
    from dotenv import load_dotenv
    load_dotenv('Credentials.env')
    
    # Run the ETL process
    print("Starting ETL process...")
    update_clean_files()
    integrate_data()
    print("ETL process completed!") 