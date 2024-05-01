import os
from dotenv import load_dotenv
import pandas as pd
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

recovery = client.get_recovery_collection(start_date="2024-01-01")
df_r = pd.json_normalize(recovery)

### Data manipulation Sleep ###

# Apply timezone offset
def apply_timezone_offset(row):
    start_time = pd.to_datetime(row['start'])
    hours, minutes = map(int, row['timezone_offset'].split(':'))
    timezone_offset = pd.Timedelta(hours=hours, minutes=minutes)
    return start_time + timezone_offset

df_s['start'] = df_s.apply(apply_timezone_offset, axis=1)

# Convert milliseconds to hours
for col in df_s.columns:
    if col.endswith('_milli'):
        df_s[col[:-6]] = df_s[col] / 1000 / 60 / 60
        df_s.drop(columns=[col], inplace=True)

# Adjust datetime format
df_s['start'] = pd.to_datetime(df_s['start'])
df_s['start'] = df_s['start'].dt.floor('s')

# Separate date and time
df_s['day'], df_s['time'] = df_s['start'].dt.date, df_s['start'].dt.time
df_s = df_s[['day', 'time'] + [col for col in df_s.columns if col not in ['day', 'time']]]

#### Considers that sleep happens first thing in the day ####

# Set as next day if time > 20:00
mask = (df_s['time'] > pd.to_datetime('20:00').time()).astype(int)
df_s['day'] = pd.to_datetime(df_s['day']) + pd.to_timedelta(mask, unit='D')

# Remove days where score_state is not 'SCORED'
df_s = df_s[df_s['score_state'] == 'SCORED'].drop(columns=['score_state'])

# Simplify column names
df_s.columns = df_s.columns.str.replace('score.', '')
df_s.columns = df_s.columns.str.replace('stage_summary.total_', '')

# Rename and reorder columns
columns_map = {'day': 'date', 'time': 'sleep_time', 'id': 'sleep_id', 'nap': 'nap', 'score': 'sleep_score',
               'sleep_performance_percentage': 'sleep_score_performance',
               'sleep_consistency_percentage': 'sleep_score_consistency',
               'sleep_efficiency_percentage': 'sleep_score_efficiency',
               'no_data_time': 'sleep_unspecified', 'awake_time': 'sleep_awake',
               'light_sleep_time': 'sleep_light', 'slow_wave_sleep_time': 'sleep_deep',
               'rem_sleep_time': 'sleep_rem', 'in_bed_time': 'sleep_duration'}
df_s.rename(columns=columns_map, inplace=True)

# Reorder columns
df_s = df_s[['date', 'sleep_time', 'sleep_id', 'nap', 'sleep_score_performance',
             'sleep_score_consistency', 'sleep_score_efficiency', 'sleep_duration',
             'sleep_rem', 'sleep_deep', 'sleep_light', 'sleep_awake', 'sleep_unspecified']]

# Eliminate naps
df_s = df_s[df_s['nap'] == False]

# Drop 'nap' and 'sleep_score' columns
df_s.drop(columns=['nap'], inplace=True)

### Data manipulation Recovery ###
# Simplify column names
df_r.columns = df_r.columns.str.replace('score.', '')

# Remove unnecessary columns
df_r.drop(columns=['cycle_id', 'user_id', 'created_at', 'updated_at', 'score_state', 'user_calibrating'], inplace=True)

# Rename columns
columns_map = {'resting_heart_rate': 'resting_hr', 'hrv_rmssd_milli':'hrv', 'spo2_percentage': 'spo2','skin_temp_celsius': 'skin_temp'}
df_r.rename(columns=columns_map, inplace=True)

# Merge sleep and recovery dataframes
df = pd.merge(df_s, df_r, on='sleep_id', how='left')

# Write to csv
df.to_csv('Data/Cleaned/Sleep_and_recovery.csv', index=False)