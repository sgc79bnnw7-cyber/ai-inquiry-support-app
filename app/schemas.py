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


ALLOWED_STATUSES = ("new", "in_progress", "closed")


class InquiryStatusUpdate(BaseModel):
    # 許可値は new / in_progress / closed。
    # 不正値も event_logs に記録するため、ここでは str で受けて
    # エンドポイント側で検証する。
    status: str = Field(..., min_length=1)


class InquiryStatusRead(BaseModel):
    id: int
    body: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InquiryListItem(BaseModel):
    id: int
    body: str
    status: str
    created_at: datetime
    latest_category: str | None = None
    latest_urgency: str | None = None

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
