from app.domain.errors import ValidationError
from app.models.schemas import (
    CustomerAddressCreate,
    CustomerAddressUpdate,
    CustomerBusinessProfileCreate,
    CustomerBusinessProfileUpdate,
    CustomerCreate,
    CustomerUpdate,
    TagCreate,
    TagUpdate,
)
from app.repositories.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository) -> None:
        self.repository = repository

    def list_customers(self) -> list[dict]:
        return self.repository.list_customers()

    def get_customer(self, customer_id: int) -> dict:
        return self.repository.get_customer(customer_id)

    def create_customer(self, payload: CustomerCreate) -> dict:
        return self.repository.create_customer(payload.model_dump())

    def update_customer(self, customer_id: int, payload: CustomerUpdate) -> dict:
        updates = payload.model_dump(exclude_unset=True)
        return self.repository.update_customer(customer_id, updates)

    def delete_customer(self, customer_id: int) -> None:
        self.repository.delete_customer(customer_id)

    def get_customer_details(self, customer_id: int) -> dict:
        customer = dict(self.get_customer(customer_id))
        customer["addresses"] = self.list_addresses(customer_id)
        customer["business_profiles"] = self.list_business_profiles(customer_id)
        customer["tags"] = self.list_customer_tags(customer_id)
        return customer

    def list_addresses(self, customer_id: int) -> list[dict]:
        return self.repository.list_addresses(customer_id)

    def get_address(self, address_id: int) -> dict:
        return self.repository.get_address(address_id)

    def create_address(self, customer_id: int, payload: CustomerAddressCreate) -> dict:
        return self.repository.create_address(customer_id, payload.model_dump())

    def update_address(self, address_id: int, payload: CustomerAddressUpdate) -> dict:
        updates = payload.model_dump(exclude_unset=True)
        return self.repository.update_address(address_id, updates)

    def delete_address(self, address_id: int) -> None:
        self.repository.delete_address(address_id)

    def list_business_profiles(self, customer_id: int) -> list[dict]:
        return self.repository.list_business_profiles(customer_id)

    def get_business_profile(self, business_profile_id: int) -> dict:
        return self.repository.get_business_profile(business_profile_id)

    def create_business_profile(self, customer_id: int, payload: CustomerBusinessProfileCreate) -> dict:
        self._validate_onboarding_date(
            payload.establishment_start_date,
            payload.onboarding_date,
        )
        return self.repository.create_business_profile(customer_id, payload.model_dump())

    def update_business_profile(
        self,
        business_profile_id: int,
        payload: CustomerBusinessProfileUpdate,
    ) -> dict:
        profile = self.get_business_profile(business_profile_id)
        updates = payload.model_dump(exclude_unset=True)
        start_date = updates.get("establishment_start_date", profile["establishment_start_date"])
        onboarding_date = updates.get("onboarding_date", profile["onboarding_date"])
        self._validate_onboarding_date(start_date, onboarding_date)
        return self.repository.update_business_profile(business_profile_id, updates)

    def delete_business_profile(self, business_profile_id: int) -> None:
        self.repository.delete_business_profile(business_profile_id)

    def list_tags(self) -> list[dict]:
        return self.repository.list_tags()

    def get_tag(self, tag_id: int) -> dict:
        return self.repository.get_tag(tag_id)

    def create_tag(self, payload: TagCreate) -> dict:
        return self.repository.create_tag(payload.model_dump())

    def update_tag(self, tag_id: int, payload: TagUpdate) -> dict:
        return self.repository.update_tag(tag_id, payload.model_dump())

    def delete_tag(self, tag_id: int) -> None:
        self.repository.delete_tag(tag_id)

    def list_customer_tags(self, customer_id: int) -> list[dict]:
        return self.repository.list_customer_tags(customer_id)

    def assign_tag_to_customer(self, customer_id: int, tag_id: int) -> list[dict]:
        return self.repository.assign_tag_to_customer(customer_id, tag_id)

    def remove_tag_from_customer(self, customer_id: int, tag_id: int) -> list[dict]:
        return self.repository.remove_tag_from_customer(customer_id, tag_id)

    def _validate_onboarding_date(self, establishment_start_date, onboarding_date) -> None:
        if onboarding_date <= establishment_start_date:
            raise ValidationError("onboarding_date must be greater than establishment_start_date.")
