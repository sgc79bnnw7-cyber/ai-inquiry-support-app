from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.ai_classifier import classify_inquiry_text
from app.ai_reply import generate_reply_draft
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
def list_inquiries(
    status: str | None = None,
    keyword: str | None = None,
    category: str | None = None,
    urgency: str | None = None,
    db: Session = Depends(get_db),
) -> list[schemas.InquiryListItem]:
    return crud.list_inquiries(
        db=db,
        status=status,
        keyword=keyword,
        category=category,
        urgency=urgency,
    )


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


@app.patch(
    "/inquiries/{inquiry_id}/status",
    response_model=schemas.InquiryStatusRead,
)
def update_inquiry_status(
    inquiry_id: int,
    payload: schemas.InquiryStatusUpdate,
    db: Session = Depends(get_db),
) -> models.Inquiry:
    inquiry = crud.get_inquiry(db=db, inquiry_id=inquiry_id)
    if inquiry is None:
        crud.create_event_log(
            db=db,
            event_type="status_changed",
            status="error",
            inquiry_id=None,
            detail=f"Inquiry not found: inquiry_id={inquiry_id}",
        )
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    if payload.status not in schemas.ALLOWED_STATUSES:
        crud.create_event_log(
            db=db,
            event_type="status_changed",
            status="error",
            inquiry_id=inquiry.id,
            detail=f"Invalid status: {payload.status}",
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {payload.status}",
        )

    old_status = inquiry.status
    updated = crud.update_inquiry_status(
        db=db,
        inquiry=inquiry,
        new_status=payload.status,
    )
    crud.create_event_log(
        db=db,
        event_type="status_changed",
        status="success",
        inquiry_id=updated.id,
        detail=f"{old_status} -> {updated.status}",
    )
    return updated


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


@app.post(
    "/inquiries/{inquiry_id}/reply-draft",
    response_model=schemas.ReplyDraftResponse,
)
def create_reply_draft(
    inquiry_id: int,
    db: Session = Depends(get_db),
) -> schemas.ReplyDraftResponse:
    inquiry = crud.get_inquiry(db=db, inquiry_id=inquiry_id)
    if inquiry is None:
        crud.create_event_log(
            db=db,
            event_type="reply_draft_generated",
            status="error",
            inquiry_id=None,
            detail=f"Inquiry not found: inquiry_id={inquiry_id}",
        )
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    # 最新の分類があれば参考にする（無ければ None のまま本文だけで生成）。
    category, urgency = crud.get_latest_classification(db=db, inquiry_id=inquiry.id)

    try:
        result = generate_reply_draft(
            body=inquiry.body,
            category=category,
            urgency=urgency,
        )
        crud.create_event_log(
            db=db,
            event_type="reply_draft_generated",
            status="success",
            inquiry_id=inquiry.id,
            detail=f"category={category}, urgency={urgency}",
        )
        return schemas.ReplyDraftResponse(
            inquiry_id=inquiry.id,
            reply_text=result["reply_text"],
            model_name=result["model_name"],
            prompt_version=result["prompt_version"],
            used_category=category,
            used_urgency=urgency,
        )
    except Exception as exc:
        crud.create_event_log(
            db=db,
            event_type="reply_draft_generated",
            status="error",
            inquiry_id=inquiry.id,
            detail=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"AI reply draft failed: {exc}",
        ) from exc
