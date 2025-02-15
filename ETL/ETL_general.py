# Function to obtain incremental data since the timestamps
import pandas as pd
import os
import csv
import datetime
import logging

logger = logging.getLogger(__name__)

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
    """Delete all data from the given date onwards in a CSV file.
    
    Args:
        filename: Path to CSV file
        date: datetime.date object or string in YYYY-MM-DD format
    """
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    
    date_str = date.strftime('%Y-%m-%d')
    logger.info(f"Deleting data from {date_str} onwards in {filename}")
    
    temp_filename = filename + '.tmp'
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile, \
             open(temp_filename, 'w', newline='', encoding='utf-8') as tmpfile:
            reader = csv.reader(csvfile)
            writer = csv.writer(tmpfile)
            
            # Write header
            headers = next(reader)
            writer.writerow(headers)
            
            # Write rows before the date
            for row in reader:
                if row[0] < date_str:
                    writer.writerow(row)
        
        os.replace(temp_filename, filename)
        logger.info(f"Successfully deleted data from {date_str} onwards")
        
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

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
    """Get incremental data from API since last update.
    
    Args:
        client: API client
        output_file: Path to output file
        get_data_function: Function to get data from API
        
    Returns:
        DataFrame with new data, or None if no new data
    """
    try:
        # Let the data function handle the start date logic
        df = get_data_function(client)
        if df is not None and not df.empty:
            logger.info(f"Got new data from API")
            
            # If we have existing data, merge with it
            if os.path.exists(output_file):
                df_existing = pd.read_csv(output_file)
                df_combined = pd.concat([df_existing, df], ignore_index=True)
                # Sort by date and remove duplicates, keeping latest version
                df_combined['date'] = pd.to_datetime(df_combined['date'])
                df_combined = df_combined.sort_values('date').drop_duplicates(subset=['date'], keep='last')
                df_combined['date'] = df_combined['date'].dt.strftime('%Y-%m-%d')
                df = df_combined
        else:
            logger.info("No new data found")
        return df
        
    except Exception as e:
        logger.error(f"Error getting incremental data: {str(e)}")
        return None

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

# Function to get and write the incremental data from API
def update_incremental_api(client, output_file, get_data_function):
    """Get and write incremental data from API, appending new data to existing file.
    
    Args:
        client: API client
        output_file: Path to output file
        get_data_function: Function to get data from API
    """
    # Get the incremental data
    df_incremental = get_incremental_data_api(client, output_file, get_data_function)
    
    # If we have new data, append it to the file
    if df_incremental is not None and not df_incremental.empty:
        if os.path.exists(output_file):
            # Read existing data
            df_existing = pd.read_csv(output_file)
            # Combine with new data
            df_combined = pd.concat([df_existing, df_incremental], ignore_index=True)
            # Sort by date and remove duplicates, keeping latest version
            df_combined['date'] = pd.to_datetime(df_combined['date'])
            df_combined = df_combined.sort_values('date').drop_duplicates(subset=['date'], keep='last')
            df_combined['date'] = df_combined['date'].dt.strftime('%Y-%m-%d')
            # Save combined data
            df_combined.to_csv(output_file, index=False)
            logger.info(f"Appended new data to {output_file}")
        else:
            # If file doesn't exist, just save the new data
            df_incremental.to_csv(output_file, index=False)
            logger.info(f"Created new file {output_file} with data")


def export_to_gsheets(df, sheet_name):
    """Export DataFrame to Google Sheets.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        sheet_name (str): Name of the sheet to export to
        
    Returns:
        bool: True if successful, False otherwise
    """
    import pandas as pd
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    from google.oauth2.service_account import Credentials
    import logging
    import json
    import os

    logger = logging.getLogger(__name__)
    
    try:
        # Check if credentials file exists
        creds_file = 'gsheets key.json'
        if not os.path.exists(creds_file):
            logger.error(f"Credentials file '{creds_file}' not found")
            return False
            
        # Load and validate service account credentials
        try:
            creds = service_account.Credentials.from_service_account_file(creds_file)
            scoped_credentials = creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets'])
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in credentials file '{creds_file}'")
            return False
        except ValueError as e:
            logger.error(f"Invalid credentials in '{creds_file}': {str(e)}")
            return False
            
        # Build service with retry
        try:
            service = build('sheets', 'v4', credentials=scoped_credentials, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to build Google Sheets service: {str(e)}")
            return False

        # Spreadsheet ID and range
        SPREADSHEET_ID = '197VfZCekvBev0m1vsi8kUHpuO0IoTRA90_bQRGBYYSM'
        range_name = f"{sheet_name}!A1:ZA{len(df) + 1}"  # Dynamic range based on DataFrame size
        
        # Prepare data
        df_filled = df.fillna('')
        headers = [df_filled.columns.tolist()]
        values = df_filled.values.tolist()
        data = headers + values
        
        # Clear existing content first
        try:
            service.spreadsheets().values().clear(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name
            ).execute()
            logger.info(f"Cleared existing content in sheet '{sheet_name}'")
        except Exception as e:
            logger.error(f"Failed to clear sheet '{sheet_name}': {str(e)}")
            return False
        
        # Update with new data
        try:
            response = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                valueInputOption='RAW',
                range=range_name,
                body={'majorDimension': 'ROWS', 'values': data}
            ).execute()
            
            updated_cells = response.get('updatedCells', 0)
            logger.info(f"Successfully updated {updated_cells} cells in sheet '{sheet_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update sheet '{sheet_name}': {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in export_to_gsheets: {str(e)}")
        return False