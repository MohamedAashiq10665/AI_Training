from app.core.config import Settings
from app.integrations.http_client import ResilientHttpClient
from app.integrations.providers.jsonplaceholder_client import JsonPlaceholderActivityProvider
from app.integrations.providers.openweather_client import OpenWeatherMapProvider
from app.repositories.mock_db import MockDatabase
from app.services.customer_service import CustomerService


settings = Settings.from_env()
database = MockDatabase()

jsonplaceholder_client = ResilientHttpClient(
    base_url="https://jsonplaceholder.typicode.com",
    timeout_seconds=settings.external_timeout_seconds,
    max_retries=settings.external_max_retries,
    backoff_seconds=settings.external_backoff_seconds,
)

openweather_client = ResilientHttpClient(
    base_url="https://api.openweathermap.org",
    timeout_seconds=settings.external_timeout_seconds,
    max_retries=settings.external_max_retries,
    backoff_seconds=settings.external_backoff_seconds,
)

activity_provider = JsonPlaceholderActivityProvider(
    client=jsonplaceholder_client,
    bearer_token=settings.jsonplaceholder_bearer_token,
)
weather_provider = OpenWeatherMapProvider(
    client=openweather_client,
    api_key=settings.openweather_api_key,
)

service = CustomerService(database, activity_provider, weather_provider)


def get_customer_service() -> CustomerService:
    return service
