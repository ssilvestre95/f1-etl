import os

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="F1 Analytics", page_icon="🏎️", layout="wide")


@st.cache_data(ttl=3600)
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a read-only query and return the result as a DataFrame."""
    with psycopg.connect(os.environ["DASHBOARD_DATABASE_URL"]) as conn:
        cur = conn.execute(sql, params)
        columns = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


st.title("F1 Analytics")

seasons = run_query(
    "SELECT DISTINCT season FROM analytics.driver_standings ORDER BY season DESC"
)["season"].tolist()
season = st.sidebar.selectbox("Season", seasons)

standings = run_query(
    """
    SELECT championship_position AS pos,
           driver_name AS driver,
           points, wins, podiums
    FROM analytics.driver_standings
    WHERE season = %s
    ORDER BY championship_position
    """,
    (season,),
)

race_points = run_query(
    """
    SELECT round, constructor_name, cumulative_points
    FROM analytics.constructor_points_by_race
    WHERE season = %s
    ORDER BY round
    """,
    (season,),
)

leader = standings.iloc[0]
last_round = race_points["round"].max()
latest = race_points[race_points["round"] == last_round]
top_team = latest.sort_values("cumulative_points", ascending=False).iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric(
    "Championship leader",
    leader["driver"],
    f"{leader['points']:.0f} pts",
    delta_color="off",
)
col2.metric(
    "Leading constructor",
    top_team["constructor_name"],
    f"{top_team['cumulative_points']:.0f} pts",
    delta_color="off",
)
col3.metric("Races held", int(last_round))

st.subheader(f"Drivers' championship {season}")
st.dataframe(
    standings,
    hide_index=True,
    height=400,
    column_config={
        "pos": st.column_config.NumberColumn("Pos", width="small"),
        "driver": st.column_config.TextColumn("Driver", width="medium"),
        "points": st.column_config.ProgressColumn(
            "Points",
            format="%.0f",
            min_value=0,
            max_value=float(standings["points"].max()),
            width="large",
        ),
        "wins": st.column_config.NumberColumn("Wins", width="small"),
        "podiums": st.column_config.NumberColumn("Podiums", width="small"),
    },
)

TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine F1 Team": "#FF87BC",
    "Williams": "#64C4FF",
    "RB F1 Team": "#6692FF",
    "Racing Bulls": "#6692FF",
    "Sauber": "#52E252",
    "Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
    "AlphaTauri": "#5E8FAA",
    "Alfa Romeo": "#C92D4B",
    "Renault": "#FFF500",
}
DEFAULT_COLOR = "#888888"


st.subheader(f"Constructors' points by round {season}")
evolution = race_points.pivot(
    index="round", columns="constructor_name", values="cumulative_points"
)
teams = list(evolution.columns)
st.line_chart(evolution, color=[TEAM_COLORS.get(t, DEFAULT_COLOR) for t in teams])

unmapped = [t for t in teams if t not in TEAM_COLORS]
if unmapped:
    st.caption(f"No color defined for: {', '.join(unmapped)}")