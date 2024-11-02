from time import time
from typing import Optional, Dict

from pydantic import BaseModel, Field

from midp.app.models import ClientConfiguration


class CLIConfiguration(BaseModel):
    release_version: str = '1.0'
    current_context: Optional[str] = None
    contexts: Dict[str, ClientConfiguration] = Field(default_factory=dict)
    last_update_time: float = Field(default_factory=lambda: time())
