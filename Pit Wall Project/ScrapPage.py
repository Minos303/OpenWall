import requests

BASE_URL = "https://api.openf1.org/v1"

def fetch_data(endpoint, params=None):
    if params is None:
        params = {}

    # Standard clean up sequence to eliminate layout string concatenation errors
    base = BASE_URL.rstrip('/')
    end = endpoint.lstrip('/')
    url = f"{base}/{end}"
    
    # Matches your Streamlit app's parameter preparation code block
    full_url = requests.Request('GET', url, params=params).prepare().url
    print(f"Constructed URL: {full_url}")
    
    response = requests.get(full_url)
    response.raise_for_status()
    return response.json()

# Execute your session key inquiry
try:
    print("Searching for meeting data...")
    
    # FIX: Updated circuit_short_name to match the API database exactly
    meeting_filters = {
        "year": 2023,
        "circuit_short_name": "Monte Carlo"
    }
    
    meetings_list = fetch_data("meetings", meeting_filters)
    
    if meetings_list and isinstance(meetings_list, list) and len(meetings_list) > 0:
        meeting_key = meetings_list[0]["meeting_key"]
        print(f"✅ Found Monaco 2023 Meeting Key: {meeting_key}\n")
        
        print("Searching for session data...")
        
        session_filters = {
            "meeting_key": meeting_key,
            "session_name": "Race"
        }
        
        sessions_list = fetch_data("sessions", session_filters)
        
        if sessions_list and isinstance(sessions_list, list) and len(sessions_list) > 0:
            first_match = sessions_list[0]
            session_key = first_match["session_key"]
            
            print("\n================ SUCCESS ================")
            print(f"The Monaco 2023 Session Key is: {session_key}")
            print("=========================================\n")
        else:
            print("Connected, but no racing sessions matched the parameters.")
    else:
        print("Connected, but no meetings matched the parameters.")
            
except Exception as e:
    print(f"\n❌ Execution failed: {e}")