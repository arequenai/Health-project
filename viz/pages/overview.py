import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from viz import config

def format_marathon_change(minutes):
    """Format marathon time difference in HH:MM format."""
    if pd.isna(minutes) or minutes == 0:
        return "N/A"
    try:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"
    except:
        return "N/A"

def create_sparkline(data, metric_name, height=80):
    """Create a sparkline plot for the metric with weekly averages."""
    fig = go.Figure()
    
    # Handle empty or all-NaN data
    if data.empty or data.isna().all():
        fig.update_layout(
            height=height,
            margin=dict(l=0, r=0, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False)
        )
        return fig
    
    # Calculate weekly averages (excluding NaN values)
    df_weekly = pd.DataFrame({'value': data}).reset_index()
    df_weekly.columns = ['date', 'value']
    df_weekly['week_num'] = [i // 7 for i in range(len(df_weekly))]  # Fixed integer division
    weekly_avgs = df_weekly.groupby('week_num')['value'].agg(
        lambda x: x.mean() if not x.isna().all() else pd.NA
    )
    
    # Add main line (daily values) with lighter color
    valid_data = data.dropna()
    if not valid_data.empty:
        fig.add_trace(go.Scatter(
            y=data,
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.3)', width=1.5),
            showlegend=False
        ))
    
    # Calculate y-range from valid data only
    valid_values = data.dropna()
    if not valid_values.empty:
        y_min = valid_values.min()
        y_max = valid_values.max()
        y_range = y_max - y_min if y_max != y_min else 1
        
        # Add horizontal lines for weekly averages
        prev_avg = None
        for week_num, avg in weekly_avgs.items():
            if pd.isna(avg):
                continue
                
            # Calculate x positions for the horizontal lines
            x_start = week_num * 7
            x_end = min((week_num + 1) * 7 - 1, len(data) - 1)
            
            # Determine color based on comparison with previous week
            if prev_avg is None:
                line_color = 'rgba(255, 255, 255, 0.8)'  # First week is white
                change_text = ""
            else:
                # Calculate absolute difference from previous week
                abs_diff = abs(avg - prev_avg)
                
                if metric_name in ['body_fat', 'wake_up_glucose', 'predicted_marathon']:
                    # For these metrics, lower is better
                    is_improvement = avg < prev_avg
                else:
                    # For all other metrics, higher is better
                    is_improvement = avg > prev_avg
                
                if is_improvement:
                    line_color = 'rgba(46, 204, 113, 0.8)'  # Beautiful green
                else:
                    line_color = 'rgba(230, 126, 34, 0.8)'  # Dark orange
                
                # Format change text with absolute difference
                if metric_name == 'predicted_marathon':
                    change_text = f"{'+' if not is_improvement else '-'}{format_marathon_change(abs_diff)}"
                elif metric_name in ['body_fat']:
                    change_text = f"{'+' if not is_improvement else '-'}{abs_diff:.1f}%"
                else:
                    change_text = f"{'+' if avg > prev_avg else '-'}{abs_diff:.1f}"
            
            # Add horizontal line for weekly average
            fig.add_trace(go.Scatter(
                x=[x_start, x_end],
                y=[avg, avg],
                mode='lines',
                line=dict(color=line_color, width=2),
                showlegend=False
            ))
            
            # Format and add text annotation for weekly average
            try:
                formatted_avg = format_metric_value(avg, metric_name)
                if formatted_avg != "N/A":
                    # Add value above the line (always white)
                    fig.add_annotation(
                        x=x_start,
                        y=avg + (y_range * 0.05),
                        text=formatted_avg,
                        showarrow=False,
                        font=dict(size=16, color='rgba(255, 255, 255, 0.8)'),  # Always white
                        yanchor='bottom',
                        xanchor='left'
                    )
                    
                    # Add change below the line with the status color
                    if change_text:
                        fig.add_annotation(
                            x=x_start,
                            y=avg - (y_range * 0.05),
                            text=change_text,
                            showarrow=False,
                            font=dict(size=14, color=line_color),  # Same color as the line
                            yanchor='top',
                            xanchor='left'
                        )
            except:
                continue
            
            prev_avg = avg
    
    # Update layout
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False)
    )
    
    return fig

def get_status_color(value, metric_name):
    """Get status color based on metric thresholds."""
    thresholds = {
        'sleep_score_performance': {'optimal': 80, 'warning': 60},
        'recovery_score': {'optimal': 70, 'warning': 50},
        'wake_up_glucose': {'optimal': 90, 'warning': 100},
        'body_fat': {'optimal': 15, 'warning': 20},
        'CTL': {'optimal': 80, 'warning': 60},
        'predicted_marathon': {'optimal': 210, 'warning': 240}  # in minutes
    }
    
    if metric_name not in thresholds:
        return config.COLORS['primary']
    
    t = thresholds[metric_name]
    if metric_name in ['body_fat', 'wake_up_glucose', 'predicted_marathon']:
        # Lower is better
        if value <= t['optimal']:
            return config.COLORS['success']
        elif value <= t['warning']:
            return config.COLORS['warning']
        else:
            return config.COLORS['danger']
    else:
        # Higher is better
        if value >= t['optimal']:
            return config.COLORS['success']
        elif value >= t['warning']:
            return config.COLORS['warning']
        else:
            return config.COLORS['danger']

def get_metric_info(metric_name):
    """Get metric display info including units and description."""
    info = {
        'sleep_score_performance': {'units': '', 'description': 'Sleep Performance Score'},
        'recovery_score': {'units': '', 'description': 'Recovery Score'},
        'wake_up_glucose': {'units': 'mg/dL', 'description': 'Fasting Glucose'},
        'body_fat': {'units': '%', 'description': 'Body Fat Percentage'},
        'CTL': {'units': '', 'description': 'Chronic Training Load'},
        'predicted_marathon': {'units': '', 'description': 'Predicted Marathon Time'}
    }
    return info.get(metric_name, {'units': '', 'description': metric_name})

def format_marathon_time(value):
    """Helper function to format marathon time."""
    if pd.isna(value) or value == 0:
        return "N/A"
    try:
        hours = int(value // 60)
        minutes = int(value % 60)
        return f"{hours:02d}:{minutes:02d}"
    except:
        return "N/A"

def format_metric_value(value, metric_name):
    """Format metric value based on type."""
    if pd.isna(value) or value == 0:
        return "N/A"
        
    try:
        if metric_name == 'predicted_marathon':
            return format_marathon_time(value)
        elif metric_name == 'body_fat':
            return f"{value:.1f}%"
        elif metric_name in ['CTL', 'TSB']:
            return f"{value:.1f}"
        else:
            return f"{value:.0f}"
    except:
        return "N/A"

def render_metric_card(title, df, metric_name, col):
    """Render a single metric card."""
    with col:
        # Card container with improved styling
        st.markdown("""
            <style>
            .metric-card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 0.5rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                margin-bottom: 1rem;
            }
            .metric-title {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            .metric-trend {
                font-size: 1.5rem;
                margin-left: 0.5rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Get metric info
        metric_info = get_metric_info(metric_name)
        
        # Get last 6 weeks of data
        recent_data = df[metric_name].tail(42)  # 6 weeks * 7 days
        
        # Get metric values
        current = recent_data.iloc[-1] if not recent_data.empty else None
        previous = recent_data.iloc[-8] if len(recent_data) > 8 else None
        
        # Calculate change only if both values are valid
        if current is not None and previous is not None and not pd.isna(current) and not pd.isna(previous) and previous != 0:
            change = ((current - previous) / abs(previous)) * 100
            trend = "↑" if change > 2 else "↓" if change < -2 else "→"
            trend_color = (config.COLORS['success'] if change > 2 
                          else config.COLORS['danger'] if change < -2 
                          else config.COLORS['secondary'])
        else:
            trend = "→"
            trend_color = config.COLORS['secondary']
            change = 0
        
        # Create card header with metric description
        st.markdown(f"### {title}")
        st.markdown(f"<div class='metric-title'>{metric_info['description']}</div>", unsafe_allow_html=True)
        
        # Create metric value and trend
        value_text = format_metric_value(current, metric_name)
        st.markdown(f"""
            <div style='display: flex; align-items: baseline; gap: 0.5rem;'>
                <div class='metric-value'>{value_text}</div>
                <div style='color: {trend_color};' class='metric-trend'>{trend}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Create sparkline
        if not recent_data.empty and not recent_data.isna().all():
            fig = create_sparkline(recent_data, metric_name)
            st.plotly_chart(fig, use_container_width=True, config={
                'displayModeBar': False,
                'staticPlot': True,  # This disables all interactivity
                'showTips': False
            })
        else:
            st.markdown("*No data available for trend*")

def render_overview(df):
    """Render the overview page with six metric cards."""
    st.title("Health Dashboard - Overview")
    
    # Create two rows of three columns
    row1_cols = st.columns(3)
    row2_cols = st.columns(3)
    
    # Render first row of metrics
    render_metric_card("Sleep", df, 'sleep_score_performance', row1_cols[0])
    render_metric_card("Recovery", df, 'recovery_score', row1_cols[1])
    render_metric_card("Glucose", df, 'wake_up_glucose', row1_cols[2])
    
    # Render second row of metrics
    render_metric_card("Body", df, 'body_fat', row2_cols[0])
    render_metric_card("Training", df, 'CTL', row2_cols[1])
    render_metric_card("Running", df, 'predicted_marathon', row2_cols[2]) 