import pytest
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from starlette import status

from app.api.helpers.exception import HTTPError


@pytest.fixture()
def register_route(app):  # noqa: WPS238
    class BaseSchema(BaseModel):
        name: str

    @app.get("/no-results/{result_id}")
    async def no_results(result_id):
        raise NoResultFound(f"Entity not found [{result_id}]")

    @app.get("/error-messages")
    async def error_messages():
        raise HTTPError(error_message="Test message")

    @app.get("/error-status-codes")
    async def error_status_codes():
        raise HTTPError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_message="Internal server error =(",
            error_code="internal_server_error",
        )

    @app.post("/request-validations")
    async def request_validations(_: BaseSchema):
        raise AssertionError()


@pytest.mark.asyncio
@pytest.mark.usefixtures("register_route")
async def test_should_get_no_result_found_message(async_client):
    response = await async_client.get("/no-results/123")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "error_code": "not_found",
        "error_message": "Entity not found [123]",
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("register_route")
async def test_should_get_http_error_with_message(async_client):
    response = await async_client.get("/error-messages")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "error_code": "bad_request",
        "error_message": "Test message",
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("register_route")
async def test_should_get_http_error_with_status_code(async_client):
    response = await async_client.get("/error-status-codes")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "error_code": "internal_server_error",
        "error_message": "Internal server error =(",
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("register_route")
async def test_should_get_http_error_with_request_validation(async_client):
    response = await async_client.post("/request-validations", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "error_code": "unprocessable_entity",
        "error_message": [
            {
                "loc": ["body", "name"],
                "msg": "field required",
                "type": "value_error.missing",
            },
        ],
    }
