import pytest

from app.domain.errors import ConflictError, NotFoundError
from app.models.schemas import (
    CustomerAddressCreate,
    CustomerCreate,
    CustomerUpdate,
    TagCreate,
)
from app.services.customer_service import CustomerService


def test_create_customer_adds_record(service: CustomerService) -> None:
    customer = service.create_customer(
        CustomerCreate(
            first_name="Mia",
            last_name="Lopez",
            email="mia.lopez@example.com",
            phone="+1-555-1111",
            status="Active",
            customer_type="B2C",
        )
    )

    assert customer["customer_id"] == 3
    assert service.get_customer(3)["email"] == "mia.lopez@example.com"


def test_create_customer_rejects_duplicate_email(service: CustomerService) -> None:
    with pytest.raises(ConflictError, match="already in use"):
        service.create_customer(
            CustomerCreate(
                first_name="Nora",
                last_name="Ibrahim",
                email="ava.stone@example.com",
                phone=None,
                status="Pending",
                customer_type="B2C",
            )
        )


def test_update_customer_changes_email(service: CustomerService) -> None:
    updated = service.update_customer(1, CustomerUpdate(email="ava.new@example.com"))

    assert updated["email"] == "ava.new@example.com"


def test_create_address_requires_existing_customer(service: CustomerService) -> None:
    with pytest.raises(NotFoundError, match="Customer 99 was not found"):
        service.create_address(
            99,
            CustomerAddressCreate(
                address_type="Billing",
                address_line1="20 West Street",
                city="Boston",
                state_province="MA",
                postal_code="02108",
                country_code="US",
                is_primary=True,
            ),
        )


def test_primary_address_switches_other_addresses_off(service: CustomerService) -> None:
    new_address = service.create_address(
        1,
        CustomerAddressCreate(
            address_type="Shipping",
            address_line1="44 River Lane",
            city="Austin",
            state_province="TX",
            postal_code="78702",
            country_code="US",
            is_primary=True,
        ),
    )

    addresses = service.list_addresses(1)
    primary_flags = {address["address_id"]: address["is_primary"] for address in addresses}

    assert primary_flags[new_address["address_id"]] is True
    assert primary_flags[1] is False


def test_delete_customer_cascades_related_records(service: CustomerService) -> None:
    service.delete_customer(1)

    with pytest.raises(NotFoundError):
        service.get_customer(1)
    assert service.list_tags()
    assert service.list_addresses(2) == []
    assert service.list_customer_tags(2)


def test_create_tag_rejects_duplicate_name(service: CustomerService) -> None:
    with pytest.raises(ConflictError, match="already exists"):
        service.create_tag(TagCreate(tag_name="VIP"))


def test_assign_and_remove_customer_tag(service: CustomerService) -> None:
    tags_after_assign = service.assign_tag_to_customer(1, 2)
    assert {tag["tag_id"] for tag in tags_after_assign} == {1, 2}

    tags_after_remove = service.remove_tag_from_customer(1, 2)
    assert {tag["tag_id"] for tag in tags_after_remove} == {1}