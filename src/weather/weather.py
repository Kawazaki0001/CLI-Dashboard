# The API Source is https://wttr.in
# The Github project like is : https://github.com/chubin/wttr.in
# EXP api call : https://wttr.in/kiel?format=j1
import asyncio
import toml, pathlib, json, datetime
from httpx import AsyncClient, _exceptions as e
from rich import console


class Weather :

    def __init__(self):
        self.city:str = ""
        self.location:str = self._getLocation()
        self.baseUrl:str = "https://wttr.in/" + self.location
        self.params = {
            "format" : "j1"
        }

    async def makeCall(self) :

        async with AsyncClient() as cle :
            res = await cle.get(url=self.baseUrl, params=self.params, timeout=10)
            res.raise_for_status()
            with open("res.json", "w") as f :
                json.dump(res.json(), f, ensure_ascii=False, indent=4)

            # Update the setting
            self._updateSetting()
            # Returning the object
            return self._extract_weather_data(res.json())

    def _updateSetting(self) :
        """ To update the date and hour after making calls """
        file = pathlib.Path(__file__).parent.parent.parent / "setting.toml"
        obj = {}

        with open(file , "r") as f :
            obj = toml.load(f)

        obj["user"]["last_date"], obj["user"]["country"] = datetime.datetime.strftime(datetime.datetime.now(), "%d %B, %Y") , datetime.datetime.strftime(datetime.datetime.now(), "%H:%M")

        with open(file, "w") as f :
            toml.dump(obj, f)

    def _getLocation(self) :
        """ A helper to get the Location(City and Country names) from settings.toml to forcase the weather """
        file = pathlib.Path(__file__).parent.parent.parent / "setting.toml"

        object = {}

        if not file.exists() :
            raise FileNotFoundError

        with open(file, "r") as f :
            object = toml.load(f)

        self.city = object["weather"]["city"]
        return f"{object["weather"]["city"]},{object["weather"]["country"]}"


    def _extract_weather_data(self, data: dict) -> dict:
        """Extract only the essential weather info for today and tomorrow."""

        # ─── Location ──────────────────────────────────────────────
        nearest = data.get("nearest_area", [{}])[0]
        location = {
            "city" : self.city,
            # "areaname" : nearest.get("areaName", [{}])[0].get("value"),
            "region": nearest.get("region", [{}])[0].get("value"),
            "country": nearest.get("country", [{}])[0].get("value"),
        }

        # ─── Current (today) ──────────────────────────────────────
        current = data.get("current_condition", [{}])[0]
        today = {
            "temp_C": current.get("temp_C"),
            "feels_like_C": current.get("FeelsLikeC"),
            "weather_desc": current.get("weatherDesc", [{}])[0].get("value"),
            "humidity": current.get("humidity"),
            "cloudcover": current.get("cloudcover"),
            "uvIndex": current.get("uvIndex"),
            "visibility_km": current.get("visibility"),
            "visibility_miles": current.get("visibilityMiles"),
            "observation_time": current.get("observation_time"),
        }

        # ─── Tomorrow (second day in forecast) ───────────────────
        forecast = data.get("weather", [])
        tomorrow = {}
        if len(forecast) > 1:
            day = forecast[1]
            # Get the most frequent condition from hourly data
            hourly = day.get("hourly", [])
            conditions = [h.get("weatherDesc", [{}])[0].get("value") for h in hourly if h.get("weatherDesc")]
            dominant = conditions[0] if conditions else "Unknown"
            # Use a Counter if you want the most frequent, but first is often fine
            from collections import Counter
            if conditions:
                dominant = Counter(conditions).most_common(1)[0][0]
            tomorrow = {
                "weather_desc": dominant,
                "max_temp_C": day.get("maxtempC"),
                "min_temp_C": day.get("mintempC"),

            }

        return {
        "location": location,
        "today": today,
        "tomorrow": tomorrow,
        }

