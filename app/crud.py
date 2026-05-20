from collections.abc import Mapping

from sqlalchemy.orm import Session

from app import models, schemas


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
