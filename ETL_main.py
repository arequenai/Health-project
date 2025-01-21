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
from ETL import config

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
    try:
        logger.info("Initializing Fitbit connection...")
        tokens = init_fitbit()
        df_weight = get_body_measurements(tokens)
        if not df_weight.empty:
            df_weight.to_csv(config.WEIGHT_FILE, index=False)
            logger.info(f"{config.WEIGHT_FILE}: Data obtained from Fitbit and saved")
        else:
            logger.warning("No Fitbit weight data found")
    except Exception as e:
        logger.error(f"Error getting Fitbit weight data: {str(e)}")

    # MyFitnessPal API update
    logger.info("Starting MyFitnessPal update...")
    try:
        mfp_client = init_mfp()
        get_meal_data(mfp_client, config.MFP_MEALS_FILE)
        get_meal_daily(mfp_client, config.MFP_DAILY_FILE)
    except Exception as e:
        logger.error(f"Error in MyFitnessPal update: {str(e)}")

    # Garmin update
    logger.info("Starting Garmin update...")
    logger.info("Initializing Garmin connection...")
    garmin_client = init_garmin(email_g, password_g)
    
    if garmin_client:
        logger.info("Getting Garmin daily data...")
        df_garmin = get_garmin_data(garmin_client)
        if df_garmin is not None and not df_garmin.empty:
            df_garmin.to_csv(config.GARMIN_DAILY_FILE, index=False)
            logger.info(f"{config.GARMIN_DAILY_FILE}: Data obtained and saved")
        else:
            logger.info("No new Garmin daily data to update")
        
        logger.info("Getting Garmin activities...")
        df_activities = get_garmin_activities(garmin_client)
        if df_activities is not None and not df_activities.empty:
            df_activities.to_csv(config.GARMIN_ACTIVITIES_FILE, index=False)
            logger.info(f"{config.GARMIN_ACTIVITIES_FILE}: Data obtained and saved")
            
            # Calculate TSS metrics only if we have new activities
            logger.info("Calculating TSS metrics...")
            df_tss = get_tss_data(df_activities)
            if df_tss is not None and not df_tss.empty:
                df_tss.to_csv(config.TSS_METRICS_FILE, index=False)
                logger.info(f"{config.TSS_METRICS_FILE}: TSS metrics calculated from Garmin data")
        else:
            logger.info("No new Garmin activities to update")

    # Glucose update
    logger.info("Starting Glucose update...")
    try:
        libreview_file_raw = 'Data/LibreLink/AlbertoRequena Izard_glucose.csv'
        update_incremental(libreview_file_raw, config.GLUCOSE_DAILY_FILE, get_glucose_daily)
        get_glucose_time(libreview_file_raw).to_csv('Data/Cleaned/Glucose.csv', index=False)
    except Exception as e:
        logger.error(f"Error in Glucose update: {str(e)}")

    # Replace Whoop journal update with Google Form journal update
    logger.info("Starting Journal update...")
    try:
        df_journal = get_journal_data(config.JOURNAL_SPREADSHEET_ID)
        if df_journal is not None:
            df_journal.to_csv(config.WHOOP_JOURNAL_FILE, index=False)
            logger.info(f"{config.WHOOP_JOURNAL_FILE}: Journal data obtained and saved")
        else:
            logger.warning("No new journal data found")
    except Exception as e:
        logger.error(f"Error in Journal update: {str(e)}")

    # Update Whoop sleep and recovery data
    logger.info("Starting Whoop sleep and recovery update...")
    try:
        # Initialize Whoop client
        un = os.getenv("USERNAME_W")
        pw = os.getenv("PASSWORD_W")
        if not un or not pw:
            logger.error("Whoop credentials not found in environment variables")
            return
            
        client = init_whoop(un, pw)
        if client:
            df = get_sleep_recovery_data(client)
            if df is not None:
                df.to_csv(config.WHOOP_SLEEP_RECOVERY_FILE, index=False)
                logger.info(f"{config.WHOOP_SLEEP_RECOVERY_FILE}: Sleep and recovery data obtained and saved")
            else:
                logger.warning("No new sleep and recovery data found")
        else:
            logger.error("Failed to initialize Whoop client")
    except Exception as e:
        logger.error(f"Error in Whoop sleep and recovery update: {str(e)}")

    logger.info('Clean data files update completed')

def integrate_data():
    """Integrate all data sources into a single file and upload to Google Sheets"""
    
    # Get all key dfs from Cleaned Data
    df_t = pd.read_csv(config.TSS_METRICS_FILE)
    df_s = pd.read_csv(config.WHOOP_SLEEP_RECOVERY_FILE)
    df_f = pd.read_csv(config.MFP_DAILY_FILE)
    df_g = pd.read_csv(config.GLUCOSE_DAILY_FILE)
    df_gar = pd.read_csv(config.GARMIN_DAILY_FILE)
    df_j = pd.read_csv(config.WHOOP_JOURNAL_FILE)
    df_w = pd.read_csv(config.WEIGHT_FILE)

    # Filter out today from MFP per day scrapped
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    df_f = df_f[df_f['date']!=today]

    # Convert all dates to datetime for consistent filtering
    for df in [df_t, df_s, df_f, df_g, df_gar, df_j, df_w]:
        df['date'] = pd.to_datetime(df['date'])
    
    # Filter all data to start from config start date
    start_date = pd.to_datetime(config.DATA_START_DATE)
    df_t = df_t[df_t['date'] >= start_date]
    df_s = df_s[df_s['date'] >= start_date]
    df_f = df_f[df_f['date'] >= start_date]
    df_g = df_g[df_g['date'] >= start_date]
    df_gar = df_gar[df_gar['date'] >= start_date]
    df_j = df_j[df_j['date'] >= start_date]
    df_w = df_w[df_w['date'] >= start_date]

    # Print the min and the max date of each df
    print('\nData ranges:')
    print('TSS metrics: ', df_t['date'].min().strftime('%Y-%m-%d'),' to ',df_t['date'].max().strftime('%Y-%m-%d'))
    print('Sleep and recovery: ',df_s['date'].min().strftime('%Y-%m-%d'),' to ',df_s['date'].max().strftime('%Y-%m-%d'))
    print('MFP per day scrapped: ',df_f['date'].min().strftime('%Y-%m-%d'),' to ',df_f['date'].max().strftime('%Y-%m-%d'))
    print('Glucose daily: ',df_g['date'].min().strftime('%Y-%m-%d'),' to ',df_g['date'].max().strftime('%Y-%m-%d'))
    print('Garmin daily: ',df_gar['date'].min().strftime('%Y-%m-%d'),' to ',df_gar['date'].max().strftime('%Y-%m-%d'))
    print('Journal: ',df_j['date'].min().strftime('%Y-%m-%d'),' to ',df_j['date'].max().strftime('%Y-%m-%d'))
    print('Weight: ',df_w['date'].min().strftime('%Y-%m-%d'),' to ',df_w['date'].max().strftime('%Y-%m-%d'))

    # Clean up column names and remove duplicates
    # Rename fat to body_fat in weight data if not already renamed
    if 'fat' in df_w.columns:
        df_w = df_w.rename(columns={'fat': 'body_fat'})
    
    # Remove redundant columns
    if 'tss' in df_gar.columns:
        df_gar = df_gar.drop(columns=['tss'])
    if 'sleep_id' in df_s.columns:
        df_s = df_s.drop(columns=['sleep_id'])

    # Standardize journal responses
    def standardize_response(x):
        if pd.isna(x) or x == '':
            return ''
        x = str(x).lower()
        if x.startswith('yes') or x == 'true':
            return 'Yes'
        if x.startswith('no') or x == 'false':
            return 'No'
        return ''

    for col in df_j.columns:
        if col not in ['date', 'Timestamp', 'drinks']:
            df_j[col] = df_j[col].apply(standardize_response)

    # Perform an outer join on all dfs
    df = df_t.merge(df_s, on='date', how='outer')
    df = df.merge(df_f, on='date', how='outer')
    df = df.merge(df_g, on='date', how='outer')
    df = df.merge(df_gar, on='date', how='outer')
    df = df.merge(df_j, on='date', how='outer')
    df = df.merge(df_w, on='date', how='outer')

    # Sort by date
    df = df.sort_values('date')
    
    # Format decimal places for different metric types
    
    # Sleep metrics (2 decimals for durations, 0 for scores)
    sleep_duration_cols = ['sleep_duration', 'sleep_rem', 'sleep_deep', 'sleep_light', 'sleep_awake']
    sleep_score_cols = ['sleep_score_performance', 'sleep_score_consistency', 'sleep_score_efficiency']
    
    for col in sleep_duration_cols:
        if col in df.columns:
            df[col] = df[col].round(2)
    
    for col in sleep_score_cols:
        if col in df.columns:
            df[col] = df[col].round(0)
    
    # Recovery metrics
    if 'recovery_score' in df.columns:
        df['recovery_score'] = df['recovery_score'].round(0)
    if 'resting_hr' in df.columns:
        df['resting_hr'] = df['resting_hr'].round(0)
    if 'hrv' in df.columns:
        df['hrv'] = df['hrv'].round(0)
    if 'spo2' in df.columns:
        df['spo2'] = df['spo2'].round(1)
    if 'skin_temp' in df.columns:
        df['skin_temp'] = df['skin_temp'].round(1)
    
    # Training metrics
    if 'training_load' in df.columns:
        df['training_load'] = df['training_load'].round(0)
    if 'intensity' in df.columns:
        df['intensity'] = df['intensity'].round(2)
    if 'duration' in df.columns:
        df['duration'] = df['duration'].round(0)
    if 'strength_minutes' in df.columns:
        df['strength_minutes'] = df['strength_minutes'].round(0)
    
    # Weight and nutrition metrics (1 decimal for weight and body fat, 0 for calories/macros)
    if 'weight' in df.columns:
        df['weight'] = df['weight'].round(1)
    if 'bmi' in df.columns:
        df['bmi'] = df['bmi'].round(1)
    if 'body_fat' in df.columns:
        df['body_fat'] = df['body_fat'].round(1)
    
    nutrition_cols = ['calories', 'protein', 'carbs', 'fat', 'sodium', 'sugar', 
                     'calories_consumed', 'calories_goal', 'calories_net',
                     'calories_consumed_breakfast', 'calories_consumed_lunch',
                     'calories_consumed_dinner', 'calories_consumed_snacks']
    for col in nutrition_cols:
        if col in df.columns:
            df[col] = df[col].round(0)
    
    # Glucose metrics (0 decimals for glucose values, 1 decimal for percentages)
    glucose_cols = ['mean_glucose', 'std_glucose', 'max_glucose', 'wake_up_glucose']
    glucose_pct_cols = ['time_in_range', 'time_above_range', 'time_below_range']
    
    for col in glucose_cols:
        if col in df.columns:
            df[col] = df[col].round(0)
    
    for col in glucose_pct_cols:
        if col in df.columns:
            df[col] = df[col].round(1)
            
    # Stress metrics (1 decimal for percentages)
    stress_pct_cols = ['restStressPercentage', 'lowStressPercentage', 
                      'mediumStressPercentage', 'highStressPercentage']
    for col in stress_pct_cols:
        if col in df.columns:
            df[col] = df[col].round(1)
            
    # Body battery metrics (0 decimals)
    battery_cols = ['bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryDuringSleep']
    for col in battery_cols:
        if col in df.columns:
            df[col] = df[col].round(0)
            
    # TSS metrics (1 decimal)
    tss_cols = ['TSS', 'CTL', 'ATL', 'TSB']
    for col in tss_cols:
        if col in df.columns:
            df[col] = df[col].round(1)
    
    # Convert back to string format for date
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Remove any empty rows (where all columns except date are NaN)
    df = df.dropna(how='all', subset=df.columns.difference(['date']))

    # Save to CSV
    df.to_csv('Data/Cleaned/Integrated_data.csv', index=False)
    print('\nIntegrated data file created: ',df['date'].min(),' to ',df['date'].max())

    # Export DataFrame to Google Sheets
    print('\nUploading to Google Sheets...')
    sheet_name = 'Integrated_data'
    export_to_gsheets(df, sheet_name)
    print(f"Successfully uploaded to Google Sheets sheet: {sheet_name}")

if __name__ == "__main__":
    print("Starting ETL process...")
    update_clean_files()
    integrate_data()
    print("ETL process completed!") 