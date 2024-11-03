
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def sncf_departures_alternating_colors(val):
    color = "#0064ab" if (val.name % 2) == 0 else "#003a79"
    return [f'color: white; background-color: {color}'] * len(val)


def sncf_arrivals_alternating_colors(val):
    color = "#187936" if (val.name % 2) == 0 else "#1f5628"
    return [f'color: white; background-color: {color}'] * len(val)


def style_trips_results(df, trip_type):
    df.reset_index(drop=True, inplace=True)
    df_styler = df.style.format(thousands=" ",
                                subset="trip_headsign")
    if trip_type == "departures":
        df_styler = df_styler.apply(sncf_departures_alternating_colors, axis=1)
    elif trip_type == "arrivals":
        df_styler = df_styler.apply(sncf_arrivals_alternating_colors, axis=1)

    return df_styler


viridis = plt.cm.get_cmap('viridis_r', 256)
viridis_colors = viridis.colors


def viridis_based_on_value(val, min_val=0, max_val=100, opacity=1.0):
    norm = mcolors.Normalize(vmin=min_val, vmax=max_val)
    color = viridis(norm(val))
    rgba_color = list(color)
    rgba_color[3] = opacity  # Ajuster l'opacité
    return rgba_color


def viridis_based_on_value_hex(val, min_val=0, max_val=100):
    return mcolors.to_hex(viridis_based_on_value(val, min_val, max_val))


route_detail_domain = ["TGV", "TER", "Bus"]
route_detail_range = ["#4A628A", "#7AB2D3", "#B9E5E8"]

pickup_dropoff_domain = ["Departure", "Arrival", "Departure/Arrival"]
pickup_dropoff_range = ["#6A9AB0", "#3A6D8C", "#EAD8B1"]
