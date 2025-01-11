import streamlit as st
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from Dashboard.config import status_thresholds, column_name_mapping
from Dashboard.helpers import get_status_color, format_value, format_trend
from Dashboard.metrics import calculate_summary
from Dashboard.charts import create_performance_chart, create_recovery_charts, create_nutrition_chart, create_daily_view_chart
from Dashboard.llm import load_model, generate_insights


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
glucose_data = pd.read_csv('Data/Cleaned/Glucose.csv')
glucose_data['date'] = pd.to_datetime(glucose_data['date'])
meals = pd.read_csv('Data/Cleaned/MFP meals scrapped.csv')
meals['date'] = pd.to_datetime(meals['date'])

# Map column names to human-readable names
data.rename(columns=column_name_mapping, inplace=True)

# Calculate metrics for summary page
try:
    summary = calculate_summary(data, status_thresholds)
except KeyError as e:
    st.error(f"KeyError: {e}. Please check if the column exists in the data.")
    st.stop()

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'Summary'

# Streamlit app
st.title('Health Metrics Dashboard')

# Create sidebar for page navigation
st.sidebar.title('Navigation')
if st.sidebar.button('Summary'):
    st.session_state.page = 'Summary'
if st.sidebar.button('Training'):
    st.session_state.page = 'Training'
if st.sidebar.button('Recovery'):
    st.session_state.page = 'Recovery'
if st.sidebar.button('Nutrition'):
    st.session_state.page = 'Nutrition'

# Summary Page
if st.session_state.page == 'Summary':
    st.header('Summary')
    col1, col2, col3 = st.columns([1, 1, 1], gap="large")  # Adjusted column gap

    summary_text = ""

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
                summary_text += f"{metric}: {format_value(metric, details['value'])} ({format_trend(metric, details['trend'])})\n"

    # Button to generate insights
    if st.button('Generate Insights'):
        # Load the model and tokenizer
        tokenizer, model = load_model()
        insights = generate_insights(summary_text, tokenizer, model)
        st.subheader("Key Insights")
        st.write(insights)

# Training Page
elif st.session_state.page == 'Training':
    st.header('Training')
    fig = create_performance_chart(data)
    st.plotly_chart(fig, use_container_width=True)

# Recovery Page
elif st.session_state.page == 'Recovery':
    st.header('Recovery')
    for fig in create_recovery_charts(data):
        st.plotly_chart(fig, use_container_width=True)

# Nutrition Page
elif st.session_state.page == 'Nutrition':
    st.header('Nutrition')
    
    # Create tabs
    tab1, tab2 = st.tabs(["Overview", "Daily View"])
    
    with tab1:
        fig = create_nutrition_chart(data)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = create_daily_view_chart(data, glucose_data, meals)

