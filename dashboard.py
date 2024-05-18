import streamlit as st
import pandas as pd
from Dashboard.config import status_thresholds, column_name_mapping
from Dashboard.helpers import get_status_color, format_value, format_trend
from Dashboard.metrics import calculate_summary
from Dashboard.charts import create_performance_chart, create_recovery_charts, create_nutrition_chart

# Custom CSS to make the entire dashboard wider, increase the font size, and enlarge the colored dots
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 90%;
        padding: 2rem;
    }
    .summary-container {
        font-size: 1.2rem;
    }
    .colored-dot {
        font-size: 1.5rem;
        margin-left: 5px;  /* Adjust the margin as needed */
    }
    .value-dot {
        display: flex;
        justify-content: flex-end;  /* Align to the right */
        align-items: center;
    }
    .header-right {
    text-align: right;  /* Align header text to the right */
    }
    .column-margin {
        margin-right: 30px;  /* Add margin between columns */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Load data
data = pd.read_csv('Data/Cleaned/Integrated_data.csv')
data['date'] = pd.to_datetime(data['date'])

# Map column names to human-readable names
data.rename(columns=column_name_mapping, inplace=True)

# Calculate metrics for summary page
try:
    summary = calculate_summary(data, status_thresholds)
except KeyError as e:
    st.error(f"KeyError: {e}. Please check if the column exists in the data.")
    st.stop()

# Streamlit app
st.title('Health Metrics Dashboard')

# Create tabs
tabs = st.tabs(["Summary", "Training", "Recovery", "Nutrition"])

# Summary Tab
with tabs[0]:
    st.header('Summary')
    col1, col2, col3 = st.columns([1, 1, 1], gap="large")  # Adjusted column gap

    for col, block in zip([col1, col2, col3], ['training', 'recovery', 'nutrition']):
        with col:
            st.subheader(block.capitalize())
            sub_col1, sub_col2, sub_col3 = st.columns([2, 1, 1])
            with sub_col2:
                st.markdown("<div class='header-right'><strong>L2W</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</div>", unsafe_allow_html=True)
            with sub_col3:
                st.markdown("<div class='header-right'><strong>Δ vs 1m</strong>&nbsp;&nbsp;&nbsp;&nbsp;</div>", unsafe_allow_html=True)
            for metric, details in summary[block].items():
                sub_col1, sub_col2, sub_col3 = st.columns([2, 1, 1])
                with sub_col1:
                    st.markdown(f"<div class='summary-container'><strong>{metric}</strong></div>", unsafe_allow_html=True)
                with sub_col2:
                    st.markdown(f"<div class='summary-container value-dot'>{format_value(metric, details['value'])} <span class='colored-dot'>{details['status']}</span></div>", unsafe_allow_html=True)
                with sub_col3:
                    st.markdown(f"<div class='summary-container value-dot'>{format_trend(metric, details['trend'])} <span class='colored-dot'>{details['trend_status']}</span></div>", unsafe_allow_html=True)

# Training Tab
with tabs[1]:
    st.header('Training')
    fig = create_performance_chart(data)
    st.plotly_chart(fig, use_container_width=True)

# Recovery Tab
with tabs[2]:
    st.header('Recovery')
    for fig in create_recovery_charts(data):
        st.plotly_chart(fig, use_container_width=True)

# Nutrition Tab
with tabs[3]:
    st.header('Nutrition')
    fig = create_nutrition_chart(data)
    st.plotly_chart(fig, use_container_width=True)
