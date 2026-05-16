from sqlalchemy.orm import Session

from app import models, schemas


def create_inquiry(db: Session, inquiry: schemas.InquiryCreate) -> models.Inquiry:
    db_inquiry = models.Inquiry(body=inquiry.body)
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
    return db_inquiry
