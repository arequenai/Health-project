import myfitnesspal
import datetime
import csv
import os
from ETL.ETL_general import get_most_recent_date, delete_data_from_date

def init_mfp():
    """Initialize and return a MyFitnessPal client."""
    return myfitnesspal.Client()

# Function to get meal data from MyFitnessPal and append to a CSV file
def get_meal_data(client, filename):
    end_date = datetime.datetime.now().date()
    most_recent_date = get_most_recent_date(filename)

    # Delete the last day to rewrite it
    delete_data_from_date(filename, most_recent_date)
    start_date = most_recent_date

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
            print(f'{filename}: Data per meal obtained and (re-)written for {current_date.strftime("%Y-%m-%d")}')
            current_date += datetime.timedelta(days=1)

# Function to get daily summary data from MyFitnessPal and append to a CSV file
def get_meal_daily(client, filename):

    end_date = datetime.datetime.now().date()
    most_recent_date = get_most_recent_date(filename)

    # Delete the last day to rewrite it
    delete_data_from_date(filename, most_recent_date)
    start_date = most_recent_date

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
            print(f'{filename}: Data per day obtained and (re-)written for {current_date.strftime("%Y-%m-%d")}')
            current_date += datetime.timedelta(days=1)

def main():

    meals_file = 'Data/Cleaned/MFP meals scrapped.csv'
    meals_daily_file = 'Data/Cleaned/MFP per day scrapped.csv'

    client = init_mfp()
    get_meal_data(client, meals_file)
    get_meal_daily(client, meals_daily_file)

if __name__ == "__main__":
    main()
