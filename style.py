
def sncf_alternating_colors(val):
    color = "#0064ab" if (val.name % 2) == 0 else "#003a79"
    return [f'color: white; background-color: {color}'] * len(val)


def style_trips_results(df):
    df.reset_index(drop=True, inplace=True)
    df_styler = df.style.format(thousands=" ",
                                subset="trip_headsign")
    df_styler.apply(sncf_alternating_colors, axis=1)

    return df_styler
