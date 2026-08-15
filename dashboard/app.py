import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

st.set_page_config(page_title="Brussels Bike Share Intelligence", page_icon="🚲", layout="wide")
st.title("🚲 Brussels Bike Share Intelligence")
st.caption("Live Villo! availability snapshots, historical signals and weather context.")

@st.cache_data(ttl=300)
def read_data() -> pd.DataFrame:
    url = os.getenv("DATABASE_URL", "postgresql+psycopg://mobility:mobility@localhost:5433/mobility")
    engine = create_engine(url)
    stations = pd.read_sql("""SELECT s.*, d.station_name, d.latitude, d.longitude, d.capacity
        FROM fact_station_status s JOIN dim_bike_station d USING (station_id)
        ORDER BY snapshot_at DESC""", engine)
    weather = pd.read_sql("SELECT * FROM fact_mobility_weather ORDER BY observed_at", engine)
    return stations, weather

try:
    data, weather = read_data()
except (SQLAlchemyError, ValueError):
    st.info("Run the ETL first: `mobility-etl`. Then reload this page.")
    st.stop()

latest_at = data.snapshot_at.max()
view = data[data.snapshot_at.eq(latest_at)].copy()
one, two, three = st.columns(3)
one.metric("Live stations", f"{len(view):,}")
two.metric("Bikes available", f"{view.available_bikes.sum():,}")
three.metric("Empty stations", f"{view.available_bikes.eq(0).sum():,}")
st.caption(f"Latest source snapshot: {latest_at:%d %b %Y, %H:%M UTC}")
left, right = st.columns(2)
with left:
    st.plotly_chart(px.scatter_map(view, lat="latitude", lon="longitude", size="available_bikes", color="availability_state", hover_name="station_name", hover_data=["available_bikes", "available_docks", "occupancy_pct"], zoom=10, height=520, title="Current Villo! station availability"), use_container_width=True)
with right:
    st.plotly_chart(px.bar(view.sort_values("available_bikes").head(15), x="available_bikes", y="station_name", orientation="h", color="availability_state", title="15 stations with least available bikes"), use_container_width=True)
if not weather.empty:
    forecast = weather[weather.city.eq("Brussels")]
    st.plotly_chart(px.line(forecast, x="observed_at", y="estimated_mobility_demand", color_discrete_sequence=["#2563eb"], title="Brussels weather-adjusted demand signal"), use_container_width=True)
