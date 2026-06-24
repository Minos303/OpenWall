#Day 2

#Update Github:
#git add .
#git commit -m "Update project files"
#git push origin main


#Download from Github
#cd OpenWall
#git pull origin main

#Linux Run: python "Pit Wall Project/PitWall_Main.py"


import requests
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
import json
import urllib.parse
import urllib.request
from pick import pick



#For Future Use:
#from pick import pick

#options = ["Option 1", "Option 2", "Option 3"....]

#selection, index = pick(options, "Please select an option: ")

#print(f"You selected: {selection} (index: {index})")





user_country = ""
user_year = ""
user_session = ""
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




#User Input
user_country = ["Sakhir", "Jeddah", "Melbourne", "Baku", "Miami", "Imola", "Monte Carlo", "Catalunya", "Montreal", "Spielberg", "Silverstone", "Hungaroring", "Spa-Francorchamps", "Zandvoort", "Monza", "Singapore", "Suzuka", "Lusail", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Yas Marina Circuit"]
selection, index = pick(user_country, "Select the Gran Prix: ")
print(f"Gran Prix: {selection} (index: {index})")


user_year = ["2020", "2021", "2022", "2023", "2024"]
selection, index = pick(user_year, "Select the Gran Prix: ")
print(f"Gran Prix: {selection} (index: {index})")


user_session = ["Qualifying", "Race", "Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Sprint Race"]
selection, index = pick(user_session, "Select the Gran Prix: ")
print(f"Gran Prix: {selection} (index: {index})")

print (f"Session Selected:{user_country}, {user_session}, {user_year}")
print (f"Grabbing Key...")

#Generate session key
key = get_session_key(user_year, user_country, user_session)
print (f"Target Session Key: {key}")