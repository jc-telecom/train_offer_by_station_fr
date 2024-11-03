from src.imports.imports import *
from src.style.style import *
from src.utils.utils import *
from src.utils.feed_utils import *
from src.utils.map_utils import *
import altair as alt
import folium
from streamlit_folium import st_folium


def rendrer_route_type_legend(df_today_time_table, show_title=False):
    check_if_column_exists(df_today_time_table, [
        "route_detail", "route_emoji"])
    if show_title:
        st.markdown("**🚉 Route type legend**")
    routes = df_today_time_table[[
        "route_detail", "route_emoji"]].drop_duplicates()
    texts = [
        f"{row['route_emoji']} {row['route_detail']}"
        for index, row in routes.iterrows()
    ]
    st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(texts))


def render_global_metrics(df_today_time_table):
    # Calculate the number of trips
    num_trips = df_today_time_table.shape[0]
    st.metric("🕗 Number of trips", num_trips)


def render_trips_tab(df_today_time_table, trip_type, title):
    if trip_type not in ["departures", "arrivals"]:
        raise ValueError("trip_type must be 'departures' or 'arrivals'")

    time_column = "departure_time" if trip_type == "departures" else "arrival_time"
    destination_column = "destination_stop_name" if trip_type == "departures" else "origin_stop_name"
    show_only_next_trips_label = "Show only next departures" if trip_type == "departures" else "Show only next arrivals"
    metrics_labels = [
        {"departures": "Number of departures today",
            "arrivals": "Number of arrivals"},
        {"departures": "Next departure", "arrivals": "Next arrival"}]

    # Tab title
    st.title(title, "next_trips")

    # Tab metrics
    col_metric_1, col_metric_2 = st.columns(2)
    next_trip = df_today_time_table[df_today_time_table[time_column] > now_paris().time()].iloc[0][time_column].strftime(
        "%H:%M") if df_today_time_table[df_today_time_table[time_column] > now_paris().time()].shape[0] > 0 else "😴"
    metrics_values = [
        {"departures": df_today_time_table.shape[0],
            "arrivals": df_today_time_table.shape[0]},
        {"departures": next_trip or "None",
            "arrivals": next_trip or "None"}
    ]
    for index, col_metric in enumerate([col_metric_1, col_metric_2]):
        col_metric.metric(
            label=metrics_labels[index][trip_type], value=metrics_values[index][trip_type])

    if show_only_next_trips := st.toggle(show_only_next_trips_label, False):
        df_today_time_table = df_today_time_table[df_today_time_table[time_column] > now_paris(
        ).time()]

    # Dispay the dataframe
    column_order = ["route_emoji", time_column, "trip_headsign",
                    destination_column, "route_short_name"]
    st.dataframe(style_trips_results(df_today_time_table, trip_type),
                 use_container_width=True, hide_index=True,
                 column_order=column_order,
                 column_config={

        "route_emoji": st.column_config.Column(
            "Type"),
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
    rendrer_route_type_legend(df_today_time_table)


def render_trips_by_hour(df_today_time_table):
    df_today_time_table_by_hour = transform_drop_off_pickup_type_to_hr(
        df_today_time_table)
    df_today_time_table_by_hour["arrival_hour"] = df_today_time_table_by_hour["arrival_time"].apply(
        lambda x: x.hour)

    barChart_hour_distribution = (alt.Chart(df_today_time_table_by_hour).mark_bar().encode(
        x=alt.X('arrival_hour:O', title="Hours",
                axis=alt.Axis(
                    format='s', labelExpr="datum.value + 'h'", grid=False),
                scale=alt.Scale(domain=list(range(24)), padding=0.1)),
        y=alt.Y('count(arrival_hour):Q', title=None,
                axis=alt.Axis(
                    tickMinStep=1, format="d")),
        color=alt.Color('drop_off_pickup_type:N',
                        scale=alt.Scale(domain=pickup_dropoff_domain,
                                        range=pickup_dropoff_range),
                        legend=alt.Legend(orient='bottom'), title="Trips type"),
        tooltip=[alt.Tooltip('arrival_hour:O', title='Hour'),
                 alt.Tooltip('count(arrival_hour):Q', title='Count'),
                 alt.Tooltip('drop_off_pickup_type:N', title='Type')]
    ))

    st.altair_chart(barChart_hour_distribution, use_container_width=True)
    st.info("""
            **Description :**
            * *Arrival* : Train that drops off passengers but does not pick up any (end of the line)
            * *Departure* : Train that picks up passengers but does not drop off any (start of the line)
            * *Departure/Arrival* : Train that picks up and drops off passengers
            """)


def render_trips_by_type(df_today_time_table):

    df_today_time_table["arrival_hour"] = df_today_time_table["arrival_time"].apply(
        lambda x: x.hour)

    barChart_type_hour_distribution = alt.Chart(df_today_time_table).mark_bar().encode(
        x=alt.X('arrival_hour:O', title="Hours",
                axis=alt.Axis(
                    format='s', labelExpr="datum.value + 'h'", grid=False),
                scale=alt.Scale(domain=list(range(24)), padding=0.1)),
        y=alt.Y('count(arrival_hour):Q', title=None,
                axis=alt.Axis(
                    tickMinStep=1, format="d")),
        color=alt.Color('route_detail:N',
                        scale=alt.Scale(domain=route_detail_domain,
                                        range=route_detail_range),
                        legend=alt.Legend(orient='bottom'), title="Route type"),
        tooltip=[alt.Tooltip('arrival_hour:O', title='Hour'),
                 alt.Tooltip('count(arrival_hour):Q', title='Count'),
                 alt.Tooltip('route_detail:N', title='Type')]
    )

    st.altair_chart(barChart_type_hour_distribution, use_container_width=True)


def render_top_10_most_served(gtfs_station_feeds, df_today_time_table_intermediate_stops):

    df_most_served_station = df_today_time_table_intermediate_stops.groupby(
        ["intermediate_stop_name", "route_detail"]).size().reset_index(name='count')

    df_most_served_station["count_station"] = df_most_served_station.apply(
        lambda x: df_most_served_station[df_most_served_station["intermediate_stop_name"] == x["intermediate_stop_name"]]["count"].sum(), axis=1)

    # To get the top 10 most served stations need to sum the count of each station (considering the route type)
    top_10_stations = df_most_served_station.groupby(
        'intermediate_stop_name')['count_station'].sum().nlargest(10).index
    df_most_served_station_10 = df_most_served_station[df_most_served_station["intermediate_stop_name"].isin(
        top_10_stations)].sort_values(["count_station"], ascending=False)

    barChart_most_served_stations = (alt.Chart(df_most_served_station_10).mark_bar().encode(
        x=alt.X('count:Q', title=None,
                axis=alt.Axis(
                    tickMinStep=1, format="d")),
        y=alt.Y('intermediate_stop_name:N', title=None,
                sort=df_most_served_station_10["intermediate_stop_name"].tolist(
                ),
                axis=alt.Axis(labelLimit=200, labelPadding=10)),

        color=alt.Color('route_detail:N', scale=alt.Scale(domain=route_detail_domain,
                        range=route_detail_range),                        legend=alt.Legend(orient='bottom'), title="Route type"),
        tooltip=[alt.Tooltip('count:Q', title='Count'),
                 alt.Tooltip('intermediate_stop_name:N', title='Station'),
                 alt.Tooltip('route_detail:N', title='Type')]


    ))

    st.altair_chart(
        barChart_most_served_stations, use_container_width=True)


def render_destination_map(gtfs_station_feeds, df_today_time_table_intermediate_stops):
    df_today_time_table_coord = gtfs_station_feeds.add_stations_coordinates(
        df_today_time_table_intermediate_stops, stop_id="intermediate_stop_id", right_prefix="intermediate_")
    station_coordinates = gtfs_station_feeds.get_station_coordinates()
    station_coordinates_list = [
        station_coordinates["stop_lat"], station_coordinates["stop_lon"]]
    map_data = df_today_time_table_coord[df_today_time_table_coord["intermediate_stop_name"] != gtfs_station_feeds.station_name].groupby(
        ["intermediate_stop_name", "intermediate_stop_lat", "intermediate_stop_lon"]).size().reset_index(name='count').sort_values(by="count", ascending=False, ignore_index=True)

    m = folium.Map(location=station_coordinates_list, tiles="Cartodb Positron")
    for idx, row in map_data.sort_values(by="count", ascending=True, ignore_index=True).iterrows():
        color = viridis_based_on_value_hex(
            row["count"], map_data["count"].min(), map_data["count"].max())

        folium.PolyLine(
            locations=[station_coordinates_list, [
                row["intermediate_stop_lat"], row["intermediate_stop_lon"]]],
            color=color,
            line_cap="round",
            weight=normalize_value(
                row["count"], map_data["count"].min(), map_data["count"].max(), 0.25, 10),
            opacity=normalize_value(
                row["count"], map_data["count"].min(), map_data["count"].max(), 0.3, 1)

        ).add_to(m)
        folium.CircleMarker(
            location=[row["intermediate_stop_lat"],
                      row["intermediate_stop_lon"]],
            radius=normalize_value(
                row["count"], map_data["count"].min(), map_data["count"].max(), 0.25, 12),
            color=color,
            fill=True,
            fill_color="#FFFFFF",
            fill_opacity=1,
            popup=f"{row['intermediate_stop_name']} ({row['count']} trips)",
        ).add_to(m)

    map_bounds = get_map_bounds(map_data.head(10), "intermediate_stop_lat",
                                "intermediate_stop_lon", center=station_coordinates_list)
    m.fit_bounds(map_bounds)

    st_data = st_folium(m, width=1500, returned_objects=[])
