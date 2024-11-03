from src.imports.imports import *
from src.utils.utils import *
from src.utils.feed_utils import *
from src.utils.logger import log_message
# Used to load the GTFS data from the URL
import requests
import zipfile
import io
import emoji


class Feed:

    def __init__(self, url, name, config=None, load=False):
        self.url = url
        self.name = name
        self.config = config

        self.agency = None
        self.calendar_dates = None
        self.feed_info = None
        self.routes = None
        self.stop_times = None
        self.stops = None
        self.trips = None

        self.today_trips = None
        self.today_departures = None
        self.today_arrivals = None

        # self.station_name = None
        # self.station_feed = None

        if load:
            self.load()

    gtfs_config = {
        "agency": {"txt_file": "agency.txt", "required": False, "columns": ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang"]},
        "calendar_dates": {"txt_file": "calendar_dates.txt", "required": True, "columns": ["service_id", "date", "exception_type"]},
        "feed_info": {"txt_file": "feed_info.txt", "required": False, "columns": ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date", "feed_end_date", "feed_version"]},
        "routes": {"txt_file": "routes.txt", "required": True, "columns": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_desc", "route_type", "route_url", "route_color", "route_text_color"]},
        "stop_times": {"txt_file": "stop_times.txt", "required": True, "columns": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "stop_headsign", "pickup_type", "drop_off_type", "shape_dist_traveled"
                                                                                   ]},
        "stops": {"txt_file": "stops.txt", "required": True, "columns": ["stop_id", "stop_name", "stop_desc", "stop_lat", "stop_lon", "zone_id", "stop_url", "location_type", "parent_station"
                                                                         ]},
        "transfers": {"txt_file": "transfers.txt", "required": False, "columns": ["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"]},
        "trips": {"txt_file": "trips.txt", "required": True, "columns": ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "block_id", "shape_id"]}}

    def load(self, logger_container=False):
        feed_url = self.url
        log_message(
            f"---> Start the loading of the {self.name} GTFS data from {feed_url}", logger_container)

        response = requests.get(feed_url)
        if response.status_code != 200:
            raise ImportError("Failed to download GTFS data:" +
                              response.status_code)

        if not zipfile.is_zipfile(io.BytesIO(response.content)):
            raise FileExistsError("The file is not a zip file")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for key, record in self.gtfs_config.items():
                if record["txt_file"] in z.namelist():
                    with z.open(record["txt_file"]) as txt_file:
                        log_message(
                            f"INFO: [{self.name}] Loading {record["txt_file"]}...", logger_container)
                        # st.write(f"Loading {record["txt_file"]}...")
                        df = pd.read_csv(txt_file, sep=",")
                        if getattr(self, key, None) is None:
                            setattr(self, key, df)
                        else:
                            setattr(self, key, pd.concat(
                                [getattr(self, key), df]).drop_duplicates())
                        log_message(
                            f"SUCCESS: Loaded {len(getattr(self, key))} records from {record["txt_file"]}", logger_container)
                elif record["required"]:
                    raise FileNotFoundError(
                        f"Required file {record["txt_file"]} not found in GTFS data")

        # Manage cases where the stop_times is higher than 24h (e.g. 25:00:00) -> can happen in GTFS
        df_stop_times = self.stop_times
        date = self.calendar_dates["date"].astype(str).unique()[0]
        log_message(
            f"INFO: [{self.name}] Parsing departure time...", logger_container)
        df_stop_times["departure_time"] = df_stop_times["departure_time"].apply(
            lambda x: gtfs_time_to_datetime(date, x)
        )
        log_message(
            f"INFO: [{self.name}] Parsing arrival time...", logger_container)
        # Convertir arrival_time en datetime une seule fois
        df_stop_times["arrival_time"] = df_stop_times["arrival_time"].apply(
            lambda x: gtfs_time_to_datetime(date, x)
        )
        self.stop_times = df_stop_times

        self.loaded = True

        return self

    def get_stations(self) -> list:
        df = self.stop_times[["stop_id"]].drop_duplicates()
        df = self.add_stop_names(df)
        return np.sort(df["stop_name"].unique().tolist())

    def get_today_trips(self):
        if self.today_trips is None:
            today = now_paris().strftime("%Y%m%d")
            df_today_calendar = self.calendar_dates.loc[self.calendar_dates["date"] == int(
                today)]

            df = self.stops[["stop_id"]].merge(
                self.stop_times[["stop_id", "trip_id", "pickup_type", "drop_off_type"]], on="stop_id")
            df = df.merge(
                self.trips[["trip_id", "route_id",
                            "service_id"]], on="trip_id")
            df = df.merge(df_today_calendar, on="service_id")
            df = df.merge(
                self.routes[["route_id"]], on="route_id")

            self.today_trips = df

        return self.today_trips

    def get_today_departures(self):
        if self.today_departures is None:
            if self.today_trips is None:
                self.today_trips = self.get_today_trips()
            df_today_departures = self.today_trips[self.today_trips["pickup_type"] == 0]
            self.today_departures = df_today_departures
        return self.today_departures

    def get_today_arrivals(self):
        if self.today_arrivals is None:
            if self.today_trips is None:
                self.today_trips = self.get_today_trips()
            df_today_arrivals = self.today_trips[self.today_trips["drop_off_type"] == 0]
            self.today_arrivals = df_today_arrivals
        return self.today_arrivals

    def get_time_table_info(self):
        df = self.get_today_trips() if self.today_trips is None else self.today_trips
        df = self.add_stop_names(df)
        df = self.add_departure_arrival_time(df)
        df = self.add_trip_info(df)
        df = self.add_route_info(df)
        df = self.add_route_type_detail(df)
        if isinstance(self, StationFeed):
            df = self.add_origin_stop(df)
            df = self.add_destination_stop(df)
        return df

    def get_departures_from_df(self, df):
        return df[df["pickup_type"] == 0]

    def get_arrivals_from_df(self, df):
        return df[df["drop_off_type"] == 0]

    # Merging methods

    def merge_feed_files(self, df, Feed_attr, left_on, right_on, feed_subset, right_prefix="", how="inner"):
        check_if_column_exists(df, left_on)
        feed_file = getattr(self, Feed_attr)
        feed_file_prefixed = feed_file.add_prefix(right_prefix)
        feed_subset = [
            f"{right_prefix}{col}" for col in feed_subset] if right_prefix else feed_subset
        if right_prefix:
            right_on = [f"{right_prefix}{col}" for col in right_on] if isinstance(
                right_on, list) else f"{right_prefix}{right_on}"
        df = df.merge(feed_file_prefixed[feed_subset],
                      left_on=left_on, right_on=right_on, how=how, copy=False)
        if left_on != right_on:
            df.drop(columns=[right_on], inplace=True)
        return df

    def add_stop_names(self, df, stop_id="stop_id", subset=None, right_prefix=""):
        if subset is None:
            subset = ["stop_id", "stop_name"]
        return self.merge_feed_files(df, "stops", stop_id, "stop_id", subset, right_prefix)

    def add_departure_arrival_time(self, df, stop_id="stop_id", trip_id="trip_id", subset=None, right_prefix=""):
        if subset is None:
            subset = ["stop_id", "trip_id", "arrival_time", "departure_time"]
        return self.merge_feed_files(df, "stop_times", [stop_id, trip_id], ["stop_id", "trip_id"], subset, right_prefix)

    def add_trip_info(self, df, trip_id="trip_id", route_id="route_id", subset=None, right_prefix=""):
        if subset is None:
            subset = ["trip_id", "route_id", "trip_headsign"]
        return self.merge_feed_files(df, "trips", [trip_id, route_id], ["trip_id", "route_id"], subset, right_prefix)

    def add_route_info(self, df, route_id="route_id", subset=None, right_prefix=""):
        if subset is None:
            subset = ["route_id", "route_short_name", "route_long_name",
                      "route_color", "route_text_color", "route_type"]
        return self.merge_feed_files(df, "routes", route_id, "route_id", subset, right_prefix)

    def add_route_type_detail(self, df, show_emoji=True, route_type="route_type", right_prefix=""):
        if df.empty:
            return df
        required_columns = {"route_type", "stop_id"}
        if not required_columns.issubset(df.columns):
            raise ValueError(
                f'{required_columns} columns are required. {df.columns} columns were passed')
        # The SNCF GTS route_type is not 100% reliable. Some routes pass by "Car" station but are tagged as train. Therefore, we will use the stop_id as a first condition to determine the route type
        df[route_type] = df.apply(
            lambda x: 3 if "Car" in x["stop_id"] else x[route_type], axis=1)
        df["route_detail"] = df[route_type].apply(
            lambda x: self.config["route_type"][str(x)]["name"])

        if show_emoji:
            df["route_emoji"] = df[route_type].apply(
                lambda x: emoji.emojize(self.config["route_type"][str(x)]["emoji"], language='alias'))
        return df

    def add_stations_coordinates(self, df, stop_id="stop_id", right_prefix=""):
        subset = ["stop_id", "stop_lat", "stop_lon"]
        if isinstance(self, StationFeed):
            df = self.parent_feed.merge_feed_files(
                df, "stops", stop_id, "stop_id", subset, right_prefix)
        else:
            df = self.merge_feed_files(
                df, "stops", stop_id, "stop_id", subset, right_prefix)
        return df


class StationFeed(Feed):
    def __init__(self, parent_feed,  url: str, name: str, station: str, config=None, load=False):
        super().__init__(url, name, config)
        self.station = station
        self.parent_feed = parent_feed
        if load:
            self.load()

    def load(self, logger_container):
        self.stops = self.parent_feed.stops[self.parent_feed.stops["stop_name"].str.contains(
            self.station, case=False)]

        self.stop_times = self.parent_feed.stop_times[self.parent_feed.stop_times["stop_id"].isin(
            self.stops["stop_id"].unique())]

        self.trips = self.parent_feed.trips[self.parent_feed.trips["trip_id"].isin(
            self.stop_times["trip_id"].unique())]

        self.routes = self.parent_feed.routes[self.parent_feed.routes["route_id"].isin(
            self.trips["route_id"].unique())]

        self.calendar_dates = self.parent_feed.calendar_dates[self.parent_feed.calendar_dates["service_id"].isin(
            self.trips["service_id"].unique())]

        self.transfers = self.parent_feed.transfers[self.parent_feed.transfers["from_stop_id"].isin(
            self.stops["stop_id"].unique())]

        self.loaded = True

        return self

    def get_station_coordinates(self):
        coord = self.stops[["stop_lat", "stop_lon"]
                           ].drop_duplicates().reset_index(drop=True)
        return coord.to_dict('records')[0] if len(coord) == 1 else {}

    def add_intermediate_stop(self, df, stop_name=True):
        df = df[df["feed_name"] == self.name]
        # Get the stops except the selected one
        df_stops_except_selected = self.parent_feed.stop_times[~self.parent_feed.stop_times["stop_id"].isin(
            df["stop_id"].unique())]
        df = df.merge(df_stops_except_selected[["trip_id", "stop_id"]].add_prefix("intermediate_"), left_on="trip_id", right_on="intermediate_trip_id", how="inner",
                      suffixes=("", "_intermediate_stop"), copy=False).drop(columns="intermediate_trip_id")
        df = self.parent_feed.add_stop_names(
            df, stop_id="intermediate_stop_id", right_prefix="intermediate_")
        return df

    def add_origin_stop(self, df, stop_id="stop_id", subset=None, right_prefix=""):
        df_station_trips_stops = self.parent_feed.stop_times[self.parent_feed.stop_times["trip_id"].isin(
            df["trip_id"].unique())][["trip_id", "stop_id", "stop_sequence"]]

        df_station_trips_origin_stop = df_station_trips_stops[
            df_station_trips_stops["stop_sequence"] == 0].drop(columns="stop_sequence")
        df_station_trips_origin_stop = df_station_trips_origin_stop.add_prefix(
            "origin_")
        df_station_trips_origin_stop = self.parent_feed.add_stop_names(
            df_station_trips_origin_stop, stop_id="origin_stop_id", right_prefix="origin_")
        return df.merge(df_station_trips_origin_stop[["origin_trip_id", "origin_stop_name"]], left_on="trip_id", right_on="origin_trip_id", copy=False, how="left").drop(columns="origin_trip_id")

    def add_destination_stop(self, df, stop_id="stop_id", subset=None, right_prefix=""):
        df_station_trips_stops = self.parent_feed.stop_times[self.parent_feed.stop_times["trip_id"].isin(
            df["trip_id"].unique())][["trip_id", "stop_id", "stop_sequence"]]

        df_station_trips_destination_stop = df_station_trips_stops.loc[
            df_station_trips_stops.groupby("trip_id")["stop_sequence"].idxmax()
        ].drop(columns="stop_sequence")
        df_station_trips_destination_stop = df_station_trips_destination_stop.add_prefix(
            "destination_")
        df_station_trips_destination_stop = self.parent_feed.add_stop_names(
            df_station_trips_destination_stop, stop_id="destination_stop_id", right_prefix="destination_")
        return df.merge(df_station_trips_destination_stop[["destination_trip_id", "destination_stop_name"]], left_on="trip_id", right_on="destination_trip_id", copy=False, how="left").drop(columns="destination_trip_id").reset_index(drop=True)
