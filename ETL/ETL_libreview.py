import pandas as pd
import os
from dotenv import load_dotenv
from whoop import WhoopClient

# Apply timezone offset
def apply_timezone_offset(row):
    start_time = pd.to_datetime(row['end'])
    hours, minutes = map(int, row['timezone_offset'].split(':'))
    timezone_offset = pd.Timedelta(hours=hours, minutes=minutes)
    return start_time + timezone_offset

# Function to extract and clean glucose data from a CSV file
def get_glucose_time(file_path, start_date):
    # Read the glucose data file
    df = pd.read_csv(file_path, skiprows=1)
    
    # Select necessary columns and rename them
    df = df[['Sello de tiempo del dispositivo', 'Historial de glucosa mg/dL', 'Escaneo de glucosa mg/dL']]
    df.columns = ['timestamp', 'glucose', 'scan_glucose']
    
    # Combine glucose readings from two columns into one, prioritizing non-NaN values
    df['glucose'] = df['glucose'].combine_first(df['scan_glucose'])
    df = df.drop(columns=['scan_glucose'])
    
    # Convert timestamps into Python datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True)
    
    # Extract date and time from the timestamp
    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.time
    df = df.drop(columns=['timestamp'])
    
    # Reorder columns for clarity
    df = df[['date', 'time', 'glucose']]
    
    # Remove rows where glucose data is missing
    df = df[df['glucose'].notna()]
    
    # Create a full datetime column to enable filtering
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
    
    # Filter the dataframe for entries on or after the start date
    df = df[df['datetime'] >= pd.to_datetime(start_date)]
    df = df.sort_values('datetime')
    
    # Ensure 'date' is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    
    return df

# Function to aggregate daily glucose data and fetch wake-up times
def get_glucose_daily(file_path, start_date):
    df = get_glucose_time(file_path, start_date)

    # Load environment variables for API credentials
    load_dotenv("Credentials.env")
    un = os.getenv("USERNAME_W")
    pw = os.getenv("PASSWORD_W")
    
    # Authenticate with Whoop API
    client = WhoopClient(un, pw)
    
    # Fetch sleep data from Whoop
    sleep = client.get_sleep_collection(start_date="2024-01-01")
    df_s = pd.json_normalize(sleep)
    
    # Filter out nap entries
    df_s = df_s[df_s['nap'] == False]
    
    # Adjust for timezone differences in the data
    df_s['end'] = df_s.apply(apply_timezone_offset, axis=1)
    df_s['end'] = pd.to_datetime(df_s['end'])
    
    # Extract date and wake-up time from the adjusted end time
    df_s['day'], df_s['time'] = df_s['end'].dt.date, df_s['end'].dt.time
    df_s = df_s[['day', 'time']]
    df_s = df_s.rename(columns={'time': 'wakeuptime'})
    df_s['wakeuptime'] = df_s['wakeuptime'].astype(str).str[:-7]
    df_s['wakeuptime'] = df_s['wakeuptime'].replace('0', '07:00:00')
    
    # Ensure 'day' is in datetime format before merging
    df_s['day'] = pd.to_datetime(df_s['day'])
    
    # Merge the glucose data with the wake-up times
    df = pd.merge(df, df_s, left_on='date', right_on='day', how='left')
    
    # Specify the time format to avoid the warning
    df['wakeuptime'] = pd.to_datetime(df['wakeuptime'], format='%H:%M:%S').dt.time
    
    # Filter glucose readings to only include those after the wake-up time
    df = df[df['time'] >= df['wakeuptime']]
    df = df.dropna(subset=['glucose'])
    df = df.sort_values('datetime')
    
    # Group by date and calculate wake-up glucose and daily statistics
    # Get the first reading for each day as the wake-up glucose
    wake_up_glucose = df.groupby('date').first().reset_index()[['date', 'glucose']]
    wake_up_glucose = wake_up_glucose.rename(columns={'glucose': 'wake_up_glucose'})

    # Calculate max, mean, and std of glucose for each day
    daily_stats = df.groupby('date')['glucose'].agg(['mean', 'std', 'max']).reset_index()
    daily_stats = daily_stats.rename(columns={'mean': 'mean_glucose', 'std': 'std_glucose', 'max': 'max_glucose'})

    # Merge wake-up glucose with daily stats
    daily_glucose_data = pd.merge(daily_stats, wake_up_glucose, on='date', how='left')

    # Change date from datetime to date
    daily_glucose_data['date'] = daily_glucose_data['date'].dt.date

    return daily_glucose_data

def main():
    
    file_path = 'Data/LibreLink/AlbertoRequena Izard_glucose.csv'
    start_date = '2024-03-23'

    # Process time-specific glucose data
    df_time = get_glucose_time(file_path, start_date)
    # Aggregate daily data and integrate wake-up times
    df_daily = get_glucose_daily(file_path, start_date)

    # Save the cleaned and processed data to CSV files
    df_time.to_csv('Data/Cleaned/Glucose.csv', index=False)
    print('Glucose data extracted and saved to Data/Cleaned/Glucose.csv')

    df_daily.to_csv('Data/Cleaned/Glucose_daily.csv', index=False)
    print('Glucose data aggregated and saved to Data/Cleaned/Glucose_daily.csv')

if __name__ == "__main__":
    main()
