from datetime import datetime, timedelta
import pytz


def now_paris():
    utc_now = datetime.now(pytz.utc)

    # Convertir l'heure UTC en heure de Paris
    paris_tz = pytz.timezone('Europe/Paris')
    return utc_now.astimezone(paris_tz)


def check_if_column_exists(df, columns):
    if isinstance(columns, list):
        if missing_columns := [
            col for col in columns if col not in df.columns
        ]:
            raise ValueError(
                f"Missing columns: {missing_columns} -> Available columns: {df.columns}")
    elif columns not in df.columns:
        raise ValueError(
            f"Missing column: {columns} -> Available columns: {df.columns}")


def normalize_value(x, min_val, max_val, min_range, max_range):
    return min_range + (max_range - min_range) * (x - min_val) / (max_val - min_val)
