from collections.abc import Mapping

from sqlalchemy.orm import Session

from app import models, schemas


def create_event_log(
    db: Session,
    event_type: str,
    status: str,
    inquiry_id: int | None = None,
    detail: str | None = None,
) -> models.EventLog:
    log = models.EventLog(
        event_type=event_type,
        inquiry_id=inquiry_id,
        status=status,
        detail=detail,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_inquiry(db: Session, inquiry_id: int) -> models.Inquiry | None:
    return db.get(models.Inquiry, inquiry_id)


def create_inquiry(db: Session, inquiry: schemas.InquiryCreate) -> models.Inquiry:
    db_inquiry = models.Inquiry(body=inquiry.body)
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
    return db_inquiry


def create_ai_classification(
    db: Session,
    inquiry_id: int,
    classification_result: Mapping[str, str],
) -> models.AIClassification:
    db_classification = models.AIClassification(
        inquiry_id=inquiry_id,
        category=classification_result["category"],
        urgency=classification_result["urgency"],
        reason=classification_result["reason"],
        model_name=classification_result["model_name"],
        prompt_version=classification_result["prompt_version"],
    )
    db.add(db_classification)
    db.commit()
    db.refresh(db_classification)
    return db_classification
