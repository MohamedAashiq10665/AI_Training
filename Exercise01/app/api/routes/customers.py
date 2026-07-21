from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_customer_service
from app.domain.errors import ConflictError, NotFoundError, ValidationError
from app.models.schemas import (
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerAddressUpdate,
    CustomerBusinessProfileCreate,
    CustomerBusinessProfileResponse,
    CustomerBusinessProfileUpdate,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
    TagResponse,
)
from app.services.customer_service import CustomerService


router = APIRouter(prefix="/customers", tags=["customers"])


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if isinstance(error, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if isinstance(error, ValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    raise error


@router.get("", response_model=list[CustomerResponse])
def list_customers(service: CustomerService = Depends(get_customer_service)) -> list[dict]:
    return service.list_customers()


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.create_customer(payload)
    except (ConflictError, ValidationError) as error:
        _raise_http_error(error)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, service: CustomerService = Depends(get_customer_service)) -> dict:
    try:
        return service.get_customer(customer_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.update_customer(customer_id, payload)
    except (ConflictError, NotFoundError, ValidationError) as error:
        _raise_http_error(error)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, service: CustomerService = Depends(get_customer_service)) -> None:
    try:
        service.delete_customer(customer_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.get("/{customer_id}/details", response_model=CustomerDetailResponse)
def get_customer_details(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.get_customer_details(customer_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.get("/{customer_id}/addresses", response_model=list[CustomerAddressResponse])
def list_customer_addresses(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> list[dict]:
    try:
        return service.list_addresses(customer_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.post(
    "/{customer_id}/addresses",
    response_model=CustomerAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_address(
    customer_id: int,
    payload: CustomerAddressCreate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.create_address(customer_id, payload)
    except (NotFoundError, ValidationError) as error:
        _raise_http_error(error)


@router.get("/addresses/{address_id}", response_model=CustomerAddressResponse)
def get_customer_address(
    address_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.get_address(address_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.put("/addresses/{address_id}", response_model=CustomerAddressResponse)
def update_customer_address(
    address_id: int,
    payload: CustomerAddressUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.update_address(address_id, payload)
    except (NotFoundError, ValidationError) as error:
        _raise_http_error(error)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_address(
    address_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> None:
    try:
        service.delete_address(address_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.get("/{customer_id}/business-profiles", response_model=list[CustomerBusinessProfileResponse])
def list_customer_business_profiles(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> list[dict]:
    try:
        return service.list_business_profiles(customer_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.post(
    "/{customer_id}/business-profiles",
    response_model=CustomerBusinessProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_business_profile(
    customer_id: int,
    payload: CustomerBusinessProfileCreate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.create_business_profile(customer_id, payload)
    except (NotFoundError, ValidationError) as error:
        _raise_http_error(error)


@router.get(
    "/business-profiles/{business_profile_id}",
    response_model=CustomerBusinessProfileResponse,
)
def get_customer_business_profile(
    business_profile_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.get_business_profile(business_profile_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.put(
    "/business-profiles/{business_profile_id}",
    response_model=CustomerBusinessProfileResponse,
)
def update_customer_business_profile(
    business_profile_id: int,
    payload: CustomerBusinessProfileUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.update_business_profile(business_profile_id, payload)
    except (NotFoundError, ValidationError) as error:
        _raise_http_error(error)


@router.delete("/business-profiles/{business_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_business_profile(
    business_profile_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> None:
    try:
        service.delete_business_profile(business_profile_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.get("/{customer_id}/tags", response_model=list[TagResponse])
def list_customer_tags(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> list[dict]:
    try:
        return service.list_customer_tags(customer_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.post("/{customer_id}/tags/{tag_id}", response_model=list[TagResponse])
def assign_tag_to_customer(
    customer_id: int,
    tag_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> list[dict]:
    try:
        return service.assign_tag_to_customer(customer_id, tag_id)
    except (NotFoundError, ConflictError) as error:
        _raise_http_error(error)


@router.delete("/{customer_id}/tags/{tag_id}", response_model=list[TagResponse])
def remove_tag_from_customer(
    customer_id: int,
    tag_id: int,
    service: CustomerService = Depends(get_customer_service),
) -> list[dict]:
    try:
        return service.remove_tag_from_customer(customer_id, tag_id)
    except NotFoundError as error:
        _raise_http_error(error)
