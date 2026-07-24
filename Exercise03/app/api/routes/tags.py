from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_customer_service
from app.domain.errors import ConflictError, NotFoundError
from app.models.schemas import TagCreate, TagResponse, TagUpdate
from app.services.customer_service import CustomerService


router = APIRouter(prefix="/tags", tags=["tags"])


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if isinstance(error, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    raise error


@router.get("", response_model=list[TagResponse])
def list_tags(service: CustomerService = Depends(get_customer_service)) -> list[dict]:
    return service.list_tags()


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, service: CustomerService = Depends(get_customer_service)) -> dict:
    try:
        return service.create_tag(payload)
    except ConflictError as error:
        _raise_http_error(error)


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: int, service: CustomerService = Depends(get_customer_service)) -> dict:
    try:
        return service.get_tag(tag_id)
    except NotFoundError as error:
        _raise_http_error(error)


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    payload: TagUpdate,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    try:
        return service.update_tag(tag_id, payload)
    except (ConflictError, NotFoundError) as error:
        _raise_http_error(error)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, service: CustomerService = Depends(get_customer_service)) -> None:
    try:
        service.delete_tag(tag_id)
    except NotFoundError as error:
        _raise_http_error(error)
