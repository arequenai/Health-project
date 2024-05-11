# Initialize
import pandas as pd
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta

# Path to your Apple Health XML export
xml_file_path = 'Data/Apple health/exportacion.xml'

# Load and parse the XML file
tree = ET.parse(xml_file_path)
root = tree.getroot()

# Initialize variables for date range
min_date, max_date = None, None

# Determine the date range
for record in root.findall('.//Record'):
    if record.attrib.get('sourceName') == 'MyFitnessPal':
        start_date = datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').date()
        if min_date is None or start_date < min_date:
            min_date = start_date
        if max_date is None or start_date > max_date:
            max_date = start_date

# Create a mapping of xml names for MyFitnessPal to human-readable names
food_mapping = {
    'HKQuantityTypeIdentifierDietaryCalcium': 'calcium',
    'HKQuantityTypeIdentifierDietaryCarbohydrates':'carbs',
    'HKQuantityTypeIdentifierDietaryCholesterol': 'cholesterol',
    'HKQuantityTypeIdentifierDietaryEnergyConsumed': 'calories',
    'HKQuantityTypeIdentifierDietaryFatMonounsaturated': 'monounsaturated fat',
    'HKQuantityTypeIdentifierDietaryFatPolyunsaturated': 'polyunsaturated fat',
    'HKQuantityTypeIdentifierDietaryFatSaturated': 'saturated fat',
    'HKQuantityTypeIdentifierDietaryFatTotal': 'fat',
    'HKQuantityTypeIdentifierDietaryFiber': 'fiber',
    'HKQuantityTypeIdentifierDietaryIron': 'iron',
    'HKQuantityTypeIdentifierDietaryPotassium': 'potassium',
    'HKQuantityTypeIdentifierDietaryProtein': 'protein',
    'HKQuantityTypeIdentifierDietarySodium': 'sodium',
    'HKQuantityTypeIdentifierDietarySugar': 'sugar',
    'HKQuantityTypeIdentifierDietaryVitaminC': 'vitamin_c'
}

# Get food data parsing MyFitnessPal records from the xml
data = []

for record in root.findall('.//Record'):
    if record.attrib.get('sourceName') == 'MyFitnessPal':
        start_date = datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').date()
        if start_date >= min_date and start_date <= max_date:
            data.append({
                'date': start_date,
                'time': datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').time(),
                'type': food_mapping.get(record.attrib.get('type'), 'Unknown'),
                'food': record.attrib.get('value'),
                'unit': record.attrib.get('unit'),
         })

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Group by date, time and type
df = df.groupby(['date', 'time', 'type'])['food'].sum().unstack().reset_index()

# Handle situations in which a variable has two decimal dots. In that case, it should just keep the first one
for col in df.columns[3:]:
    df[col] = df[col].apply(lambda x: x if x is None or (isinstance(x, str) and x.count('.') <= 1) else x[:x.find('.', x.find('.') + 1)] if isinstance(x, str) else x)

# Remove files in which only the unknown column has data
df = df.dropna(subset=df.columns[3:], how='all')

# Write the DataFrame to a CSV file
df.to_csv('Data/Cleaned/Food.csv', index=False)
print("Food CSV file has been created.")

### Weight data

# Create a mapping of xml names for MyFitnessPal to human-readable names
weight_mapping = {
    'HKQuantityTypeIdentifierBodyFatPercentage': 'fat_percentage',
    'HKQuantityTypeIdentifierLeanBodyMass':'lean_body_mass',
    'HKQuantityTypeIdentifierBodyMassIndex': 'BMI',
    'HKQuantityTypeIdentifierBodyMass': 'weight'
}

# Get weight data parsing MyFitnessPal records from the xml
data = []

for record in root.findall('.//Record'):
    if record.attrib.get('sourceName') == 'VeSync':
        start_date = datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').date()
        if start_date >= min_date and start_date <= max_date:
            data.append({
                'date': start_date,
                'type': weight_mapping.get(record.attrib.get('type'), 'Unknown'),
                'value': record.attrib.get('value')
         })

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Convert 'value' column to numeric
df['value'] = pd.to_numeric(df['value'], errors='coerce')

# Group by date
df = df.groupby(['date', 'type'])['value'].mean().unstack().reset_index()

# Remove type column
df.columns.name = None

# Write the DataFrame to a CSV file
df.to_csv('Data/Cleaned/Weight.csv', index=False)
print("Weight CSV file has been created.")