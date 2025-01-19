import pandas as pd
import datetime
import logging
import os
from .ETL_general import export_to_gsheets

logger = logging.getLogger(__name__)

def get_form_data(spreadsheet_id):
    """Get journal data from Google Form responses."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        
        logger.info("Loading credentials...")
        try:
            creds = service_account.Credentials.from_service_account_file(
                'gsheets key.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return None
        
        logger.info("Building service...")
        try:
            service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"Error building service: {str(e)}")
            return None
        
        logger.info("Getting form responses...")
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Form Responses 1'
            ).execute()
        except Exception as e:
            logger.error(f"Error getting form responses: {str(e)}")
            return None
        
        values = result.get('values', [])
        if not values:
            logger.warning('No journal data found')
            return None
            
        logger.info(f"Processing {len(values)-1} form responses...")
        headers = values[0]
        data = values[1:]
        
        # Ensure all data rows have the same number of columns as headers
        max_cols = len(headers)
        padded_data = [row + [''] * (max_cols - len(row)) for row in data]
        
        # Convert to DataFrame
        df = pd.DataFrame(padded_data, columns=headers)
        
        # Process timestamp and date
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Handle empty dates - use day before timestamp
        date_col = 'Day logging (if empty, yesterday)'
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df.loc[df[date_col].isna(), date_col] = df.loc[df[date_col].isna(), 'Timestamp'] - pd.Timedelta(days=1)
        
        # Create column map based on actual form columns
        column_map = {
            'Timestamp': 'Timestamp',
            'Day logging (if empty, yesterday)': 'date',
            'Avoid processed foods?': 'avoid_processed_foods',
            'Eat close to bedtime?': 'bed_full',
            'Feeling sick or ill?': 'sick_or_ill',
            'Consume alcohol?': 'alcohol',
            'How many drinks': 'drinks',
            'Read non-screen in bed?': 'read_bed',
            'Stretch?': 'stretch',
            'Screen in bed?': 'screen_bed'
        }
        
        # Remove any columns that don't exist in the form
        column_map = {k: v for k, v in column_map.items() if k in df.columns}
        logger.info(f"Using column map: {column_map}")
        
        # Rename columns
        df = df.rename(columns=column_map)
        
        # Drop unnecessary columns
        keep_cols = list(column_map.values())
        df = df[keep_cols]
        
        # Convert date to date format
        df['date'] = df['date'].dt.date
        
        # Handle drinks column if it exists
        if 'drinks' in df.columns:
            df['drinks'] = pd.to_numeric(df['drinks'], errors='coerce').fillna(0)
            df.loc[df['alcohol'] == 'No', 'drinks'] = 0
            
        # Sort by date
        df = df.sort_values('date')
        
        logger.info("Form data processed successfully")
        return df
        
    except Exception as e:
        logger.error(f"Error getting form data: {str(e)}")
        return None

def get_whoop_journal_data():
    """Get historical journal data from Whoop CSV."""
    try:
        whoop_file = 'Data/Whoop/journal_entries.csv'
        if not os.path.exists(whoop_file):
            logger.warning(f"Whoop journal file not found: {whoop_file}")
            return None
            
        logger.info("Processing Whoop journal data...")
        df = pd.read_csv(whoop_file)
        
        def set_date(row):
            date = datetime.datetime.strptime(row['Cycle start time'], '%Y-%m-%d %H:%M:%S')
            if date.hour < 12:
                date -= datetime.timedelta(days=1)
            return date.date()
        
        df['date'] = df.apply(set_date, axis=1)
        df = df[['date', 'Question text', 'Answered yes']]
        pd.set_option('future.no_silent_downcasting', True)
        df['Answered yes'] = df['Answered yes'].replace({True: "Yes", False: "No"}).infer_objects(copy=False)
        df_u = df.pivot_table(index='date', columns='Question text', values='Answered yes', aggfunc='sum')
        df_u.reset_index(inplace=True)
        
        # Map Whoop questions to our standard format
        whoop_map = {
            'Avoid consuming processed foods?': 'avoid_processed_foods',
            'Eat any food close to bedtime?': 'bed_full',
            'Feeling sick or ill?': 'sick_or_ill',
            'Have an injury or wound': 'injury',
            'Have any alcoholic drinks?': 'alcohol',
            'Read (non-screened device) while in bed?': 'read_bed',
            'Spend time stretching?': 'stretch',
            'Viewed a screen device in bed?': 'screen_bed'
        }
        
        # Keep only the columns we need and rename them
        columns_to_keep = ['date'] + list(whoop_map.keys())
        df_u = df_u[columns_to_keep]
        df_u = df_u.rename(columns=whoop_map)
        
        logger.info("Whoop journal data processed successfully")
        return df_u
        
    except Exception as e:
        logger.error(f"Error getting Whoop journal data: {str(e)}")
        return None

def get_journal_data(spreadsheet_id):
    """Get combined journal data, prioritizing Whoop data when available."""
    
    # Get both data sources
    whoop_data = get_whoop_journal_data()
    form_data = get_form_data(spreadsheet_id)
    
    if whoop_data is None and form_data is None:
        logger.error("No journal data available from either source")
        return None
    
    if whoop_data is None:
        logger.info("Using only form data")
        return form_data
        
    if form_data is None:
        logger.info("Using only Whoop data")
        return whoop_data
    
    # Convert dates to datetime for proper comparison
    whoop_data['date'] = pd.to_datetime(whoop_data['date'])
    form_data['date'] = pd.to_datetime(form_data['date'])
    
    # Get the latest date in Whoop data
    last_whoop_date = whoop_data['date'].max()
    
    # Use Whoop data up to last_whoop_date, then form data after that
    combined_data = pd.concat([
        whoop_data[whoop_data['date'] <= last_whoop_date],
        form_data[form_data['date'] > last_whoop_date]
    ])
    
    # Convert date back to date format
    combined_data['date'] = combined_data['date'].dt.date
    
    # Sort by date
    combined_data = combined_data.sort_values('date')
    
    logger.info(f"Combined data from {combined_data['date'].min()} to {combined_data['date'].max()}")
    return combined_data

def main():
    """Main function to test the journal data retrieval."""
    # Your form's spreadsheet ID
    SPREADSHEET_ID = '1E0pWgt9Zifdx3S3iqpyAjTHijn-xZcXYLRXvqwgo-tg'  # Form responses spreadsheet
    
    df = get_journal_data(SPREADSHEET_ID)
    if df is not None:
        print("\nFirst few entries:")
        print(df.head())
        
        # Save to CSV
        output_file = 'Data/Cleaned/Journal.csv'
        df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

if __name__ == "__main__":
    main() 