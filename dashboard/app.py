import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

st.set_page_config(page_title="Belgium Mobility Signals", page_icon="🚲", layout="wide")
st.title("🚲 Belgium Mobility Signals")
st.caption("A portfolio ETL dashboard — weather forecasts translated into a transparent demand signal.")

@st.cache_data(ttl=300)
def read_data() -> pd.DataFrame:
    url = os.getenv("DATABASE_URL", "postgresql+psycopg://mobility:mobility@localhost:5432/mobility")
    return pd.read_sql("SELECT * FROM fact_mobility_weather ORDER BY observed_at", create_engine(url))

try:
    data = read_data()
except (SQLAlchemyError, ValueError):
    st.info("Run the ETL first: `mobility-etl`. Then reload this page.")
    st.stop()

city = st.selectbox("City", sorted(data.city.unique()))
view = data[data.city.eq(city)]
one, two, three = st.columns(3)
one.metric("Forecast rows", f"{len(view):,}")
two.metric("Avg. demand signal", f"{view.estimated_mobility_demand.mean():.0f}")
three.metric("Rainy hours", f"{view.is_rainy.mean():.0%}")
st.plotly_chart(px.line(view, x="observed_at", y="estimated_mobility_demand", color_discrete_sequence=["#2563eb"], title=f"Expected demand — {city}"), use_container_width=True)
st.plotly_chart(px.bar(view, x="observed_at", y="precipitation_mm", color="is_rainy", title="Precipitation forecast"), use_container_width=True)
