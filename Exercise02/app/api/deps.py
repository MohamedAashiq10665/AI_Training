from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.customer_repository import SqlAlchemyCustomerRepository
from app.services.customer_service import CustomerService


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(SqlAlchemyCustomerRepository(db))
