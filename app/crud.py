from collections.abc import Mapping

from sqlalchemy import text
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


def get_metrics(db: Session) -> schemas.MetricsResponse:
    row = db.execute(text("""
        SELECT
          COUNT(*) FILTER (WHERE event_type = 'inquiry_created'          AND status = 'success') AS total_inquiries,
          COUNT(*) FILTER (WHERE event_type = 'classification_completed'                        ) AS classified_count,
          COUNT(*) FILTER (WHERE event_type = 'classification_completed' AND status = 'success') AS classification_success_count,
          COUNT(*) FILTER (WHERE event_type = 'classification_completed' AND status = 'error'  ) AS classification_error_count
        FROM event_logs
    """)).fetchone()

    classified = row.classified_count
    rate = round(100.0 * row.classification_success_count / classified, 1) if classified > 0 else 0.0

    return schemas.MetricsResponse(
        total_inquiries=row.total_inquiries,
        classified_count=classified,
        classification_success_count=row.classification_success_count,
        classification_error_count=row.classification_error_count,
        classification_success_rate=rate,
    )


def get_inquiry(db: Session, inquiry_id: int) -> models.Inquiry | None:
    return db.get(models.Inquiry, inquiry_id)


def list_inquiries(db: Session) -> list[models.Inquiry]:
    return (
        db.query(models.Inquiry)
        .order_by(models.Inquiry.id.desc())
        .all()
    )


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
