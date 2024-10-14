import streamlit as st
import pandas as pd
from Feed import Feed, transform_drop_off_pickup_type_to_hr
import time
from datetime import datetime
from blocks import *
import altair as alt


st.title("🚄 Train offer by station")


# Load TER GTFS data


@st.cache_data(show_spinner=False)
def load_gtfs_data(feeds_url=[]):
    progress_bar = st.progress(0.1, text="Loading GTFS data...")
    gtfs = Feed().load(feeds_url, progress_bar=progress_bar, progress_bar_start=0.1)
    progress_bar.empty()
    return gtfs


ter_gtfs_url = "https://eu.ftp.opendatasoft.com/sncf/gtfs/export-ter-gtfs-last.zip"
tgv_gtfs_url = "https://eu.ftp.opendatasoft.com/sncf/gtfs/export_gtfs_voyages.zip"
gtfs = load_gtfs_data([ter_gtfs_url, tgv_gtfs_url])

st.success(f"{gtfs.trips.shape[0]} trips loaded", icon="✅")


# Train station selection
all_stations = gtfs.get_stations()
station_selected = st.selectbox(
    "**Please select a train station**",
    all_stations,
    index=None,
    placeholder="Select a train station...",
)
if station_selected:
    st.write("You selected:", station_selected)


if station_selected:

    # Load data for selected station
    with st.status(f"Loading data for {station_selected}...", expanded=True) as status:
        st.write("Loading all trips...")
        df_today_trips = gtfs.get_today_trips(station_selected)
        time.sleep(0.2)
        st.write("Loading departures...")
        time.sleep(0.2)
        df_today_departures = gtfs.get_today_departures(
            station_selected, df_today_trips)
        time.sleep(0.2)
        st.write("Loading arrivals...")
        df_today_arrivals = gtfs.get_today_arrivals(
            station_selected, df_today_trips)
        status.update(
            label="Data loaded", state="complete", expanded=False
        )

    st.divider()

    # Display departures and arrivals
    tab_departures, tab_arrivals = st.tabs(["🏁 Departures", "🚩 Arrivals"])
    with tab_departures:
        render_trips_tab(df_today_departures, "departures",
                         "Today's departures")
    with tab_arrivals:
        render_trips_tab(df_today_arrivals, "arrivals", "Today's arrivals")

    st.divider()

    # Display departures by hour
    st.title("Trips by hour")

    df_today_trips_by_hour = transform_drop_off_pickup_type_to_hr(
        df_today_trips)
    df_today_trips_by_hour["arrival_hour"] = df_today_trips_by_hour["arrival_time"].apply(
        lambda x: x.hour)
    # df_today_trips_by_hour = pd.pivot_table(df_today_trips_by_hour, values="trip_id", columns=[
    #                                         "drop_off_pickup_type"], index=["arrival_hour"], aggfunc="count", fill_value=0)

    bars = (alt.Chart(df_today_trips_by_hour).mark_bar(size=20).encode(
        x=alt.X('arrival_hour:Q', title="Hours",
                axis=alt.Axis(
                    format='d', labelExpr="datum.value + 'h'", grid=False),
            scale=alt.Scale(domain=[3, 23])),
        y=alt.Y('count(arrival_hour):Q', title=None,
                axis=alt.Axis(
                    tickMinStep=1, format="d")),
        color=alt.Color('drop_off_pickup_type:N',
                        scale=alt.Scale(
                            range=['#fde725', '#95d840', '#20a387']),
                        legend=alt.Legend(orient='bottom', description="jes"), title="Trips type"),
        tooltip=[alt.Tooltip('arrival_hour:O', title='Hour'),
                 alt.Tooltip('count(arrival_hour):Q', title='Count'),
                 alt.Tooltip('drop_off_pickup_type:N', title='Type')]
        # column='site:N'
    ))

    st.altair_chart(bars, use_container_width=True)
    st.info("""
            **Description :**
            * *Arrival* : Train that drops off passengers but does not pick up any (end of the line)
            * *Departure* : Train that picks up passengers but does not drop off any (start of the line)
            * *Departure/Arrival* : Train that picks up and drops off passengers
            """)

    # test = df_today_trips_by_hour.groupby(
    #     ["arrival_hour", "drop_off_pickup_type"])
    # st.dataframe(test)

    # bc_today_trips_by_hour = st.bar_chart(df_today_trips_by_hour, color=(
    #     "#fde725", "#95d840", "#20a387"))

    # st.dataframe(df_today_trips)
