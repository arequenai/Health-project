from garminconnect import Garmin
email = "requenalberto@gmail.com"
password = "Piensa00G"

api = Garmin(email, password)
api.login()
print("Logged in!")
stats = api.get_stats("2023-01-01")
print(stats)