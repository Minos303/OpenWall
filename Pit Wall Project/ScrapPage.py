import requests
import json

def fetch_openf1_tracks_by_year():
    base_url = "https://api.openf1.org/v1/meetings"
    found_tracks = set()
    
    # We poll individual years because the root endpoint requires parameters
    years_to_check = [2023, 2024, 2025, 2026]
    
    print("Connecting to OpenF1 endpoints via structured year filters...")
    
    for year in years_to_check:
        try:
            # Query strings must have parameters or OpenF1 throws an HTML error page
            response = requests.get(f"{base_url}?year={year}", timeout=10)
            
            if response.status_code == 200:
                try:
                    meetings_data = response.json()
                    
                    # Track data validation
                    if isinstance(meetings_data, list):
                        for meeting in meetings_data:
                            track_name = meeting.get("circuit_short_name")
                            if track_name:
                                found_tracks.add(track_name.strip())
                except json.JSONDecodeError:
                    # Catch instances where a future year drops an HTML error page
                    pass
            else:
                print(f"[{year}] Server returned status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{year}] Connection failed: {e}")

    # Format exactly to your desired list style
    final_track_list = sorted(list(found_tracks))
    
    print("\n--- COPIED EXACT OPENF1 ARRAY OUTPUT ---")
    print(json.dumps(final_track_list))
    return final_track_list

if __name__ == "__main__":
    fetch_openf1_tracks_by_year()
