import pandas as pd
import pulp
import datetime as dt
from ETL.ETL_general import get_most_recent_date, delete_data_from_date

def schedule_meals(start_date, food_t_path, items_path, tolerance=2):
    # Define custom parser functions using the specified formats
    date_parser = lambda x: pd.to_datetime(x, format='%Y-%m-%d')
    time_parser = lambda x: pd.to_datetime(x, format='%H:%M:%S')

    # Import data using custom parsers
    food_t = pd.read_csv(food_t_path, converters={
        'date': date_parser,
        'time': time_parser
    })
    items = pd.read_csv(items_path, converters={'date': date_parser})

    # Filter the data starting from start_date
    food_t = food_t[food_t['date'] >= pd.to_datetime(start_date)]
    items = items[items['date'] >= pd.to_datetime(start_date)]

    # Define preferred meal times
    preferred_times = {'breakfast': 7, 'lunch': 13, 'dinner': 20}

    results_df = pd.DataFrame()
    unique_dates = pd.Series(pd.unique(food_t['date']))
    for current_date in unique_dates:
        daily_food_t = food_t[food_t['date'] == current_date].copy()  # Explicit copy to avoid SettingWithCopyWarning
        daily_items = items[items['date'] == current_date]
        
        daily_food_t.reset_index(drop=True, inplace=True)
        daily_items.reset_index(drop=True, inplace=True)
        
        # Use .loc to safely assign time_hours without causing SettingWithCopyWarning
        daily_food_t.loc[:, 'time_hours'] = daily_food_t['time'].dt.hour

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

        # Use the PULP_CBC_CMD solver with output suppressed
        solver = pulp.PULP_CBC_CMD(msg=0)
        status = prob.solve(solver)

        print(f"Meal schedule matching: Status on {current_date.date()}: {pulp.LpStatus[status]}")

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

def update_meal_schedule(food_t_path, items_path, output_file):
    # Get the most recent date from the output file
    most_recent_date_output = get_most_recent_date(output_file)
    # Get the most recent date from the input files
    most_recent_food_t = get_most_recent_date(food_t_path)
    most_recent_items = get_most_recent_date(items_path)
    
    # Only perform update if we have input data (at least to redo the last day)
    min_date_input = min(most_recent_food_t, most_recent_items)
    if most_recent_date_output <= min_date_input:
        # Delete from output the last day
        delete_data_from_date(output_file, most_recent_date_output)
        # Calculate from the most recent day (which we just deleted) onwards
        start_date = most_recent_date_output
        scheduled_meals = schedule_meals(start_date, food_t_path, items_path)
        # Append the scheduled meals to the output file
        scheduled_meals.to_csv(output_file, mode='a', header=False, index=False)
        print(f"{output_file}: Incremental meal scheduling results updated and (re-)written from {start_date}")
    else:
        print(f"{output_file}: No new input data to update the meal schedule")

def main():

    import pandas as pd
    ### Main Function
    output_file = 'Data/Cleaned/MealSchedule.csv'
    food_t_path = 'Data/Cleaned/Food.csv'
    items_path = 'Data/Cleaned/MFP meals scrapped.csv'
    
    update_meal_schedule(food_t_path, items_path, output_file)

if __name__ == "__main__":
    main()
