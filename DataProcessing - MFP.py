# Initialize
import pandas as pd
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta

# Path to your Apple Health XML export
xml_file_path = 'Data/Apple health/exportacion.xml'
# Path to the CSV file you want to create
csv_file_path = 'Data/Cleaned/Food.csv'

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

# Write the DataFrame to a CSV file
df.to_csv(csv_file_path, index=False)
print("Food CSV file has been created.")