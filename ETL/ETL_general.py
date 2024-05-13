# Function to obtain incremental data since the timestamps
import pandas as pd
import os
import datetime

# Function to obtain incremental data since the timestamps
def get_incremental_data(input_file, output_file, get_data_function):
    
    input_date = datetime.datetime.fromtimestamp(os.path.getmtime(input_file)).date()
    output_date = datetime.datetime.fromtimestamp(os.path.getmtime(output_file)).date()
    today = datetime.datetime.today().date()

    # Check if the output file's data is older than the input file's data
    if output_date != today:
        if input_date != today:
            print(f"Wanted to update data from '{input_file}', but input data is not up to date")
            return None
        else:
            df = get_data_function(input_file, output_date)
            if df is not None: print(f"Data from '{input_file}' to update '{output_file}' obtained")
            else: print(f"No data was found on '{input_file}' to update '{output_file}'")
            return df
    else:
        print(f"Data from '{input_file}' is already up to date")
        return None
    
# Function to obtain incremental data since the timestamps, from API
def get_incremental_data_api(client, output_file, get_data_function):
    
    output_date = datetime.datetime.fromtimestamp(os.path.getmtime(output_file)).date()
    today = datetime.datetime.today().date()

    # Check if the output file's data is older than the input file's data
    if output_date != today:
        df = get_data_function(client, output_date)
        if df is not None: print(f"Data from API to update '{output_file}' obtained")
        else: print(f"No data was found on API to update '{output_file}'")
        return df
    else:
        print(f"Data for '{output_file}' is already up to date")
        return None

# Updates file with new data, substituting the days found in df_incremental and adding new days
def write_incremental_data(df_incremental, file_path):
    
    import os, datetime
    import pandas as pd

    df_existing = pd.read_csv(file_path)

    # If df_existing is not empty and has date column, proceed to remove overlapping dates
    if not df_existing.empty and 'date' in df_existing.columns and 'date' in df_incremental.columns:
        # Convert date columns to datetime to ensure matching formats
        df_existing['date'] = pd.to_datetime(df_existing['date'])
        df_incremental['date'] = pd.to_datetime(df_incremental['date'])
        
        # Find dates to remove from the existing DataFrame
        dates_to_remove = df_incremental['date'].unique()
        
        # Filter out the rows with these dates
        df_existing = df_existing[~df_existing['date'].isin(dates_to_remove)]

    # Append new data
    updated_df = pd.concat([df_existing, df_incremental], ignore_index=True)
    
    # Save the updated DataFrame back to the CSV
    updated_df.to_csv(file_path, index=False)
    
    # Print the file path and the dates added
    print(f"Updated to '{file_path}' from: {df_incremental['date'].min().strftime('%Y-%m-%d')} to {df_incremental['date'].max().strftime('%Y-%m-%d')}")

# Function to get and write the incremental data
def update_incremental(input_file, output_file, get_data_function):
    
    df_incremental = get_incremental_data(input_file, output_file, get_data_function)

    if df_incremental is not None and not df_incremental.empty:
        write_incremental_data(df_incremental, output_file)


# Function to get and write the incremental data
def update_incremental_api(client, output_file, get_data_function):
    
    df_incremental = get_incremental_data_api(client, output_file, get_data_function)
    if df_incremental is not None and not df_incremental.empty:
        write_incremental_data(df_incremental, output_file)
