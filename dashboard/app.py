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

st.subheader(f"Drivers' championship {season}")
st.dataframe(standings, hide_index=True)