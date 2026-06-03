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


class AIClassificationRead(BaseModel):
    id: int
    inquiry_id: int
    category: str
    urgency: str
    reason: str
    model_name: str
    prompt_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricsResponse(BaseModel):
    total_inquiries: int
    classified_count: int
    classification_success_count: int
    classification_error_count: int
    classification_success_rate: float
