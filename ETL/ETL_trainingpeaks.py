import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def get_tp_data(file_path, start_date):
    # Load workout data from CSV
    df = pd.read_csv(file_path, parse_dates=['WorkoutDay'])
    
    # Rename WorkoutDay to Date
    df.rename(columns={'WorkoutDay': 'Date'}, inplace=True)
    df.sort_values('Date', inplace=True)
    df.set_index('Date', inplace=True)

    # Keep only date and TSS columns
    df = df[['TSS']]

    # Aggregate TSS per day
    df = df.resample('D').sum()

    # Ensure TSS is a float
    df['TSS'] = df['TSS'].astype(float)

    # Sort the DataFrame by Date to ensure proper sequence
    df.sort_values(by='Date', inplace=True)

    # Reset index to make 'Date' a regular column
    df.reset_index(inplace=True)

    # Filter data from the specified start date
    df = df[df['Date'] >= pd.to_datetime(start_date)]

    # Initialize CTL and ATL with 0 for the first 42 days
    df['CTL'] = 0
    df['ATL'] = 0
    df['CTL'] = df['CTL'].astype(float)
    df['ATL'] = df['ATL'].astype(float)

    # Iterate over the DataFrame and calculate CTL and ATL iteratively
    for i in range(42, len(df)):
        df.at[i, 'CTL'] = df.at[i - 1, 'CTL'] + (df.at[i, 'TSS'] - df.at[i - 1, 'CTL']) / 42
        df.at[i, 'ATL'] = df.at[i - 1, 'ATL'] + (df.at[i, 'TSS'] - df.at[i - 1, 'ATL']) / 7

    # Calculate TSB as the difference between CTL and ATL of the previous day
    df['TSB'] = df['CTL'].shift(1) - df['ATL'].shift(1)

    # Rename the Date column to date
    df.rename(columns={'Date': 'date'}, inplace=True)

    return df

def main():
    file_path = 'Data/TrainingPeaks/workouts.csv'
    start_date = '2022-01-01'  # Example start date, adjust as needed

    # Get the processed TrainingPeaks data
    tp_data = get_tp_data(file_path, start_date)

    # Save the data to a CSV file
    tp_data.to_csv('Data/Cleaned/TSS metrics.csv', index=False)
    print("TrainingPeaks data saved to 'Data/Cleaned/TSS metrics.csv'")

if __name__ == "__main__":
    main()
