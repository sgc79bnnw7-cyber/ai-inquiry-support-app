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


def update_inquiry_status(
    db: Session,
    inquiry: models.Inquiry,
    new_status: str,
) -> models.Inquiry:
    inquiry.status = new_status
    db.commit()
    db.refresh(inquiry)
    return inquiry


def list_inquiries(
    db: Session,
    *,
    status: str | None = None,
    keyword: str | None = None,
) -> list[schemas.InquiryListItem]:
    # 指定された条件だけを WHERE に AND で積んでいく（動的クエリ構築）。
    query = db.query(models.Inquiry)
    if status:
        query = query.filter(models.Inquiry.status == status)
    if keyword:
        # 本文の部分一致（大文字小文字を区別しない ILIKE）。
        query = query.filter(models.Inquiry.body.ilike(f"%{keyword}%"))
    inquiries = query.order_by(models.Inquiry.id.desc()).all()

    # 問い合わせごとの「最新の分類」を1件だけ取得する。
    # DISTINCT ON (inquiry_id) は、inquiry_id でグループ化したうえで
    # ORDER BY の並びで最初の1行（= id が最大 = 最新の分類）を返す PostgreSQL の機能。
    rows = db.execute(text("""
        SELECT DISTINCT ON (inquiry_id) inquiry_id, category, urgency
        FROM ai_classifications
        ORDER BY inquiry_id, id DESC
    """)).fetchall()
    latest_by_inquiry = {
        row.inquiry_id: (row.category, row.urgency) for row in rows
    }

    items: list[schemas.InquiryListItem] = []
    for inquiry in inquiries:
        category, urgency = latest_by_inquiry.get(inquiry.id, (None, None))
        items.append(
            schemas.InquiryListItem(
                id=inquiry.id,
                body=inquiry.body,
                status=inquiry.status,
                created_at=inquiry.created_at,
                latest_category=category,
                latest_urgency=urgency,
            )
        )
    return items


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
