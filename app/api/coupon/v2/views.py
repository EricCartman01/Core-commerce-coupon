from fastapi import APIRouter, Depends
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_412_PRECONDITION_FAILED,
)

from app.api.coupon.v2.schema import (
    CouponReservedInputSchema,
    CouponUnreservedConfirmedInputSchema,
    MessageError,
)
from app.api.helpers.exception import DomainException, HTTPError
from app.db.dependencies import get_db_session
from app.services.coupon import CouponService

router = APIRouter()


@router.put(
    "/reserved",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def add_reserved(
    coupon_reserved_input: CouponReservedInputSchema,
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
        return await coupon_service.add_reserved(
            coupon_reserved_input.code,
            coupon_reserved_input,
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
    "/unreserved",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def remove_reserved(
    coupon_unreserved: CouponUnreservedConfirmedInputSchema,
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Remove reserved to coupon model in database.

    :param code: Coupon code to resenved.
    :param coupon_service: CouponService instance.

    :return: Success with No Content.

    :raises HTTPError: 404 - Coupon not found
    """
    try:
        coupon_service: CouponService = CouponService(db_session)
        return await coupon_service.remove_reserved(
            coupon_unreserved.code,
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
    "/confirmed",
    status_code=HTTP_204_NO_CONTENT,
    responses={HTTP_404_NOT_FOUND: {"model": MessageError}},
)
async def add_confirmed(
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
            coupon_confirmed.code,
            coupon_confirmed.transaction_id,
        )
    except NoResultFound:
        raise HTTPError(
            status_code=HTTP_404_NOT_FOUND,
            error_message="coupon not found",
            error_code="coupon_not_exists",
        )
