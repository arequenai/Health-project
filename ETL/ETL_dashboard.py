#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import logging
import sys
from datetime import datetime
from . import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def calculate_derived_metrics(df):
    """Calculate BMI and fat weight from existing metrics."""
    # Constants
    HEIGHT_M = 1.73  # User's height in meters
    
    # Calculate BMI = weight / height^2
    if 'weight' in df.columns:
        df['bmi'] = df['weight'] / (HEIGHT_M ** 2)
    
    # Calculate fat weight = weight * (body_fat_percentage / 100)
    if 'weight' in df.columns and 'body_fat' in df.columns:
        df['fat_weight'] = df['weight'] * (df['body_fat'] / 100)
    
    return df

def create_dashboard_data():
    """Create daily dashboard data with all required metrics."""
    logger.info("Starting dashboard data creation...")
    
    # Load integrated data
    try:
        df = pd.read_csv(config.INTEGRATED_DATA_PATH)
        df['date'] = pd.to_datetime(df['date'])
        logger.info(f"Loaded data from {df['date'].min()} to {df['date'].max()}")
    except Exception as e:
        logger.error(f"Error loading integrated data: {str(e)}")
        return None
    
    # Calculate derived metrics
    df = calculate_derived_metrics(df)
    
    # Apply rounding to metrics
    rounding_rules = {
        # Sleep metrics (0 decimals for scores, 2 for durations)
        'sleep_score_performance': 0,
        'sleep_score_consistency': 0,
        'sleep_score_efficiency': 0,
        'sleep_duration': 2,
        'sleep_rem': 2,
        'sleep_deep': 2,
        'sleep_light': 2,
        'sleep_awake': 2,
        
        # Recovery metrics (0 decimals for scores and HR, 1 for TSB)
        'recovery_score': 0,
        'resting_hr': 0,
        'hrv': 0,
        'TSB': 1,
        'averageStressLevel': 0,
        'bodyBatteryHighestValue': 0,
        'bodyBatteryLowestValue': 0,
        
        # Glucose metrics (0 decimals)
        'wake_up_glucose': 0,
        'mean_glucose': 0,
        'max_glucose': 0,
        'std_glucose': 0,
        'time_in_range': 0,
        
        # Body composition (1 decimal)
        'weight': 1,
        'body_fat': 1,
        'bmi': 1,
        'fat_weight': 1,
        
        # Training metrics (1 decimal for load metrics, 0 for others)
        'CTL': 1,
        'ATL': 1,
        'TSS': 1,
        'training_load': 0,
        'distance': 0,
        'elevationGain': 0,
        'strength_minutes': 0,
        
        # Nutrition metrics (0 decimals)
        'calories_net': 0,
        'calories_consumed': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0,
        'sugar': 0,
        
        # New Garmin metrics
        'vo2max': 1,              # 1 decimal for VO2max
        'predicted_5k': 0,        # 0 decimals for race times (in minutes)
        'predicted_10k': 0,
        'predicted_half': 0,
        'predicted_marathon': 0
    }
    
    # Define all required columns in order
    required_columns = [
        # Date
        'date',
        
        # Sleep metrics
        'sleep_score_performance',  # key
        'sleep_duration', 'sleep_score_efficiency', 'bodyBatteryHighestValue',
        'bed_full', 'read_bed', 'sleep_start_time',
        
        # Recovery metrics
        'recovery_score',  # key
        'resting_hr', 'hrv', 'TSB',
        'alcohol', 'stretch', 'averageStressLevel',
        
        # Glucose metrics
        'wake_up_glucose',  # key
        'mean_glucose', 'max_glucose', 'std_glucose',
        'sugar', 'carbs', 'snacks',
        
        # Strength metrics
        'muscle_mass',  # key
        'bench_1rm', 'pullups_num', 'squat_1rm',
        'jefit_entries', 'strength_minutes', 'protein',
        
        # Body composition metrics
        'body_fat',  # key
        'weight', 'fat_weight', 'bmi',
        'calories_net', 'avoid_processed_foods', 'fat',
        
        # Running metrics
        'predicted_marathon',  # key
        'vo2max', 'predicted_5k', 'predicted_10k',
        'predicted_half', 'distance', 'elevationGain',
        'CTL'
    ]
    
    # Create DataFrame with required columns
    dashboard_df = pd.DataFrame(columns=required_columns)
    
    # Copy existing columns from integrated data
    for col in required_columns:
        if col in df.columns:
            dashboard_df[col] = df[col]
    
    # Apply rounding rules
    for col, decimals in rounding_rules.items():
        if col in dashboard_df.columns:
            dashboard_df[col] = dashboard_df[col].round(decimals)
    
    # Ensure date is in correct format
    dashboard_df['date'] = pd.to_datetime(dashboard_df['date']).dt.strftime('%Y-%m-%d')
    
    # Sort by date
    dashboard_df = dashboard_df.sort_values('date')
    
    return dashboard_df

def main():
    """Main function to create dashboard data."""
    logger.info("Starting dashboard ETL process...")
    
    # Create dashboard data
    df = create_dashboard_data()
    
    if df is not None:
        # Save to CSV
        output_file = config.DASHBOARD_DATA_PATH
        df.to_csv(output_file, index=False)
        logger.info(f"Dashboard data saved to {output_file}")
        
        # Print summary
        logger.info("\nDashboard data summary:")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"Number of rows: {len(df)}")
        
        # Print columns with non-null values
        non_null_cols = df.columns[df.notna().any()].tolist()
        logger.info("\nColumns with data:")
        for col in non_null_cols:
            if col != 'date':
                non_null_count = df[col].notna().sum()
                logger.info(f"- {col}: {non_null_count} entries")
        
        logger.info("\nDashboard ETL process completed successfully!")
    else:
        logger.error("Failed to create dashboard data")

if __name__ == "__main__":
    main() 