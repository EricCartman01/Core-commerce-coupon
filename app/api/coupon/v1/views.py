from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from loguru import logger
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_412_PRECONDITION_FAILED,
)

from app.api.coupon.v1.schema import (
    CouponInputSchema,
    CouponInputWithManyCustomers,
    CouponReservedInputSchema,
    CouponSchema,
    CouponUnreservedConfirmedInputSchema,
    CouponUpdateSchema,
    CouponValidateSchema,
    MessageError,
)
from app.api.helpers.exception import DomainException, HTTPError
from app.db.dependencies import get_db_session
from app.repository.coupon import CouponRepository
from app.services.coupon import CouponService

router = APIRouter()


@router.get("")
async def index(
    page: int = Query(1, description="page"),
    size: int = Query(50, le=100, description="size"),
    active: bool = Query(None, description="Status of coupon"),
    valid_from: datetime = Query(None, description="Valid From of coupon"),
    valid_until: datetime = Query(None, description="Valid Until of coupon"),
    description: str = Query(None, description="Description of coupon"),
    code: str = Query(None, description="Code of Coupon"),
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    List all coupons or filter by query params.

    :param active: Filter by active
    :param valid_from: Filter by valid_from
    :param valid_until: Filter by valid_until
    :param description: Filter by description
    :param code: Filter by code
    :param coupon_service: CouponService

    :return: Paginate with list of coupons
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        result = await coupon_service.get_filter(
            {
                "active": active,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "description": description,
                "code": code,
            },
            page,
            size,
        )

        return result
    except Exception as e:
        logger.exception(f"Consult error: {e}")
        raise e


@router.post("", status_code=HTTP_201_CREATED, response_model=CouponSchema)
async def create(
    new_coupon_object: CouponInputSchema,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Create coupon model in database.

    :param new_coupon_object: CouponInputSchema object to create.
    :param coupon_service: CouponService instance.

    :return: Coupon object created.
    """
    coupon_service: CouponService = CouponService(db_session)
    return await coupon_service.create_coupon(new_coupon_object)


@router.put(
    "/{code}/reserved",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def add_reserved(
    code: str,
    coupon_reserverd_input: CouponReservedInputSchema,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Add reserved to coupon model in database.

    :param code: Coupon code to resenved.
    :param coupon_service: CouponService instance.

    :return: Success with No Content.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.add_reserved(code, coupon_reserverd_input)
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )
    except DomainException as exception:
        raise HTTPError(
            status_code=HTTP_412_PRECONDITION_FAILED,
            error_message=str(exception),
            error_code=exception.error_code,
        )


@router.put(
    "/{code}/unreserved",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def remove_reserved(
    code: str,
    coupon_unreserved: CouponUnreservedConfirmedInputSchema,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Remove reserved to coupon model in database.

    :param code: Coupon code to reserved.
    :param coupon_service: CouponService instance.

    :return: Success with No Content.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.remove_reserved(
            code,
            coupon_unreserved.transaction_id,
        )
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )
    except DomainException as exception:
        raise HTTPError(
            status_code=HTTP_412_PRECONDITION_FAILED,
            error_message=str(exception),
            error_code=exception.error_code,
        )


@router.put(
    "/{code}/confirmed",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def add_confirmed(
    code: str,
    coupon_confirmed: CouponUnreservedConfirmedInputSchema,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Add confirmed to coupon model in database.

    :param code: new coupon model item.
    :param coupon_service: CouponService instance.

    :return: Success with No Content.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.add_confirmed(
            code,
            coupon_confirmed.transaction_id,
        )
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )


@router.get("/validate", response_model=CouponValidateSchema)
async def get_valid_coupon(
    code: str,
    customer_key: str,
    purchase_amount: Decimal,
    first_purchase: bool,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Get valid coupon model in database.

    :param code: Coupon code to valid.
    :param customer_key: Customer key use coupon.
    :param purchase_amount: Total amount of purchase.
    :param first_purchase: Indicates if is the first purchase.
    :param coupon_service: CouponService instance.


    :return: Coupon object.

    :raises HTTPError: 404 - Coupon not found
    """

    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.validate_coupon(
            code,
            customer_key,
            purchase_amount,
            first_purchase,
        )
    except DomainException as exception:
        raise HTTPError(
            status_code=HTTP_412_PRECONDITION_FAILED,
            error_message=str(exception),
            error_code=exception.error_code,
        )


@router.get(
    "/{coupon_id}",
    status_code=HTTP_200_OK,
    response_model=CouponSchema,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def show(
    coupon_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Get a coupon model in database by id.

    :param coupon_id: new coupon model item.
    :param coupon_repository: CouponRepository instance.

    :return: new coupon model.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_repository: CouponRepository = CouponRepository(db_session)
        coupon = await coupon_repository.get_by_id(coupon_id)
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )
    return coupon


@router.put(
    "/{coupon_id}",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def update(
    coupon_id: str,
    updated_coupon_object: CouponUpdateSchema,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Update coupon in database.

    :param coupon_id: new coupon model item.
    :param updated_coupon_object: updated coupon item.
    :param coupon_service: CouponService instance.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        await coupon_service.update_by_id(
            coupon_id,
            updated_coupon_object.dict(),
        )
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )
    except DomainException as exception:
        raise HTTPError(
            status_code=HTTP_412_PRECONDITION_FAILED,
            error_message=str(exception),
            error_code=exception.error_code,
        )


@router.delete(
    "/{coupon_id}",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def delete(
    coupon_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Delete coupon in database.

    :param coupon_id: Id of coupon to delete.
    :param coupon_service: CouponService instance.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        await coupon_service.delete_by_id(coupon_id)
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )


@router.post(
    "/{coupon_id}/activate",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def activate_coupon(
    coupon_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Activate a coupon.

    :param coupon_id: coupon id to active.

    :return: Success with No Content.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.activate_coupon(coupon_id)

    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )


@router.post(
    "/{coupon_id}/deactivate",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def deactivate_coupon(
    coupon_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Deactivate a coupon.

    :param coupon_id: coupon id to active.

    :return: Success with No Content.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.deactivate_coupon(coupon_id)

    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )


@router.post("/bulk/by-client", status_code=HTTP_202_ACCEPTED)
async def bulk_create(
    background_tasks: BackgroundTasks,
    form_data: CouponInputWithManyCustomers = Depends(
        CouponInputWithManyCustomers.as_form,
    ),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        coupon_service: CouponService = CouponService(db_session)
        task_model = await coupon_service.create_task(
            form_data,
            background_tasks,
        )
    except Exception as e:
        raise HTTPError(
            status_code=HTTP_412_PRECONDITION_FAILED,
            error_message=str(e),
            error_code="bulk_create_error",
        )
    return {"task_id": task_model.id}
