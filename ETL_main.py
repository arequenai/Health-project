#!/usr/bin/env python3

# Import necessary modules and functions
import os, datetime
import pandas as pd
from ETL.ETL_general import update_incremental, update_incremental_api, get_most_recent_date, export_to_gsheets
from ETL.ETL_garmin_api import init_garmin, get_garmin_data, get_garmin_activities
from ETL.ETL_whoop import init_whoop, get_sleep_recovery_data, get_journal_data
from ETL.ETL_mfp_api import init_mfp, get_meal_data, get_meal_daily
from ETL.ETL_libreview import get_glucose_daily, get_glucose_time
from ETL.ETL_tss_calculation import get_tss_data
from ETL.ETL_fitbit import init_fitbit, get_body_measurements

def update_clean_files():
    """Update data of intermediate clean files"""
    
    # Weight data update from Fitbit
    weight_file = 'Data/Cleaned/Weight.csv'
    try:
        tokens = init_fitbit()
        df_weight = get_body_measurements(tokens)
        if not df_weight.empty:
            df_weight.to_csv(weight_file, index=False)
            print(f"{weight_file}: Data obtained from Fitbit and saved")
        else:
            print("No Fitbit weight data found")
    except Exception as e:
        print(f"Error getting Fitbit weight data: {str(e)}")

    # MyFitnessPal API update
    meals_file = 'Data/Cleaned/MFP meals scrapped.csv'
    meals_daily_file = 'Data/Cleaned/MFP per day scrapped.csv'
    mfp_client = init_mfp()
    get_meal_data(mfp_client, meals_file)
    get_meal_daily(mfp_client, meals_daily_file)

    # Garmin update
    garmin_file = 'Data/Cleaned/Garmin_daily.csv'
    activities_file = 'Data/Cleaned/garmin_activities.csv'
    email_g = os.getenv("USERNAME_G")
    password_g = os.getenv("PASSWORD_G")
    garmin_client = init_garmin(email_g, password_g)
    
    # Get Garmin data and activities
    df_garmin = get_garmin_data(garmin_client)
    df_garmin.to_csv(garmin_file, index=False)
    print(f"{garmin_file}: Data obtained and saved")
    
    df_activities = get_garmin_activities(garmin_client)
    if df_activities is not None:
        df_activities.to_csv(activities_file, index=False)
        print(f"{activities_file}: Data obtained and saved")
        
        # Calculate TSS metrics from Garmin data
        tss_file = 'Data/Cleaned/TSS metrics.csv'
        tss_data = get_tss_data(df_activities)
        tss_data.to_csv(tss_file, index=False)
        print(f"{tss_file}: TSS metrics calculated from Garmin data")

    # Glucose update
    libreview_file_raw = 'Data/LibreLink/AlbertoRequena Izard_glucose.csv'
    glucose_daily_file = 'Data/Cleaned/Glucose_daily.csv'
    glucose_time_file = 'Data/Cleaned/Glucose.csv'
    glucose_time_raw = 'Data/LibreLink/AlbertoRequena Izard_glucose.csv'
    update_incremental(libreview_file_raw, glucose_daily_file, get_glucose_daily)
    get_glucose_time(glucose_time_raw).to_csv(glucose_time_file, index=False)

    # Whoop API update
    whoop_file = 'Data/Cleaned/Sleep_and_recovery.csv'
    journal_file_raw = 'Data/Whoop/journal_entries.csv'
    journal_file = 'Data/Cleaned/Journal.csv'
    email_w = os.getenv("USERNAME_W")
    password_w = os.getenv("PASSWORD_W")
    whoop_client = init_whoop(email_w, password_w)
    update_incremental_api(whoop_client, whoop_file, get_sleep_recovery_data)
    get_journal_data(journal_file_raw, journal_file)  # Not incremental for now

    print('Clean data files updated')

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