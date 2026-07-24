from typing import Protocol


class CustomerActivityProvider(Protocol):
    def get_customer_activity(self, external_user_id: int) -> dict:
        """Returns normalized activity data for a customer from an external provider."""


class WeatherProvider(Protocol):
    def get_current_weather(self, city: str, country_code: str) -> dict:
        """Returns normalized weather data for a location."""
