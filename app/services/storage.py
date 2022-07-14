import uuid
from abc import ABC, abstractmethod

import boto3

from app.settings import settings


class StorageServiceAbstract(ABC):
    @abstractmethod
    def upload_file_obj(self, file_name):
        pass


class StorageAWSService(StorageServiceAbstract):
    def __init__(self):
        self.s3_client = boto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region_name,
        ).client("s3")

    def upload_file_obj(
        self,
        file: str,
    ) -> str:
        file_key: str = str(uuid.uuid4())
        self.s3_client.put_object(
            Body=file,
            Bucket=settings.aws_s3_bucket,
            Key=f"{file_key}",
        )

        return file_key
