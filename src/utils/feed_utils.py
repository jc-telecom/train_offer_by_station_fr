from src.imports.imports import *
from datetime import datetime, timedelta
from src.utils.utils import check_if_column_exists


def concat_feeds_df(feeds_dfs, feeds_name) -> pd.DataFrame:
    for i, feed_df in enumerate(feeds_dfs):
        feeds_dfs[i] = feed_df.assign(feed_name=feeds_name[i])
    return pd.concat(feeds_dfs)


def merge_feed_files(df, Feed, Feed_attr, left_on, right_on, Feed_subset, right_prefix="", how="inner"):
    check_if_column_exists(df, left_on)
    df = df.merge(
        getattr(Feed, Feed_attr).add_prefix(right_prefix)[Feed_subset], left_on=left_on, right_on=right_on, how=how, copy=False)
    if left_on != right_on:
        df.drop(columns=[right_on], inplace=True)
    return df


def transform_drop_off_pickup_type_to_hr(df):
    if "pickup_type" not in df.columns or "drop_off_type" not in df.columns:
        raise ValueError("pickup_type and drop_off_type columns are required")

    df["drop_off_pickup_type"] = df.apply(
        lambda x: "Departure" if x["pickup_type"] == 0 and x["drop_off_type"] == 1 else "Arrival" if x["pickup_type"] == 1 and x["drop_off_type"] == 0 else "Departure/Arrival",  axis=1)
    return df


def transfom_route_type_to_hr(df):
    if "route_type" not in df.columns or "feed_name" not in df.columns:
        raise ValueError("route_type and feed_name column are required")

    df["route_type"] = df["route_type"].replace(
        {0: "Tram", 1: "Metro", 2: "Train", 3: "Bus", 4: "Ferry", 5: "Cable car", 6: "Gondola", 7: "Funicular"})
    return df


def gtfs_time_to_datetime(gtfs_date, gtfs_time):
    hours, minutes, seconds = tuple(
        int(token) for token in gtfs_time.split(":")
    )

    return (
        (datetime.strptime(str(gtfs_date), "%Y%m%d") + timedelta(
            hours=hours, minutes=minutes, seconds=seconds
        )).time()
    )
