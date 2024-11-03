def get_map_bounds(df, lat_col, lon_col, center=None):
    sw = df[[lat_col, lon_col]].min().values.tolist()
    ne = df[[lat_col, lon_col]].max().values.tolist()
    if center:
        sw = min(sw, center)
        ne = max(ne, center)
    return [sw, ne]
