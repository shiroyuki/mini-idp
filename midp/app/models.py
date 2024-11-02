from pydantic import BaseModel


class ClientConfiguration(BaseModel):
    base_url: str
