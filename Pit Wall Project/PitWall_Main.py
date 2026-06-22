import requests
import pandas as pd
import matplotlib.pyplot as plt
user_country = ""
user_year = ""
user_session = ""

BASE_URL = "https://openf1.org"

allowed_countries = ["Australia", "Bahrain", "China", "Spain", "Monaco", "Azerbaijan", "Canada", "France", "Austria", "United Kingdom", "Hungary", "Belgium", "Netherlands", "Italy", "Singapore", "Russia", "Japan", "United States", "Mexico", "Brazil", "Abu Dhabi"]
while True: 
    user_country = input("Enter the country of the Grand Prix: ")
    if user_country in allowed_countries:
        break
    #elif user_country == "New Zealand":
        #print("I wish")
    else:
        print("Invalid country. Please enter a valid country from the list.")


allowed_years = ["2020", "2021", "2022", "2023"]
while True: 
    user_year = input("Enter the year of the Grand Prix: ")
    if str(user_year) in allowed_years:
        break
    else:       
        print("Invalid year. Please enter a valid year from the list.")

        
allowed_sessions = ["Qualifying", "Race", "Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Sprint Race"]
while True: 
    user_session = input("Enter the session of the Grand Prix: ")
    if user_session in allowed_sessions:
        break
    else:
        print("Invalid session. Please enter a valid session from the list.")



user_session = input("Enter the session of the Grand Prix: ")
session_url = f"{BASE_URL}/sessions?country_name={user_country}&session_name={user_session}&year={user_year}"
print(session_url)