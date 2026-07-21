from datetime import datetime, timezone

from app.domain.errors import ConflictError, NotFoundError, ValidationError
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
from app.repositories.mock_db import MockDatabase


class CustomerService:
    def __init__(self, database: MockDatabase) -> None:
        self.database = database

    def list_customers(self) -> list[dict]:
        return sorted(self.database.customers.values(), key=lambda item: item["customer_id"])

    def get_customer(self, customer_id: int) -> dict:
        customer = self.database.customers.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} was not found.")
        return customer

    def create_customer(self, payload: CustomerCreate) -> dict:
        self._ensure_unique_email(payload.email)
        now = datetime.now(timezone.utc)
        customer = {
            "customer_id": self.database.next_customer_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "email": payload.email,
            "phone": payload.phone,
            "status": payload.status,
            "customer_type": payload.customer_type,
            "created_at": now,
            "updated_at": now,
        }
        self.database.customers[customer["customer_id"]] = customer
        self.database.next_customer_id += 1
        return customer

    def update_customer(self, customer_id: int, payload: CustomerUpdate) -> dict:
        customer = self.get_customer(customer_id)
        updates = payload.model_dump(exclude_unset=True)
        email = updates.get("email")
        if email is not None:
            self._ensure_unique_email(email, customer_id)
        customer.update(updates)
        customer["updated_at"] = datetime.now(timezone.utc)
        return customer

    def delete_customer(self, customer_id: int) -> None:
        self.get_customer(customer_id)
        del self.database.customers[customer_id]

        address_ids = [key for key, value in self.database.addresses.items() if value["customer_id"] == customer_id]
        for address_id in address_ids:
            del self.database.addresses[address_id]

        business_profile_ids = [
            key
            for key, value in self.database.business_profiles.items()
            if value["customer_id"] == customer_id
        ]
        for business_profile_id in business_profile_ids:
            del self.database.business_profiles[business_profile_id]

        self.database.customer_tags = {
            relation for relation in self.database.customer_tags if relation[0] != customer_id
        }

    def get_customer_details(self, customer_id: int) -> dict:
        customer = dict(self.get_customer(customer_id))
        customer["addresses"] = self.list_addresses(customer_id)
        customer["business_profiles"] = self.list_business_profiles(customer_id)
        customer["tags"] = self.list_customer_tags(customer_id)
        return customer

    def list_addresses(self, customer_id: int) -> list[dict]:
        self.get_customer(customer_id)
        return sorted(
            [item for item in self.database.addresses.values() if item["customer_id"] == customer_id],
            key=lambda item: item["address_id"],
        )

    def get_address(self, address_id: int) -> dict:
        address = self.database.addresses.get(address_id)
        if address is None:
            raise NotFoundError(f"Address {address_id} was not found.")
        return address

    def create_address(self, customer_id: int, payload: CustomerAddressCreate) -> dict:
        self.get_customer(customer_id)
        address = {
            "address_id": self.database.next_address_id,
            "customer_id": customer_id,
            **payload.model_dump(),
        }
        self.database.addresses[address["address_id"]] = address
        self.database.next_address_id += 1
        if address["is_primary"]:
            self._set_primary_address(customer_id, address["address_id"])
        return address

    def update_address(self, address_id: int, payload: CustomerAddressUpdate) -> dict:
        address = self.get_address(address_id)
        updates = payload.model_dump(exclude_unset=True)
        customer_id = updates.get("customer_id", address["customer_id"])
        self.get_customer(customer_id)
        address.update(updates)
        address["customer_id"] = customer_id
        if address.get("is_primary"):
            self._set_primary_address(customer_id, address_id)
        return address

    def delete_address(self, address_id: int) -> None:
        self.get_address(address_id)
        del self.database.addresses[address_id]

    def list_business_profiles(self, customer_id: int) -> list[dict]:
        self.get_customer(customer_id)
        return sorted(
            [
                item
                for item in self.database.business_profiles.values()
                if item["customer_id"] == customer_id
            ],
            key=lambda item: item["business_profile_id"],
        )

    def get_business_profile(self, business_profile_id: int) -> dict:
        profile = self.database.business_profiles.get(business_profile_id)
        if profile is None:
            raise NotFoundError(f"Business profile {business_profile_id} was not found.")
        return profile

    def create_business_profile(self, customer_id: int, payload: CustomerBusinessProfileCreate) -> dict:
        self.get_customer(customer_id)
        profile = {
            "business_profile_id": self.database.next_business_profile_id,
            "customer_id": customer_id,
            **payload.model_dump(),
        }
        self.database.business_profiles[profile["business_profile_id"]] = profile
        self.database.next_business_profile_id += 1
        return profile

    def update_business_profile(
        self,
        business_profile_id: int,
        payload: CustomerBusinessProfileUpdate,
    ) -> dict:
        profile = self.get_business_profile(business_profile_id)
        updates = payload.model_dump(exclude_unset=True)
        customer_id = updates.get("customer_id", profile["customer_id"])
        self.get_customer(customer_id)
        profile.update(updates)
        profile["customer_id"] = customer_id
        return profile

    def delete_business_profile(self, business_profile_id: int) -> None:
        self.get_business_profile(business_profile_id)
        del self.database.business_profiles[business_profile_id]

    def list_tags(self) -> list[dict]:
        return sorted(self.database.tags.values(), key=lambda item: item["tag_id"])

    def get_tag(self, tag_id: int) -> dict:
        tag = self.database.tags.get(tag_id)
        if tag is None:
            raise NotFoundError(f"Tag {tag_id} was not found.")
        return tag

    def create_tag(self, payload: TagCreate) -> dict:
        self._ensure_unique_tag_name(payload.tag_name)
        tag = {"tag_id": self.database.next_tag_id, "tag_name": payload.tag_name}
        self.database.tags[tag["tag_id"]] = tag
        self.database.next_tag_id += 1
        return tag

    def update_tag(self, tag_id: int, payload: TagUpdate) -> dict:
        tag = self.get_tag(tag_id)
        self._ensure_unique_tag_name(payload.tag_name, tag_id)
        tag["tag_name"] = payload.tag_name
        return tag

    def delete_tag(self, tag_id: int) -> None:
        self.get_tag(tag_id)
        del self.database.tags[tag_id]
        self.database.customer_tags = {
            relation for relation in self.database.customer_tags if relation[1] != tag_id
        }

    def list_customer_tags(self, customer_id: int) -> list[dict]:
        self.get_customer(customer_id)
        tag_ids = [tag_id for current_customer_id, tag_id in self.database.customer_tags if current_customer_id == customer_id]
        return sorted([self.database.tags[tag_id] for tag_id in tag_ids], key=lambda item: item["tag_id"])

    def assign_tag_to_customer(self, customer_id: int, tag_id: int) -> list[dict]:
        self.get_customer(customer_id)
        self.get_tag(tag_id)
        relation = (customer_id, tag_id)
        if relation in self.database.customer_tags:
            raise ConflictError(f"Tag {tag_id} is already assigned to customer {customer_id}.")
        self.database.customer_tags.add(relation)
        return self.list_customer_tags(customer_id)

    def remove_tag_from_customer(self, customer_id: int, tag_id: int) -> list[dict]:
        self.get_customer(customer_id)
        self.get_tag(tag_id)
        relation = (customer_id, tag_id)
        if relation not in self.database.customer_tags:
            raise NotFoundError(f"Tag {tag_id} is not assigned to customer {customer_id}.")
        self.database.customer_tags.remove(relation)
        return self.list_customer_tags(customer_id)

    def _ensure_unique_email(self, email: str, excluded_customer_id: int | None = None) -> None:
        normalized_email = email.strip().lower()
        for customer in self.database.customers.values():
            same_customer = customer["customer_id"] == excluded_customer_id
            if not same_customer and customer["email"].strip().lower() == normalized_email:
                raise ConflictError(f"Email '{email}' is already in use.")

    def _ensure_unique_tag_name(self, tag_name: str, excluded_tag_id: int | None = None) -> None:
        normalized_name = tag_name.strip().lower()
        for tag in self.database.tags.values():
            same_tag = tag["tag_id"] == excluded_tag_id
            if not same_tag and tag["tag_name"].strip().lower() == normalized_name:
                raise ConflictError(f"Tag '{tag_name}' already exists.")

    def _set_primary_address(self, customer_id: int, selected_address_id: int) -> None:
        for address in self.database.addresses.values():
            if address["customer_id"] == customer_id:
                address["is_primary"] = address["address_id"] == selected_address_id
