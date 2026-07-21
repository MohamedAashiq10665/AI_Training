from datetime import date
from unittest.mock import Mock

import pytest

from app.domain.errors import ValidationError
from app.models.schemas import (
    CustomerBusinessProfileUpdate,
    CustomerCreate,
)
from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import CustomerService


def test_create_customer_calls_repository() -> None:
    repository = Mock(spec=CustomerRepository)
    service = CustomerService(repository)
    payload = CustomerCreate(
        first_name="Mia",
        last_name="Lopez",
        email="mia.lopez@example.com",
        phone="+1-555-1111",
        status="Active",
        customer_type="B2C",
    )
    repository.create_customer.return_value = {"customer_id": 7, "email": payload.email}

    customer = service.create_customer(payload)

    assert customer["customer_id"] == 7
    repository.create_customer.assert_called_once_with(payload.model_dump())


def test_update_business_profile_rejects_invalid_date_order() -> None:
    repository = Mock(spec=CustomerRepository)
    repository.get_business_profile.return_value = {
        "business_profile_id": 2,
        "customer_id": 5,
        "company_name": "Northwind",
        "job_title": "Ops",
        "lead_source": "Referral",
        "lifecycle_stage": "Lead",
        "establishment_start_date": date(2025, 1, 1),
        "onboarding_date": date(2025, 2, 1),
    }
    service = CustomerService(repository)

    with pytest.raises(ValidationError, match="onboarding_date must be greater"):
        service.update_business_profile(
            2,
            CustomerBusinessProfileUpdate(
                establishment_start_date=date(2025, 3, 1),
                onboarding_date=date(2025, 2, 1),
            ),
        )

    repository.update_business_profile.assert_not_called()