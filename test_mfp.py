#!/usr/bin/env python3

import logging
from ETL.ETL_mfp_api import init_mfp
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test MyFitnessPal API integration."""
    logger.info("Starting MyFitnessPal API test...")
    
    try:
        # Initialize MFP client
        logger.info("Initializing MyFitnessPal client...")
        client = init_mfp()
        
        # Try to get today's and yesterday's data
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        logger.info(f"Attempting to get data for {yesterday}...")
        diary = client.get_date(yesterday.year, yesterday.month, yesterday.day)
        
        # Print summary of yesterday's data
        logger.info("\nYesterday's nutrition summary:")
        logger.info(f"Calories: {diary.totals['calories']}")
        logger.info(f"Carbs: {diary.totals['carbohydrates']}g")
        logger.info(f"Fat: {diary.totals['fat']}g")
        logger.info(f"Protein: {diary.totals['protein']}g")
        
        # Print meals
        logger.info("\nMeals logged yesterday:")
        for meal in diary.meals:
            if len(meal.entries) > 0:
                logger.info(f"\n{meal.name}:")
                for entry in meal.entries:
                    logger.info(f"- {entry.name}: {entry.nutrition_information['calories']} calories")
        
        logger.info("\nMyFitnessPal authentication and data retrieval successful!")
            
    except Exception as e:
        logger.error(f"Error in MyFitnessPal test: {str(e)}")

if __name__ == "__main__":
    main() 