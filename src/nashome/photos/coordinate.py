from datetime import datetime, timezone
from numbers import Real
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
import re


def convert_dms_to_decimal(dms: Real|str) -> float:
    if isinstance(dms, Real):
        return float(dms)

    match = re.match(r'(\d+)\s+deg\s+(\d+)\'\s+([\d.]+)"\s+([NSEW])', dms)

    if not match:
        raise ValueError(f"Invalid DMS format: {dms}")

    degrees = float(match.group(1))
    minutes = float(match.group(2))
    seconds = float(match.group(3))
    direction = match.group(4)

    decimal = degrees + minutes / 60 + seconds / 3600

    if direction in ("S", "W"):
        decimal *= -1

    return decimal


def convert_local_time_to_gps_utc(local_datetime: datetime, latitude: float, longitude: float) -> datetime:
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lat=latitude, lng=longitude)

    if timezone_name is None:
        raise ValueError("Could not determine timezone")

    local_tz = ZoneInfo(timezone_name)

    # attach timezone to local datetime
    local_dt = local_datetime.replace(tzinfo=local_tz)

    # convert to UTC
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt


class CoordinateType:
    def __init__(self, name:str, string_greater_zero:str, string_less_zero:str):
        self.name = name
        self.string_greater_zero = string_greater_zero
        self.string_less_zero = string_less_zero


LATITUDE = CoordinateType("Latitude", "N", "S")
LONGITUDE = CoordinateType("Longitude", "E", "W")
ALTITUDE = CoordinateType("Altitude", "Above Sea Level", "Below Sea Level")
