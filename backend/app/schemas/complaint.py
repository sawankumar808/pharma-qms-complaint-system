from typing import Optional
from pydantic import BaseModel, ConfigDict


class ExtractRequest(BaseModel):
    """Payload for POST /api/complaints/extract — raw text pasted or extracted from a file."""

    raw_text: str


class AIAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    completeness_score: float
    missing_fields: list[str]

    risk_level: str
    risk_rationale: str

    is_duplicate: bool
    duplicate_of_id: Optional[str] = None
    duplicate_similarity: float

    root_cause_suggestion: str
    capa_suggestion: str
    summary: str


class ExtractedFields(BaseModel):
    product_name: str = ""
    batch_number: str = ""
    complainant_name: str = ""
    complainant_email: str = ""
    date_of_incident: str = ""
    complaint_description: str = ""


class ExtractResponse(BaseModel):
    """What the frontend uses to auto-populate the Log Customer Complaint form + AI Copilot panel."""

    extracted: ExtractedFields
    assessment: AIAssessmentOut


class ComplaintCreate(BaseModel):
    product_name: str
    batch_number: str
    complainant_name: str
    complainant_email: str
    date_of_incident: str
    complaint_description: str
    source_channel: str = "Manual Entry"
    raw_input_text: str = ""
    assessment: Optional[AIAssessmentOut] = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_name: str
    batch_number: str
    complainant_name: str
    complainant_email: str
    date_of_incident: str
    complaint_description: str
    source_channel: str
    severity: str
    status: str
    created_at: str

    assessment: Optional[AIAssessmentOut] = None
