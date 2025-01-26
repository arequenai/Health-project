"""Main Streamlit application for health metrics visualization."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import os
import subprocess

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from viz import config
from viz.pages.overview import render_overview

# Page config
st.set_page_config(
    page_title="Health Dashboard",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Set dark theme
st.markdown("""
    <style>
    /* Dark theme */
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
        color: white;
    }
    [data-testid="stSidebar"] {
        background-color: #262730;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Disable hover effects and tooltips */
    .stPlotlyChart {pointer-events: none;}
    [data-testid="StyledFullScreenButton"] {display: none;}
    .modebar {display: none !important;}
    .js-plotly-plot .plotly .modebar {display: none !important;}
    iframe {pointer-events: none;}
    
    /* General styling */
    .main {
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

def update_data():
    """Run the ETL process to update all data."""
    try:
        # Run ETL_main.py from the project root
        etl_script = os.path.join(root_dir, 'ETL_main.py')
        result = subprocess.run([sys.executable, etl_script], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            st.sidebar.success("Data updated successfully!")
            # Force a rerun of the app to load new data
            st.rerun()
        else:
            st.sidebar.error(f"Error updating data: {result.stderr}")
    except Exception as e:
        st.sidebar.error(f"Error running update: {str(e)}")

def load_data():
    """Load and preprocess data."""
    # Construct absolute path
    data_path = os.path.join(root_dir, config.DASHBOARD_DATA_PATH)
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df

def main():
    """Main application function."""
    # Add update button in sidebar
    if st.sidebar.button("🔄 Update Data"):
        update_data()
    
    # Load data
    df = load_data()
    
    # Simplified navigation
    page = st.sidebar.radio("", ["Overview", "Training", "Recovery", "Nutrition"])
    
    # For Overview page, always show last 6 weeks
    if page == "Overview":
        end_date = df['date'].max()
        start_date = end_date - timedelta(weeks=6)
        df_filtered = df[df['date'] >= start_date]
        render_overview(df_filtered)
    else:
        # Date range selector for other pages
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        start_date = st.sidebar.date_input("Start date", min_date)
        end_date = st.sidebar.date_input("End date", max_date)
        
        df_filtered = df[(df['date'] >= pd.Timestamp(start_date)) & 
                        (df['date'] <= pd.Timestamp(end_date))]
        
        if page == "Training":
            st.title("Training Metrics - Coming Soon")
        elif page == "Recovery":
            st.title("Recovery Metrics - Coming Soon")
        elif page == "Nutrition":
            st.title("Nutrition Metrics - Coming Soon")

if __name__ == "__main__":
    main() 