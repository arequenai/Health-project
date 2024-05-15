# Function to obtain incremental data since the timestamps
import pandas as pd
import os
import csv
import datetime

# Function to get the most recent date from a CSV file
def get_most_recent_date(filename):
    if filename.endswith('.csv'):
        try:
            # Using pandas to handle headers and date parsing more robustly
            df = pd.read_csv(filename, nrows=0)  # Read only headers
            first_column_name = df.columns[0]
            if first_column_name.lower() == 'date':
                # If first column is indeed called 'date', read dates from this column
                df = pd.read_csv(filename, usecols=[first_column_name])
                df[first_column_name] = pd.to_datetime(df[first_column_name], errors='coerce')
                most_recent_date = df[first_column_name].dropna().max()
                return most_recent_date.date() if most_recent_date else None
            else:
                # If not, use the file's last modification time
                return datetime.datetime.fromtimestamp(os.path.getmtime(filename)).date()
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return None
    else:
        # For non-csv files or if any other error occurred
        try:
            return datetime.datetime.fromtimestamp(os.path.getmtime(filename)).date()
        except OSError:
            return None

# Function to delete all data from that date onwards
def delete_data_from_date(filename, date):
    temp_filename = filename + '.tmp'
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile, open(temp_filename, 'w', newline='', encoding='utf-8') as tmpfile:
        reader = csv.reader(csvfile)
        writer = csv.writer(tmpfile)
        headers = next(reader)
        writer.writerow(headers)
        for row in reader:
            if row[0] < date.strftime('%Y-%m-%d'):
                writer.writerow(row)
    os.replace(temp_filename, filename)

# Function to obtain incremental data since the timestamps
def get_incremental_data(input_file, output_file, get_data_function):
    
    input_date = get_most_recent_date(input_file)
    start_date = get_most_recent_date(output_file) + datetime.timedelta(days=1) # Start from first new day
    today = datetime.datetime.today().date()

    # Always rewrite the last day
    if input_date != today:
        print(f"{output_file}: Tried to update, but input '{input_file}' is not up to date")
        return None
    else:
        df = get_data_function(input_file, start_date)
        if df is not None: print(f"{output_file}: Data from '{input_file}' from {start_date} obtained")
        else: print(f"{output_file}: No data was found on '{input_file}' to update")
        return df

    
# Function to obtain incremental data since the timestamps, from API
def get_incremental_data_api(client, output_file, get_data_function):
    
    start_date = get_most_recent_date(output_file) + datetime.timedelta(days=1) # Start from first new day

    df = get_data_function(client, start_date)
    if df is not None: print(f"{output_file}: Data from API from {start_date} obtained")
    else: print(f"{output_file}: No data was found on API to update")
    return df

# Function to get and write the incremental data
def update_incremental(input_file, output_file, get_data_function):
    
    # Delete the last date
    last_date = get_most_recent_date(output_file)
    delete_data_from_date(output_file, last_date)

    # Get the incremental data
    df_incremental = get_incremental_data(input_file, output_file, get_data_function)

    # Write the incremental data to the output file
    if df_incremental is not None and not df_incremental.empty:
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for _, row in df_incremental.iterrows():
                writer.writerow(row)
        print(f"{output_file}: Data from {last_date} (re-)written")

# Function to get and write the incremental data
def update_incremental_api(client, output_file, get_data_function):

    # Delete the last date
    last_date = get_most_recent_date(output_file)
    delete_data_from_date(output_file, last_date)

    # Get the incremental data
    df_incremental = get_incremental_data_api(client, output_file, get_data_function)
    
    # Write the incremental data to the output file
    if df_incremental is not None and not df_incremental.empty:
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for _, row in df_incremental.iterrows():
                writer.writerow(row)
        print(f"{output_file}: Data from {last_date} (re-)written")


def export_to_gsheets(df, sheet_name):

    import pandas as pd
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    # Load service account credentials
    creds = service_account.Credentials.from_service_account_file('gsheets key.json')
    scoped_credentials = creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets'])

    # Authenticate with Google Sheets API
    service = build('sheets', 'v4', credentials=scoped_credentials, cache_discovery=False)

    # Spreadsheet ID and range for Health Dashboards
    SPREADSHEET_ID_input = '197VfZCekvBev0m1vsi8kUHpuO0IoTRA90_bQRGBYYSM'

    # Specify the range including the sheet name
    range_name = f"{sheet_name}!A1:ZA1000"
    
    # Fill NaN values with empty strings
    df_filled = df.fillna('')
    
    # Get DataFrame headers and values
    headers = [df_filled.columns.tolist()]
    values = df_filled.values.tolist()
    
    # Concatenate headers with values
    data = headers + values
    
    # Update the spreadsheet with DataFrame values including headers
    response = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID_input,
        valueInputOption='RAW',
        range=range_name,
        body=dict(
            majorDimension='ROWS',
            values=data)
    ).execute()