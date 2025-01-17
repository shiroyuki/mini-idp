from enum import Enum
from typing import Any, List, TypeVar

import jsonpatch
from pydantic import BaseModel, Field

T = TypeVar("T")


class _PatchOperationType(str, Enum):
    add = "add"
    remove = "remove"
    replace = "replace"
    # There are more operations but this code will ignore unused ones.


class SimpleJsonPatchOperation(BaseModel):
    op: _PatchOperationType
    path: str
    value: Any


def apply_changes(obj: T, operations: List[SimpleJsonPatchOperation]) -> T:
    patch = jsonpatch.JsonPatch([o.model_dump() for o in operations])
    print(f"PANDA: obj = {obj}; patch = {patch}")
    return patch.apply(obj)