from Dashboard.config import status_thresholds

def get_status_color(value, metric, type='L2W'):
    levels = status_thresholds[metric][type]['levels']
    colors = status_thresholds[metric][type]['colors']
    for i in range(len(levels) - 1):
        if levels[i] <= value < levels[i + 1]:
            return colors[i]
    return colors[-1]

def format_value(metric, value):
    if 'percentage' in metric:
        return f"{value * 100:.0f}%"
    elif 'weight' in metric.lower():  # Check if the metric is weight
        return f"{value:.1f}"  # Format weight with one decimal place
    else:
        return f"{value:.0f}"

def format_trend(metric, trend):
    if 'percentage' in metric:
        return f"{trend * 100:.0f}%"
    elif 'weight' in metric.lower():  # Check if the metric is weight
        return f"{trend:.1f}"  # Format weight trend with one decimal place
    elif trend > 0:
        return f"+{trend:.0f}"
    else:
        return f"{trend:.0f}"
