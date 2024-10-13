import pandas as pd
import requests
import zipfile
import io
import numpy as np
from datetime import datetime


class Feed:

    def __init__(self):
        self.feed_url = ""
        self.agency = None
        self.calendar_dates = None
        self.feed_info = None
        self.routes = None
        self.stop_times = None
        self.stops = None
        self.trips = None

    gtfs_config = {
        "agency": {"txt_file": "agency.txt", "required": False},
        "calendar_dates": {"txt_file": "calendar_dates.txt", "required": True},
        "feed_info": {"txt_file": "feed_info.txt", "required": False},
        "routes": {"txt_file": "routes.txt", "required": True},
        "stop_times": {"txt_file": "stop_times.txt", "required": True},
        "stops": {"txt_file": "stops.txt", "required": True},
        "transfers": {"txt_file": "transfers.txt", "required": False},
        "trips": {"txt_file": "trips.txt", "required": True}}

    def load(self, feed_url):

        self.feed_url = feed_url

        response = requests.get(feed_url)

        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                for key, record in self.gtfs_config.items():
                    if record["txt_file"] in z.namelist():
                        with z.open(record["txt_file"]) as txt_file:
                            print(f"INFO: Loading {record['txt_file']}...")
                            df = pd.read_csv(txt_file, sep=",")
                            setattr(self, key, df)
                            print(
                                f"SUCCESS: Loaded {len(df)} records from {record['txt_file']}")
                    elif record["required"]:
                        raise Exception(
                            f"Required file {record['txt_file']} not found in GTFS data")
        else:
            raise Exception("Failed to download GTFS data:" +
                            response.status_code)

        return self

    # Merge methods

    def add_stop_names(self, df, stop_id_col_name="stop_id", subset=["stop_id", "stop_name"]):
        return df.merge(
            self.stops[subset], on=stop_id_col_name, how="left")

    def add_stop_times(self, df, stop_id_col_name="stop_id", subset=[
            "trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "pickup_type", "drop_off_type"]):
        return df.merge(
            self.stop_times[subset], on=stop_id_col_name)

    def add_trips(self, df, trip_id_col_name="trip_id",  subset=["route_id", "service_id", "trip_id", "trip_headsign"]):
        return df.merge(
            self.trips[subset], on=trip_id_col_name)

    def add_route(self, df, route_id_col_name="route_id", subset=["route_id", "route_short_name", "route_long_name", "route_color", "route_text_color"]):
        return df.merge(
            self.routes[subset], on=route_id_col_name)

    def get_stations(self):
        return np.sort(self.stops['stop_name'].unique())

    def filter_stops(self, stop_name):
        return self.stops[self.stops['stop_name'].str.contains(stop_name, case=False)]

    def get_starting_terminus_stops(self, stop_name=True):
        # Keep only the starting stops
        df_starting_stop = self.stop_times[(self.stop_times["pickup_type"] == 0) & (self.stop_times["drop_off_type"] == 1)][[
            "stop_id", "trip_id"]]
        # Keep only the terminus stops
        df_terminus_stop = self.stop_times[(self.stop_times["pickup_type"] == 1) & (
            self.stop_times["drop_off_type"] == 0)][["stop_id", "trip_id"]]

        columns_name = [['starting_stop_id', 'starting_stop_name'],
                        ['terminus_stop_id', 'terminus_stop_name']]

        dfs = [df_starting_stop, df_terminus_stop]
        for idx, df in enumerate(dfs):
            # Add the stop names if required
            if stop_name:
                df = self.add_stop_names(df)
                # Rename the columns to make the distinction between the station stop name and the terminus stop name
                df.rename(
                    columns={"stop_id": columns_name[idx][0]}, inplace=True)
            df.rename(
                columns={"stop_name": columns_name[idx][1]}, inplace=True)

            # Update the DataFrame in the list
            dfs[idx] = df

        # Unpack the list back into separate variables
        df_starting_stop, df_terminus_stop = dfs

        return df_starting_stop, df_terminus_stop

    def add_starting_terminus_stops(self, df, stop_name=True):
        df_starting_stop, df_terminus_stop = self.get_starting_terminus_stops(
            stop_name)
        return df.merge(df_starting_stop, on="trip_id").merge(df_terminus_stop, on="trip_id")

    def get_today_trips(self, station_name):
        today = datetime.today().strftime('%Y%m%d')
        df_today_calendar = self.calendar_dates[self.calendar_dates['date'] == int(
            today)]
        df_stations_stops = self.filter_stops(station_name)
        if df_stations_stops.empty:
            raise Exception(
                f"Station '{station_name}' not found in GTFS data.")

        df = self.add_stop_times(df_stations_stops)
        df = self.add_trips(df)
        df = self.add_route(df)
        df = df.merge(
            df_today_calendar[["service_id", "date"
                               ]], on="service_id")

        df = df[["trip_id", "stop_name", "arrival_time", "departure_time", "stop_sequence", "pickup_type", "drop_off_type", "trip_headsign",
                 "route_short_name", "route_long_name", "route_color", "route_text_color", "date"]]
        df.sort_values(by="departure_time", inplace=True)

        df["arrival_time"] = pd.to_datetime(
            df["arrival_time"]).dt.time
        df["departure_time"] = pd.to_datetime(
            df["departure_time"]).dt.time

        df = self.add_starting_terminus_stops(df)

        return df

    def get_today_departures(self, station_name, df_today_trips=None):
        if df_today_trips is None:
            df_today_trips = self.get_today_trips(station_name)
        return df_today_trips[df_today_trips["pickup_type"] == 0]

    def get_today_arrivals(self, station_name, df_today_trips=None):
        if df_today_trips is None:
            df_today_trips = self.get_today_trips(station_name)
        return df_today_trips[df_today_trips["drop_off_type"] == 0]


def transform_drop_off_pickup_type_to_hr(df):
    if "pickup_type" not in df.columns or "drop_off_type" not in df.columns:
        raise ValueError("pickup_type and drop_off_type columns are required")

    df["drop_off_pickup_type"] = df.apply(
        lambda x: "Departure" if x["pickup_type"] == 0 and x["drop_off_type"] == 1 else "Arrival" if x["pickup_type"] == 1 and x["drop_off_type"] == 0 else "Departure/Arrival",  axis=1)
    return df
