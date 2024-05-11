import pandas as pd
import numpy as np

DATA_GLUCOSE = '2024-03-23'

# Read the CSV
df = pd.read_csv('Data/LibreLink/AlbertoRequena Izard_glucose.csv', skiprows=1)

# Keep only columns we need
df = df[['Sello de tiempo del dispositivo', 'Historial de glucosa mg/dL', 'Escaneo de glucosa mg/dL']]

# Rename columns
df.columns = ['timestamp', 'glucose', 'scan_glucose']

# Combine rows 2 and 3, taking whichever is not NaN
df['glucose'] = df['glucose'].combine_first(df['scan_glucose'])
# Drop the scan_glucose column
df = df.drop(columns=['scan_glucose'])
# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True)
# Separate date and time
df['date'] = df['timestamp'].dt.date
df['time'] = df['timestamp'].dt.time
# Drop the timestamp column
df = df.drop(columns=['timestamp'])
# Change columns order
df = df[['date', 'time', 'glucose']]

# Filter for only where glucose isn't NaN
df = df[df['glucose'].notna()]

# Save to CSV
df.to_csv('Data/Cleaned/Glucose.csv', index=False)
print('Glucose data extracted and saved to Data/Cleaned/Glucose.csv')

### Continues to create daily data

# Create datetime from date and time
df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

# Filter data for since the first date we tracked glucose data
df = df[df['datetime'] >= DATA_GLUCOSE]
df = df.sort_values('datetime')

# Calculate the average glucose and standard deviation for each day
df = df.dropna(subset=['glucose'])
df_d = df.groupby('date').agg({'glucose': ['mean', 'std', 'max']}).reset_index()

# Transform the multi-index columns to single index
df_d.columns = ['date', 'mean_glucose', 'std_glucose', 'max_glucose']

# Get wake up time from Whoop API
import os
from dotenv import load_dotenv
from whoop import WhoopClient

# Initialize
load_dotenv("Credentials.env")
un = os.getenv("USERNAME_W")
pw = os.getenv("PASSWORD_W")
client = WhoopClient(un, pw)
profile = client.get_profile()

# Get sleep as pandas dataframe
sleep = client.get_sleep_collection(start_date="2024-01-01")
df_s = pd.json_normalize(sleep)

# Select for not naps
df_s = df_s[df_s['nap'] == False]

# Apply timezone offset
def apply_timezone_offset(row):
    start_time = pd.to_datetime(row['end'])
    hours, minutes = map(int, row['timezone_offset'].split(':'))
    timezone_offset = pd.Timedelta(hours=hours, minutes=minutes)
    return start_time + timezone_offset

df_s['end'] = df_s.apply(apply_timezone_offset, axis=1)

# Adjust datetime format
df_s['end'] = pd.to_datetime(df_s['end'])

# Separate date and time
df_s['day'], df_s['time'] = df_s['end'].dt.date, df_s['end'].dt.time
df_s = df_s[['day', 'time'] + [col for col in df_s.columns if col not in ['day', 'time']]]

# Keep only date and time, rename time to wakeuptime, and drop miliseconds from it
df_s = df_s[['day', 'time']]
df_s = df_s.rename(columns={'time': 'wakeuptime'})
df_s['wakeuptime'] = df_s['wakeuptime'].astype(str).str[:-7]

# If wakeuptime is 0, set 7am
df_s['wakeuptime'] = df_s['wakeuptime'].replace('0', '07:00:00')

# Ensure both dataframes have the date on the same format
df['date'] = pd.to_datetime(df['date'])
df_s['day'] = pd.to_datetime(df_s['day'])

# merge df and df_s dataframes by date
df = pd.merge(df, df_s, left_on='date', right_on='day', how='left')

# Create a new dataframe where we only keep the glucose data from the time right after wakeuptime
df['wakeuptime'] = pd.to_datetime(df['wakeuptime']).dt.time
df = df[df['time'] >= df['wakeuptime']]

df = df.dropna(subset=['glucose'])
df = df.sort_values('datetime')

# Keep only the latest reading for each day
df_w = df.groupby('date').first().reset_index()
df_w = df_w[['date', 'glucose']]
df_w = df_w.rename(columns={'date': 'day', 'glucose': 'wake_up_glucose'})

# Make sure both dataframes have the same format for date
df_d['date'] = pd.to_datetime(df_d['date'])
df_w['day'] = pd.to_datetime(df_w['day'])

# Merge dt_w back to df_d merging by day/date
df_d = pd.merge(df_d, df_w, left_on='date', right_on='day', how='left')
df_d = df_d.drop(columns=['day'])

# Save the data to a csv file
df_d.to_csv('Data/Cleaned/Glucose_daily.csv', index=False)
print('Glucose data aggregated and saved to Data/Cleaned/Glucose_daily.csv')