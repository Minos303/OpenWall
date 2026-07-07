import os
import io
import time
import json
import random
import threading
import requests
import urllib.error
import urllib.parse
import urllib.request
from urllib.request import urlopen
from datetime import datetime, timedelta
from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import dearpygui.dearpygui as dpg
from PIL import Image

seconds_elapsed = []
car_speed = []
car_throttle = []
car_brake = []
car_rpm = []
car_gear = []

track_x = []
track_y = []
driver_x = [0]
driver_y = [0]
location_data = []

grid_locations = {}
grid_colors = {}
grid_names = {}
grid_indices = {}
processed_laps = []
data_point = []
loc_data_point = []

max_history_points = 100 
time_counter = 0.0
data_index = 0

user_country = ""
user_year = ""
user_session = "Race"
user_driver = ""
user_team = ""
driver_name = ""
driver_surname = ""
driver_acronym = ""
driver_standing = 0
driver_team = ""
team_standing = 0
width, height = 100, 100  
pixel_data = []
starting_index = 0

current_track_flag = "CLEAR"
latest_race_message = "No messages"
line_color = [255, 30, 0, 255]
line_weight = 5.0
time_speed = [0.05, 0.1, 0.15, 0.2, 0.4, 0.8, 2, 20, 200, 2000]
speed_index = 1
is_paused = False
show_all_drivers = False
track_color = [90, 90, 90, 255]
set_team_name = [255, 255, 255, 255]
map_x_limits = (-1000, 1000)
map_y_limits = (-1000, 1000)

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

app = Flask(__name__)

@app.route('/')
def main_dashboard():
    return render_template('index.html', user_driver=user_driver, user_team=user_team)


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

        if len(loc_data_point) > 0:
            closest_match = min(
                loc_data_point,
                key=lambda item: abs(datetime.fromisoformat(item['date']) - current_frame_time)
            )
            if data_index < len(data_point):
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


dpg.create_context()
dpg.create_viewport(title='Open Wall Configurations', width=1000, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_global_font_scale(2)

setup_complete = False
data_download_started = False
available_sessions_dict = {}
available_drivers_dict = {}
key = None


def year_changed(sender, app_data):
    res = requests.get(f"https://api.openf1.org/v1/meetings?year={app_data}")
    data = res.json()
    countries = []
    for m in data:
        if m['circuit_short_name'] not in countries:
            countries.append(m['circuit_short_name'])
    dpg.configure_item("country_combo", items=countries)
    dpg.set_value("country_combo", "")
    dpg.configure_item("driver_combo", items=[])


def country_changed(sender, app_data):
    global available_drivers_dict, key
    year = dpg.get_value("year_combo")
    res = requests.get(f"https://api.openf1.org/v1/meetings?year={year}&circuit_short_name={app_data}")
    meeting_data = res.json()
    if len(meeting_data) > 0:
        m_key = meeting_data[0]['meeting_key']
        s_res = requests.get(f"https://api.openf1.org/v1/sessions?meeting_key={m_key}")
        s_data = s_res.json()
        
        for s in s_data:
            if s['session_name'].lower() == "race":
                key = s['session_key']
                break
                
        if key:
            res = requests.get(f"https://api.openf1.org/v1/drivers?session_key={key}")
            d_data = res.json()
            available_drivers_dict = {}
            for d in d_data:
                name_str = f"{d['driver_number']} - {d['first_name']} {d['last_name']}"
                available_drivers_dict[name_str] = d['driver_number']
            d_names = list(available_drivers_dict.keys())
            dpg.configure_item("driver_combo", items=d_names)
    dpg.set_value("driver_combo", "")


def async_download_worker():
    global user_year, user_country, user_session, user_driver, setup_complete
    global driver_name, driver_surname, driver_acronym, driver_standing, driver_team, team_standing
    global width, height, pixel_data, set_team_name, data_point, loc_data_point, processed_laps, starting_index
    global map_x_limits, map_y_limits, track_x, track_y
    
    try:
        dpg.configure_item("load_btn", label="Fetching Driver Standing...")
        try:
            response = urlopen(f'https://api.openf1.org/v1/championship_drivers?session_key={key}&driver_number={user_driver}')
            data = json.loads(response.read().decode('utf-8'))
            driver_standing = data[0]['position_current'] if data else 0
        except Exception:
            driver_standing = 0

        dpg.configure_item("load_btn", label="Fetching Profile Registry...")
        response_driver = urlopen(f'https://api.openf1.org/v1/drivers?driver_number={user_driver}&session_key={key}')
        data_driver = json.loads(response_driver.read().decode('utf-8'))

        driver_name = data_driver[0]['first_name']
        driver_surname = data_driver[0]['last_name']
        driver_acronym = data_driver[0]['name_acronym']
        driver_team = data_driver[0]['team_name']
        driver_url = data_driver[0]['headshot_url']
        team_url = urllib.parse.quote(driver_team)

        if " " in driver_team:
            driver_team = driver_team.replace(" ", "_")
        set_team_name = team_data.get(driver_team, [255, 255, 255, 255])

        dpg.configure_item("load_btn", label="Downloading Profile Avatar...")
        res_img = requests.get(driver_url)
        img = Image.open(io.BytesIO(res_img.content)).convert("RGBA")
        width, height = img.size
        try:
            pixel_data = [x / 255.0 for pixel in img.get_flattened_data() for x in pixel]
        except AttributeError:
            pixel_data = [x / 255.0 for pixel in list(img.getdata()) for x in pixel]

        dpg.configure_item("load_btn", label="Fetching Constructing Standings...")
        try:
            response = urlopen(f'https://api.openf1.org/v1/championship_teams?session_key={key}&team_name={team_url}')
            data_team = json.loads(response.read().decode('utf-8'))
            team_standing = data_team[0]['position_current'] if data_team else 0
        except Exception:
            team_standing = 0

        dpg.configure_item("load_btn", label="Locating Lap Datestamps...")
        try:
            lap_response = urlopen(f'https://api.openf1.org/v1/laps?session_key={key}&driver_number={user_driver}&lap_number<=2')
            lap_data = json.loads(lap_response.read().decode('utf-8'))
            if lap_data:
                lap_data_sorted = sorted(lap_data, key=lambda x: x.get('lap_number', 999))
                date = lap_data_sorted[0].get('date_start') or lap_data_sorted[0].get('date')
                if not date: raise ValueError()
            else: raise ValueError()
        except Exception:
            response = urlopen(f'https://api.openf1.org/v1/car_data?driver_number={user_driver}&session_key={key}')
            current_data = json.loads(response.read().decode('utf-8'))
            date = current_data[0]['date']
        dt_date = datetime.fromisoformat(date)

        bulk_params = {
            "driver_number": user_driver,
            "session_key": key,
            "date>": dt_date.isoformat(),
            "date<": (dt_date + timedelta(minutes=45)).isoformat() 
        }

        dpg.configure_item("load_btn", label="Downloading Car Telemetry...")
        query_string = urllib.parse.urlencode(bulk_params)
        base_url = "https://api.openf1.org/v1/car_data"
        response = urlopen(f"{base_url}?{query_string}")
        data_point = json.loads(response.read().decode('utf-8'))

        dpg.configure_item("load_btn", label="Downloading Track Arrays...")
        loc_response = urlopen(f"https://api.openf1.org/v1/location?{query_string}")
        raw_loc_data_point = json.loads(loc_response.read().decode('utf-8'))
        loc_data_point = [f for f in raw_loc_data_point if f.get('x') is not None and f.get('y') is not None and f['x'] != 0 and f['y'] != 0]

        dpg.configure_item("load_btn", label="Synchronizing Lap Intervals...")
        laps_response = urlopen(f'https://api.openf1.org/v1/laps?session_key={key}&driver_number={user_driver}')
        all_laps = json.loads(laps_response.read().decode('utf-8'))
        for lap in all_laps:
            if lap.get('date_start') and lap.get('lap_duration'):
                start_dt = datetime.fromisoformat(lap['date_start'])
                processed_laps.append({
                    'number': lap['lap_number'],
                    'start': start_dt,
                    'end': start_dt + timedelta(seconds=lap['lap_duration'])
                })

        dpg.configure_item("load_btn", label="Mapping Entire Grid...")
        all_drivers_response = urlopen(f'https://api.openf1.org/v1/drivers?session_key={key}')
        all_drivers_data = json.loads(all_drivers_response.read().decode('utf-8'))

        for drv_info in all_drivers_data[:12]: 
            drv_num = drv_info['driver_number']
            if drv_num == user_driver: continue
            drv_team = drv_info['team_name'].replace(" ", "_")
            grid_colors[drv_num] = team_data.get(drv_team, [255, 255, 255, 255])
            grid_names[drv_num] = f"{drv_info.get('first_name', '')} {drv_info.get('last_name', '')}"
            
            drv_params = {"driver_number": drv_num, "session_key": key, "date>": dt_date.isoformat(), "date<": (dt_date + timedelta(minutes=15)).isoformat()}
            try:
                drv_response = urlopen(f"https://api.openf1.org/v1/location?{urllib.parse.urlencode(drv_params)}", timeout=3)
                drv_loc_data = json.loads(drv_response.read().decode('utf-8'))
                v_locs = [f for f in drv_loc_data if f.get('x') is not None and f.get('y') is not None and f['x'] != 0]
                if v_locs:
                    grid_locations[drv_num] = v_locs
            except Exception: pass
        
        grid_indices = {drv: 0 for drv in grid_locations.keys()}

        seen_cords = set()
        for frame in loc_data_point:
            rounded_cord = (round(frame['x'], 0), round(frame['y'], 0))
            if rounded_cord not in seen_cords:
                seen_cords.add(rounded_cord)
                track_x.append(frame['x'])
                track_y.append(frame['y'])

        if track_x and track_y:
            x_min, x_max = min(track_x), max(track_x)
            y_min, y_max = min(track_y), max(track_y)
            max_range = max(x_max - x_min, y_max - y_min)
            x_center, y_center = (x_min + x_max) / 2, (y_min + y_max) / 2
            map_x_limits = (x_center - max_range / 2, x_center + max_range / 2)
            map_y_limits = (y_center - max_range / 2, y_center + max_range / 2)

        launch_index = 0
        for index, frame in enumerate(data_point):
            if frame.get("speed", 0) > 0:
                launch_index = index
                break
        starting_index = max(0, launch_index - 50)
        
        setup_complete = True
    except Exception as err:
        print(f"Error during ingestion layer: {err}")
        setup_complete = True


def start_clicked():
    global user_year, user_country, user_session, user_driver, data_download_started
    if data_download_started: return
    
    user_year = dpg.get_value("year_combo")
    user_country = dpg.get_value("country_combo")
    driver_str = dpg.get_value("driver_combo")
    
    if (user_year != "") and (user_country != "") and (driver_str != "") and (key is not None):
        if driver_str in available_drivers_dict:
            user_driver = available_drivers_dict[driver_str]
        else:
            user_driver = driver_str.split(" - ")[0]
            
        data_download_started = True
        dpg.configure_item("spinner_indicator", show=True)
        threading.Thread(target=async_download_worker, daemon=True).start()
    else:
        print("Missing selections!")


with dpg.window(label="Session Setup", tag="setup_window", width=900, height=700, no_close=True):
    dpg.add_text("Select Gran Prix Settings:")
    dpg.add_spacer(height=10)
    dpg.add_combo(label="Year", items=["2023", "2024", "2025", "2026"], tag="year_combo", callback=year_changed, width=400)
    dpg.add_spacer(height=10)
    dpg.add_combo(label="Country", items=[], tag="country_combo", callback=country_changed, width=400)
    dpg.add_spacer(height=10)
    dpg.add_combo(label="Driver", items=[], tag="driver_combo", width=400)
    dpg.add_spacer(height=30)
    
    with dpg.group(horizontal=True):
        dpg.add_button(label="Load Telemetry Data", tag="load_btn", callback=start_clicked, width=350, height=60)
        dpg.add_spacer(width=20)
        dpg.add_loading_indicator(tag="spinner_indicator", radius=5.0, speed=2.0, show=False, color=[255, 30, 0, 255])


while dpg.is_dearpygui_running() and not setup_complete:
    dpg.render_dearpygui_frame()

if not data_download_started or not data_point:
    exit()

dpg.delete_item("setup_window")


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
    dpg.add_dynamic_texture(width, height, pixel_data, tag="driver_headshot_texture")


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

    dpg.add_spacer(height=25)
    dpg.add_separator()
    dpg.add_spacer(height=25)

    with dpg.child_window(height = 110, border=True, tag="Controls"):
        dpg.add_spacer(height=15)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=10)
            dpg.add_button(label="Pause", callback=pause_playback, width=100, height=35)
            dpg.add_button(label="Resume", callback=resume_playback, width=100, height=35)
            dpg.add_button(label="Exit", callback=lambda: dpg.stop_dearpygui(), width=100, height=35)
            dpg.add_spacer(width=20)
            dpg.add_button(label="<<", callback=lambda: slow_down(), width=60, height=35)
            dpg.add_button(label=">>", callback=lambda: speed_up(), width=60, height=35)
            dpg.add_spacer(width=10)
            dpg.add_text("Speed: 1x", tag="speed_indicator_tag", color=[255, 255, 255, 255])
            dpg.add_spacer(width=40)
            lap_options = [f"Lap {lap['number']}" for lap in processed_laps]
            dpg.add_combo(items=lap_options, label="Jump to Lap", callback=jump_to_lap_callback, width=150)
            dpg.add_spacer(width=20)
            dpg.add_button(label="Toggle Full Grid", callback=toggle_grid_view, height=35)

    dpg.add_spacer(height=25)
    dpg.add_separator()
    dpg.add_spacer(height=25)


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
    
    dpg.add_spacer(height=35)
    dpg.add_separator()
    dpg.add_spacer(height=35)


    with dpg.plot(label="Speed Playback", height=380, width=-1):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Speed (km/h)", tag="y_axis")
        dpg.set_axis_limits("y_axis", -10, 350)
        dpg.add_line_series(seconds_elapsed, car_speed, label="Speed", parent="y_axis", tag="Speed_series_tag")

    dpg.add_spacer(height=35)


    with dpg.table(header_row=False, width=-1, policy=dpg.mvTable_SizingStretchProp):
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            with dpg.plot(label="Throttle Playback", height=380, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="throttle_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Throttle Value (%)", tag="throttle_y_axis")
                dpg.set_axis_limits("throttle_y_axis", -5, 105)
                dpg.add_line_series(seconds_elapsed, car_throttle, label="Throttle", parent="throttle_y_axis", tag="Throttle_series_tag")
            with dpg.plot(label="Brake Playback", height=380, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="brake_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Brake Value (%)", tag="Brake_y_axis")
                dpg.set_axis_limits("Brake_y_axis", -10, 105)
                dpg.add_line_series(seconds_elapsed, car_brake, label="Brake", parent="Brake_y_axis", tag="Brake_series_tag")
        with dpg.table_row():
            with dpg.plot(label="rpm Playback", height=380, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="rpm_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="RPM", tag="rpm_y_axis")
                dpg.set_axis_limits("rpm_y_axis", -10, 15100)
                dpg.add_line_series(seconds_elapsed, car_rpm, label="RPM", parent="rpm_y_axis", tag="rpm_series_tag")
            with dpg.plot(label="Gear Playback", height=380, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag="gear_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Gear", tag="gear_y_axis")
                dpg.set_axis_limits("gear_y_axis", -1, 9)
                dpg.add_line_series(seconds_elapsed, car_gear, label="Gear", parent="gear_y_axis", tag="Gear_series_tag")


print("Processing finished. Launching stream dashboard panels.")
dpg.set_global_font_scale(2)
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
time.sleep(0.1)
