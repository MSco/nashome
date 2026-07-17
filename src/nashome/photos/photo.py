from datetime import datetime
from numbers import Real
from pathlib import Path
import re
import subprocess

from nashome.photos.coordinate import convert_dms_to_decimal, convert_local_time_to_gps_utc
from nashome.photos.coordinate import CoordinateType
from nashome.photos.coordinate import ALTITUDE, LATITUDE, LONGITUDE


class Photo:
    def __init__(self, path: Path|str):
        self.path = Path(path)
        self.date = None
        self.new_filename = None
        self._extract_datetime_from_filename(self.path.name)


    def _extend_command_with_coordinate(self, cmd: list[str], coordinate_type: CoordinateType, coord_value: float | str) -> list[str]:
        if isinstance(coord_value, str):
            cmd.append(f"-GPS{coordinate_type.name}={coord_value}")
        else:
            cmd.extend([f"-GPS{coordinate_type.name}={abs(coord_value)}", 
                        f"-GPS{coordinate_type.name}Ref={coordinate_type.string_greater_zero if coord_value >= 0 else coordinate_type.string_less_zero}"])
        return cmd


    def _extract_datetime_from_filename(self, filename:str) -> tuple[datetime,str]:
        patterns = [
            r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})(.*)\.jpe?g', # Screenshot_YYYY-MM-DD-HH-MM-SS_<hashcode>.jpg
            r'IMG[-_](\d{4})(\d{2})(\d{2})([-_]WA\d+.*)\.jpe?g',  # IMG-YYYYMMDD-WAXXXX.jpg
            r'IMG[-_]?(\d{4})(\d{2})(\d{2})[-_]?(\d{2})(\d{2})(\d{2})(.*)\.jpe?g', # IMG(-_)YYYYMMDD(-_)HHMMSS.jpg
            r'(\d{4})(\d{2})(\d{2})[-_](\d{2})(\d{2})(\d{2})(.*)\.jpe?g'  # YYYYMMDD_HHMMSS.jpg
        ]

        for pattern in patterns:
            match_filename = re.match(pattern, filename)
            if match_filename is not None:
                groups = match_filename.groups()
                date_str = "".join(groups[:3])
                if len(groups)>=6:
                    time_str = "".join(groups[3:6])
                    date = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
                    base_str = f"{date_str}_{time_str}"
                else:
                    date = datetime.strptime(date_str, '%Y%m%d')
                    base_str = date_str
                self.date = date 
                self.new_filename = f"IMG_{base_str}{groups[-1]}.jpg"
                break


    def has_exif_gps(self) -> bool:
        result = subprocess.run([
                "exiftool",
                "-GPSLatitude",
                "-GPSLongitude",
                "-s3",
                str(self.path),
            ],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()
        return bool(output)


    def update_exif_datetime(self, dry_run: bool = False):
        datetime_str = self.date.strftime("%Y:%m:%d %H:%M:%S")
        print(f"{'[DRY RUN] ' if dry_run else ''}Writing EXIF date={datetime_str} to {self.path}")

        if not dry_run:
            subprocess.run([
                "exiftool",
                "-overwrite_original",
                f"-DateTimeOriginal={datetime_str}",
            f"-CreateDate={datetime_str}",
            f"-ModifyDate={datetime_str}",
            str(self.path),
        ])
            

    def update_exif_gps(self, latitude: float | str, longitude: float | str, altitude: float | None = None):
        if self.has_exif_gps():
            print(f"GPS EXIF data found in {self.path}. Skipping update.")
            return

        cmd = [
            "exiftool",
            "-overwrite_original",
            "-GPSProcessingMethod=GPS",
            "-GPSVersionID=2.3.0.0",
        ]

        # Latitude
        cmd = self._extend_command_with_coordinate(cmd, LATITUDE, latitude)

        # Longitude
        cmd = self._extend_command_with_coordinate(cmd, LONGITUDE, longitude)

        # Altitude
        if altitude is not None:
            cmd = self._extend_command_with_coordinate(cmd, ALTITUDE, altitude)

        # GPS timestamp
        utc_datetime = convert_local_time_to_gps_utc(self.date, convert_dms_to_decimal(latitude), convert_dms_to_decimal(longitude))
        cmd.extend([
            f"-GPSDateStamp={utc_datetime.strftime('%Y:%m:%d')}",
            f"-GPSTimeStamp={utc_datetime.strftime('%H:%M:%S')}",
        ])

        cmd.append(str(self.path))

        print(" ".join(cmd))

        subprocess.run(cmd, check=True)