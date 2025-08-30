import pandas as pd
import json
from itertools import combinations

print("Starting advanced data processing for the new dashboard...")

# --- Step 1: Load All Raw Data ---

match_df = pd.read_csv('match_summary.csv')
batting_df = pd.read_csv('batting_summary.csv')
bowling_df = pd.read_csv('bowling_summary.csv')
print("Successfully loaded match_summary.csv, batting_summary.csv, and bowling_summary.csv")

# --- Step 2: Clean and Standardize Data ---
print("Cleaning and standardizing team names...")

def standardize_team_name(name):
    """Standardizes team names to their current or most common form."""
    if not isinstance(name, str):
        return name
    name = name.strip().upper()
    team_map = {
        'KINGS XI PUNJAB': 'PUNJAB KINGS',
        'DELHI DAREDEVILS': 'DELHI CAPITALS',
        'DECCAN CHARGERS': 'DECCAN CHARGERS', # Kept as a distinct legacy team
        'RISING PUNE SUPERGIANT': 'RISING PUNE SUPERGIANTS',
        'ROYAL CHALLENGERS BANGALORE': 'ROYAL CHALLENGERS BENGALURU'
    }
    return team_map.get(name, name)

# Apply standardization across all relevant columns in all dataframes
for df in [match_df, batting_df, bowling_df]:
    for col in df.columns:
        if 'Team' in col or 'Winner' in col:
            df[col] = df[col].apply(standardize_team_name)

# --- Step 3: Prepare Data for Each Feature ---

# Feature 1: Live Scorecard Style Match Details
print("Processing Feature 1: Full Scorecards...")
full_scorecard_data = {}
for index, match in match_df.iterrows():
    match_key = match['Match Details']
    
    # Filter batting and bowling for the current match
    current_batting = batting_df[batting_df['Match Details'] == match_key]
    current_bowling = bowling_df[bowling_df['Match Details'] == match_key]
    
    innings_order = current_batting['Team Batting'].unique()
    
    match_scorecard = {
        'match_info': match.to_dict(),
        'innings': {}
    }
    
    for i, team in enumerate(innings_order, 1):
        inning_batting = current_batting[current_batting['Team Batting'] == team]
        # The bowling team is the other team in the match
        bowling_team = match['Team 2'] if match['Team 1'] == team else match['Team 1']
        inning_bowling = current_bowling[current_bowling['Team Bowling'] == bowling_team]

        match_scorecard['innings'][f'inning_{i}'] = {
            'batting_team': team,
            'batting_card': inning_batting.to_dict('records'),
            'bowling_team': bowling_team,
            'bowling_card': inning_bowling.to_dict('records')
        }
    full_scorecard_data[match_key] = match_scorecard

with open('scorecard_data.json', 'w') as f:
    json.dump(full_scorecard_data, f, indent=2)
print(" -> Created scorecard_data.json")


# Feature 3: Leaderboard Section
print("Processing Feature 3: Seasonal Leaderboards...")
leaderboard_data = {}
all_seasons = sorted(match_df['IPL Edition'].unique(), reverse=True)

for season in all_seasons:
    season_batting = batting_df[batting_df['IPL Edition'] == season]
    season_bowling = bowling_df[bowling_df['IPL Edition'] == season]
    
    # Top 10 Batsmen
    top_batsmen = season_batting.groupby('Batsman Names')['Runs Scored'].sum().nlargest(10).reset_index()
    
    # Top 10 Bowlers
    top_bowlers = season_bowling.groupby('Bowler Name')['Wickets'].sum().nlargest(10).reset_index()
    
    leaderboard_data[season] = {
        'top_batsmen': top_batsmen.to_dict('records'),
        'top_bowlers': top_bowlers.to_dict('records')
    }

with open('leaderboards.json', 'w') as f:
    json.dump(leaderboard_data, f, indent=2)
print(" -> Created leaderboards.json")


# Feature 4: Head-to-Head Comparison
print("Processing Feature 4: Head-to-Head Stats...")
h2h_data = {}
all_teams = pd.concat([match_df['Team 1'], match_df['Team 2']]).dropna().unique()

for team1, team2 in combinations(all_teams, 2):
    h2h_key = f"{team1} vs {team2}"
    
    # Find all matches between the two teams
    h2h_matches = match_df[
        ((match_df['Team 1'] == team1) & (match_df['Team 2'] == team2)) |
        ((match_df['Team 1'] == team2) & (match_df['Team 2'] == team1))
    ].copy()
    
    if not h2h_matches.empty:
        team1_wins = (h2h_matches['Winner'] == team1).sum()
        team2_wins = (h2h_matches['Winner'] == team2).sum()
        
        # Get last 5 encounters
        last_5 = h2h_matches.sort_values(by='Date', ascending=False).head(5)
        
        h2h_data[h2h_key] = {
            'total_matches': len(h2h_matches),
            'team1_wins': int(team1_wins),
            'team2_wins': int(team2_wins),
            'last_5_encounters': last_5[['Date', 'Winner', 'Winning Details']].to_dict('records')
        }

with open('h2h_data.json', 'w') as f:
    json.dump(h2h_data, f, indent=2)
print(" -> Created h2h_data.json")

# Bonus File: A simple list of all teams for dropdowns
print("Creating a list of all teams...")
with open('teams.json', 'w') as f:
    json.dump(sorted(all_teams.tolist()), f, indent=2)
print(" -> Created teams.json")


print("\nBackend processing complete! You now have four new JSON files ready for the dashboard.")
