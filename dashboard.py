import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Load data from CSV
data = pd.read_csv('Data/Integrated_data.csv')

# Convert 'date' column to datetime
data['date'] = pd.to_datetime(data['date'])

# Define status thresholds (these can be modified)
status_thresholds = {
    'TSS': {'low': 40, 'high': 70},
    'CTL': {'low': 30, 'high': 60},
    'ATL': {'low': 40, 'high': 70},
    'sleep_score_performance': {'low': 50, 'high': 80},
    'sleep_score_consistency': {'low': 50, 'high': 80},
    'sleep_score_efficiency': {'low': 70, 'high': 90},
    'BMI': {'low': 18.5, 'high': 24.9},
    'fat_percentage': {'low': 10, 'high': 20},
    'lean_body_mass': {'low': 50, 'high': 70}
}

# Define function to get status color
def get_status_color(value, metric):
    if value < status_thresholds[metric]['low']:
        return 'red'
    elif value > status_thresholds[metric]['high']:
        return 'green'
    else:
        return 'yellow'

# Calculate metrics for summary page
last_2_weeks = data[data['date'] >= datetime.now() - timedelta(days=14)]
previous_month = data[(data['date'] < datetime.now() - timedelta(days=14)) & (data['date'] >= datetime.now() - timedelta(days=44))]

metrics = {
    'training': ['TSS', 'CTL', 'ATL'],
    'recovery': ['sleep_score_performance', 'sleep_score_consistency', 'sleep_score_efficiency'],
    'nutrition': ['BMI', 'fat_percentage', 'lean_body_mass']
}

summary = {block: {} for block in metrics}

for block, metric_list in metrics.items():
    for metric in metric_list:
        summary[block][metric] = {
            'value': last_2_weeks[metric].mean(),
            'trend': last_2_weeks[metric].mean() - previous_month[metric].mean(),
            'status': get_status_color(last_2_weeks[metric].mean(), metric),
            'trend_status': get_status_color(last_2_weeks[metric].mean() - previous_month[metric].mean(), metric)
        }

# Streamlit app
st.title('Health Metrics Dashboard')

# Summary Page
st.header('Summary')

for block, metric_list in summary.items():
    st.subheader(block.capitalize())
    for metric, details in metric_list.items():
        st.markdown(f"**{metric}:** {details['value']:.2f} [{details['status']}]")
        st.markdown(f"**Trend (last 2 weeks vs previous month):** {details['trend']:.2f} [{details['trend_status']}]")

# Detailed Pages
for block, metric_list in metrics.items():
    st.header(f"{block.capitalize()} Details")
    for metric in metric_list:
        fig = px.line(data, x='date', y=metric, title=f"{metric} Over Time")
        st.plotly_chart(fig)
