from typing import Any, Tuple

from sqlalchemy import Column, String, Table, TypeDecorator, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import as_declarative, declarative_mixin, declared_attr
from sqlalchemy.sql.functions import FunctionElement

from app.db.meta import meta


class CustomID(TypeDecorator):
    impl = String
    cache_ok = False

    def __init__(self):
        super().__init__(length=64)


class CreateCustomID(FunctionElement):
    name = "custom_id"


@compiles(CreateCustomID)
def create_custom_id_default(element, compiler, **kwargs):
    return compiler.process(  # pragma: no cover
        text(
            "concat(CAST(EXTRACT(EPOCH FROM now()) AS BIGINT),text('-'),gen_random_uuid())",  # noqa: E501
        ),
    )


@as_declarative(metadata=meta)
class Base:
    """
    Base for all models.

    It has some type definitions to
    enhance autocompletion.
    """

    __tablename__: str
    __table__: Table
    __table_args__: Tuple[Any, ...]
