from unittest.mock import patch

import pytest

from app.services.storage import StorageAWSService


@pytest.mark.asyncio
@patch("boto3.Session.client")
async def test_upload_file_obj(mock_client):

    # GIVEN
    storage_service = StorageAWSService()
    file_key = storage_service.upload_file_obj("file.csv")

    assert file_key is not None
