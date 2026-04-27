import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

class ExifExtractor:
    @staticmethod
    def extract(image_path: str) -> dict:
        """Extracts EXIF metadata including GPS coordinates and dates from an image."""
        if not os.path.exists(image_path):
            return {}
            
        metadata = {}
        try:
            image = Image.open(image_path)
            info = image._getexif()
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        gps_data = {}
                        for t in value:
                            sub_decoded = GPSTAGS.get(t, t)
                            gps_data[sub_decoded] = value[t]
                        metadata["GPSInfo"] = gps_data
                    else:
                        if isinstance(value, (bytes, str, int, float)):
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode('utf-8')
                                except UnicodeDecodeError:
                                    value = str(value)
                            metadata[decoded] = value
                            
                # Calculate decimal coordinates if GPS info exists
                if "GPSInfo" in metadata:
                    lat = ExifExtractor._get_decimal_from_dms(metadata["GPSInfo"].get('GPSLatitude'), metadata["GPSInfo"].get('GPSLatitudeRef'))
                    lon = ExifExtractor._get_decimal_from_dms(metadata["GPSInfo"].get('GPSLongitude'), metadata["GPSInfo"].get('GPSLongitudeRef'))
                    if lat and lon:
                        metadata["Coordinates"] = {"lat": lat, "lon": lon}
                        
            return metadata
        except Exception as e:
            print(f"Error extracting EXIF: {e}")
            return {}

    @staticmethod
    def _get_decimal_from_dms(dms, ref):
        if not dms or not ref:
            return None
        try:
            degrees = dms[0]
            minutes = dms[1] / 60.0
            seconds = dms[2] / 3600.0
            if isinstance(degrees, tuple): degrees = degrees[0]/degrees[1]
            if isinstance(minutes, tuple): minutes = minutes[0]/minutes[1]
            if isinstance(seconds, tuple): seconds = seconds[0]/seconds[1]
            
            decimal = float(degrees) + float(minutes) + float(seconds)
            if ref in ['S', 'W']:
                decimal = -decimal
            return round(decimal, 6)
        except Exception:
            return None
