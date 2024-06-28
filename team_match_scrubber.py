import requests
import pandas as pd

# Function to get user input for target team
def get_target_team():
    while True:
        target_team = input("Enter the target team (e.g., frc1710): ").strip()
        if target_team.startswith("frc") and target_team[3:].isdigit():
            return target_team
        else:
            print("Invalid team format. Please enter a team in the format 'frcXXXX'.")

# Function to ask the user if they want to filter out off-season events
def filter_offseason_events():
    while True:
        filter_choice = input("Do you want to filter out off-season events? (yes/no): ").strip().lower()
        if filter_choice in ["yes", "no"]:
            return filter_choice == "yes"
        else:
            print("Invalid choice. Please enter 'yes' or 'no'.")

# API base URL and X-TBA-Auth-Key
base_url = "https://www.thebluealliance.com/api/v3"
auth_key = "it's a secret to everybody"  # Your actual TBA Auth Key

# Headers with X-TBA-Auth-Key
headers = {
    "X-TBA-Auth-Key": auth_key,
    "Accept": "application/json"  # Specify the content type you expect
}

# Get target team from user
target_team = get_target_team()

# Ask user if they want to filter out off-season events
filter_offseason = filter_offseason_events()

team_years_participated = []

# List to store all match data
all_matches = []

# Get years participated
full_url = f"{base_url}/team/{target_team}/years_participated"

try:
    team_years_participated_response = requests.get(full_url, headers=headers)
    
    if team_years_participated_response.status_code == 200:
        team_years_participated_data = team_years_participated_response.json()
        team_years_participated = team_years_participated_data
    else:
        print(f"Failed to retrieve team data. Status code: {team_years_participated_response.status_code}")
        print(f"Response text: {team_years_participated_response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")

# Get matches for each year the team participated
for year in team_years_participated:
    # Get events for the year
    full_url = f"{base_url}/team/{target_team}/events/{year}"

    try:
        team_events_response = requests.get(full_url, headers=headers)
      
        # Check if the request was successful
        if team_events_response.status_code == 200:
            team_events_data = team_events_response.json()
            # Filter events based on user choice
            if filter_offseason:
                regular_events = [event for event in team_events_data if event['event_type'] != 99]
            else:
                regular_events = team_events_data
            regular_events.sort(key=lambda x: x['start_date'])
        else:
            print(f"Failed to retrieve event data for {year}. Status code: {team_events_response.status_code}")
            print(f"Response text: {team_events_response.text}")
            continue
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        continue
    
    for event in regular_events:
        event_key = event['key']
        full_url = f"{base_url}/event/{event_key}/matches"

        try:
            event_matches_response = requests.get(full_url, headers=headers)

            # Check if the request was successful
            if event_matches_response.status_code == 200:
                event_matches_data = event_matches_response.json()
                # Sort matches by comp_level ("qm", "ef", "qf", "sf", "f") and then match_number within each comp_level
                comp_level_order = {"qm": 0, "ef": 1, "qf": 2, "sf": 3, "f": 4}
                event_matches_data.sort(key=lambda x: (comp_level_order[x['comp_level']], x['match_number']))
                # Extend the list with event match data
                all_matches.extend(event_matches_data)
            else:
                print(f"Failed to retrieve match data for event {event_key}. Status code: {event_matches_response.status_code}")
                print(f"Response text: {event_matches_response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        
        print(f"{event['name']} ({event_key}) scan finished")

# Process match data and extract team keys for each alliance
processed_matches = []
team_stats = {}
matches_played = 0
wins = 0
losses = 0
record = 0
win_loss_ratio = 0
wins_above_even = 0

for match in all_matches:
    red_teams = match["alliances"]["red"]["team_keys"]
    blue_teams = match["alliances"]["blue"]["team_keys"]
    red_score = match["alliances"]["red"]["score"]
    blue_score = match["alliances"]["blue"]["score"]

    if target_team in red_teams or target_team in blue_teams:
        matches_played += 1

        if target_team in red_teams:
            teammates = [team for team in red_teams if team != target_team]
            opponents = blue_teams
            result = "win" if red_score > blue_score else "loss" if red_score < blue_score else "tie"
            alliance = "red"
        else:
            teammates = [team for team in blue_teams if team != target_team]
            opponents = red_teams
            result = "win" if blue_score > red_score else "loss" if blue_score < red_score else "tie"
            alliance = "blue"

        if result == "win":
            wins += 1
            wins_above_even += 1
        else:
            losses += 1
            wins_above_even -= 1

        record = wins / matches_played if matches_played > 0 else wins

        win_loss_ratio = wins / losses if losses > 0 else wins

        match_info = {
            "matches_played": matches_played,
            "year": int(match["key"][:4]),
            "match_key": match["key"],
            "event_key": match["event_key"],
            "comp_level": match["comp_level"],
            "match_number": match["match_number"],
            "set_number": match.get("set_number", ""),
            "teammate_1": target_team,
            "teammate_2": teammates[0] if len(teammates) > 0 else None,
            "teammate_3": teammates[1] if len(teammates) > 1 else None,
            "opponent_1": opponents[0],
            "opponent_2": opponents[1],
            "opponent_3": opponents[2] if len(opponents) > 2 else None,
            "result": result,
            "wins": wins,
            "losses": losses,
            "record": record,
            "win_loss_ratio": win_loss_ratio,
            "wins_above_even": wins_above_even
        }
        processed_matches.append(match_info)
        
        # Update stats for teammates
        for team in teammates:
            if team not in team_stats:
                team_stats[team] = {
                    f"matches_with_{target_team}": 0,
                    f"on_alliance_with_{target_team}": 0,
                    f"opposing_{target_team}": 0,
                    f"wins_with_{target_team}": 0,
                    f"losses_with_{target_team}": 0,
                    f"ties_with_{target_team}": 0,
                    f"wins_against_{target_team}": 0,
                    f"losses_against_{target_team}": 0,
                    f"ties_against_{target_team}": 0
                }
            team_stats[team][f"matches_with_{target_team}"] += 1
            team_stats[team][f"on_alliance_with_{target_team}"] += 1
            if result == "win":
                team_stats[team][f"wins_with_{target_team}"] += 1
            elif result == "loss":
                team_stats[team][f"losses_with_{target_team}"] += 1
            elif result == "tie":
                team_stats[team][f"ties_with_{target_team}"] += 1

        # Update stats for opponents
        for team in opponents:
            if team not in team_stats:
                team_stats[team] = {
                    f"matches_with_{target_team}": 0,
                    f"on_alliance_with_{target_team}": 0,
                    f"opposing_{target_team}": 0,
                    f"wins_with_{target_team}": 0,
                    f"losses_with_{target_team}": 0,
                    f"ties_with_{target_team}": 0,
                    f"wins_against_{target_team}": 0,
                    f"losses_against_{target_team}": 0,
                    f"ties_against_{target_team}": 0
                }
            team_stats[team][f"matches_with_{target_team}"] += 1
            team_stats[team][f"opposing_{target_team}"] += 1
            if result == "win":
                team_stats[team][f"losses_against_{target_team}"] += 1
            elif result == "loss":
                team_stats[team][f"wins_against_{target_team}"] += 1
            elif result == "tie":
                team_stats[team][f"ties_against_{target_team}"] += 1

# Convert the processed match data into a DataFrame
df_matches = pd.DataFrame(processed_matches)
df_stats = pd.DataFrame.from_dict(team_stats, orient="index").reset_index().rename(columns={"index": "team_key"})

# Create a Pandas Excel writer using XlsxWriter as the engine
with pd.ExcelWriter(f"tba_{target_team}_match_data.xlsx", engine='xlsxwriter') as writer:
    df_matches.to_excel(writer, sheet_name='Matches', index=False)
    df_stats.to_excel(writer, sheet_name='Team Stats', index=False)
    
print(f"Data successfully saved to tba_{target_team}_match_data.xlsx")
