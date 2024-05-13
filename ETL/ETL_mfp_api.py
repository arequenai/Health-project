import myfitnesspal
import datetime
import csv
import os

def init_mfp():
    """Initialize and return a MyFitnessPal client."""
    return myfitnesspal.Client()

# Function to get the most recent date from a CSV file
def get_most_recent_date(filename):
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            last_row = None
            for last_row in reader:
                pass
            if last_row:
                return datetime.datetime.strptime(last_row[0], '%Y-%m-%d')
    except FileNotFoundError:
        return None

# Function to delete the last day's data from a CSV file
def delete_last_day_data(filename, date):
    temp_filename = filename + '.tmp'
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile, open(temp_filename, 'w', newline='', encoding='utf-8') as tmpfile:
        reader = csv.reader(csvfile)
        writer = csv.writer(tmpfile)
        headers = next(reader)
        writer.writerow(headers)
        for row in reader:
            if row[0] != date.strftime('%Y-%m-%d'):
                writer.writerow(row)
    os.replace(temp_filename, filename)

# Function to get meal data from MyFitnessPal and append to a CSV file
def get_meal_data(client, filename):
    start_date = datetime.datetime.strptime('2024-03-16', '%Y-%m-%d')
    end_date = datetime.datetime.now()
    most_recent_date = get_most_recent_date(filename)
    if most_recent_date and most_recent_date >= start_date:
        delete_last_day_data(filename, most_recent_date)
        start_date = most_recent_date + datetime.timedelta(days=1)

    fieldnames = ['date', 'meal', 'food', 'quant', 'calories', 'carbs', 'fat', 'protein', 'sodium', 'sugar']
    mode = 'a' if os.path.exists(filename) else 'w'
    with open(filename, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        current_date = start_date
        while current_date <= end_date:
            diary = client.get_date(current_date.year, current_date.month, current_date.day)
            for meal in diary.meals:
                for food in meal.entries:
                    row_data = {
                        'date': current_date.strftime('%Y-%m-%d'),
                        'meal': meal.name,
                        'food': food.name,
                        'quant': food.quantity,
                        'calories': food.nutrition_information['calories'],
                        'carbs': food.nutrition_information['carbohydrates'],
                        'fat': food.nutrition_information['fat'],
                        'protein': food.nutrition_information['protein'],
                        'sodium': food.nutrition_information['sodium'],
                        'sugar': food.nutrition_information['sugar']
                    }
                    writer.writerow(row_data)
            print(f'MPF data per meal finished {current_date.strftime("%Y-%m-%d")}')
            current_date += datetime.timedelta(days=1)

# Function to get daily summary data from MyFitnessPal and append to a CSV file
def get_meal_daily(client, filename):
    start_date = datetime.datetime.strptime('2024-03-16', '%Y-%m-%d')
    end_date = datetime.datetime.now()
    most_recent_date = get_most_recent_date(filename)
    if most_recent_date and most_recent_date >= start_date:
        delete_last_day_data(filename, most_recent_date)
        start_date = most_recent_date + datetime.timedelta(days=1)

    fieldnames = ['date', 'calories_burned', 'carbs', 'fat', 'protein', 'sodium', 'sugar', 'calories_consumed', 'calories_goal', 'calories_net',
                  'calories_consumed_breakfast', 'calories_consumed_lunch', 'calories_consumed_dinner', 'calories_consumed_snacks']
    mode = 'a' if os.path.exists(filename) else 'w'
    with open(filename, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        current_date = start_date
        while current_date <= end_date:
            diary = client.get_date(current_date.year, current_date.month, current_date.day)
            exercises = diary.exercises[0].entries if diary.exercises else []
            calories_burned = sum(entry.get_as_dict()['nutrition_information'].get('calories burned', 0) for entry in exercises)
            calories_meal = {name: diary.meals[i].totals['calories'] if len(diary.meals[i].entries) else 0 for i, name in enumerate(['breakfast', 'lunch', 'dinner', 'snacks'])}
            writer.writerow({
                'date': current_date.strftime('%Y-%m-%d'),
                'calories_burned': calories_burned,
                'carbs': diary.totals['carbohydrates'],
                'fat': diary.totals['fat'],
                'protein': diary.totals['protein'],
                'sodium': diary.totals['sodium'],
                'sugar': diary.totals['sugar'],
                'calories_consumed': diary.totals['calories'],
                'calories_goal': diary.goals['calories'],
                'calories_net': diary.totals['calories'] - diary.goals['calories'],
                'calories_consumed_breakfast': calories_meal['breakfast'],
                'calories_consumed_lunch': calories_meal['lunch'],
                'calories_consumed_dinner': calories_meal['dinner'],
                'calories_consumed_snacks': calories_meal['snacks']
            })
            print(f'MFP data per day finished {current_date.strftime("%Y-%m-%d")}')
            current_date += datetime.timedelta(days=1)

def main():
    client = init_mfp()
    start_date = datetime.datetime.strptime('2024-03-16', '%Y-%m-%d')

    get_meal_data(client, start_date)
    get_meal_daily(client, start_date)

if __name__ == "__main__":
    main()
