# Define status thresholds and colors for each metric
status_thresholds = {
    'CTL': {
        'L2W': {'levels': [0, 30, 50], 'colors': ['🔴', '🟡', '🟢']},
        'delta': {'levels': [-float('inf'), -5, 0], 'colors': ['🔴', '🟡', '🟢']}
    },
    'TSB': {
        'L2W': {'levels': [-float('inf'), -20, -5, 10, float('inf')], 'colors': ['🔴', '🟢', '🟡', '🔴']},
        'delta': {'levels': [-float('inf'), 0, 5, float('inf')], 'colors': ['🟢', '🟡', '🔴']},
    },
    'ATL': {
        'L2W': {'levels': [0, 40, 70, 100], 'colors': ['🔴', '🟡', '🟢', '🔴']},
        'delta': {'levels': [-float('inf'), -5, 0, 5, float('inf')], 'colors': ['🔴', '🟡', '🟢', '🔴']}
    },
    'Recovery score': {
        'L2W': {'levels': [0, 33, 66], 'colors': ['🔴', '🟡', '🟢']},
        'delta': {'levels': [-float('inf'), -5, 0, float('inf')], 'colors': ['🔴', '🟡', '🟢']}
    },
    'Sleep score': {
        'L2W': {'levels': [0, 50, 75], 'colors': ['🔴', '🟡', '🟢']},
        'delta': {'levels': [-float('inf'), -5, 0, float('inf')], 'colors': ['🔴', '🟡', '🟢']}
    },
    'Stress': {
        'L2W': {'levels': [0, 30, 50], 'colors': ['🟢', '🟡', '🔴']},
        'delta': {'levels': [-float('inf'), 0, 5, float('inf')], 'colors': ['🟢', '🟡', '🔴']}
    },
    'Weight': {
        'L2W': {'levels': [0, 67, 69], 'colors': ['🟢', '🟡', '🔴']},
        'delta': {'levels': [-float('inf'), 0, 0.5, float('inf')], 'colors': ['🟢', '🟡', '🔴']}
    },
    'Net calories': {
        'L2W': {'levels': [-float('inf'), 0, 150], 'colors': ['🟢', '🟡', '🔴']},
        'delta': {'levels': [-float('inf'), 0, 50], 'colors': ['🟢', '🟡', '🔴']},
    },
    'Mean glucose': {
        'L2W': {'levels': [0, 95, 100], 'colors': ['🟢', '🟡', '🔴']},
        'delta': {'levels': [-float('inf'), 0, 5, float('inf')], 'colors': ['🟢', '🟡', '🔴']}
    },

}
# Map column names to human-readable names
column_name_mapping = {
    'mean_glucose': 'Mean glucose',
    'calories_net': 'Net calories',
    'sleep_score_performance': 'Sleep score',
    'recovery_score': 'Recovery score',
    'averageStressLevel': 'Stress',
    'BMI': 'BMI',
    'fat_percentage': 'Fat %',
    'lean_body_mass': 'Lean mass',
    'weight': 'Weight'
}
