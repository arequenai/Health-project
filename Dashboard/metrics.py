from datetime import timedelta
from Dashboard.helpers import get_status_color

def calculate_summary(data, status_thresholds):
    # Find the last date in the dataset
    last_date = data['date'].max()

    # Calculate the date ranges based on the last date
    last_2_weeks = data[data['date'] >= last_date - timedelta(days=14)]
    previous_month = data[(data['date'] < last_date - timedelta(days=14)) & (data['date'] >= last_date - timedelta(days=44))]

    metrics = {
        'training': ['CTL', 'TSB', 'ATL'],
        'recovery': ['Recovery score', 'Sleep score', 'Stress'],
        'nutrition': ['Weight', 'Net calories', 'Mean glucose']
    }

    summary = {block: {} for block in metrics}

    for block, metric_list in metrics.items():
        for metric in metric_list:
            if metric not in data.columns:
                raise KeyError(f"Column '{metric}' not found in data.")
            if metric in status_thresholds:
                summary[block][metric] = {
                    'value': last_2_weeks[metric].mean(),
                    'trend': last_2_weeks[metric].mean() - previous_month[metric].mean(),
                    'status': get_status_color(last_2_weeks[metric].mean(), metric, type='L2W'),
                    'trend_status': get_status_color(last_2_weeks[metric].mean() - previous_month[metric].mean(), metric, type='delta')
                }
    return summary
