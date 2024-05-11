# Import necessary modules and functions
import os, datetime
import ETL
from ETL.ETL_garmin_api import init_garmin, get_garmin_data
from ETL.ETL_whoop import init_whoop, get_sleep_recovery_data
from ETL.ETL_mfp_api import init_mfp, get_meal_data, get_meal_daily

def main():
    
    ### Update everything that works directly through APIs ###

    # Load environment variables 
    email_g = os.getenv("USERNAME_G")
    password_g = os.getenv("PASSWORD_G")
    email_w = os.getenv("USERNAME_W")
    password_w = os.getenv("PASSWORD_W")

    # Garmin API update
    garmin_client = init_garmin(email_g, password_g)
    get_garmin_data(garmin_client)

    # Whoop API update
    whoop_client = init_whoop(email_w, password_w)
    get_sleep_recovery_data(whoop_client)

    # MyFitnessPal API update
    mfp_client = init_mfp()
    start_date = datetime.datetime.strptime('2024-03-16', '%Y-%m-%d')
    end_date = datetime.datetime.now() - datetime.timedelta(days=1)
    get_meal_data(mfp_client, start_date, end_date)
    get_meal_daily(mfp_client, start_date, end_date)
    
    print("Garmin, Whoop and MFP API data updates completed successfully.")

if __name__ == "__main__":
    main()
