import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Flight Data Dashboard", layout="wide")
st.title("Trip.com flights data interactive Dashboard")

df = pd.read_csv('trip_flights_final.csv')

df["Departure Time"] = pd.to_datetime(df["Departure Time"], errors="coerce")
df["Arrival Time"] = pd.to_datetime(df["Arrival Time"], errors="coerce")

df = df.dropna(subset=["Departure Time", "Arrival Time", "Price(in dollars)"])

df["Duration_in_hours"] = (
    df["Arrival Time"] - df["Departure Time"]
).dt.total_seconds() / 3600

df = df[df["Duration_in_hours"].notna()]

st.sidebar.header("Filters")

from_city = st.sidebar.selectbox(
    "From",
    sorted(df["From"].unique())
)

to_city = st.sidebar.selectbox(
    "To",
    sorted(df["To"].unique())
)

airlines = sorted(df["Airline"].unique())
selected_airlines = st.sidebar.multiselect(
    "Airline",
    airlines,
    default=airlines
)

price_min, price_max = int(df["Price(in dollars)"].min()), int(df["Price(in dollars)"].max())
price_range = st.sidebar.slider(
    "Price (in $)",
    price_min,
    price_max,
    (price_min, price_max)
)

dur_min, dur_max = int(df["Duration_in_hours"].min()), int(df["Duration_in_hours"].max())
if dur_min == dur_max:
    st.sidebar.info(f"All flights have duration ≈ {dur_min} hours")
    duration_range = (dur_min, dur_max)
else:
    duration_range = st.sidebar.slider(
        "Duration (in hours)",
        dur_min,
        dur_max,
        (dur_min, dur_max)
    )

filtered_df = df[
    (df["From"] == from_city)
    & (df["To"] == to_city)
    & (df["Airline"].isin(selected_airlines))
    & (df["Price(in dollars)"].between(*price_range))
    & (df["Duration_in_hours"].between(*duration_range))
]

st.caption(f"Showing **{filtered_df.shape[0]}** flights after filters")

if filtered_df.empty:
    st.warning("No flights match the selected filters.")
    st.stop()

fig = px.scatter(
    filtered_df,
    x="Duration_in_hours",
    y="Price(in dollars)",
    color="Airline",
    size="Duration_in_hours",
    hover_data=[
        "Airline",
        "From",
        "To",
        "Departure Time",
        "Arrival Time",
        "Price(in dollars)",
        "Duration_in_hours"
    ],
    labels={
        "Duration_in_hours": "Duration (hours)",
        "Price(in dollars)": "Price ($)"
    },
    title="Price vs Duration of Flights"
)

fig.update_layout(
    legend_title="Airline",
    xaxis_title="Duration (hours)",
    yaxis_title="Price ($)"
)
fig1 = px.scatter(
    filtered_df,
    x = 'Price(in dollars)',
    y = 'Airline',
    color='Airline',
    title = 'Airline vs Price distribution',
    labels= {'Price(in dollars)':'Price ($)'}, 
    hover_data=['Airline','Price(in dollars)','From','To','Departure Time','Arrival Time'],
    color_discrete_sequence=px.colors.qualitative.Plotly
)

fig1.update_layout(
    legend_title="Airline", 
    xaxis_title="Price ($)", 
    yaxis_title="Airline"
)

try:
   st.plotly_chart(fig, use_container_width=True)
   st.plotly_chart(fig1, use_container_width=True)
except st.errors.StreamlitAPIException as e: 
    print(f"Error displaying plot: {e}")
