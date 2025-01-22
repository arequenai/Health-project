#!/usr/bin/env python3

import logging
from ETL.ETL_fitbit import init_fitbit, get_body_measurements
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test Fitbit API integration."""
    logger.info("Starting Fitbit API test...")
    
    # Load environment variables
    load_dotenv('Credentials.env')
    
    try:
        # Initialize Fitbit client
        logger.info("Initializing Fitbit client...")
        tokens = init_fitbit()
        
        # Get weight data
        logger.info("Getting weight data...")
        df = get_body_measurements(tokens)
        
        if not df.empty:
            logger.info("\nWeight data summary:")
            logger.info(f"Number of entries: {len(df)}")
            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            logger.info("\nFirst few entries:")
            print(df.head())
            logger.info("\nLast few entries:")
            print(df.tail())
        else:
            logger.warning("No weight data found")
            
    except Exception as e:
        logger.error(f"Error in Fitbit test: {str(e)}")

if __name__ == "__main__":
    main() 