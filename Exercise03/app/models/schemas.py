from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CustomerStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    ARCHIVED = "Archived"
    PENDING = "Pending"


class CustomerType(str, Enum):
    B2C = "B2C"
    B2B = "B2B"


class AddressType(str, Enum):
    BILLING = "Billing"
    SHIPPING = "Shipping"
    OFFICE = "Office"


class LifecycleStage(str, Enum):
    LEAD = "Lead"
    OPPORTUNITY = "Opportunity"
    CUSTOMER = "Customer"
    CHURNED = "Churned"


class CustomerCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    phone: str | None = None
    status: CustomerStatus = CustomerStatus.PENDING
    customer_type: CustomerType = CustomerType.B2C


class CustomerUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=3)
    phone: str | None = None
    status: CustomerStatus | None = None
    customer_type: CustomerType | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    status: CustomerStatus
    customer_type: CustomerType
    created_at: datetime
    updated_at: datetime


class CustomerAddressCreate(BaseModel):
    address_type: AddressType
    address_line1: str = Field(min_length=1)
    address_line2: str | None = None
    city: str = Field(min_length=1)
    state_province: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    is_primary: bool = False


class CustomerAddressUpdate(BaseModel):
    customer_id: int | None = None
    address_type: AddressType | None = None
    address_line1: str | None = Field(default=None, min_length=1)
    address_line2: str | None = None
    city: str | None = Field(default=None, min_length=1)
    state_province: str | None = Field(default=None, min_length=1)
    postal_code: str | None = Field(default=None, min_length=1)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    is_primary: bool | None = None


class CustomerAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    address_id: int
    customer_id: int
    address_type: AddressType
    address_line1: str
    address_line2: str | None = None
    city: str
    state_province: str
    postal_code: str
    country_code: str
    is_primary: bool


class CustomerBusinessProfileCreate(BaseModel):
    company_name: str = Field(min_length=1)
    job_title: str | None = None
    lead_source: str | None = None
    lifecycle_stage: LifecycleStage = LifecycleStage.LEAD


class CustomerBusinessProfileUpdate(BaseModel):
    customer_id: int | None = None
    company_name: str | None = Field(default=None, min_length=1)
    job_title: str | None = None
    lead_source: str | None = None
    lifecycle_stage: LifecycleStage | None = None


class CustomerBusinessProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_profile_id: int
    customer_id: int
    company_name: str
    job_title: str | None = None
    lead_source: str | None = None
    lifecycle_stage: LifecycleStage


class TagCreate(BaseModel):
    tag_name: str = Field(min_length=1)


class TagUpdate(BaseModel):
    tag_name: str = Field(min_length=1)


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tag_id: int
    tag_name: str


class CustomerDetailResponse(CustomerResponse):
    addresses: list[CustomerAddressResponse]
    business_profiles: list[CustomerBusinessProfileResponse]
    tags: list[TagResponse]


class ExternalActivityResponse(BaseModel):
    open_todos: int
    total_todos: int
    recent_post_titles: list[str]


class WeatherResponse(BaseModel):
    provider: str
    city: str
    temperature_c: float
    condition: str
    wind_speed_mps: float


class EnrichedCustomerProfileResponse(BaseModel):
    customer: CustomerDetailResponse
    external_activity: ExternalActivityResponse | None = None
    weather: WeatherResponse | None = None
    warnings: list[str] = Field(default_factory=list)
    retrieved_at: datetime
