from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InquiryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    body: str = Field(..., min_length=1)


class InquiryRead(BaseModel):
    id: int
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
