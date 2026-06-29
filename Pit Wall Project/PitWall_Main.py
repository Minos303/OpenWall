

#Update Github:
#git add .
#git commit -m "Update project files"
#git push origin main


#Download from Github
#cd OpenWall
#git pull origin main

#Linux Run: 
#python -m venv venv
#source venv/bin/activate.fish
#pip install pick requests panda
#python "Pit Wall Project/PitWall_Main.py"





from operator import index


import requests
import urllib.error
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
import json
import urllib.parse
import urllib.request
from pick import pick
import os
from flask import Flask, render_template
import pandas as pd
from datetime import datetime, timedelta
import time
import streamlit as st
import random
import threading
import dearpygui.dearpygui as dpg


seconds_elapsed = []
car_speed = []
car_throttle = []
car_brake = []
car_rpm = []
car_gear = []
data_index = []

max_history_points = 100  # Keep the last 20 seconds of data on screen (100 points / 5Hz)
time_counter = 0.0
data_index = 0



user_country = ""
user_year = ""
user_session = ""
user_driver = ""
user_team = ""

country_selection = ""
year_selection = ""
session_selection = ""
telementary_chart = st.empty()
speed_history_list = []



app = Flask(__name__)

@app.route('/')
def main_dashboard():
    driver = user_driver
    team = user_team
    return render_template('index.html', user_driver=driver, user_team=team)





def get_session_key(year, circuit_short_name, session_name):
    BASE_URL = "https://api.openf1.org/v1"
    meeting_params = {"year": year, "circuit_short_name": circuit_short_name}
    meeting_response = requests.get(f"{BASE_URL}/meetings", params=meeting_params)
    if meeting_response.status_code == 404 or not meeting_response.json():
        print("Invalid Driver") #For future notice error 23 means that the meeting parameters did not return any results. This is likely due to a mismatch between the user input and the API database. Please ensure that the circuit name is correct and matches the API's expected format.
        return None
    meeting_key = meeting_response.json()[0]["meeting_key"]
    session_params = {"meeting_key": meeting_key, "session_name": session_name}
    session_response = requests.get(f"{BASE_URL}/sessions", params=session_params)
    if session_response.status_code == 404 or not session_response.json():
        print("Invalid Driver") #For future notice error 86 means that the session parameters did not return any results after sending the meeting key. This is likely due to a mismatch between the user input and the API database. Please ensure that the session name is correct and matches the API's expected format.
        return None
    return  session_response.json()[0]["session_key"]

def stream_data():
    global time_counter, data_index
    while data_index < len(data_point):
        next_speed_value = data_point[data_index]['speed']
        next_throttle_value = data_point[data_index]['throttle']
        next_brake_value = data_point[data_index]['brake']
        next_gear_value = data_point[data_index]['n_gear']
        next_rpm_value = data_point[data_index]['rpm']

        time_counter += 0.2
        seconds_elapsed.append(time_counter)
        car_speed.append(next_speed_value)
        car_throttle.append(next_throttle_value)
        car_brake.append(next_brake_value)
        car_gear.append(next_gear_value)
        car_rpm.append(next_rpm_value)
        

        if len(seconds_elapsed) > max_history_points:
            seconds_elapsed.pop(0)
            car_speed.pop(0)
            car_gear.pop(0)
            car_brake.pop(0)
            car_rpm.pop(0)
            car_throttle.pop(0)
            

        dpg.set_value("Speed_series_tag", [seconds_elapsed, car_speed])
        dpg.set_value("Throttle_series_tag", [seconds_elapsed, car_throttle])
        # dpg.set_value("Brake_series_tag", [seconds_elapsed, car_brake])
        # dpg.set_value("rpm_series_tag", [seconds_elapsed, car_rpm])
        # dpg.set_value("Gear_series_tag", [seconds_elapsed, car_gear])

        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")
        data_index += 1
        time.sleep(0.2)

dpg.create_context()
with dpg.window(label="Stream playback", width=800, height=500):
    

    with dpg.plot(label="Speed Playback", height=400, width=-1):
        dpg.add_plot_legend()
        
        dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag="y_axis")
        dpg.set_axis_limits("y_axis", -10, 350)
        dpg.add_line_series(
            seconds_elapsed, 
            car_speed, 
            label="Dataset Track 1", 
            parent="y_axis", 
            tag="Speed_series_tag"
        )
    with dpg.plot(label="Throttle Playback", height=400, width=-1):
        dpg.add_plot_legend()
        
        dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="throttle_x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag="throttle_y_axis")
        dpg.set_axis_limits("throttle_y_axis", -5, 100)
        dpg.add_line_series(
            seconds_elapsed, 
            car_throttle, 
            label="Dataset Track 1", 
            parent="throttle_y_axis", 
            tag="Throttle_series_tag"
        )


        





    #User Input

selection_year = ["2023", "2024", "2025", "2026"]
user_year, index = pick(selection_year, "Select the Gran Prix: ")
print(f"Gran Prix: {user_year} (index: {index})")

if (user_year == "2023"):
    selection_country_2023 = ["Sakhir", "Jeddah", "Melbourne", "Baku", "Miami", "Monte Carlo", "Catalunya", "Montreal", "Spielberg", "Silverstone", "Hungaroring", "Spa-Francorchamps", "Zandvoort", "Monza", "Singapore", "Suzuka", "Lusail", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Yas Marina Circuit"]
    user_country_2023, index = pick(selection_country_2023, "Select the Gran Prix: ")
    user_country = user_country_2023

if (user_year == "2024"):
    selection_country_2024 = ["Sakhir", "Jeddah", "Melbourne", "Suzuka", "Shanghai", "Miami", "Imola", "Monte Carlo", "Montreal", "Catalunya", "Spielberg", "Silverstone", "Hungaroring", "Spa-Francorchamps", "Zandvoort", "Monza", "Baku", "Singapore", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Lusail", "Yas Marina Circuit"]
    user_country_2024, index = pick(selection_country_2024, "Select the Gran Prix: ")
    user_country = user_country_2024

if (user_year == "2025"):
    selection_country_2025 = ["Melbourne", "Shanghai", "Suzuka", "Sakhir", "Jeddah", "Miami", "Imola", "Monte Carlo", "Catalunya", "Montreal", "Spielberg", "Silverstone", "Spa-Francorchamps", "Hungaroring", "Zandvoort", "Monza", "Baku", "Singapore", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Lusail", "Yas Marina Circuit"]
    user_country_2025, index = pick(selection_country_2025, "Select the Gran Prix: ")
    user_country = user_country_2025

if (user_year == "2026"):
    selection_country_2026 = ["Melbourne", "Shanghai", "Suzuka", "Sakhir", "Miami", "Montreal", "Madring", "Monte Carlo", "Catalunya", "Spielberg", "Silverstone", "Spa-Francorchamps", "Hungaroring", "Zandvoort", "Monza", "Baku", "Singapore", "Austin", "Mexico City", "Interlagos", "Las Vegas", "Lusail", "Yas Marina Circuit"]
    user_country_2026, index = pick(selection_country_2026, "Select the Gran Prix: ")
    user_country = user_country_2026

print(f"Gran Prix: {user_country} (index: {index})")


if (user_year == "2023") and (user_country_2023 in ["Baku", "Spielberg", "Spa-Francorchamps", "Lusail", "Austin", "Interlagos"]) or (user_year == "2024") and (user_country_2024 in ["Shanghai", "Miami", "Spielberg", "Austin", "Interlagos", "Lusail"]) or (user_year ==  "2025") and (user_country_2025 in ["Shanghai", "Miami", "Spa-Francorchamps", "Austin", "Interlagos", "Lusail"]) or (user_year == "2026") and (user_country_2026 in ["Shanghai", "Miami", "Montreal", "Silverstone", "Zandvoort", "Singapore"]):
    selection_session = ["Qualifying", "Race", "Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Sprint"]
    user_session, index = pick(selection_session, "Select the Gran Prix: ")
    print(f"Gran Prix: {user_session} (index: {index})")
else:
    selection_session = ["Qualifying", "Race", "Practice 1", "Practice 2", "Practice 3"]
    user_session, index = pick(selection_session, "Select the Gran Prix: ")
    print(f"Gran Prix: {user_session} (index: {index})")

selection_driver = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 14, 16, 18, 20, 22, 23, 24, 27, 30, 31, 41, 43, 44, 55, 63, 77, 81, 87]
user_driver, index = pick(selection_driver, "Select the Gran Prix: ")
print(f"Gran Prix: {user_driver} (index: {index})")



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
print (f"{date}")
dt_date = datetime.fromisoformat(date)

bulk_params = {
    "driver_number": user_driver,
    "session_key": key,
    "date>": dt_date.isoformat(),
    "date<": (dt_date + timedelta(minutes=90)).isoformat()
}

print("Downloading Data...")



query_string = urllib.parse.urlencode(bulk_params)

base_url = "https://api.openf1.org/v1/car_data"
full_url = f"{base_url}?{query_string}"
response = urlopen(full_url)
data_point = json.loads(response.read().decode('utf-8'))


print("Data Downloaded. Processing...")

log_time=""

#get_session_key(user_year, user_country, user_session)
#app.run()

launch_index = 0

for index, frame in enumerate(data_point):
    if frame["speed"] > 0:
        launch_index = index
        break

starting_index = max(0, launch_index - 50)

time_legnth = 10000
#print(data_point)

#st.title("Pit Wall Live Dashboard")
#st.write("Driver: {driver_name}")

print("Race data about to start, Press CTR C to exit")
time.sleep(5) 


dpg.create_viewport(title='Data Matrix Visualiser', width=820, height=540)
dpg.setup_dearpygui()
dpg.show_viewport()

data_index = starting_index
data_index = starting_index
playback_thread = threading.Thread(target=stream_data, daemon=True)
playback_thread.start()

dpg.start_dearpygui()
dpg.destroy_context()

for i in range(starting_index, time_legnth):
    seperate_value = data_point[i]
    current_time_raw = seperate_value['date']
    try:
        clean_time = datetime.fromisoformat(current_time_raw).strftime("%H:%M:%S.%f")[:-3]
    except Exception:
        clean_time = current_time_raw


    seperate_value = data_point[i]
    current_speed = seperate_value['speed']
    current_gear = seperate_value['n_gear']
    current_throttle = seperate_value['throttle']
    current_brake = seperate_value['brake']
    current_rpm = seperate_value['rpm']
    
    speed_history_list.append(current_speed)
    print(f"Time: {clean_time}| Speed: {current_speed}kph Gear: {current_gear} Throttle: {current_throttle}% Brake: {current_brake}% Rpm: {current_rpm}")

    if len(speed_history_list) > 0:
        speed_history_list.pop(0)

    #telementary_chart.line_chart(speed_history_list)

time.sleep(0.1) 

