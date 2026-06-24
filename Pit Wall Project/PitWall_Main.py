#Day 2

#Update Github:
#git add .
#git commit -m "Update project files"
#git push origin main


#Download from Github
#cd OpenWall
#git pull origin main

#Linux Run: python "Pit Wall Project/PitWall_Main.py"

#Create Virtual Environment: 
# python -m venv venv
# source venv/bin/activate.fish



import requests
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
import json
import urllib.parse
import urllib.request
from pick import pick
import tkinter
import customtkinter
import tkinter as tk
import customtkinter as ctk  



user_country = ""
user_year = ""
user_session = ""
user_driver = ""
user_team = ""

country_selection = ""
year_selection = ""
session_selection = ""

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

Intro_app = customtkinter.CTk()
Intro_app.title("F1 Pit Wall App")
Intro_app.geometry("400x300")

title = customtkinter.CTkLabel(Intro_app, text="Open Pit Wall")
title.pack(pady=10, padx=10)

def user_country_dropdown(country_selection):
    user_country = country_selection
    print(f"Selected Country: {user_country}")

def user_year_dropdown(year_selection):
    user_year = year_selection
    print(f"Selected Year: {user_year}")

def user_session_dropdown(session_selection):
    user_session = session_selection
    print(f"Selected Session: {user_session}")

def submit_button():
    user_country = country_dropdown_widget.get()
    user_year = year_dropdown_widget.get()
    user_session = session_dropdown_widget.get()
    print(f"Session Selected: {user_country}, {user_session}, {user_year}")

country_dropdown_widget = ctk.CTkOptionMenu(
    Intro_app,
    values=["Sakhir", "Jeddah", "Melbourne", "Baku", "Miami", "Imola", "Monte Carlo", "Catalunya", "Montreal", "Spielberg", "Silverstone", "Hungaroring", "Spa-Francorchamps", "Zandvoort", "Monza", "Singapore", "Suzuka", "Lusail", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Yas Marina Circuit"],
    command=user_country_dropdown
)
country_dropdown_widget.pack(pady=10, padx=10)
country_dropdown_widget.set("Sakhir")

year_dropdown_widget = ctk.CTkOptionMenu(
    Intro_app,
    values=["2020", "2021", "2022", "2023"],
    command=user_year_dropdown
)
year_dropdown_widget.pack(pady=10, padx=10)
year_dropdown_widget.set("2022")

session_dropdown_widget = ctk.CTkOptionMenu(
    Intro_app,
    values=["Qualifying", "Race", "Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Sprint Race"],
    command=user_session_dropdown
)
session_dropdown_widget.pack(pady=10, padx=10)
session_dropdown_widget.set("Race")

button = ctk.CTkButton(Intro_app, text="Next", command=submit_button)
button.pack(pady=10, padx=10)





def get_session_key(year, circuit_short_name, session_name):
    BASE_URL = "https://api.openf1.org/v1"
    meeting_params = {"year": year, "circuit_short_name": circuit_short_name}
    meeting_response = requests.get(f"{BASE_URL}/meetings", params=meeting_params)
    if meeting_response.status_code == 404 or not meeting_response.json():
        print("Error 23") #For future notice error 23 means that the meeting parameters did not return any results. This is likely due to a mismatch between the user input and the API database. Please ensure that the circuit name is correct and matches the API's expected format.
        return None
    meeting_key = meeting_response.json()[0]["meeting_key"]
    session_params = {"meeting_key": meeting_key, "session_name": session_name}
    session_response = requests.get(f"{BASE_URL}/sessions", params=session_params)
    if session_response.status_code == 404 or not session_response.json():
        print("Error 86") #For future notice error 86 means that the session parameters did not return any results after sending the meeting key. This is likely due to a mismatch between the user input and the API database. Please ensure that the session name is correct and matches the API's expected format.
        return None
    return  session_response.json()[0]["session_key"]


gui_true = input("Do you want to use the GUI? (y/n): ")
if gui_true == "y":
    Intro_app.mainloop()

else:
#User Input
    selection_country = ["Sakhir", "Jeddah", "Melbourne", "Baku", "Miami", "Imola", "Monte Carlo", "Catalunya", "Montreal", "Spielberg", "Silverstone", "Hungaroring", "Spa-Francorchamps", "Zandvoort", "Monza", "Singapore", "Suzuka", "Lusail", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Yas Marina Circuit"]
    user_country, index = pick(selection_country, "Select the Gran Prix: ")
    print(f"Gran Prix: {user_country} (index: {index})")


    selection_year = ["2020", "2021", "2022", "2023", "2024"]
    user_year, index = pick(selection_year, "Select the Gran Prix: ")
    print(f"Gran Prix: {user_year} (index: {index})")


    selection_session = ["Qualifying", "Race", "Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Sprint Race"]
    user_session, index = pick(selection_session, "Select the Gran Prix: ")
    print(f"Gran Prix: {user_session} (index: {index})")


    user_driver = input("Enter the driver number: ")
    print (f"Session Selected:{user_country}, {user_session}, {user_year}, {user_driver}")
    print (f"Grabbing Key...")

#Generate session key
    key = get_session_key(user_year, user_country, user_session)
    print (f"Target Session Key: {key}")

    response = urlopen(f'https://api.openf1.org/v1/championship_drivers?session_key={key}&driver_number={user_driver}')
    data = json.loads(response.read().decode('utf-8'))


    response_driver = urlopen(f'https://api.openf1.org/v1/drivers?driver_number={user_driver}&session_key={key}')
    data_driver = json.loads(response_driver.read().decode('utf-8'))


    driver_name = data_driver[0]['first_name']
    driver_surname = data_driver[0]['last_name']
    driver_acronym = data_driver[0]['name_acronym']
    driver_standing = data[0]['position_current']
    driver_team = data_driver[0]['team_name']

    team_url = urllib.parse.quote(driver_team)

    print(f"Driver Name: {driver_name} {driver_surname}")
    print(f"Driver Acronym: {driver_acronym}")
    print(f"Driver Number: {user_driver}")
    print(f"Current Standings: {driver_standing}")
    print(f"Current Team: {driver_team}")

    response = urlopen(f'https://api.openf1.org/v1/championship_teams?session_key={key}&team_name={team_url}')
    data_team = json.loads(response.read().decode('utf-8'))

    team_standing = data_team[0]['position_current']
    print(f"Current Team Standings: {team_standing}")

 




response = urlopen(f'https://api.openf1.org/v1/car_data?driver_number={user_driver}&session_key={key}')
current_data = json.loads(response.read().decode('utf-8'))


date = current_data[0]['date']

response = urlopen(f'https://api.openf1.org/v1/car_data?driver_number=1&session_key=7779&date=2023-03-19T16:01:03.621000+00:00')
current_data = json.loads(response.read().decode('utf-8'))
print(current_data)

