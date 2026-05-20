from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.ai_classifier import classify_inquiry_text
from app.database import Base, engine, get_db


Base.metadata.create_all(bind=engine)

app = FastAPI(title="ai-inquiry-support-app")


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/inquiries", response_model=schemas.InquiryRead, status_code=201)
def create_inquiry(
    inquiry: schemas.InquiryCreate,
    db: Session = Depends(get_db),
) -> models.Inquiry:
    return crud.create_inquiry(db=db, inquiry=inquiry)


@app.post(
    "/inquiries/{inquiry_id}/classify",
    response_model=schemas.AIClassificationRead,
    status_code=201,
)
def classify_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
) -> models.AIClassification:
    inquiry = crud.get_inquiry(db=db, inquiry_id=inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    try:
        classification_result = classify_inquiry_text(inquiry.body)
        return crud.create_ai_classification(
            db=db,
            inquiry_id=inquiry.id,
            classification_result=classification_result,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI classification failed: {exc}",
        ) from exc
