import folium
from streamlit_folium import st_folium
import altair as alt
from src.utils.source_reader import read_source_file
from src.assets.blocks import *
from src.classes.Feeds import *
from src.imports.imports import *


st.set_page_config(
    page_title="Train offer by station",
    page_icon="🚅",
    layout="wide",
)


st.title("🚄 Train offer by station")
col_description, col_logo = st.columns([3, 1])
col_description.write(
    "A simple streamlit app showing key metrics of the SNCF railway offer in France based on GTFS Schedule feeds.")

with col_logo:
    st.image(
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpxh8YP21u7oxu6k5Qa3bRxX5rou54GcFltw&s", width=50)
# css style
st.markdown(
    "<style>.st-emotion-cache-1kyxreq.e115fcil2{justify-content: flex-end}</style>", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
# Function to load GTFS data
def load_gtfs_data(feeds_url, feeds_name, feeds_configs=None):
    with st.spinner(text=f"Downloading GTFS data for {", ".join(gtfs_names)}... (this could take up to 1 minute)"):
        code = st.code("Loading GTFS data...")
        feeds = Feeds(feeds_url, feeds_name, feeds_configs).load(
            logger_container=code)
        code.empty()
    return feeds


# Read source file that stores GTFS feeds information
source_file = read_source_file()
gtfs_names = [value["name"] for key, value in source_file.items()]
gtfs_urls = [value["url"] for key, value in source_file.items()]
gtfs_feeds_config = [value["config"] for key, value in source_file.items()]
gtfs_feeds = load_gtfs_data(
    gtfs_urls, gtfs_names, gtfs_feeds_config)

# Display the number of trips loaded
trips_loaded = gtfs_feeds.get_trips_count()
st.success(f" {"{:,}".format(trips_loaded)} trips loaded", icon="✅")

# Get the overall time table
df_today_time_table = gtfs_feeds.get_time_table_info()


####################################################
# Train station selection
all_stations = gtfs_feeds.get_stations()
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
        gtfs_station_feeds = gtfs_feeds.create_station_feeds(
            station_selected).load()
        df_today_time_table = gtfs_station_feeds.get_time_table_info()
        time.sleep(0.1)

        st.write("Loading departures...")
        df_today_departures = gtfs_station_feeds.get_departures_from_dfs(
            df_today_time_table)
        time.sleep(0.1)

        st.write("Loading arrivals...")
        df_today_arrivals = gtfs_station_feeds.get_arrivals_from_dfs(
            df_today_time_table)
        status.update(label="Data loaded", state="complete", expanded=False)
    st.divider()

    # Display summary
    st.title("📌 Summary")
    st.markdown("""
                ### 1. [Today's timetable](#next_trips)
                ### 2. [Trips by hour](#trips_by_hour)
                ### 3. [Trips by type](#trips_by_type)
                ### 4. [Top 10 most served train stations](#most_served_train_stations)
                """)
    st.divider()

    ####################################################
    # Display departures and arrivals
    col_departures, col_arrivals = st.columns(2)
    # tab_departures, tab_arrivals = st.tabs(["🏁 Departures", "🚩 Arrivals"])
    with col_departures:
        render_trips_tab(df_today_departures, "departures",
                         "➡️ Today's departures")
    with col_arrivals:
        render_trips_tab(df_today_arrivals,
                         "arrivals", "⏸️ Today's arrivals")

    st.divider()

    # Display departures by hour
    col_trips_by_hour, col_trips_by_type = st.columns(2)
    with col_trips_by_hour:
        st.title("⏰ Trips by hour", "trips_by_hour")
        render_trips_by_hour(df_today_time_table)

    # Display departures by route type
    with col_trips_by_type:
        st.title("🚉 Trips by type", "trips_by_type")
        render_trips_by_type(df_today_time_table)
    st.divider()

    #############################
    # Mot served train stations

    st.title(
        f"🔝 Top 10 most served train stations from {station_selected}",  "most_served_train_stations")
    df_today_time_table_intermediate_stops = gtfs_station_feeds.add_intermediate_stop(
        df_today_time_table)
    render_top_10_most_served(
        gtfs_station_feeds, df_today_time_table_intermediate_stops)
    st.divider()

    #############################
    # Map of stations served
    st.title("🗺️ Location of stations served")
    render_destination_map(
        gtfs_station_feeds, df_today_time_table_intermediate_stops)
