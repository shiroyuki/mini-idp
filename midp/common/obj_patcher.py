from enum import Enum
from typing import Any, List, TypeVar, Union

import jsonpatch
from pydantic import BaseModel, Field

T = TypeVar("T")


class OperationType(str, Enum):
    add = "add"
    remove = "remove"
    replace = "replace"
    # There are more operations but this code will ignore unused ones.


class PatchOperation(BaseModel):
    op: Union[OperationType, str]
    path: str
    value: Any


def apply_changes(obj: T, operations: List[PatchOperation]) -> T:
    patch = jsonpatch.JsonPatch([o.model_dump() for o in operations])
    return patch.apply(obj)