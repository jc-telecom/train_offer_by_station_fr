import streamlit as st
import pandas as pd
from datetime import datetime
from style import *


def render_trips_tab(df, trip_type, title):
    if trip_type not in ["departures", "arrivals"]:
        raise ValueError("trip_type must be 'departures' or 'arrivals'")

    time_column = "departure_time" if trip_type == "departures" else "arrival_time"
    destination_column = "terminus_stop_name" if trip_type == "departures" else "starting_stop_name"
    show_only_next_trips_label = "Show only next departures" if trip_type == "departures" else "Show only next arrivals"

    # Tab title
    st.title(title, "next_trips")

    # Tab metrics
    col_metric_1, col_metric_2 = st.columns(2)
    metrics_labels = [
        {"departures": "Number of departures today",
            "arrivals": "Number of arrivals"},
        {"departures": "Next departure", "arrivals": "Next arrival"}]
    next_trip = df[df[time_column] > datetime.now(
    ).time()].iloc[0][time_column].strftime("%H:%M") if df[df[time_column] > datetime.now().time()].shape[0] > 0 else None
    metrics_values = [
        {"departures": df.shape[0],
            "arrivals": df.shape[0]},
        {"departures": next_trip if next_trip else "None",
            "arrivals": next_trip if next_trip else "None"}
    ]

    for index, col_metric in enumerate([col_metric_1, col_metric_2]):
        col_metric.metric(
            label=metrics_labels[index][trip_type], value=metrics_values[index][trip_type])

    ########################################
    # DATAFRAME

    # Display only the next trips button
    show_only_next_trips = st.toggle(
        show_only_next_trips_label, False)
    if show_only_next_trips:
        df = df[df[time_column] > datetime.now(
        ).time()]

    # Show the dataframe
    column_order = [time_column, "trip_headsign",
                    destination_column, "route_short_name"]
    st.dataframe(style_trips_results(df),
                 use_container_width=True, hide_index=True,
                 column_order=column_order,
                 column_config={
        time_column: st.column_config.TimeColumn(
            "Departure time" if trip_type == "departures" else "Arrival time",
            format="HH:mm",
        ),
        "trip_headsign": st.column_config.NumberColumn(
            "Train number",
        ),
        "route_short_name": st.column_config.Column(
            "Line",
        ),
        destination_column: st.column_config.Column(
            "Destination" if trip_type == "departures" else "Origin",
        ),
    },)
