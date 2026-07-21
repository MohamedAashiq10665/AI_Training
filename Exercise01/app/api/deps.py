from app.repositories.mock_db import MockDatabase
from app.services.customer_service import CustomerService


database = MockDatabase()
service = CustomerService(database)


def get_customer_service() -> CustomerService:
    return service
