import plotly.express as px
import plotly.graph_objects as go

import plotly.graph_objects as go

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

