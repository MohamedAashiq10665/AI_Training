from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.schemas import AddressType, CustomerStatus, CustomerType, LifecycleStage


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    status = Column(Enum(CustomerStatus, native_enum=False), nullable=False)
    customer_type = Column(Enum(CustomerType, native_enum=False), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    business_profiles = relationship(
        "CustomerBusinessProfile",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    customer_tags = relationship("CustomerTag", back_populates="customer", cascade="all, delete-orphan")


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    address_type = Column(Enum(AddressType, native_enum=False), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country_code = Column(String(2), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)

    customer = relationship("Customer", back_populates="addresses")


class CustomerBusinessProfile(Base):
    __tablename__ = "customer_business_profiles"

    business_profile_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(150), nullable=False)
    job_title = Column(String(150), nullable=True)
    lead_source = Column(String(150), nullable=True)
    lifecycle_stage = Column(Enum(LifecycleStage, native_enum=False), nullable=False)
    establishment_start_date = Column(Date, nullable=False)
    onboarding_date = Column(Date, nullable=False)

    customer = relationship("Customer", back_populates="business_profiles")


class Tag(Base):
    __tablename__ = "tags"

    tag_id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String(100), nullable=False, unique=True, index=True)

    customer_tags = relationship("CustomerTag", back_populates="tag", cascade="all, delete-orphan")


class CustomerTag(Base):
    __tablename__ = "customer_tags"
    __table_args__ = (UniqueConstraint("customer_id", "tag_id", name="uq_customer_tag"),)

    customer_tag_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), nullable=False)

    customer = relationship("Customer", back_populates="customer_tags")
    tag = relationship("Tag", back_populates="customer_tags")
