
from src.imports.imports import *
from src.classes.Feed import *
from src.utils.feed_utils import concat_feeds_df


class Feeds:
    def __init__(self, feeds_url: List[str], feeds_name: List[str], feeds_config=None, load=False):
        if len(feeds_url) != len(feeds_name):
            raise ValueError(
                "The number of feeds URL and feeds name should be the same")
        self.feeds_url = feeds_url
        self.feeds_name = feeds_name
        self.feeds_config = feeds_config
        self.loaded = False

        self.feeds = []
        if load:
            self.load()

    def load(self, logger_container=False):
        for idx in range(len(self.feeds_url)):
            self.feeds.append(Feed(
                url=self.feeds_url[idx],
                name=self.feeds_name[idx],
                config=self.feeds_config[idx] if self.feeds_config is not None else None)
                .load(logger_container=logger_container))
        self.loaded = True
        return self

    def create_station_feeds(self, station_name, load=False):
        if station_name in self.get_stations():
            return StationFeeds(
                feeds=self.feeds,
                feeds_url=self.feeds_url,
                feeds_name=self.feeds_name, station_name=station_name,
                feeds_config=self.feeds_config,
                load=load)
        else:
            raise ValueError(
                f"Station {station_name} not found in the feeds")

    def get_stations(self) -> List[str]:
        stations = []
        for feed in self.feeds:
            stations.extend(feed.get_stations())
        return sorted(list(set(stations)), key=locale.strxfrm)

    def get_trips_count(self):
        return concat_feeds_df([gtfs.trips for gtfs in self.feeds], self.feeds_name).shape[0]

    def get_today_trips(self):
        return concat_feeds_df([gtfs.get_today_trips() for gtfs in self.feeds], self.feeds_name).sort_values("trip_id", ignore_index=True)

    def get_today_departures(self):
        return concat_feeds_df([gtfs.get_today_departures() for gtfs in self.feeds], self.feeds_name).sort_values("trip_id", ignore_index=True)

    def get_today_arrivals(self):
        return concat_feeds_df([gtfs.get_today_arrivals() for gtfs in self.feeds], self.feeds_name).sort_values("trip_id", ignore_index=True)

    def get_time_table_info(self):
        return concat_feeds_df([gtfs.get_time_table_info() for gtfs in self.feeds], self.feeds_name).sort_values("departure_time",  ignore_index=True)

    def get_departures_from_dfs(self, df):
        return df[df["pickup_type"] == 0]

    def get_arrivals_from_dfs(self, df):
        return df[df["drop_off_type"] == 0]

    def get_station_coordinates(self):
        # gtfs.get_station_coordinates() return dict so we need to merge the dict
        for idx, feed in enumerate(self.feeds):
            if idx == 0:
                coordinates = feed.get_station_coordinates()
            else:
                coordinates.update(feed.get_station_coordinates())
        return coordinates

    def add_stations_coordinates(self, df, stop_id="stop_id", right_prefix=""):
        return concat_feeds_df([gtfs.add_stations_coordinates(df, stop_id, right_prefix) for gtfs in self.feeds], self.feeds_name)


class StationFeeds(Feeds):
    def __init__(self, feeds, feeds_url: List[str], feeds_name: List[str], station_name: str, feeds_config=None, load=False):
        super().__init__(feeds_url, feeds_name, feeds_config)
        self.station_name = station_name
        self.parent_feeds = feeds
        self.feeds = []
        self.loaded = False
        if load:
            self.load()

    def load(self, logger_container=False):
        for idx in range(len(self.feeds_url)):
            self.feeds.append(StationFeed(
                parent_feed=self.parent_feeds[idx], url=self.feeds_url[idx],
                name=self.feeds_name[idx],
                station=self.station_name,
                config=self.feeds_config[idx] if self.feeds_config is not None else None)
                .load(logger_container=logger_container))
        self.loaded = True
        return self

    def add_intermediate_stop(self, df, stop_name=True):
        return concat_feeds_df([gtfs.add_intermediate_stop(df) for gtfs in self.feeds], self.feeds_name)
