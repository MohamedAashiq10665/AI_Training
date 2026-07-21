from datetime import datetime
from typing import Protocol

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.errors import ConflictError, NotFoundError
from app.models.db_models import Customer, CustomerAddress, CustomerBusinessProfile, CustomerTag, Tag
from app.models.schemas import (
    AddressType,
    CustomerStatus,
    CustomerType,
    LifecycleStage,
)


class CustomerRepository(Protocol):
    def list_customers(self) -> list[dict]: ...

    def get_customer(self, customer_id: int) -> dict: ...

    def create_customer(self, payload: dict) -> dict: ...

    def update_customer(self, customer_id: int, payload: dict) -> dict: ...

    def delete_customer(self, customer_id: int) -> None: ...

    def list_addresses(self, customer_id: int) -> list[dict]: ...

    def get_address(self, address_id: int) -> dict: ...

    def create_address(self, customer_id: int, payload: dict) -> dict: ...

    def update_address(self, address_id: int, payload: dict) -> dict: ...

    def delete_address(self, address_id: int) -> None: ...

    def list_business_profiles(self, customer_id: int) -> list[dict]: ...

    def get_business_profile(self, business_profile_id: int) -> dict: ...

    def create_business_profile(self, customer_id: int, payload: dict) -> dict: ...

    def update_business_profile(self, business_profile_id: int, payload: dict) -> dict: ...

    def delete_business_profile(self, business_profile_id: int) -> None: ...

    def list_tags(self) -> list[dict]: ...

    def get_tag(self, tag_id: int) -> dict: ...

    def create_tag(self, payload: dict) -> dict: ...

    def update_tag(self, tag_id: int, payload: dict) -> dict: ...

    def delete_tag(self, tag_id: int) -> None: ...

    def list_customer_tags(self, customer_id: int) -> list[dict]: ...

    def assign_tag_to_customer(self, customer_id: int, tag_id: int) -> list[dict]: ...

    def remove_tag_from_customer(self, customer_id: int, tag_id: int) -> list[dict]: ...


class SqlAlchemyCustomerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_customers(self) -> list[dict]:
        rows = self.db.query(Customer).order_by(Customer.customer_id).all()
        return [self._serialize_customer(row) for row in rows]

    def get_customer(self, customer_id: int) -> dict:
        customer = self.db.get(Customer, customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} was not found.")
        return self._serialize_customer(customer)

    def create_customer(self, payload: dict) -> dict:
        self._ensure_unique_email(payload["email"])
        customer = Customer(**payload)
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return self._serialize_customer(customer)

    def update_customer(self, customer_id: int, payload: dict) -> dict:
        customer = self.db.get(Customer, customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} was not found.")
        email = payload.get("email")
        if email is not None:
            self._ensure_unique_email(email, customer_id)
        for key, value in payload.items():
            setattr(customer, key, value)
        customer.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(customer)
        return self._serialize_customer(customer)

    def delete_customer(self, customer_id: int) -> None:
        customer = self.db.get(Customer, customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} was not found.")
        self.db.delete(customer)
        self.db.commit()

    def list_addresses(self, customer_id: int) -> list[dict]:
        self._get_customer_entity(customer_id)
        rows = self.db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer_id).order_by(CustomerAddress.address_id).all()
        return [self._serialize_address(row) for row in rows]

    def get_address(self, address_id: int) -> dict:
        address = self.db.get(CustomerAddress, address_id)
        if address is None:
            raise NotFoundError(f"Address {address_id} was not found.")
        return self._serialize_address(address)

    def create_address(self, customer_id: int, payload: dict) -> dict:
        self._get_customer_entity(customer_id)
        address = CustomerAddress(customer_id=customer_id, **payload)
        self.db.add(address)
        self.db.flush()
        if address.is_primary:
            self._set_primary_address(customer_id, address.address_id)
        self.db.commit()
        self.db.refresh(address)
        return self._serialize_address(address)

    def update_address(self, address_id: int, payload: dict) -> dict:
        address = self.db.get(CustomerAddress, address_id)
        if address is None:
            raise NotFoundError(f"Address {address_id} was not found.")

        customer_id = payload.get("customer_id", address.customer_id)
        self._get_customer_entity(customer_id)
        for key, value in payload.items():
            setattr(address, key, value)
        if address.is_primary:
            self._set_primary_address(address.customer_id, address.address_id)
        self.db.commit()
        self.db.refresh(address)
        return self._serialize_address(address)

    def delete_address(self, address_id: int) -> None:
        address = self.db.get(CustomerAddress, address_id)
        if address is None:
            raise NotFoundError(f"Address {address_id} was not found.")
        self.db.delete(address)
        self.db.commit()

    def list_business_profiles(self, customer_id: int) -> list[dict]:
        self._get_customer_entity(customer_id)
        rows = self.db.query(CustomerBusinessProfile).filter(
            CustomerBusinessProfile.customer_id == customer_id
        ).order_by(CustomerBusinessProfile.business_profile_id).all()
        return [self._serialize_business_profile(row) for row in rows]

    def get_business_profile(self, business_profile_id: int) -> dict:
        row = self.db.get(CustomerBusinessProfile, business_profile_id)
        if row is None:
            raise NotFoundError(f"Business profile {business_profile_id} was not found.")
        return self._serialize_business_profile(row)

    def create_business_profile(self, customer_id: int, payload: dict) -> dict:
        self._get_customer_entity(customer_id)
        row = CustomerBusinessProfile(customer_id=customer_id, **payload)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._serialize_business_profile(row)

    def update_business_profile(self, business_profile_id: int, payload: dict) -> dict:
        row = self.db.get(CustomerBusinessProfile, business_profile_id)
        if row is None:
            raise NotFoundError(f"Business profile {business_profile_id} was not found.")
        customer_id = payload.get("customer_id", row.customer_id)
        self._get_customer_entity(customer_id)
        for key, value in payload.items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return self._serialize_business_profile(row)

    def delete_business_profile(self, business_profile_id: int) -> None:
        row = self.db.get(CustomerBusinessProfile, business_profile_id)
        if row is None:
            raise NotFoundError(f"Business profile {business_profile_id} was not found.")
        self.db.delete(row)
        self.db.commit()

    def list_tags(self) -> list[dict]:
        rows = self.db.query(Tag).order_by(Tag.tag_id).all()
        return [self._serialize_tag(row) for row in rows]

    def get_tag(self, tag_id: int) -> dict:
        row = self.db.get(Tag, tag_id)
        if row is None:
            raise NotFoundError(f"Tag {tag_id} was not found.")
        return self._serialize_tag(row)

    def create_tag(self, payload: dict) -> dict:
        self._ensure_unique_tag_name(payload["tag_name"])
        row = Tag(**payload)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._serialize_tag(row)

    def update_tag(self, tag_id: int, payload: dict) -> dict:
        row = self.db.get(Tag, tag_id)
        if row is None:
            raise NotFoundError(f"Tag {tag_id} was not found.")
        self._ensure_unique_tag_name(payload["tag_name"], tag_id)
        row.tag_name = payload["tag_name"]
        self.db.commit()
        self.db.refresh(row)
        return self._serialize_tag(row)

    def delete_tag(self, tag_id: int) -> None:
        row = self.db.get(Tag, tag_id)
        if row is None:
            raise NotFoundError(f"Tag {tag_id} was not found.")
        self.db.delete(row)
        self.db.commit()

    def list_customer_tags(self, customer_id: int) -> list[dict]:
        self._get_customer_entity(customer_id)
        rows = self.db.query(Tag).join(CustomerTag, CustomerTag.tag_id == Tag.tag_id).filter(
            CustomerTag.customer_id == customer_id
        ).order_by(Tag.tag_id).all()
        return [self._serialize_tag(row) for row in rows]

    def assign_tag_to_customer(self, customer_id: int, tag_id: int) -> list[dict]:
        self._get_customer_entity(customer_id)
        self._get_tag_entity(tag_id)
        existing = self.db.query(CustomerTag).filter(
            CustomerTag.customer_id == customer_id,
            CustomerTag.tag_id == tag_id,
        ).first()
        if existing is not None:
            raise ConflictError(f"Tag {tag_id} is already assigned to customer {customer_id}.")
        self.db.add(CustomerTag(customer_id=customer_id, tag_id=tag_id))
        self.db.commit()
        return self.list_customer_tags(customer_id)

    def remove_tag_from_customer(self, customer_id: int, tag_id: int) -> list[dict]:
        self._get_customer_entity(customer_id)
        self._get_tag_entity(tag_id)
        existing = self.db.query(CustomerTag).filter(
            CustomerTag.customer_id == customer_id,
            CustomerTag.tag_id == tag_id,
        ).first()
        if existing is None:
            raise NotFoundError(f"Tag {tag_id} is not assigned to customer {customer_id}.")
        self.db.delete(existing)
        self.db.commit()
        return self.list_customer_tags(customer_id)

    def _ensure_unique_email(self, email: str, excluded_customer_id: int | None = None) -> None:
        query = self.db.query(Customer).filter(func.lower(Customer.email) == email.strip().lower())
        if excluded_customer_id is not None:
            query = query.filter(Customer.customer_id != excluded_customer_id)
        if query.first() is not None:
            raise ConflictError(f"Email '{email}' is already in use.")

    def _ensure_unique_tag_name(self, tag_name: str, excluded_tag_id: int | None = None) -> None:
        query = self.db.query(Tag).filter(func.lower(Tag.tag_name) == tag_name.strip().lower())
        if excluded_tag_id is not None:
            query = query.filter(Tag.tag_id != excluded_tag_id)
        if query.first() is not None:
            raise ConflictError(f"Tag '{tag_name}' already exists.")

    def _set_primary_address(self, customer_id: int, selected_address_id: int) -> None:
        rows = self.db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer_id).all()
        for row in rows:
            row.is_primary = row.address_id == selected_address_id

    def _get_customer_entity(self, customer_id: int) -> Customer:
        customer = self.db.get(Customer, customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} was not found.")
        return customer

    def _get_tag_entity(self, tag_id: int) -> Tag:
        tag = self.db.get(Tag, tag_id)
        if tag is None:
            raise NotFoundError(f"Tag {tag_id} was not found.")
        return tag

    def _serialize_customer(self, customer: Customer) -> dict:
        return {
            "customer_id": customer.customer_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "phone": customer.phone,
            "status": CustomerStatus(customer.status),
            "customer_type": CustomerType(customer.customer_type),
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
        }

    def _serialize_address(self, address: CustomerAddress) -> dict:
        return {
            "address_id": address.address_id,
            "customer_id": address.customer_id,
            "address_type": AddressType(address.address_type),
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "city": address.city,
            "state_province": address.state_province,
            "postal_code": address.postal_code,
            "country_code": address.country_code,
            "is_primary": address.is_primary,
        }

    def _serialize_business_profile(self, row: CustomerBusinessProfile) -> dict:
        return {
            "business_profile_id": row.business_profile_id,
            "customer_id": row.customer_id,
            "company_name": row.company_name,
            "job_title": row.job_title,
            "lead_source": row.lead_source,
            "lifecycle_stage": LifecycleStage(row.lifecycle_stage),
            "establishment_start_date": row.establishment_start_date,
            "onboarding_date": row.onboarding_date,
        }

    def _serialize_tag(self, row: Tag) -> dict:
        return {"tag_id": row.tag_id, "tag_name": row.tag_name}
