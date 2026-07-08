#git add.
#git commit -m "Updated project UI and telemetry parser"
#git push origin main

#cd OpenWall
#git pull origin main
#Linux Run: python "Pit Wall Project/PitWall_Main.py"


import io
import time
import threading
import requests
from datetime import datetime, timedelta
import dearpygui.dearpygui as dpg
from PIL import Image





class F1TelemetryApp:
    TEAM_COLORS = {
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
        "Cadillac": [128, 0, 128, 255]
    }

    SPEEDS = [0.05, 0.1, 0.15, 0.2, 0.4, 0.8, 2.0, 20.0, 200.0, 2000.0]




    def __init__(self):
        self.http = requests.Session()
        self.base_url = "https://api.openf1.org/v1"
        
        self.session_key = None
        self.selected_year = ""
        self.selected_country = ""
        self.driver_num = ""
        
        self.driver_name = ""
        self.driver_surname = ""
        self.driver_code = ""
        
        self.driver_rank = 0
        self.team_name = ""
        self.team_rank = 0
        self.team_color = [255, 255, 255, 255]
        
        self.w, self.h = 100, 100
        self.pixels = []
        
        self.old_scale_factor = 1.0 
        
        self.t_data = []
        self.spd_data = []
        self.thr_data = []
        self.brk_data = []
        self.rpm_data = []
        self.gear_data = []
        
        self.track_x, self.track_y = [], []
        self.current_x, self.current_y = [0], [0]
        
        self.grid_locs = {}
        self.grid_colors = {}
        self.grid_names = {}
        self.laps = []
        self.telemetry = []
        self.locations = []
        
        self.max_history = 100
        self.elapsed = 0.0
        self.idx = 0
        self.start_idx = 0
        self.speed_idx = 1
        
        self.paused = False
        self.show_grid = False
        self.flag = "CLEAR"
        self.notice = "No messages"




    def run(self):
        dpg.create_context()
        dpg.create_viewport(title='Open Wall Configurations', width=1200, height=900)
        dpg.setup_dearpygui()
        
        self.build_ui()
        
        dpg.show_viewport()
        dpg.set_global_font_scale(1.2)
        dpg.maximize_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()




    def build_ui(self):
        with dpg.texture_registry(tag="tex_reg", show=False):
            dpg.add_dynamic_texture(1, 1, [1.0, 1.0, 1.0, 1.0], tag="driver_headshot_texture")

        with dpg.window(tag="main_window"):
            
            with dpg.group(tag="setup_layer"):
                with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column() 
                    dpg.add_table_column(init_width_or_weight=450.0) 
                    dpg.add_table_column() 
                    
                    with dpg.table_row():
                        dpg.add_text("") 
                        
                        with dpg.group():
                            dpg.add_spacer(height=60)
                            dpg.add_text("Select Grand Prix Settings:", color=[0, 210, 255, 255])
                            dpg.add_spacer(height=15)
                            dpg.add_combo(label="Year", items=["2023", "2024", "2025", "2026"], tag="year_combo", callback=self.on_year_change, width=320)
                            dpg.add_spacer(height=10)
                            dpg.add_combo(label="Country", items=[], tag="country_combo", callback=self.on_country_change, width=320)
                            dpg.add_spacer(height=10)
                            dpg.add_combo(label="Driver", items=[], tag="driver_combo", width=320)
                            dpg.add_spacer(height=25)
                            
                            dpg.add_button(label="Load Telemetry Data", tag="load_btn", callback=self.on_load_click, width=320, height=50)
                            dpg.add_spacer(height=30)
                            
                            with dpg.group(horizontal=False):
                                dpg.add_loading_indicator(tag="spinner_indicator", radius=5.0, speed=2.5, show=False, color=[0, 210, 255, 255])
                                dpg.add_spacer(height=10)
                                dpg.add_text("", tag="loading_status_text", color=[200, 200, 200, 255])
                        
                        dpg.add_text("") 

            with dpg.group(tag="telemetry_layer", show=False):
                with dpg.child_window(height=220, border=True):
                    with dpg.group(horizontal=True):
                        with dpg.group(tag="headshot_container"):
                            dpg.add_image("driver_headshot_texture", width=180, height=180, tag="ui_headshot_img")
                        dpg.add_spacer(width=15)

                        with dpg.group():
                            dpg.add_text("", tag="ui_driver_name", color=[255, 255, 255, 255])
                            dpg.add_text("", tag="ui_driver_details", color=[255, 255, 255, 255])
                            dpg.add_text("", tag="ui_team_name")
                            dpg.add_text("", tag="ui_driver_standing", color=[255, 255, 255, 255])
                            dpg.add_text("", tag="ui_team_standing")
                        
                        dpg.add_spacer(width=200)
                        with dpg.group():
                            dpg.add_text("Lap: 1", tag="lap_indicator_tag", color=[255, 30, 0, 255])
                            dpg.add_text("Current Flag: Fetching...", tag="flag_text_tag", color=[255, 30, 0, 255])
                            dpg.add_text("Latest Notice: Fetching...", tag="message_text_tag", wrap=400, color=[255, 30, 0, 255])
                        
                        dpg.add_spacer(width=200)
                        with dpg.group():
                            dpg.add_text("Session: Race", color=[255, 255, 255, 255])
                            dpg.add_text("", tag="ui_session_year", color=[255, 255, 255, 255])
                            dpg.add_text("", tag="ui_session_country", color=[255, 255, 255, 255])

                dpg.add_spacer(height=20)
                
                with dpg.child_window(height=110, border=True):
                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=10)
                        dpg.add_button(label="Pause", callback=self.pause_playback, width=100, height=35)
                        dpg.add_button(label="Resume", callback=self.resume_playback, width=100, height=35)
                        dpg.add_button(label="Exit", callback=lambda: dpg.stop_dearpygui(), width=100, height=35)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label="<<", callback=self.decrease_speed, width=60, height=35)
                        dpg.add_button(label=">>", callback=self.increase_speed, width=60, height=35)
                        dpg.add_spacer(width=10)
                        dpg.add_text("Speed: 1x", tag="speed_indicator_tag", color=[255, 255, 255, 255])
                        dpg.add_spacer(width=40)
                        dpg.add_combo(items=[], label="Jump to Lap", tag="lap_jump_combo", callback=self.jump_to_lap, width=150)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label="Toggle Full Grid", callback=self.toggle_grid, height=35)

                dpg.add_spacer(height=20)

                with dpg.plot(label="Track Map", height=600, width=-1, tag="track_series_tag"):
                    self.map_axis_x = dpg.add_plot_axis(dpg.mvXAxis, no_tick_labels=True)
                    self.map_axis_y = dpg.add_plot_axis(dpg.mvYAxis, no_tick_labels=True)
                    dpg.add_scatter_series([], [], parent=self.map_axis_y, tag="base_track_series")
                    dpg.add_scatter_series([], [], parent=self.map_axis_y, tag="grid_location_tag")
                    dpg.add_scatter_series([], [], parent=self.map_axis_y, tag="driver_location_tag")

                dpg.add_spacer(height=20)
                
                self.create_line_plot("Speed Playback", "Speed (km/h)", "Speed_series_tag", [-10, 350], "Speed")
                
                dpg.add_spacer(height=20)
                
                with dpg.table(header_row=False, width=-1, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    with dpg.table_row():
                        self.create_line_plot("Throttle Playback", "Throttle (%)", "Throttle_series_tag", [-5, 105], "Throttle")
                        self.create_line_plot("Brake Playback", "Brake (%)", "Brake_series_tag", [-10, 105], "Brake")
                    with dpg.table_row():
                        self.create_line_plot("RPM Playback", "RPM", "rpm_series_tag", [-10, 15100], "RPM")
                        self.create_line_plot("Gear Playback", "Gear", "Gear_series_tag", [-1, 9], "Gear")

        dpg.set_primary_window("main_window", True)




    def create_line_plot(self, title, y_label, tag, y_limits, series_label):
        with dpg.plot(label=title, height=280, width=-1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Timeline (Seconds)", tag=tag + "_xaxis")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label=y_label)
            dpg.set_axis_limits(y_axis, y_limits[0], y_limits[1])
            dpg.add_line_series([], [], label=series_label, parent=y_axis, tag=tag)




    def on_year_change(self, sender, app_data):
        response = self.http.get(f"{self.base_url}/meetings", params={"year": app_data}).json()
        countries = []
        for m in response:
            if 'circuit_short_name' in m:
                name = m['circuit_short_name']
                if name not in countries:
                    countries.append(name)
        dpg.configure_item("country_combo", items=countries)
        dpg.set_value("country_combo", "")
        dpg.configure_item("driver_combo", items=[])




    def on_country_change(self, sender, app_data):
        year = dpg.get_value("year_combo")
        meetings = self.http.get(f"{self.base_url}/meetings", params={"year": year, "circuit_short_name": app_data}).json()
        
        if meetings:
            meeting_key = meetings[0]['meeting_key']
            sessions = self.http.get(f"{self.base_url}/sessions", params={"meeting_key": meeting_key}).json()
            
            for s in sessions:
                if s['session_name'].lower() == "race":
                    self.session_key = s['session_key']
                    break
                    
            if self.session_key:
                drivers = self.http.get(f"{self.base_url}/drivers", params={"session_key": self.session_key}).json()
                self.driver_registry = {f"{d['driver_number']} - {d['first_name']} {d['last_name']}": d['driver_number'] for d in drivers}
                dpg.configure_item("driver_combo", items=list(self.driver_registry.keys()))
        dpg.set_value("driver_combo", "")




    def on_load_click(self):
        self.selected_year = dpg.get_value("year_combo")
        self.selected_country = dpg.get_value("country_combo")
        driver_string = dpg.get_value("driver_combo")
        
        if self.selected_year and self.selected_country and driver_string and self.session_key:
            self.driver_num = self.driver_registry.get(driver_string, driver_string.split(" - ")[0])
            dpg.configure_item("spinner_indicator", show=True)
            dpg.set_value("loading_status_text", "Preparing to load...")
            threading.Thread(target=self.download_telemetry_worker, daemon=True).start()




    def download_telemetry_worker(self):
        try:
            dpg.set_value("loading_status_text", "Loading driver standing...")
            champ_res = self.http.get(f"{self.base_url}/championship_drivers", params={"session_key": self.session_key, "driver_number": self.driver_num}).json()
            self.driver_rank = champ_res[0]['position_current'] if champ_res else 0

            dpg.set_value("loading_status_text", "Loading profiles...")
            driver_res = self.http.get(f"{self.base_url}/drivers", params={"driver_number": self.driver_num, "session_key": self.session_key}).json()

            self.driver_name = driver_res[0]['first_name']
            self.driver_surname = driver_res[0]['last_name']
            self.driver_code = driver_res[0]['name_acronym']
            self.team_name = driver_res[0]['team_name']
            headshot_url = driver_res[0]['headshot_url']
            self.team_color = self.TEAM_COLORS.get(self.team_name.replace(" ", "_"), [255, 255, 255, 255])

            dpg.set_value("loading_status_text", "Loading driver photo...")
            img_data = self.http.get(headshot_url).content
            img = Image.open(io.BytesIO(img_data)).convert("RGBA")
            self.w, self.h = img.size
            
            if hasattr(img, 'get_flattened_data'):
                self.pixels = [x / 255.0 for p in img.get_flattened_data() for x in p]
            else:
                self.pixels = [x / 255.0 for p in list(img.getdata()) for x in p]

            dpg.set_value("loading_status_text", "Loading constructor standing...")
            team_res = self.http.get(f"{self.base_url}/championship_teams", params={"session_key": self.session_key, "team_name": self.team_name}).json()
            self.team_rank = team_res[0]['position_current'] if team_res else 0

            dpg.set_value("loading_status_text", "Loading laps...")
            lap_res = self.http.get(f"{self.base_url}/laps", params={"session_key": self.session_key, "driver_number": self.driver_num}).json()
            valid_laps = sorted([l for l in lap_res if l.get('date_start')], key=lambda x: x.get('lap_number', 0))
            
            if valid_laps:
                initial_timestamp = valid_laps[0]['date_start']
            else:
                car_fallback = self.http.get(f"{self.base_url}/car_data", params={"driver_number": self.driver_num, "session_key": self.session_key}).json()
                initial_timestamp = car_fallback[0]['date']
                
            start_datetime = datetime.strptime(initial_timestamp[:19], "%Y-%m-%dT%H:%M:%S")

            query_params = {
                "driver_number": self.driver_num,
                "session_key": self.session_key,
                "date>": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "date<": (start_datetime + timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%S")
            }

            dpg.set_value("loading_status_text", "Loading car telemetry...")
            self.telemetry = self.http.get(f"{self.base_url}/car_data", params=query_params).json()

            dpg.set_value("loading_status_text", "Loading track layouts...")
            raw_locations = self.http.get(f"{self.base_url}/location", params=query_params).json()
            self.locations = []
            for f in raw_locations:
                if f.get('x') is not None and f.get('y') is not None and f['x'] != 0:
                    f['parsed_date'] = datetime.strptime(f['date'][:19], "%Y-%m-%dT%H:%M:%S")
                    self.locations.append(f)

            for lap in valid_laps:
                if lap.get('lap_duration'):
                    lap_start = datetime.strptime(lap['date_start'][:19], "%Y-%m-%dT%H:%M:%S")
                    self.laps.append({
                        'number': lap['lap_number'],
                        'start': lap_start,
                        'end': lap_start + timedelta(seconds=lap['lap_duration'])
                    })

            dpg.set_value("loading_status_text", "Mapping fields...")
            all_drivers = self.http.get(f"{self.base_url}/drivers", params={"session_key": self.session_key}).json()
            other_drivers = [d for d in all_drivers if d['driver_number'] != self.driver_num]

            for d_info in other_drivers:
                d_num = d_info['driver_number']
                self.grid_colors[d_num] = self.TEAM_COLORS.get(d_info['team_name'].replace(" ", "_"), [255, 255, 255, 255])
                self.grid_names[d_num] = f"{d_info.get('first_name', '')} {d_info.get('last_name', '')}"
                
                grid_query = {
                    "driver_number": d_num, 
                    "session_key": self.session_key, 
                    "date>": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"), 
                    "date<": (start_datetime + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S")
                }
                try:
                    grid_loc_data = self.http.get(f"{self.base_url}/location", params=grid_query, timeout=3).json()
                    filtered_locs = []
                    for f in grid_loc_data:
                        if f.get('x') is not None and f.get('y') is not None and f['x'] != 0:
                            f['parsed_date'] = datetime.strptime(f['date'][:19], "%Y-%m-%dT%H:%M:%S")
                            filtered_locs.append(f)
                    if filtered_locs:
                        self.grid_locs[d_num] = filtered_locs
                except Exception:
                    pass

            seen_coords = set()
            for frame in self.locations:
                coord_key = (round(frame['x'], 0), round(frame['y'], 0))
                if coord_key not in seen_coords:
                    seen_coords.add(coord_key)
                    self.track_x.append(frame['x'])
                    self.track_y.append(frame['y'])

            if self.track_x and self.track_y:
                min_x, max_x = min(self.track_x), max(self.track_x)
                min_y, max_y = min(self.track_y), max(self.track_y)
                max_range = max(max_x - min_x, max_y - min_y)
                center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
                dpg.set_axis_limits(self.map_axis_x, center_x - max_range / 2, center_x + max_range / 2)
                dpg.set_axis_limits(self.map_axis_y, center_y - max_range / 2, center_y + max_range / 2)

            moving_index = 0
            for i, frame in enumerate(self.telemetry):
                if frame.get("speed", 0) > 0:
                    moving_index = i
                    break
            self.start_idx = max(0, moving_index - 50)
            self.idx = self.start_idx

            self.apply_ui_assets()
            
        except Exception as e:
            print(f"Data ingestion failed: {e}")
            dpg.set_value("loading_status_text", "Failed to load data.")
            self.apply_ui_assets()




    def apply_ui_assets(self):
        if dpg.does_item_exist("ui_headshot_img"):
            dpg.delete_item("ui_headshot_img")
        if dpg.does_item_exist("driver_headshot_texture"):
            dpg.delete_item("driver_headshot_texture")
            
        if dpg.does_item_exist("active_driver_theme"):
            dpg.delete_item("active_driver_theme")
        if dpg.does_item_exist("track_layout_theme"):
            dpg.delete_item("track_layout_theme")
            
        for d_num in list(self.grid_locs.keys()):
            if dpg.does_item_exist(f"theme_driver_{d_num}"):
                dpg.delete_item(f"theme_driver_{d_num}")
            if dpg.does_item_exist(f"grid_location_tag_{d_num}"):
                dpg.delete_item(f"grid_location_tag_{d_num}")
            if dpg.does_item_exist(f"annotation_tag_{d_num}"):
                dpg.delete_item(f"annotation_tag_{d_num}")

        if len(self.pixels) != (self.w * self.h * 4):
            self.w, self.h = 1, 1
            self.pixels = [0.15, 0.15, 0.15, 1.0]

        dpg.add_dynamic_texture(self.w, self.h, self.pixels, tag="driver_headshot_texture", parent="tex_reg")
        dpg.add_image("driver_headshot_texture", width=180, height=180, tag="ui_headshot_img", parent="headshot_container")

        with dpg.theme(tag="active_driver_theme"):
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 12.0, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, self.team_color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, self.team_color, category=dpg.mvThemeCat_Plots)

        for d_num, color_config in self.grid_colors.items():
            if d_num in self.grid_locs:
                with dpg.theme(tag=f"theme_driver_{d_num}"):
                    with dpg.theme_component(dpg.mvScatterSeries):
                        dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 5.0, category=dpg.mvThemeCat_Plots)
                        dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, color_config, category=dpg.mvThemeCat_Plots)
                        dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, color_config, category=dpg.mvThemeCat_Plots)

        dpg.set_value("ui_driver_name", f"Driver: {self.driver_name} {self.driver_surname}")
        dpg.set_value("ui_driver_details", f"Driver Acronym: {self.driver_code} | Driver Number: {self.driver_num}")
        dpg.set_value("ui_team_name", f"Team: {self.team_name}")
        dpg.configure_item("ui_team_name", color=self.team_color)
        dpg.set_value("ui_driver_standing", f"Championship Standings: {self.driver_rank}")
        dpg.set_value("ui_team_standing", f"Team Standings: {self.team_rank}")
        dpg.configure_item("ui_team_standing", color=self.team_color)
        dpg.set_value("ui_session_year", f"Year: {self.selected_year}")
        dpg.set_value("ui_session_country", f"Grand Prix: {self.selected_country}")

        lap_options = [f"Lap {lap['number']}" for lap in self.laps]
        dpg.configure_item("lap_jump_combo", items=lap_options)

        dpg.set_value("base_track_series", [self.track_x, self.track_y])
        dpg.bind_item_theme("driver_location_tag", "active_driver_theme")
        
        with dpg.theme(tag="track_layout_theme"):
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, [90, 90, 90, 255], category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, [90, 90, 90, 255], category=dpg.mvThemeCat_Plots)
        dpg.bind_item_theme("base_track_series", "track_layout_theme")

        for d_num in self.grid_locs.keys():
            dpg.add_scatter_series([], [], parent=self.map_axis_y, tag=f"grid_location_tag_{d_num}", label=self.grid_names[d_num])
            dpg.bind_item_theme(f"grid_location_tag_{d_num}", f"theme_driver_{d_num}")
            dpg.add_plot_annotation(label=self.grid_names[d_num], default_value=[0.0, 0.0], offset=[10.0, -10.0], tag=f"annotation_tag_{d_num}", parent="track_series_tag")

        dpg.configure_item("setup_layer", show=False)
        dpg.configure_item("telemetry_layer", show=True)

        threading.Thread(target=self.stream_telemetry, daemon=True).start()
        threading.Thread(target=self.fetch_race_control, daemon=True).start()




    def jump_to_lap(self, sender, app_data):
        target_lap = int(app_data.split()[-1])
        target_time = next((lap['start'] for lap in self.laps if lap['number'] == target_lap), None)
        
        if target_time:
            self.t_data.clear()
            self.spd_data.clear()
            self.thr_data.clear()
            self.brk_data.clear()
            self.rpm_data.clear()
            self.gear_data.clear()
            
            for i, frame in enumerate(self.telemetry):
                frame_time = datetime.strptime(frame['date'][:19], "%Y-%m-%dT%H:%M:%S")
                if frame_time >= target_time:
                    self.idx = i
                    start_time = datetime.strptime(self.telemetry[self.start_idx]['date'][:19], "%Y-%m-%dT%H:%M:%S")
                    self.elapsed = (frame_time - start_time).total_seconds()
                    break




    def stream_telemetry(self):
        last_x, last_y = 0.0, 0.0

        while self.idx < len(self.telemetry):
            frame_start = time.perf_counter()
            while self.paused:
                time.sleep(0.1)
                if not dpg.is_dearpygui_running():
                    return
                frame_start = time.perf_counter()
                
            current_frame = self.telemetry[self.idx]
            
            self.elapsed += 0.2
            self.t_data.append(self.elapsed)
            self.spd_data.append(current_frame.get('speed') or 0)
            self.thr_data.append(current_frame.get('throttle') or 0)
            self.brk_data.append(current_frame.get('brake') or 0)
            self.gear_data.append(current_frame.get('n_gear') or 0)
            self.rpm_data.append(current_frame.get('rpm') or 0)
            
            # if 'n_gear' in current_frame:
            #     self.gear_data.append(current_frame['n_gear'])
            # else:
            #     self.gear_data.append(current_frame.get('gear', 0))
            #
            # # Debug Trace Dump 
            # # print(f"TS: {current_frame.get('date')} | RPM: {current_frame.get('rpm')} | G: {current_frame.get('n_gear')}")
            # # print(f"SPD: {current_frame.get('speed')} THR: {current_frame.get('throttle')} BRK: {current_frame.get('brake')}")
            #
            # if len(self.t_data) > self.max_history:
            #     self.t_data.pop(0)
            #     self.spd_data.pop(0)
            #     self.thr_data.pop(0)
            #     self.brk_data.pop(0)
            #     self.gear_data.pop(0)
            #     self.rpm_data.pop(0)

            if len(self.t_data) > self.max_history:
                for arr in [self.t_data, self.spd_data, self.thr_data, self.brk_data, self.gear_data, self.rpm_data]:
                    arr.pop(0)

            frame_timestamp = datetime.strptime(current_frame['date'][:19], "%Y-%m-%dT%H:%M:%S")
            active_lap = "OUT"
            for lap in self.laps:
                if lap['start'] <= frame_timestamp <= lap['end']:
                    active_lap = lap['number']
                    break
                
            dpg.set_value("Speed_series_tag", [self.t_data, self.spd_data])
            dpg.set_value("Throttle_series_tag", [self.t_data, self.thr_data])
            dpg.set_value("Brake_series_tag", [self.t_data, self.brk_data])
            dpg.set_value("rpm_series_tag", [self.t_data, self.rpm_data])
            dpg.set_value("Gear_series_tag", [self.t_data, self.gear_data])
            dpg.set_value("lap_indicator_tag", f"Lap: {active_lap}")

            if self.t_data:
                min_x = self.t_data[0]
                max_x = self.t_data[-1]
                dpg.set_axis_limits("Speed_series_tag_xaxis", min_x, max_x)
                dpg.set_axis_limits("Throttle_series_tag_xaxis", min_x, max_x)
                dpg.set_axis_limits("Brake_series_tag_xaxis", min_x, max_x)
                dpg.set_axis_limits("rpm_series_tag_xaxis", min_x, max_x)
                dpg.set_axis_limits("Gear_series_tag_xaxis", min_x, max_x)

            if self.locations:
                closest_location = min(self.locations, key=lambda item: abs(item['parsed_date'] - frame_timestamp))
                target_x, target_y = closest_location['x'], closest_location['y']
                if last_x == 0.0 and last_y == 0.0:
                    last_x, last_y = target_x, target_y
                
                steps = 1 if self.SPEEDS[self.speed_idx] >= 0.8 else 5
                for _ in range(steps):
                    last_x += (target_x - last_x) * 0.35
                    last_y += (target_y - last_y) * 0.35
                    dpg.set_value("driver_location_tag", [[last_x], [last_y]])
                    time.sleep(0.005)
            
            if self.show_grid:
                for driver_num, locs in self.grid_locs.items():
                    if locs:
                        match = min(locs, key=lambda item: abs(item['parsed_date'] - frame_timestamp))
                        dpg.set_value(f"grid_location_tag_{driver_num}", [[match['x']], [match['y']]])
                        dpg.set_value(f"annotation_tag_{driver_num}", [match['x'], match['y']])

            self.idx += 1

            step_duration = 0.2 / (self.SPEEDS[self.speed_idx] / 0.2)
            execution_time = time.perf_counter() - frame_start
            remaining_sleep = step_duration - execution_time
            if remaining_sleep > 0:
                time.sleep(remaining_sleep)




    def fetch_race_control(self):
        api_url = f"{self.base_url}/race_control"
        request_params = {"session_key": self.session_key}
        flag_colors = {
            "RED": [255, 0, 0, 255], "YELLOW": [255, 255, 0, 255], 
            "GREEN": [0, 255, 0, 255], "BLUE": [0, 100, 255, 255], 
            "BLACK AND WHITE": [220, 220, 220, 255]
        }
        
        while dpg.is_dearpygui_running():
            try:
                response = self.http.get(api_url, params=request_params, timeout=5).json()
                if response:
                    latest_event = response[-1]
                    self.flag = latest_event.get("flag") or "CLEAR"
                    self.notice = latest_event.get("message") or "No messages"
                    
                    dpg.set_value("flag_text_tag", f"Current Flag: {self.flag}")
                    dpg.set_value("message_text_tag", f"Latest Notice: {self.notice}")
                    dpg.configure_item("flag_text_tag", color=flag_colors.get(self.flag, [255, 255, 255, 255]))
            except Exception:
                pass
            time.sleep(4)




    def pause_playback(self):
        self.paused = True




    def resume_playback(self):
        self.paused = False




    def increase_speed(self):
        if self.speed_idx < len(self.SPEEDS) - 1:
            self.speed_idx += 1
            dpg.set_value("speed_indicator_tag", f"Speed: {(self.SPEEDS[self.speed_idx] / 0.2):.2f}x")




    def decrease_speed(self):
        if self.speed_idx > 0:
            self.speed_idx -= 1
            dpg.set_value("speed_indicator_tag", f"Speed: {(self.SPEEDS[self.speed_idx] / 0.2):.2f}x")




    def toggle_grid(self):
        self.show_grid = not self.show_grid
        for driver_num in self.grid_locs.keys():
            dpg.configure_item(f"grid_location_tag_{driver_num}", show=self.show_grid)
            dpg.configure_item(f"annotation_tag_{driver_num}", show=self.show_grid)
        if not self.show_grid:
            dpg.set_value("grid_location_tag", [[], []])
            for driver_num in self.grid_locs.keys():
                dpg.set_value(f"grid_location_tag_{driver_num}", [[], []])




if __name__ == "__main__":
    app = F1TelemetryApp()
    app.run()
