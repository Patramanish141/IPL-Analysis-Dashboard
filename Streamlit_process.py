import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re

# -------------------- Helper to clean team names --------------------
def clean_team_name(name):
    return re.sub(r",.*", "", name).strip()

# -------------------- Improved Sorting --------------------
def match_sort_key(details):
    details = details.lower()
    if "final" in details and "semi" not in details:
        return 9999
    if "semi" in details:
        return 9997
    if "qualifier" in details or "eliminator" in details:
        return 9998
    match_num = re.findall(r'(\d+)(st|nd|rd|th) match', details)
    if match_num:
        return int(match_num[0][0])
    return 9996

# -------------------- Season Winners Dictionary --------------------
season_winners = {
    2008: "Rajasthan Royals",
    2009: "Deccan Chargers",
    2010: "Chennai Super Kings",
    2011: "Chennai Super Kings",
    2012: "Kolkata Knight Riders",
    2013: "Mumbai Indians",
    2014: "Kolkata Knight Riders",
    2015: "Mumbai Indians",
    2016: "Sunrisers Hyderabad",
    2017: "Mumbai Indians",
    2018: "Chennai Super Kings",
    2019: "Mumbai Indians",
    2020: "Mumbai Indians",
    2021: "Chennai Super Kings",
    2022: "Gujarat Titans",
    2023: "Chennai Super Kings"
}

# -------------------- Load Data --------------------
with open("IPL DASHBOARD JSON.json") as f:
    data = json.load(f)

matches = []
for match_name, match_data in data.items():
    info = match_data["match_info"]
    info["Match"] = match_name
    matches.append(info)

df_matches = pd.DataFrame(matches)

# -------------------- Dashboard Title --------------------
st.title("🏏 IPL Analysis Dashboard")
st.markdown("Welcome to the interactive IPL dashboard!")

# -------------------- Overall Metrics --------------------
all_teams = set()
for match in df_matches['Match']:
    t1, t2 = match.split(" vs ")
    all_teams.add(clean_team_name(t1))
    all_teams.add(clean_team_name(t2))

col1, col2, col3 = st.columns(3)
col1.metric("Total Matches", len(df_matches))
col2.metric("Total Teams", len(all_teams))
col3.metric("Seasons", df_matches['IPL Edition'].nunique())

# -------------------- Sidebar Filters --------------------
st.sidebar.header("Filters 🎛️")
season = st.sidebar.selectbox("Select Season", sorted(df_matches['IPL Edition'].unique()))
filtered_df = df_matches[df_matches['IPL Edition'] == season]

# sort matches properly
filtered_df = filtered_df.sort_values(by="Match Details", key=lambda x: x.map(match_sort_key))

# -------------------- Season-specific Metrics --------------------
st.markdown(f"### 📊 Stats for {season} Season")
col1, col2 = st.columns(2)
col1.metric("Matches this Season", len(filtered_df))

teams_in_season = set()
for match in filtered_df['Match']:
    t1, t2 = match.split(" vs ")
    teams_in_season.add(clean_team_name(t1))
    teams_in_season.add(clean_team_name(t2))
col2.metric("Teams this Season", len(teams_in_season))

winner = season_winners.get(season, "Data Not Available")
st.markdown(f"🏆 **Winner of {season} Season:** {winner}")

# -------------------- Tabs --------------------
tab1, tab2, tab3 = st.tabs(["📅 Match Info", "📊 Stats", "📈 Visuals"])

# ---- Tab 1: Match Info ----
with tab1:
    st.subheader("Match Information")
    for idx, row in filtered_df.reset_index(drop=True).iterrows():
        match_title = f"📌 {row['Match Details']}"
        with st.expander(match_title, expanded=False):
            st.write(f"**Date:** {row['Date']}")
            st.write(f"**Time:** {row['Time']}")
            st.write(f"**Season:** {row['IPL Edition']}")
            st.write(f"**Winner:** {row.get('Winner', 'Data Not Available')}")

# ---- Tab 2: Stats ----
with tab2:
    st.subheader("Team Appearances")
    teams = filtered_df['Match'].str.split(" vs ").explode()
    teams = teams.apply(clean_team_name)
    team_counts = teams.value_counts().reset_index()
    team_counts.columns = ["Team", "Matches Played"]
    st.dataframe(team_counts)

# ---- Tab 3: Visuals ----
with tab3:
    st.subheader("Matches per Season (Overall IPL)")
    fig = px.histogram(df_matches, x="IPL Edition", title="Matches per Season")
    st.plotly_chart(fig)
