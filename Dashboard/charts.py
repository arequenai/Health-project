import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import plotly.graph_objects as go

from Dashboard.config import status_thresholds


def create_performance_chart(data):
    fig = go.Figure()

    # Add CTL as a light blue area graph
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['CTL'],
        mode='lines', fill='tozeroy',
        line=dict(color='lightblue'),
        name='CTL'
    ))

    # Add ATL as a pink line
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['ATL'],
        mode='lines',
        line=dict(color='orange', width=3),
        name='ATL'
    ))


    fig.add_trace(go.Scatter(
        x=data['date'], y=data['TSB'],
        mode='lines',
        line=dict(color='white', width=3),
        name='TSB',
        yaxis='y2'
    ))


    # Update layout to include secondary y-axis for TSB
    fig.update_layout(
        title='Performance Management Chart',
        xaxis_title='Date',
        yaxis_title='Score',
        yaxis=dict(title='CTL/ATL'),
        yaxis2=dict(
            title='TSB',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    height=600
    )

    return fig


import plotly.graph_objects as go
import plotly.express as px

def create_recovery_charts(data):
    # Create a figure for the recovery score bar chart with conditional coloring
    recovery_colors = data['Recovery score'].apply(lambda x: 'green' if x > 66 else 'yellow' if x > 33 else 'red')
    
    recovery_fig = go.Figure()
    recovery_fig.add_trace(go.Bar(
        x=data['date'], 
        y=data['Recovery score'],
        marker_color=recovery_colors,
        name='Recovery score'
    ))

    # Add lines for sleep score and stress level
    recovery_fig.add_trace(go.Scatter(
        x=data['date'], y=data['Sleep score'],
        mode='lines',
        line=dict(color='blue'),
        name='Sleep score'
    ))

    recovery_fig.add_trace(go.Scatter(
        x=data['date'], y=data['Stress'],
        mode='lines',
        line=dict(color='red'),
        name='Stress'
    ))

    # Update layout
    recovery_fig.update_layout(
        title='Recovery Metrics',
        xaxis_title='Date',
        yaxis_title='Score',
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    height=600
    )

    return [recovery_fig]


import plotly.graph_objects as go

def create_nutrition_chart(data):
    # Conditional coloring for net calories
    net_calories_colors = data['Net calories'].apply(lambda x: 'green' if x < 0 else 'yellow' if x <= 150 else 'red')

    # Conditional coloring for mean glucose dots
    glucose_marker_colors = data['Mean glucose'].apply(lambda x: 'green' if x < 90 else 'yellow' if x <= 100 else 'red')

    # Create figure
    fig = go.Figure()

    # Add Net Calories Bar with conditional coloring
    fig.add_trace(go.Bar(
        x=data['date'],
        y=data['Net calories'],
        marker=dict(color=net_calories_colors),
        name='Net calories'
    ))

    # Add Mean Glucose Line with Dots on a secondary y-axis
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['Mean glucose'],
        mode='lines+markers',
        line=dict(color='white', width=3),  # Set line color to white and width to 3
        marker=dict(color=glucose_marker_colors, size=8),  # Customize marker appearance with conditional colors
        name='Mean glucose',
        yaxis='y2'
    ))

    # Update layout
    fig.update_layout(
        title='Nutrition Metrics',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Net Calories'),
        yaxis2=dict(title='Mean Glucose', overlaying='y', side='right'),
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',  # Optional: set background to transparent for better visibility of white line
    height=600
    )

    return fig

import streamlit as st
import plotly.graph_objects as go
from Dashboard.helpers import get_status_color
from datetime import datetime

def create_daily_view_chart(data, glucose_data, meals):
    # Create an empty Plotly figure for now
    fig = go.Figure()

    # Create the list of dates and mean glucose values, sorted by date in descending order
    date_list = data[['date', 'Mean glucose']].dropna().sort_values(by='date', ascending=False)
    date_list['color'] = date_list['Mean glucose'].apply(lambda x: get_status_color(x, 'Mean glucose'))

    # Create a dropdown menu for selecting a date
    date_options = {f"{row['date'].strftime('%Y-%m-%d')}: {row['Mean glucose']:.1f} {row['color']}": row['date'] for index, row in date_list.iterrows()}
    selected_date_label = st.selectbox('Select a date', list(date_options.keys()))
    selected_date = date_options[selected_date_label]

    # Filter glucose_data based on selected date
    filtered_glucose_data = glucose_data[glucose_data['date'] == selected_date]

    # Add a trace for glucose over time with white lines
    fig.add_trace(go.Scatter(x=filtered_glucose_data['datetime'], y=filtered_glucose_data['glucose'], mode='lines', line=dict(color='white'), name='Glucose'))

    # Add semitransparent red band in the background for glucose levels above 140
    fig.add_shape(
        type="rect",
        xref="paper", yref="y",
        x0=0, y0=140, x1=1, y1=max(filtered_glucose_data['glucose']),
        fillcolor="red", opacity=0.2, layer="below", line_width=0,
    )

    # Add semitransparent green band in the background for glucose levels below 100
    fig.add_shape(
        type="rect",
        xref="paper", yref="y",
        x0=0, y0=0, x1=1, y1=100,
        fillcolor="green", opacity=0.2, layer="below", line_width=0,
    )

    # Get sleep_time and sleep_duration from the data
    sleep_time_str = data[data['date'] == selected_date]['sleep_time'].values[0]
    sleep_duration = data[data['date'] == selected_date]['sleep_duration'].values[0]

    # Parse sleep_time from 'HH:MM:SS' to datetime
    sleep_time = datetime.strptime(sleep_time_str, '%H:%M:%S').time()
    
    # Convert sleep time and duration to datetime objects
    sleep_start = pd.Timestamp.combine(selected_date, sleep_time)
    sleep_end = sleep_start + pd.Timedelta(hours=sleep_duration)

    # Adjust if sleep time is after 8 PM
    if sleep_start.hour >= 20:
        sleep_start -= pd.Timedelta(days=1)
        sleep_end -= pd.Timedelta(days=1)

    # Calculate sleep duration in hours and minutes
    sleep_duration_hours = int(sleep_duration)
    sleep_duration_minutes = int((sleep_duration - sleep_duration_hours) * 60)
    sleep_duration_str = f"{sleep_duration_hours}h {sleep_duration_minutes}m"

    # Add sleep time arrow
    fig.add_shape(
        type="line",
        x0=sleep_start, y0=0, x1=sleep_end, y1=0,
        line=dict(color="lightblue", width=3),
        xref="x", yref="y"
    )

    fig.add_annotation(
        x=sleep_start + (sleep_end - sleep_start) / 2,
        y=-10,  # Position it below the x-axis
        text=f"Sleep ({sleep_duration_str})",
        showarrow=False,
        font=dict(color="lightblue")
    )

    # Add thin blue vertical lines at the beginning and end of sleep
    fig.add_shape(
        type="line",
        x0=sleep_start, y0=0, x1=sleep_start, y1=max(filtered_glucose_data['glucose']),
        line=dict(color="lightblue", width=1, dash="dot"),
        xref="x", yref="y"
    )
    fig.add_shape(
        type="line",
        x0=sleep_end, y0=0, x1=sleep_end, y1=max(filtered_glucose_data['glucose']),
        line=dict(color="lightblue", width=1, dash="dot"),
        xref="x", yref="y"
    )


    # Update layout
    fig.update_layout(
        title=f'Glucose Levels for {selected_date_label}',
        xaxis_title='Time',
        yaxis_title='Glucose',
        height=600,
        plot_bgcolor='rgba(0, 0, 0, 0)'  # Optional: set background to transparent
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Filter meals data based on selected date
    meals_for_date = meals[meals['date'] == selected_date]

    # Aggregate the meal data by meal type and round the values to integers, renaming columns
    meal_types = ['breakfast', 'lunch', 'dinner', 'snacks']
    meal_summaries = {
        meal_type: meals_for_date[meals_for_date['meal'] == meal_type][['calories', 'carbs', 'fat', 'protein', 'sugar']]
        .agg(lambda x: round(x.sum()))
        .rename({'calories': 'cals', 'protein': 'prot'})
        for meal_type in meal_types
    }

    import re
    def clean_food_name(food):
        # Remove everything to the right of a comma, including the comma
        if ',' in food:
            food = food.split(',')[0]
        
        # Remove everything to the left of a dash, including the dash and the space
        if ' - ' in food:
            food = food.split(' - ')[1]

        # Remove weird characters
        food = re.sub(r'[^a-zA-ZñÑáéíóúÁÉÍÓÚ\s]', '', food)

        # Capitalize first letter of each word and make the rest lowercase
        food = food.capitalize()

        return food

    # Display meal summaries and food names in four columns
    cols = st.columns(4)
    for col, meal_type in zip(cols, meal_types):
        with col:
            st.subheader(meal_type.capitalize())
            if not meal_summaries[meal_type].empty:
                summary = meal_summaries[meal_type].to_frame().T
                st.table(summary)
                # List food names
                foods = meals_for_date[meals_for_date['meal'] == meal_type]['food'].apply(clean_food_name).tolist()
                for food in foods:
                    st.write(food)
            else:
                st.write("No data")


    return fig
