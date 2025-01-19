import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import shap

# Load the data
df_garmin = pd.read_csv('Data/Cleaned/garmin_activities.csv')
df_tp = pd.read_csv('Data/Cleaned/TSS metrics.csv')

# Convert dates
df_garmin['date'] = pd.to_datetime(df_garmin['date'])
df_tp['date'] = pd.to_datetime(df_tp['date'])

# Create activity categories
def categorize_activity(types):
    types = set(types)
    if any(t in types for t in ['running', 'trail_running']):
        return 'running'
    elif 'strength_training' in types:
        return 'strength'
    else:
        return 'other'

# Ensure numeric columns
numeric_cols = ['tss', 'training_load', 'duration', 'aerobic_te', 'anaerobic_te', 'avg_hr', 'max_hr']
for col in numeric_cols:
    df_garmin[col] = pd.to_numeric(df_garmin[col], errors='coerce')

# Group Garmin data by date and aggregate metrics
df_garmin_daily = df_garmin.groupby('date').agg({
    'tss': 'sum',
    'training_load': 'sum',
    'type': list,
    'duration': 'sum',
    'aerobic_te': 'sum',
    'anaerobic_te': 'sum',
    'avg_hr': 'mean',
    'max_hr': 'max'
}).reset_index()

# Fill NaN values with 0
df_garmin_daily = df_garmin_daily.fillna(0)

# Add activity category
df_garmin_daily['activity_category'] = df_garmin_daily['type'].apply(categorize_activity)

# Add is_trail flag for running activities
df_garmin_daily['is_trail'] = df_garmin_daily['type'].apply(
    lambda x: 1 if any('trail_running' in t for t in x) else 0
)

# Merge with TrainingPeaks data
df_merged = pd.merge(df_garmin_daily, df_tp[['date', 'TSS']], on='date', how='inner')
df_merged = df_merged.rename(columns={'TSS': 'tp_tss'})

# Function to train model and get metrics for a category
def analyze_category(data, category, features):
    # Filter data for category
    cat_data = data[data['activity_category'] == category].copy()
    
    if len(cat_data) < 2:
        return None
    
    X = cat_data[features]
    y = cat_data['tp_tss']
    
    # Ensure all features are numeric
    for col in features:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(0)
    
    # Train model
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate predictions and R²
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # Calculate SHAP values
    explainer = shap.LinearExplainer(model, X)
    shap_values = explainer.shap_values(X)
    
    # Get feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'coefficient': model.coef_,
        'shap_importance': np.abs(shap_values).mean(axis=0)
    })
    
    # Create formula string
    formula = f"TSS = {model.intercept_:.2f}"
    for feat, coef in zip(features, model.coef_):
        formula += f" + ({coef:.4f} × {feat})"
    
    return {
        'category': category,
        'n_samples': len(cat_data),
        'r2': r2,
        'formula': formula,
        'feature_importance': feature_importance,
        'model': model
    }

# Define features for each category
running_features = ['training_load', 'duration', 'aerobic_te', 'avg_hr', 'is_trail']
strength_features = ['training_load', 'duration', 'aerobic_te', 'anaerobic_te']
other_features = ['training_load', 'duration', 'aerobic_te']

# Analyze each category
results = {}
results['running'] = analyze_category(df_merged, 'running', running_features)
results['strength'] = analyze_category(df_merged, 'strength', strength_features)
results['other'] = analyze_category(df_merged, 'other', other_features)

# Print results
for category, result in results.items():
    if result:
        print(f"\n=== {category.upper()} ===")
        print(f"Number of samples: {result['n_samples']}")
        print(f"R² Score: {result['r2']:.3f}")
        print("\nFormula:")
        print(result['formula'])
        print("\nFeature Importance (SHAP values):")
        print(result['feature_importance'].sort_values('shap_importance', ascending=False))
        print("\n" + "="*50)

# Plot actual vs predicted values for each category
plt.figure(figsize=(15, 5))
for i, (category, result) in enumerate(results.items()):
    if result:
        plt.subplot(1, 3, i+1)
        cat_data = df_merged[df_merged['activity_category'] == category]
        X = cat_data[result['feature_importance']['feature'].tolist()]
        y_pred = result['model'].predict(X)
        plt.scatter(cat_data['tp_tss'], y_pred, alpha=0.5)
        plt.plot([0, max(cat_data['tp_tss'])], [0, max(cat_data['tp_tss'])], 'r--')
        plt.xlabel('Actual TSS')
        plt.ylabel('Predicted TSS')
        plt.title(f'{category.capitalize()} (R² = {result["r2"]:.3f})')

plt.tight_layout()
plt.savefig('tss_predictions.png') 