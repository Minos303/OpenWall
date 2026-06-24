import requests
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
import json
import urllib.parse
import urllib.request
from pick import pick


options = ["Option 1", "Option 2", "Option 3"]

selection, index = pick(options, "Please select an option: ")

print(f"You selected: {selection} (index: {index})")



allowed_countries = ["Sakhir", "Jeddah", "Melbourne", "Baku", "Miami", "Imola", "Monte Carlo", "Catalunya", "Montreal", "Spielberg", "Silverstone", "Hungaroring", "Spa-Francorchamps", "Zandvoort", "Monza", "Singapore", "Suzuka", "Lusail", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Yas Marina Circuit"]
while True: 
    user_country = input("Enter the country of the Grand Prix, type 'help' for a list of valid countries: ")
    if user_country in allowed_countries:
        break
    #elif user_country == "New Zealand":
        #print("I wish")
    elif user_country.lower() == "help":
        print("Valid countries are:")
        for country in allowed_countries:
            print(f"- {country}")
    else:
        print("Invalid country. Please enter a valid country from the list.")



allowed_years = ["2020", "2021", "2022", "2023", "2024"]
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
