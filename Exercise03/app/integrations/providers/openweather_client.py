from app.domain.errors import ExternalServiceError, IntegrationConfigError
from app.integrations.http_client import ResilientHttpClient


class OpenWeatherMapProvider:
    def __init__(self, client: ResilientHttpClient, api_key: str | None) -> None:
        self.client = client
        self.api_key = api_key

    def get_current_weather(self, city: str, country_code: str) -> dict:
        if not self.api_key:
            raise IntegrationConfigError("OPENWEATHER_API_KEY is not configured.")

        geocode_data = self.client.request_json(
            "GET",
            "/geo/1.0/direct",
            params={
                "q": f"{city},{country_code}",
                "limit": 1,
                "appid": self.api_key,
            },
        )

        if not isinstance(geocode_data, list) or len(geocode_data) == 0:
            raise ExternalServiceError("No weather geocoding result was found for the customer address.")

        location = geocode_data[0]
        lat = location.get("lat")
        lon = location.get("lon")
        if lat is None or lon is None:
            raise ExternalServiceError("Weather geocoding response was missing coordinates.")

        weather_data = self.client.request_json(
            "GET",
            "/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
            },
        )

        try:
            return {
                "provider": "openweathermap",
                "city": weather_data["name"],
                "temperature_c": weather_data["main"]["temp"],
                "condition": weather_data["weather"][0]["main"],
                "wind_speed_mps": weather_data["wind"]["speed"],
            }
        except (KeyError, IndexError, TypeError) as error:
            raise ExternalServiceError("Weather provider payload shape was invalid.") from error
