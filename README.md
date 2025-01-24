### Health-project

A comprehensive health tracking system that integrates data from multiple sources and provides visualization tools for analysis.

## Components

### Data Sources
1. Weight & Body Composition: Fitbit API
2. Nutrition & Meals: MyFitnessPal API
3. Activity & Training Load: Garmin API
4. Sleep & Recovery: Whoop API
5. Glucose: LibreView
6. Journal: Google Forms

### ETL Pipeline
- Automated data collection from various sources
- Data cleaning and standardization
- Integration into a unified dataset

### Visualization Dashboard
- Interactive web interface built with Streamlit
- Key metrics tracking with hierarchical organization
- Time series analysis and trend visualization
- Driver analysis for health behaviors

## Setup and Usage

### Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the ETL Pipeline
```bash
python ETL_main.py
```

### Running the Dashboard
```bash
cd viz
streamlit run app.py
```

### Manual Data Updates
Whoop
- Journal from app: More/App Settings/Data export

LibreView
- https://www.libreview.com/

## Project Structure
```
Health-project/
├── Data/               # Data storage
│   ├── Cleaned/       # Processed data
│   ├── Raw/           # Raw data from sources
│   └── ...            # Source-specific data
├── ETL/               # ETL pipeline
│   ├── ETL_*.py      # Source-specific ETL scripts
│   └── config.py     # ETL configuration
├── viz/               # Visualization layer
│   ├── assets/       # Static files
│   ├── components/   # Reusable UI components
│   ├── pages/        # Dashboard pages
│   ├── utils/        # Helper functions
│   ├── config.py     # Visualization settings
│   └── app.py        # Main Streamlit app
└── requirements.txt   # Project dependencies
```

## Backlog
- Password protect the cloud service
- Change the input source to G Drive
- Remove Apple from input, substitute weight measurements
- Nutrition: Change for overall daily view
- Dashboard: Ranking of worse meals and situations
- Change ATL for another metric
- Correlate behaviors with sleep metrics
- Validate Garmin TSS calculation
- Host online with batch updates