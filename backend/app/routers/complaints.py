from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.file_parsing import extract_text_from_bytes
from app.ai.langgraph_workflow import run_complaint_pipeline
from app.models.complaint import Complaint, AIAssessment, SeverityLevel
from app.schemas.complaint import (
    ExtractRequest,
    ExtractResponse,
    ExtractedFields,
    AIAssessmentOut,
    ComplaintCreate,
    ComplaintOut,
)

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _existing_complaints_context(db: Session) -> list[dict]:
    rows = db.scalars(select(Complaint).order_by(Complaint.created_at.desc()).limit(50)).all()
    return [
        {
            "id": c.id,
            "product_name": c.product_name,
            "batch_number": c.batch_number,
            "complaint_description": c.complaint_description,
        }
        for c in rows
    ]


def _run_pipeline_and_build_assessment(raw_text: str, db: Session) -> tuple[ExtractedFields, AIAssessmentOut]:
    context = _existing_complaints_context(db)
    result = run_complaint_pipeline(raw_text, existing_complaints=context)

    extracted = ExtractedFields(**result.get("extracted", {}))
    dup = result.get("duplicate", {})
    risk = result.get("risk", {})

    assessment = AIAssessmentOut(
        completeness_score=result.get("completeness_score", 0.0),
        missing_fields=result.get("missing_fields", []),
        risk_level=risk.get("risk_level", "Minor"),
        risk_rationale=risk.get("rationale", ""),
        is_duplicate=dup.get("is_duplicate", False),
        duplicate_of_id=dup.get("duplicate_of_id"),
        duplicate_similarity=dup.get("similarity", 0.0),
        root_cause_suggestion=result.get("root_cause", ""),
        capa_suggestion=result.get("capa", ""),
        summary=result.get("summary", ""),
    )
    return extracted, assessment


@router.post("/extract", response_model=ExtractResponse)
def extract_complaint(payload: ExtractRequest, db: Session = Depends(get_db)):
    """Run the full LangGraph pipeline over pasted/raw complaint text."""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text must not be empty")

    extracted, assessment = _run_pipeline_and_build_assessment(payload.raw_text, db)
    return ExtractResponse(extracted=extracted, assessment=assessment)


@router.post("/extract-file", response_model=ExtractResponse)
async def extract_complaint_from_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Same as /extract, but the source is an uploaded PDF/email/text file."""
    content = await file.read()
    raw_text = extract_text_from_bytes(file.filename or "upload.txt", content)
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from the uploaded file")

    extracted, assessment = _run_pipeline_and_build_assessment(raw_text, db)
    return ExtractResponse(extracted=extracted, assessment=assessment)


@router.post("", response_model=ComplaintOut)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    """Persist a complaint after the reviewer confirms/edits the AI-populated form."""
    complaint = Complaint(
        product_name=payload.product_name,
        batch_number=payload.batch_number,
        complainant_name=payload.complainant_name,
        complainant_email=payload.complainant_email,
        date_of_incident=payload.date_of_incident,
        complaint_description=payload.complaint_description,
        source_channel=payload.source_channel,
        raw_input_text=payload.raw_input_text,
        severity=(payload.assessment.risk_level if payload.assessment else SeverityLevel.MINOR),
    )
    db.add(complaint)
    db.flush()

    if payload.assessment:
        db.add(
            AIAssessment(
                complaint_id=complaint.id,
                completeness_score=payload.assessment.completeness_score,
                missing_fields=payload.assessment.missing_fields,
                risk_level=payload.assessment.risk_level,
                risk_rationale=payload.assessment.risk_rationale,
                is_duplicate=payload.assessment.is_duplicate,
                duplicate_of_id=payload.assessment.duplicate_of_id,
                duplicate_similarity=payload.assessment.duplicate_similarity,
                root_cause_suggestion=payload.assessment.root_cause_suggestion,
                capa_suggestion=payload.assessment.capa_suggestion,
                summary=payload.assessment.summary,
            )
        )

    db.commit()
    db.refresh(complaint)
    return _to_complaint_out(complaint)


@router.get("", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    rows = db.scalars(select(Complaint).order_by(Complaint.created_at.desc())).all()
    return [_to_complaint_out(c) for c in rows]


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _to_complaint_out(complaint)


def _to_complaint_out(c: Complaint) -> ComplaintOut:
    return ComplaintOut(
        id=c.id,
        product_name=c.product_name,
        batch_number=c.batch_number,
        complainant_name=c.complainant_name,
        complainant_email=c.complainant_email,
        date_of_incident=c.date_of_incident,
        complaint_description=c.complaint_description,
        source_channel=c.source_channel,
        severity=c.severity,
        status=c.status,
        created_at=c.created_at.isoformat(),
        assessment=AIAssessmentOut.model_validate(c.assessment) if c.assessment else None,
    )
