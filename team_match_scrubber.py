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
    full_url = f"{base_url}/team/{target_team}/matches/{year}"

    try:
        team_matches_response = requests.get(full_url, headers=headers)
      
        # Check if the request was successful
        if team_matches_response.status_code == 200:
            team_matches_data = team_matches_response.json()
            # Extend the list with team match data
            all_matches.extend(team_matches_data)
        else:
            print(f"Failed to retrieve match data for {year}. Status code: {team_matches_response.status_code}")
            print(f"Response text: {team_matches_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        
    print(f"{year} scan finished")

# Process match data and extract team keys for each alliance
processed_matches = []
team_stats = {}

for match in all_matches:
    red_teams = match["alliances"]["red"]["team_keys"]
    blue_teams = match["alliances"]["blue"]["team_keys"]
    red_score = match["alliances"]["red"]["score"]
    blue_score = match["alliances"]["blue"]["score"]

    if target_team in red_teams:
        teammates = [target_team] + [team for team in red_teams if team != target_team]
        opponents = blue_teams
        result = "win" if red_score > blue_score else "loss" if red_score < blue_score else "tie"
        alliance = "red"
    else:
        teammates = [target_team] + [team for team in blue_teams if team != target_team]
        opponents = red_teams
        result = "win" if blue_score > red_score else "loss" if blue_score < red_score else "tie"
        alliance = "blue"

    match_info = {
        "match_key": match["key"],
        "comp_level": match["comp_level"],
        "match_number": match["match_number"],
        "set_number": match.get("set_number", ""),
        "teammate_1": teammates[0],
        "teammate_2": teammates[1] if len(teammates) > 1 else None,
        "teammate_3": teammates[2] if len(teammates) > 2 else None,
        "opponent_1": opponents[0],
        "opponent_2": opponents[1],
        "opponent_3": opponents[2] if len(opponents) > 2 else None,
        "result": result
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
with pd.ExcelWriter(f"tba_{target_team}_matches.xlsx", engine='xlsxwriter') as writer:
    df_matches.to_excel(writer, sheet_name='Matches', index=False)
    df_stats.to_excel(writer, sheet_name='Team Stats', index=False)
    
print(f"Data successfully saved to tba_{target_team}_matches.xlsx")
