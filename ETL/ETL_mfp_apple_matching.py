import pandas as pd
import pulp
import datetime as dt

def schedule_meals(start_date, food_t_path, items_path, tolerance=2):
    # Import data
    food_t = pd.read_csv(food_t_path, parse_dates=['date', 'time'])
    items = pd.read_csv(items_path, parse_dates=['date'])

    # Filter the data starting from start_date
    food_t = food_t[food_t['date'] >= pd.to_datetime(start_date)]
    items = items[items['date'] >= pd.to_datetime(start_date)]

    # Define preferred meal times
    preferred_times = {'breakfast': 7, 'lunch': 13, 'dinner': 20}

    results_df = pd.DataFrame()
    unique_dates = pd.Series(pd.unique(food_t['date']))
    for current_date in unique_dates:
        daily_food_t = food_t[food_t['date'] == current_date]
        daily_items = items[items['date'] == current_date]
        
        daily_food_t.index = range(len(daily_food_t))
        daily_items.index = range(len(daily_items))
        
        daily_food_t['time_hours'] = daily_food_t['time'].dt.hour

        prob = pulp.LpProblem("FoodScheduling", pulp.LpMinimize)
        x = pulp.LpVariable.dicts("assignment", ((i, j) for i in range(len(daily_items)) for j in range(len(daily_food_t))),
                                  cat=pulp.LpBinary)
        
        # Objective function and constraints
        objective = pulp.lpSum(
            abs(daily_food_t.at[j, 'time_hours'] - preferred_times[daily_items.at[i, 'meal']]) * x[(i, j)]
            for i in range(len(daily_items)) for j in range(len(daily_food_t))
            if daily_items.at[i, 'meal'] in preferred_times
        )
        prob += objective
        for i in range(len(daily_items)):
            prob += pulp.lpSum(x[(i, j)] for j in range(len(daily_food_t))) == 1
        for j in range(len(daily_food_t)):
            prob += pulp.lpSum(x[(i, j)] for i in range(len(daily_items))) >= 1
            total_calories = pulp.lpSum(daily_items.at[i, 'calories'] * x[(i, j)] for i in range(len(daily_items)))
            target_calories = float(daily_food_t.at[j, 'calories'])
            prob += total_calories >= (target_calories - tolerance)
            prob += total_calories <= (target_calories + tolerance)

        prob.solve()
        
        daily_results = []
        for i in range(len(daily_items)):
            for j in range(len(daily_food_t)):
                if x[(i, j)].varValue == 1:
                    daily_results.append({
                        'date': current_date,
                        'food': daily_items.at[i, 'food'],
                        'meal': daily_items.at[i, 'meal'],
                        'time': daily_food_t.at[j, 'time']
                    })

        daily_results_df = pd.DataFrame(daily_results)
        results_df = pd.concat([results_df, daily_results_df], ignore_index=True)

    merged_results = pd.merge(items, results_df, on=['food', 'date', 'meal'], how='left')
    merged_results['time'] = merged_results['time'].dt.time
    merged_results = merged_results[['date', 'meal', 'time', 'food', 'quant', 'calories', 'carbs', 'fat', 'protein', 'sodium', 'sugar']]
    return merged_results

### Main Function

def main():
    output_file = 'Data/Cleaned/MealSchedule.csv'
    food_t_path = 'Data/Cleaned/Food.csv'
    items_path = 'Data/Cleaned/MFP meals scrapped.csv'
    
    try:
        existing_data = pd.read_csv(output_file)
        existing_data['date'] = pd.to_datetime(existing_data['date'])
        latest_date = existing_data['date'].max()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        latest_date = '2024-03-16'  # Default start date if file is not found or empty

    start_date = latest_date + pd.Timedelta(days=1)  # Increment one day to avoid duplication

    # Get the scheduled meals DataFrame for incremental dates
    scheduled_meals = schedule_meals(start_date, food_t_path, items_path)

    # Delete existing entries from start_date onwards and append new results
    updated_data = pd.concat([existing_data[existing_data['date'] < start_date], scheduled_meals], ignore_index=True)
    updated_data.to_csv(output_file, index=False)
    print(f"Incremental meal scheduling results updated and saved to '{output_file}'")

if __name__ == "__main__":
    main()
