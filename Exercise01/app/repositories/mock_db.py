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
            }
        }
        self.business_profiles = {
            1: {
                "business_profile_id": 1,
                "customer_id": 2,
                "company_name": "Northwind Advisory",
                "job_title": "Procurement Lead",
                "lead_source": "Referral",
                "lifecycle_stage": LifecycleStage.OPPORTUNITY,
            }
        }
        self.tags = {
            1: {"tag_id": 1, "tag_name": "vip"},
            2: {"tag_id": 2, "tag_name": "newsletter"},
            3: {"tag_id": 3, "tag_name": "enterprise"},
        }
        self.customer_tags = {(1, 1), (2, 3)}

        self.next_customer_id = 3
        self.next_address_id = 2
        self.next_business_profile_id = 2
        self.next_tag_id = 4
