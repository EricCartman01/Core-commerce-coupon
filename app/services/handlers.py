import csv
from io import StringIO

from loguru import logger

from app.services.coupon import CouponService
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable

from fastapi import UploadFile

COMMIT_NUMBER = 1000


async def create_coupon_by_schema(schema, db_session):
    coupon_service = CouponService(db_session)
    try:
        logger.info(f"oiii2")
        return await coupon_service.create_coupon_model(schema)
    except Exception as e:
        logger.exception(
            f"An error occurred when trying to create the coupon with "
            f"the customer_key: {schema.customer_key}. Exception: {e}",
        )


async def create_coupons_from_file(db_session, tmp_path, data):
    with open(tmp_path, "rU") as file:
        csv_reader = csv.reader(file)
        logger.info(f"oiii22 {csv_reader}")

        # coupons = []
        for row in csv_reader:
            logger.info(f"oiii {row}")
            customer_key = row[0]
            coupon = await create_coupon_by_schema(
                data.get_coupon_schema(customer_key),
                db_session,
            )
            logger.info("CHEGOU AQUI")
            db_session.add(coupon)
            logger.info("TÁ QUASE")
            await db_session.commit()
            logger.info("TAMBÉM CHEGOU AQUI")
            # if coupon:
            #     coupons.append(coupon)
            # if index % COMMIT_NUMBER == 0:
            #     logger.debug(f"Commit: {index}")
            #     await commit_coupons(db_session, coupons)
            #     coupons = []
        # if coupons:
        #     await commit_coupons(db_session, coupons)


async def commit_coupons(db_session, coupons):
    db_session.add_all(coupons)
    await db_session.commit()


def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path


async def create_bulk_coupons_by_customers(data, db_session):
    if data.file_with_customer_keys:
        logger.info(
            f"Inicio de processamento do arquivo "
            f"{data.file_with_customer_keys.filename} "
            f"com código {data.code}"
        )

        tmp_path = save_upload_file_tmp(data.file_with_customer_keys)
        try:
            await create_coupons_from_file(db_session, tmp_path, data)
        finally:
            tmp_path.unlink()

        logger.info(
            f"Fim de processamento do arquivo "
            f"{data.file_with_customer_keys.filename} "
            f"com código {data.code}"
        )
    elif data.customer_keys:
        coupons = []
        for customer_key in data.customer_keys:
            coupon = await create_coupon_by_schema(
                data.get_coupon_schema(customer_key),
                db_session,
            )
            if coupon:
                coupons.append(coupon)
        if coupons:
            await commit_coupons(db_session, coupons)
