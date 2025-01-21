# Common configuration settings for ETL processes

import datetime

# Start date for all data collection
DATA_START_DATE = datetime.date(2024, 3, 16)

# File paths
CLEANED_DATA_DIR = 'Data/Cleaned'
RAW_DATA_DIR = 'Data'

# File names
GARMIN_DAILY_FILE = f'{CLEANED_DATA_DIR}/Garmin_daily.csv'
GARMIN_ACTIVITIES_FILE = f'{CLEANED_DATA_DIR}/garmin_activities.csv'
WHOOP_SLEEP_RECOVERY_FILE = f'{CLEANED_DATA_DIR}/Sleep_and_recovery.csv'
WHOOP_JOURNAL_FILE = f'{CLEANED_DATA_DIR}/Journal.csv'
MFP_MEALS_FILE = f'{CLEANED_DATA_DIR}/MFP meals scrapped.csv'
MFP_DAILY_FILE = f'{CLEANED_DATA_DIR}/MFP per day scrapped.csv'
GLUCOSE_DAILY_FILE = f'{CLEANED_DATA_DIR}/Glucose_daily.csv'
WEIGHT_FILE = f'{CLEANED_DATA_DIR}/Weight.csv'
TSS_METRICS_FILE = f'{CLEANED_DATA_DIR}/TSS metrics.csv'

# Google Sheets settings
JOURNAL_SPREADSHEET_ID = '1E0pWgt9Zifdx3S3iqpyAjTHijn-xZcXYLRXvqwgo-tg'
INTEGRATED_DATA_SPREADSHEET_ID = '197VfZCekvBev0m1vsi8kUHpuO0IoTRA90_bQRGBYYSM' 