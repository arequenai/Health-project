import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load workout data from CSV
df = pd.read_csv('Data/TrainingPeaks/workouts.csv', parse_dates=['WorkoutDay'])
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

# Sort the DataFrame by 'Date' to ensure proper sequence
df.sort_values(by='Date', inplace=True)

# Pre-initialize with 42 zeros in 'TSS' for dates previous to the beginning
start_date = df['Date'].min()
end_date = start_date - pd.Timedelta(days=42)
while end_date < start_date:
    df.loc[len(df)] = [end_date, 0]
    end_date += pd.Timedelta(days=1)

# Sort DataFrame again after pre-initialization
df.sort_values(by='Date', inplace=True)

# Calculate Time Constants
time_constant_ctl = 42
time_constant_atl = 7  # Assuming ATL time constant as 7 days

# Initialize CTL and ATL with 0 for the first 42 days
df['CTL'] = 0
df['ATL'] = 0

# Ensure 'CTL' and 'ATL' columns are of appropriate data type
df['CTL'] = df['CTL'].astype(float)
df['ATL'] = df['ATL'].astype(float)

# Iterate over the DataFrame and calculate CTL and ATL iteratively
for i in range(43, len(df)):
    df.at[i, 'CTL'] = df.at[i-1, 'CTL'] + (df.at[i, 'TSS'] - df.at[i-1, 'CTL']) / time_constant_ctl
    df.at[i, 'ATL'] = df.at[i-1, 'ATL'] + (df.at[i, 'TSS'] - df.at[i-1, 'ATL']) / time_constant_atl

# Drop the 42 additional days
df = df.iloc[42:]

# Calculate TSB as the difference between CTL and ATL of the previous day
df['TSB'] = df['CTL'].shift(1) - df['ATL'].shift(1)

# Rename the Date column to date
df.rename(columns={'Date': 'date'}, inplace=True)

# Save to CSV
df.to_csv('Data/Cleaned/TSS metrics.csv', index=False)
print("TrainingPeaks data saved to 'Data/Cleaned/TSS metrics.csv'")