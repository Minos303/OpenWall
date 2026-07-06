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
from datetime import datetime, timedelta
import time
import streamlit as st
import random
import threading
import dearpygui.dearpygui as dpg
from PIL import Image
import io
import os

seconds_elapsed = []
car_speed = []
car_throttle = []
car_brake = []
car_rpm = []
car_gear = []
data_index = []


team_data = {
    "Mercedes": [0, 210, 190, 255],
    "Red_Bull_Racing": [0, 71, 129, 215],
    "Ferrari": [220, 0, 0, 255],
    "McLaren": [255, 135, 0, 255],
    "Alpine": [0, 0, 255, 255],
    "Aston_Martin": [0, 128, 0, 255],
    "Alfa_Romeo": [128, 0, 0, 255],
    "Haas": [128, 128, 128, 255],
    "AlphaTauri": [0, 128, 128, 255],
    "Williams": [0, 0, 128, 255],
    "Cadillac": [128, 0, 128, 255],
}


track_x = []
track_y = []
driver_x = [0]
driver_y = [0]
location_data = []

max_history_points = 100 
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

current_track_flag = "CLEAR"
latest_race_message = "No messages"
line_color = [255, 30, 0, 255]
line_weight = 5.0
time_speed = [0.05, 0.1, 0.15, 0.2, 0.4, 0.8, 2, 20, 200, 2000]
speed_index = 1
is_paused = False
show_all_drivers = False
grid_indices = {}
track_color = [90, 90, 90, 255]



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
        print("Invalid Driver") 
        return None
    meeting_key = meeting_response.json()[0]["meeting_key"]
    session_params = {"meeting_key": meeting_key, "session_name": session_name}
    session_response = requests.get(f"{BASE_URL}/sessions", params=session_params)
    if session_response.status_code == 404 or not session_response.json():
        print("Invalid Driver") 
        return None
    return  session_response.json()[0]["session_key"]



def jump_to_lap_callback(sender, app_data):
    global data_index, seconds_elapsed, car_speed, car_throttle, car_brake, car_rpm, car_gear, time_counter
    selected_lap_num = int(app_data.split()[-1])
    target_start_time = None
    for lap in processed_laps:
        if lap['number'] == selected_lap_num:
            target_start_time = lap['start']
            break
    if target_start_time:
        seconds_elapsed.clear()
        car_speed.clear()
        car_throttle.clear()
        car_brake.clear()
        car_rpm.clear()
        car_gear.clear()
    for idx, frame in enumerate(data_point):
            frame_time = datetime.fromisoformat(frame['date'])
            if frame_time >= target_start_time:
                data_index = idx
                time_counter = (frame_time - datetime.fromisoformat(data_point[starting_index]['date'])).total_seconds()
                break

def stream_data():
    global time_counter, data_index, driver_x, driver_y

    current_render_x = 0.0
    current_render_y = 0.0

    

    while data_index < len(data_point):
        frame_start = time.perf_counter()
        while is_paused:
            time.sleep(0.1)
            if not dpg.is_dearpygui_running():
                return
            frame_start = time.perf_counter()
            
        next_speed_value = data_point[data_index].get('speed') or 0
        next_throttle_value = data_point[data_index].get('throttle') or 0
        next_brake_value = data_point[data_index].get('brake') or 0
        next_gear_value = data_point[data_index].get('n_gear') or 0  
        next_rpm_value = data_point[data_index].get('rpm') or 0

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

        current_frame_time = datetime.fromisoformat(data_point[data_index]['date'])
        current_lap_num = "OUT"
        for lap in processed_laps:
            if lap['start'] <= current_frame_time <= lap['end']:
                current_lap_num = lap['number']
                break
            
        dpg.set_value("Speed_series_tag", [seconds_elapsed, car_speed])
        dpg.set_value("Throttle_series_tag", [seconds_elapsed, car_throttle])
        dpg.set_value("Brake_series_tag", [seconds_elapsed, car_brake])
        dpg.set_value("rpm_series_tag", [seconds_elapsed, car_rpm])
        dpg.set_value("Gear_series_tag", [seconds_elapsed, car_gear])
        dpg.set_value("lap_indicator_tag", f"Lap: {current_lap_num}")

        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")
        dpg.fit_axis_data("throttle_x_axis")
        dpg.fit_axis_data("brake_x_axis")
        dpg.fit_axis_data("rpm_x_axis")
        dpg.fit_axis_data("gear_x_axis")

        current_frame_time = datetime.fromisoformat(data_point[data_index]['date'])
        current_lap_num = "OUT"
        for lap in processed_laps:
            if lap['start'] <= current_frame_time <= lap['end']:
                current_lap_num = lap['number']
                break
        closest_match = min(
            loc_data_point,
            key=lambda item: abs(datetime.fromisoformat(item['date']) - current_frame_time)
        )
        if data_index < len(data_point) and data_index < len(loc_data_point):
            target_x = closest_match['x']
            target_y = closest_match['y']
            if current_render_x == 0.0 and current_render_y == 0.0:
                current_render_x = target_x
                current_render_y = target_y
            if time_speed[speed_index] >= 0.8:
                steps = 1
            else:
                steps = 5
            lerp_factor = 0.35

            for _ in range(steps):
                current_render_x += (target_x - current_render_x) * lerp_factor
                current_render_y += (target_y - current_render_y) * lerp_factor
                driver_x = [current_render_x]
                driver_y = [current_render_y]
                dpg.set_value("driver_location_tag", [driver_x, driver_y])
                time.sleep(0.005)
            if show_all_drivers:
                for drv, locs in grid_locations.items():
                    if locs:
                        closest_drv_match = min(locs, key=lambda item: abs(datetime.fromisoformat(item['date']) - current_frame_time))
                        dpg.set_value(f"grid_location_tag_{drv}", [[closest_drv_match['x']], [closest_drv_match['y']]])
                        dpg.set_value(f"annotation_tag_{drv}", [closest_drv_match['x'], closest_drv_match['y']])



        data_index += 1

        multiplier = time_speed[speed_index] / 0.2
        target_frame_duration = 0.2 / multiplier
        elapsed_time = time.perf_counter() - frame_start
        time_left_to_sleep = target_frame_duration - elapsed_time
        if time_left_to_sleep > 0:
            time.sleep(time_left_to_sleep)
        




def set_team(Red_Bull_Racing):
    User_Driver_Team = driver_team

def fetch_race_control(session_key):
    global current_track_flag, latest_race_message
    race_control_url = "https://api.openf1.org/v1/race_control"
    params = {"session_key": session_key}
    while dpg.is_dearpygui_running():
        try:
            response = requests.get(race_control_url, params=params, timeout=5)
            if response.status_code == 200 and response.json():
                events = response.json()
                latest_event = events[-1]
                current_track_flag = latest_event.get("flag") or "CLEAR"
                latest_race_message = latest_event.get("message") or "No messages"
                dpg.set_value("flag_text_tag", f"Current Flag: {current_track_flag}")
                dpg.set_value("message_text_tag", f"Latest Notice: {latest_race_message}")
                flag_colors = {
                    "RED": [255, 0, 0, 255],
                    "YELLOW": [255, 255, 0, 255],
                    "GREEN": [0, 255, 0, 255],
                    "BLUE": [0, 100, 255, 255],
                    "BLACK AND WHITE": [220, 220, 220, 255]
                }
                chosen_color = flag_colors.get(current_track_flag, [255, 255, 255, 255])
                dpg.configure_item("flag_text_tag", color=chosen_color)
        except Exception as e:
            pass
        time.sleep(4)

def speed_up():
    global speed_index
    if speed_index < len(time_speed) - 1:
        speed_index += 1
        multiplier = time_speed[speed_index] / 0.2
        dpg.set_value("speed_indicator_tag", f"Speed: {multiplier:.2f}x")

def slow_down():
    global speed_index
    if speed_index > 0:
        speed_index -= 1
        multiplier = time_speed[speed_index] / 0.2
        dpg.set_value("speed_indicator_tag", f"Speed: {multiplier:.2f}x")

def pause_playback():
    global is_paused
    is_paused = True

def resume_playback():
    global is_paused
    is_paused = False

def toggle_grid_view():
    global show_all_drivers
    show_all_drivers = not show_all_drivers
    for drv in grid_locations.keys():
        dpg.configure_item(f"grid_location_tag_{drv}", show=show_all_drivers)
        dpg.configure_item(f"annotation_tag_{drv}", show=show_all_drivers)
    if not show_all_drivers:
        dpg.set_value("grid_location_tag", [[], []])
        for drv in grid_locations.keys():
            dpg.set_value(f"grid_location_tag_{drv}", [[], []])



# User Input
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

# Generate session key
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
driver_url = data_driver[0]['headshot_url']




team_url = urllib.parse.quote(driver_team)

print(f"Driver Name: {driver_name} {driver_surname}")
print(f"Driver Acronym: {driver_acronym}")
print(f"Driver Number: {user_driver}")
print(f"Current Standings: {driver_standing}")
print(f"Current Team: {driver_team}")
print(driver_url)


if " " in driver_team:
    driver_team = driver_team.replace(" ", "_")
    print(f"Driver Team: {driver_team}")
else: 
    print(f"Driver Team: {driver_team}")

set_team_name = team_data[driver_team]

response = requests.get(driver_url)
img = Image.open(io.BytesIO(response.content)).convert("RGBA")
width, height = img.size
pixel_data = [x / 255.0 for pixel in img.getdata() for x in pixel]


response = urlopen(f'https://api.openf1.org/v1/championship_teams?session_key={key}&team_name={team_url}')
data_team = json.loads(response.read().decode('utf-8'))

team_standing = data_team[0]['position_current']
print(f"Current Team Standings: {team_standing}")


try:
    lap_response = urlopen(f'https://api.openf1.org/v1/laps?session_key={key}&driver_number={user_driver}&lap_number<=2')
    lap_data = json.loads(lap_response.read().decode('utf-8'))
    
    if lap_data:
        lap_data_sorted = sorted(lap_data, key=lambda x: x.get('lap_number', 999))
        date = lap_data_sorted[0].get('date_start') or lap_data_sorted[0].get('date')
        if date:
            print(f"Lap One: {date}")
        else:
            raise ValueError("No valid timestamp")
    else:
        raise ValueError("API empty")
except Exception as e:
    print("Lap search bypassed")
    response = urlopen(f'https://api.openf1.org/v1/car_data?driver_number={user_driver}&session_key={key}')
    current_data = json.loads(response.read().decode('utf-8'))
    date = current_data[0]['date']
    print(f"Lap one missing, error 2")
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

full_loc_url = f"https://api.openf1.org/v1/location?{query_string}"
loc_response = urlopen(full_loc_url)
raw_loc_data_point = json.loads(loc_response.read().decode('utf-8'))


loc_data_point = [
    frame for frame in raw_loc_data_point
    if frame.get('x') is not None and frame.get('y') is not None
    and frame['x'] != 0 and frame['y'] != 0

]
laps_response = urlopen(f'https://api.openf1.org/v1/laps?session_key={key}&driver_number={user_driver}')
all_laps = json.loads(laps_response.read().decode('utf-8'))
processed_laps = []
for lap in all_laps:
    if lap.get('date_start') and lap.get('lap_duration'):
        start_dt = datetime.fromisoformat(lap['date_start'])
        end_dt = start_dt + timedelta(seconds=lap['lap_duration'])
        processed_laps.append({
            'number': lap['lap_number'],
            'start': start_dt,
            'end': end_dt
        })


print (f"Downloading Full Grid Data...")
all_drivers_response = urlopen(f'https://api.openf1.org/v1/drivers?session_key={key}')
all_drivers_data = json.loads(all_drivers_response.read().decode('utf-8'))

grid_locations = {}
grid_colors = {}
grid_names = {}
for drv_info in all_drivers_data:
    drv_num = drv_info['driver_number']
    if drv_num == user_driver:
        continue
    drv_team = drv_info['team_name'].replace(" ", "_")
    drv_color = team_data.get(drv_team, [255, 255, 255, 255])
    grid_colors[drv_num] = drv_color
    grid_names[drv_num] = drv_info.get('name_acronym', f"DRV {drv_num}")
    drv_params = {
        "driver_number": drv_num,
        "session_key": key,
        "date>": dt_date.isoformat(),
        "date<": (dt_date + timedelta(minutes=90)).isoformat()
    }
    drv_query = urllib.parse.urlencode(drv_params)
    
    try:
        drv_response = urlopen(f"https://api.openf1.org/v1/location?{drv_query}")
        drv_loc_data = json.loads(drv_response.read().decode('utf-8'))
        
        valid_locs = [
            f for f in drv_loc_data 
            if f.get('x') is not None and f.get('y') is not None and f['x'] != 0
        ]
        if valid_locs:
            for f in valid_locs:
                f['dt.obj'] = datetime.fromisoformat(f['date'])
            grid_locations[drv_num] = valid_locs
    except Exception as e:
        pass
grid_indices = {drv: 0 for drv in grid_locations.keys()}













seen_cords = set()
for frame in loc_data_point:
    rounded_cord = (round(frame['x'], 0), round(frame['y'], 0))
    if rounded_cord not in seen_cords:
        seen_cords.add(rounded_cord)
        track_x.append(frame['x'])
        track_y.append(frame['y'])

x_min, x_max = min(track_x), max(track_x)
y_min, y_max = min(track_y), max(track_y)
x_range, y_range = x_max - x_min, y_max - y_min
max_range = max(x_range, y_range)

x_center, y_center = (x_min + x_max) / 2, (y_min + y_max) / 2
map_x_limits = (x_center - max_range / 2, x_center + max_range / 2)
map_y_limits = (y_center - max_range / 2, y_center + max_range / 2)

dpg.create_context()

with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [0, 0, 0, 255])
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, [255, 30, 0, 255])
        dpg.add_theme_color(dpg.mvPlotCol_PlotBorder, [50, 50, 50, 255])
        

with dpg.theme() as speed_line_theme:
    with dpg.theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line, line_color, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, line_weight, category=dpg.mvThemeCat_Plots)
with dpg.theme() as throttle_line_theme:
    with dpg.theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line, line_color, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, line_weight, category=dpg.mvThemeCat_Plots)
with dpg.theme() as brake_line_theme:
    with dpg.theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line, line_color, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, line_weight, category=dpg.mvThemeCat_Plots)
with dpg.theme() as gear_line_theme:
    with dpg.theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line, line_color, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, line_weight, category=dpg.mvThemeCat_Plots)
with dpg.theme() as rpm_line_theme:
    with dpg.theme_component(dpg.mvLineSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line, line_color, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, line_weight, category=dpg.mvThemeCat_Plots)
dpg.bind_theme(global_theme)
with dpg.theme() as track_theme:
    with dpg.theme_component(dpg.mvScatterSeries):
        dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, track_color, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, track_color, category=dpg.mvThemeCat_Plots)



with dpg.theme() as driver_dot_theme:
    with dpg.theme_component(dpg.mvScatterSeries):
        dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 12.0, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, set_team_name, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, set_team_name, category=dpg.mvThemeCat_Plots)
for drv, color in grid_colors.items():
    if drv in grid_locations:
        with dpg.theme(tag=f"theme_driver_{drv}"):
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 5.0, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, color, category=dpg.mvThemeCat_Plots)

with dpg.texture_registry():
    texture_id = dpg.add_dynamic_texture(width, height, pixel_data, tag="driver_headshot_texture")





with dpg.window(label="Stream playback", tag="main_window" ):
    with dpg.child_window(height = 220, border=True, tag="Profile Card"):
        with dpg.group(horizontal=True):
            dpg.add_image("driver_headshot_texture", width=180, height=180)
            dpg.add_spacer(width=15)

            with dpg.group():
                dpg.add_text(f"Driver: {driver_name} {driver_surname}", color=[255, 255, 255, 255])
                dpg.add_text(f"Driver Acronym: {driver_acronym} | Driver Number: {user_driver}", color=[255, 255, 255, 255])
                dpg.add_text(f"Team: {driver_team.replace('_', ' ')}", color=set_team_name)
                dpg.add_text(f"Championship Standings: {driver_standing}", color=[255, 255, 255, 255])
                dpg.add_text(f"Team Standings: {team_standing}", color=set_team_name)
            dpg.add_spacer(width=300)
            with dpg.group():
                dpg.add_text("Lap: 1", tag="lap_indicator_tag", color=[255, 0, 0, 255])
                flag_display = dpg.add_text("Current Flag: Fetching...", tag="flag_text_tag", color=[255, 0, 0, 255])
                msg_display = dpg.add_text("Latest Notice: Fetching...", tag="message_text_tag", wrap=400, color=[255, 0, 0, 255])
            dpg.add_spacer(width=300)
            with dpg.group():
                dpg.add_text(f"Session: {user_session}", color=[255, 255, 255, 255])
                dpg.add_text(f"Year: {user_year}", color=[255, 255, 255, 255])
                dpg.add_text(f"Gran Prix: {user_country}", color=[255, 255, 255, 255])

    dpg.add_separator()
    dpg.add_spacer(height=10)


    with dpg.child_window(height = 110, border=True, tag="Controls"):
        with dpg.group(horizontal=True):
            dpg.add_button(label="Pause", callback=pause_playback)
            dpg.add_button(label="Resume", callback=resume_playback)
            dpg.add_button(label="Exit", callback=lambda: dpg.stop_dearpygui())
            dpg.add_button(label="<<", callback=lambda: slow_down())
            dpg.add_button(label=">>", callback=lambda: speed_up())
            dpg.add_text("Speed: 1x", tag="speed_indicator_tag", color=[255, 255, 255, 255])
            lap_options = [f"Lap {lap['number']}" for lap in processed_laps]
            dpg.add_combo(items=lap_options, label="Jump to Lap", callback=jump_to_lap_callback, width=150)
            dpg.add_button(label="Toggle Full Grid", callback=toggle_grid_view)

    dpg.add_separator()
    dpg.add_spacer(height=10)


    
    with dpg.plot(label="Track Map", height=1140, width = -1, tag="track_series_tag"):
        map_x = dpg.add_plot_axis(dpg.mvXAxis, no_tick_labels=True)
        map_y = dpg.add_plot_axis(dpg.mvYAxis, no_tick_labels=True)
        dpg.set_axis_limits(map_x, map_x_limits[0], map_x_limits[1])
        dpg.set_axis_limits(map_y, map_y_limits[0], map_y_limits[1])
        dpg.add_scatter_series(track_x, track_y, parent=map_y)
        dpg.add_scatter_series([], [], parent=map_y, tag="grid_location_tag")
        dpg.add_scatter_series(driver_x, driver_y, parent=map_y, tag="driver_location_tag")
        dpg.bind_item_theme("driver_location_tag", driver_dot_theme)
        dpg.bind_item_theme("track_series_tag", track_theme)
        for drv in grid_locations.keys():
            tag_name = f"grid_location_tag_{drv}"
            dpg.add_scatter_series([], [], parent=map_y, tag=tag_name, label=grid_names[drv])
            dpg.bind_item_theme(tag_name, f"theme_driver_{drv}")
            dpg.add_plot_annotation(label=grid_names[drv], default_value=[0.0, 0.0], offset=[10.0, -10.0], tag=f"annotation_tag_{drv}", parent="track_series_tag")
        dpg.bind_item_theme("driver_location_tag", driver_dot_theme)
        dpg.bind_item_theme("track_series_tag", track_theme)
    

    with dpg.plot(label="Speed Playback", height=380, width=-1):
        dpg.add_plot_legend()
    
        dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Speed (km/h)", tag="y_axis")
        dpg.set_axis_limits("y_axis", -10, 350)
        dpg.add_line_series(
            seconds_elapsed, 
            car_speed, 
            label="Speed", 
            parent="y_axis", 
            tag="Speed_series_tag"
            )
    with dpg.table(header_row=False, width=-1, policy=dpg.mvTable_SizingStretchProp):
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            with dpg.plot(label="Throttle Playback", height=380, width=-1):
                dpg.add_plot_legend()
                
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="throttle_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Throttle Value (%)", tag="throttle_y_axis")
                dpg.set_axis_limits("throttle_y_axis", -5, 105)
                dpg.add_line_series(
                    seconds_elapsed, 
                    car_throttle, 
                    label="Throttle", 
                    parent="throttle_y_axis", 
                    tag="Throttle_series_tag"
                )
            with dpg.plot(label="Brake Playback", height=380, width=-1):
                dpg.add_plot_legend()
                
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="brake_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Brake Value (%)", tag="Brake_y_axis")
                dpg.set_axis_limits("Brake_y_axis", -10, 105)
                dpg.add_line_series(
                    seconds_elapsed, 
                    car_brake, 
                    label="Brake", 
                    parent="Brake_y_axis", 
                    tag="Brake_series_tag"
                )
        with dpg.table_row():
            with dpg.plot(label="rpm Playback", height=380, width=-1):
                dpg.add_plot_legend()
                
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="rpm_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="RPM", tag="rpm_y_axis")
                dpg.set_axis_limits("rpm_y_axis", -10, 15100)
                dpg.add_line_series(
                    seconds_elapsed, 
                    car_rpm, 
                    label="RPM", 
                    parent="rpm_y_axis", 
                    tag="rpm_series_tag"
                )
            with dpg.plot(label="Gear Playback", height=380, width=-1):
                dpg.add_plot_legend()
                
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="gear_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Gear", tag="gear_y_axis")
                dpg.set_axis_limits("gear_y_axis", -1, 9)
                dpg.add_line_series(
                    seconds_elapsed, 
                    car_gear, 
                    label="Gear", 
                    parent="gear_y_axis", 
                    tag="Gear_series_tag"
                )

                













print("Data Downloaded. Processing...")



log_time=""

launch_index = 0
for index, frame in enumerate(data_point):
    if frame["speed"] > 0:
        launch_index = index
        break

starting_index = max(0, launch_index - 50)
time_legnth = 10000

print("Race data about to start, Press CTRL+C to exit")
time.sleep(5) 

dpg.create_viewport(title='Open Wall')
dpg.setup_dearpygui()
dpg.set_global_font_scale(2)
dpg.show_viewport()
dpg.maximize_viewport()

data_index = starting_index
playback_thread = threading.Thread(target=stream_data, daemon=True)
playback_thread.start()

race_monitor_thread = threading.Thread(target=fetch_race_control, args=(key,), daemon=True)
race_monitor_thread.start()

dpg.bind_item_theme("Speed_series_tag", speed_line_theme)
dpg.bind_item_theme("Throttle_series_tag", throttle_line_theme)
dpg.bind_item_theme("Brake_series_tag", brake_line_theme)
dpg.bind_item_theme("rpm_series_tag", rpm_line_theme)
dpg.bind_item_theme("Gear_series_tag", gear_line_theme)

dpg.set_primary_window("main_window", True)
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()

dpg.destroy_context()




# for i in range(starting_index, time_legnth):
#      seperate_value = data_point[i]
#      current_time_raw = seperate_value['date']
#      try:
#          clean_time = datetime.fromisoformat(current_time_raw).strftime("%H:%M:%S.%f")[:-3]
#      except Exception:
#          clean_time = current_time_raw

#      seperate_value = data_point[i]
#      current_speed = seperate_value['speed']
#      current_gear = seperate_value['n_gear']
#      current_throttle = seperate_value['throttle']
#      current_brake = seperate_value['brake']
#      current_rpm = seperate_value['rpm']
    
#      speed_history_list.append(current_speed)
#      print(f"Time: {clean_time}| Speed: {current_speed}kph Gear: {current_gear} Throttle: {current_throttle}% Brake: {current_brake}% Rpm: {current_rpm}")

#      if len(speed_history_list) > 0:
#          speed_history_list.pop(0)

time.sleep(0.1)












