import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, date

def get_food_time_data(xml_file_path, start_date):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    max_date = date.today()

    # Create a mapping of xml names for MyFitnessPal to human-readable names
    food_mapping = {
        'HKQuantityTypeIdentifierDietaryCalcium': 'calcium',
        'HKQuantityTypeIdentifierDietaryCarbohydrates': 'carbs',
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

    # Collect data
    data = []
    for record in root.findall('.//Record'):
        if record.attrib.get('sourceName') == 'MyFitnessPal':
            record_date = datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').date()
            if start_date <= record_date <= max_date:
                data.append({
                    'date': record_date,
                    'time': datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').time(),
                    'type': food_mapping.get(record.attrib['type'], 'Unknown'),
                    'value': record.attrib.get('value'),
                    'unit': record.attrib.get('unit')
                })

    # Create DataFrame
    df = pd.DataFrame(data)
    df = df.groupby(['date', 'time', 'type'])['value'].sum().unstack().reset_index()

    # Handle situations in which a variable has two decimal dots. In that case, it should just keep the first one
    for col in df.columns[3:]:
        df[col] = df[col].apply(lambda x: x if x is None or (isinstance(x, str) and x.count('.') <= 1) else x[:x.find('.', x.find('.') + 1)] if isinstance(x, str) else x)

    # Remove files in which only the unknown column has data
    df = df.dropna(subset=df.columns[3:], how='all')

   
    return df

def get_weight_data(xml_file_path, start_date):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    max_date = date.today()

    # Create a mapping of xml names for MyFitnessPal to human-readable names
    weight_mapping = {
        'HKQuantityTypeIdentifierBodyFatPercentage': 'fat_percentage',
        'HKQuantityTypeIdentifierLeanBodyMass': 'lean_body_mass',
        'HKQuantityTypeIdentifierBodyMassIndex': 'BMI',
        'HKQuantityTypeIdentifierBodyMass': 'weight'
    }

    # Collect data
    data = []
    for record in root.findall('.//Record'):
        if record.attrib.get('sourceName') == 'VeSync':
            record_date = datetime.strptime(record.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').date()
            if start_date <= record_date <= max_date:
                data.append({
                    'date': record_date,
                    'type': weight_mapping.get(record.attrib['type'], 'Unknown'),
                    'value': record.attrib.get('value')
                })

    # Check if data list is empty
    if not data:
        return None  # Return None if no data is collected

    # Create DataFrame
    df = pd.DataFrame(data)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.groupby(['date', 'type'])['value'].mean().unstack().reset_index()

    return df


def main():
   
    start_date = datetime.strptime('2024-01-01', '%Y-%m-%d').date()

    food_df = get_food_time_data('Data/Apple health/exportacion.xml', start_date)
    if food_df is not None:
        food_df.to_csv('Data/Cleaned/Food.csv', index=False)
        print("Food CSV file has been created.")

    weight_df = get_weight_data('Data/Apple health/exportacion.xml', start_date)
    # Only if data is available
    if weight_df is not None:
        weight_df.to_csv('Data/Cleaned/Weight.csv', index=False)
        print("Weight CSV file has been created.")

if __name__ == "__main__":
    main()