from fastapi import Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.helpers.exception import HTTPError
from app.settings import settings


async def get_authentication(
    api_key_header: str = Security(
        APIKeyHeader(name="access_token", auto_error=False),
    ),
):
    """
    Get authentication token from request header.

    :param api_key_header: API key from request header

    :return: Authentication token

    :raises HTTPError: If authentication token is not valid
    """
    if api_key_header == str(settings.api_key):
        return api_key_header
    raise HTTPError(
        status_code=HTTP_401_UNAUTHORIZED,
        error_message="Unauthorized",
        error_code="unauthorized",
    )
