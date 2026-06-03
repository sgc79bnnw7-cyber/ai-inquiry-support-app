from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.ai_classifier import classify_inquiry_text
from app.database import Base, engine, get_db


Base.metadata.create_all(bind=engine)

app = FastAPI(title="ai-inquiry-support-app")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/metrics", response_model=schemas.MetricsResponse)
def get_metrics(db: Session = Depends(get_db)) -> schemas.MetricsResponse:
    return crud.get_metrics(db=db)


@app.get("/inquiries", response_model=list[schemas.InquiryListItem])
def list_inquiries(db: Session = Depends(get_db)) -> list[schemas.InquiryListItem]:
    return crud.list_inquiries(db=db)


@app.post("/inquiries", response_model=schemas.InquiryRead, status_code=201)
def create_inquiry(
    inquiry: schemas.InquiryCreate,
    db: Session = Depends(get_db),
) -> models.Inquiry:
    db_inquiry = crud.create_inquiry(db=db, inquiry=inquiry)
    crud.create_event_log(
        db=db,
        event_type="inquiry_created",
        status="success",
        inquiry_id=db_inquiry.id,
    )
    return db_inquiry


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
        crud.create_event_log(
            db=db,
            event_type="classification_requested",
            status="error",
            inquiry_id=None,
            detail=f"Inquiry not found: inquiry_id={inquiry_id}",
        )
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    crud.create_event_log(
        db=db,
        event_type="classification_requested",
        status="success",
        inquiry_id=inquiry.id,
    )

    try:
        classification_result = classify_inquiry_text(inquiry.body)
        result = crud.create_ai_classification(
            db=db,
            inquiry_id=inquiry.id,
            classification_result=classification_result,
        )
        crud.create_event_log(
            db=db,
            event_type="classification_completed",
            status="success",
            inquiry_id=inquiry.id,
        )
        return result
    except Exception as exc:
        crud.create_event_log(
            db=db,
            event_type="classification_completed",
            status="error",
            inquiry_id=inquiry.id,
            detail=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"AI classification failed: {exc}",
        ) from exc
