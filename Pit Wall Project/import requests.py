import requests

# 1. Target URL using the clean API endpoint without messy slashes
url = "https://openf1.org"

print("Pinging OpenF1 API safely...")
response = requests.get(url)
print(f"Server Status Code: {response.status_code}")

if response.status_code == 200:
    try:
        # The data server cleanly parses straight into a list here
        sessions_list = response.json()
        
        if sessions_list and isinstance(sessions_list, list):
            # Target index 0 to drop down into the session key dictionary
            first_match = sessions_list[0]
            session_key = first_match["session_key"]
            
            print("\n================ SUCCESS ================")
            print(f"The Monaco 2023 Session Key is: {session_key}")
            print("=========================================\n")
        else:
            print("Connected, but no racing sessions matched the parameters.")
            
    except Exception as e:
        print(f"JSON Parsing failed: {e}")
else:
    print(f"Server rejected connection: {response.status_code}")
