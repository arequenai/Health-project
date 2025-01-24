"""Configuration settings for the visualization layer."""

import datetime

# Data paths
DATA_DIR = 'Data/Cleaned'
INTEGRATED_DATA_PATH = f'{DATA_DIR}/Integrated_data.csv'
DASHBOARD_DATA_PATH = f'{DATA_DIR}/daily_dashboard_data.csv'

# Time ranges for visualizations
DEFAULT_TIMERANGE = '1M'  # 1W, 1M, 3M, 6M, 1Y
TIME_RANGES = {
    '1W': datetime.timedelta(days=7),
    '1M': datetime.timedelta(days=30),
    '3M': datetime.timedelta(days=90),
    '6M': datetime.timedelta(days=180),
    '1Y': datetime.timedelta(days=365),
}

# Metrics configuration
METRICS = {
    'sleep': {
        'name': 'Sleep Score',
        'main_metric': 'sleep_score_performance',
        'sub_metrics': [
            {'name': 'Time in Bed', 'column': 'sleep_duration'},
            {'name': 'Efficiency', 'column': 'sleep_score_efficiency'},
            {'name': 'Body Battery High', 'column': 'bodyBatteryHighestValue'}
        ],
        'drivers': [
            {'name': 'Bed Full', 'column': 'bed_full'},
            {'name': 'Read in Bed', 'column': 'read_bed'},
            {'name': 'Screen in Bed', 'column': 'screen_bed'}
        ]
    },
    'recovery': {
        'name': 'Recovery Score',
        'main_metric': 'recovery_score',
        'sub_metrics': [
            {'name': 'Resting HR', 'column': 'resting_hr'},
            {'name': 'HRV', 'column': 'hrv'},
            {'name': 'Stress', 'column': 'averageStressLevel'}
        ],
        'drivers': [
            {'name': 'Alcohol', 'column': 'alcohol'},
            {'name': 'Stretch', 'column': 'stretch'}
        ]
    },
    'glucose': {
        'name': 'Fasting Glucose',
        'main_metric': 'wake_up_glucose',
        'sub_metrics': [
            {'name': 'Mean Glucose', 'column': 'mean_glucose'},
            {'name': 'Max Glucose', 'column': 'max_glucose'},
            {'name': 'Glucose Variability', 'column': 'std_glucose'}
        ],
        'drivers': [
            {'name': 'Sugar', 'column': 'sugar'},
            {'name': 'Carbs', 'column': 'carbs'}
        ]
    },
    'body_composition': {
        'name': 'Body Composition',
        'main_metric': 'body_fat',
        'sub_metrics': [
            {'name': 'Weight', 'column': 'weight'},
            {'name': 'BMI', 'column': 'bmi'}
        ],
        'drivers': [
            {'name': 'Caloric Balance', 'column': 'calories_net'},
            {'name': 'Processed Foods', 'column': 'avoid_processed_foods'},
            {'name': 'Fat Intake', 'column': 'fat'}
        ]
    },
    'training': {
        'name': 'Training Load',
        'main_metric': 'training_load',
        'sub_metrics': [
            {'name': 'CTL', 'column': 'CTL'},
            {'name': 'ATL', 'column': 'ATL'},
            {'name': 'TSB', 'column': 'TSB'}
        ],
        'drivers': [
            {'name': 'Strength Minutes', 'column': 'strength_minutes'},
            {'name': 'Duration', 'column': 'duration'},
            {'name': 'Protein', 'column': 'protein'}
        ]
    }
}

# Styling
COLORS = {
    'primary': '#1f77b4',    # Navy blue
    'secondary': '#7f7f7f',  # Slate grey
    'background': '#ffffff', # White
    'text': '#2c3e50',      # Dark grey
    'success': '#2ecc71',   # Green
    'warning': '#f1c40f',   # Yellow
    'danger': '#e74c3c',    # Red
}

FONT = 'Inter' 