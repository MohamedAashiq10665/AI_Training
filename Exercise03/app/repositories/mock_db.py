from datetime import datetime, timezone

from app.models.schemas import AddressType, CustomerStatus, CustomerType, LifecycleStage


class MockDatabase:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        now = datetime.now(timezone.utc)

        self.customers = {
            1: {
                "customer_id": 1,
                "first_name": "Ava",
                "last_name": "Stone",
                "email": "ava.stone@example.com",
                "phone": "+1-555-1000",
                "status": CustomerStatus.ACTIVE,
                "customer_type": CustomerType.B2C,
                "created_at": now,
                "updated_at": now,
            },
            2: {
                "customer_id": 2,
                "first_name": "Omar",
                "last_name": "Rahim",
                "email": "omar.rahim@example.com",
                "phone": "+1-555-2000",
                "status": CustomerStatus.PENDING,
                "customer_type": CustomerType.B2B,
                "created_at": now,
                "updated_at": now,
            },
            3: {
                "customer_id": 3,
                "first_name": "Nia",
                "last_name": "Carter",
                "email": "nia.carter@example.com",
                "phone": "+1-555-3000",
                "status": CustomerStatus.INACTIVE,
                "customer_type": CustomerType.B2C,
                "created_at": now,
                "updated_at": now,
            },
            4: {
                "customer_id": 4,
                "first_name": "Yousef",
                "last_name": "Haddad",
                "email": "yousef.haddad@example.com",
                "phone": "+1-555-4000",
                "status": CustomerStatus.ARCHIVED,
                "customer_type": CustomerType.B2B,
                "created_at": now,
                "updated_at": now,
            },
        }

        self.addresses = {
            1: {
                "address_id": 1,
                "customer_id": 1,
                "address_type": AddressType.BILLING,
                "address_line1": "101 Main Street",
                "address_line2": None,
                "city": "Austin",
                "state_province": "TX",
                "postal_code": "78701",
                "country_code": "US",
                "is_primary": True,
            },
            2: {
                "address_id": 2,
                "customer_id": 1,
                "address_type": AddressType.SHIPPING,
                "address_line1": "400 Cedar Road",
                "address_line2": "Suite 6",
                "city": "Austin",
                "state_province": "TX",
                "postal_code": "78702",
                "country_code": "US",
                "is_primary": False,
            },
            3: {
                "address_id": 3,
                "customer_id": 2,
                "address_type": AddressType.OFFICE,
                "address_line1": "22 Harbor Avenue",
                "address_line2": None,
                "city": "Seattle",
                "state_province": "WA",
                "postal_code": "98101",
                "country_code": "US",
                "is_primary": True,
            },
            4: {
                "address_id": 4,
                "customer_id": 3,
                "address_type": AddressType.BILLING,
                "address_line1": "77 Elm Drive",
                "address_line2": None,
                "city": "Boston",
                "state_province": "MA",
                "postal_code": "02110",
                "country_code": "US",
                "is_primary": True,
            },
        }

        self.business_profiles = {
            1: {
                "business_profile_id": 1,
                "customer_id": 1,
                "company_name": "Blue Horizon",
                "job_title": "Buyer",
                "lead_source": "Campaign",
                "lifecycle_stage": LifecycleStage.CUSTOMER,
            },
            2: {
                "business_profile_id": 2,
                "customer_id": 2,
                "company_name": "Northwind Advisory",
                "job_title": "Procurement Lead",
                "lead_source": "Referral",
                "lifecycle_stage": LifecycleStage.OPPORTUNITY,
            },
            3: {
                "business_profile_id": 3,
                "customer_id": 2,
                "company_name": "Northwind Advisory",
                "job_title": "Finance Controller",
                "lead_source": "Partner",
                "lifecycle_stage": LifecycleStage.CUSTOMER,
            },
            4: {
                "business_profile_id": 4,
                "customer_id": 3,
                "company_name": "Nimble Retail",
                "job_title": "Founder",
                "lead_source": "Web",
                "lifecycle_stage": LifecycleStage.LEAD,
            },
            5: {
                "business_profile_id": 5,
                "customer_id": 4,
                "company_name": "Atlas Group",
                "job_title": "COO",
                "lead_source": "Outbound",
                "lifecycle_stage": LifecycleStage.CHURNED,
            },
        }

        self.tags = {
            1: {"tag_id": 1, "tag_name": "vip"},
            2: {"tag_id": 2, "tag_name": "newsletter"},
            3: {"tag_id": 3, "tag_name": "enterprise"},
            4: {"tag_id": 4, "tag_name": "renewal-risk"},
        }

        self.customer_tags = {(1, 1), (1, 2), (2, 3), (4, 4)}

        self.next_customer_id = 5
        self.next_address_id = 5
        self.next_business_profile_id = 6
        self.next_tag_id = 5
