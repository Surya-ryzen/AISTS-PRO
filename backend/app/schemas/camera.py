from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CameraResponse(BaseModel):
    id: int
    name: str
    source_type: str
    location: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
