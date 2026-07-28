import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class SeverityLevel(str, enum.Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


class ComplaintStatus(str, enum.Enum):
    NEW = "New"
    UNDER_REVIEW = "Under Review"
    CAPA_INITIATED = "CAPA Initiated"
    CLOSED = "Closed"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    product_name: Mapped[str] = mapped_column(String(255), default="")
    batch_number: Mapped[str] = mapped_column(String(100), default="")
    complainant_name: Mapped[str] = mapped_column(String(255), default="")
    complainant_email: Mapped[str] = mapped_column(String(255), default="")
    date_of_incident: Mapped[str] = mapped_column(String(50), default="")
    complaint_description: Mapped[str] = mapped_column(Text, default="")
    source_channel: Mapped[str] = mapped_column(String(50), default="Manual Entry") 

    severity: Mapped[str] = mapped_column(SAEnum(SeverityLevel), default=SeverityLevel.MINOR)
    status: Mapped[str] = mapped_column(SAEnum(ComplaintStatus), default=ComplaintStatus.NEW)

    raw_input_text: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment: Mapped["AIAssessment"] = relationship(
        back_populates="complaint", uselist=False, cascade="all, delete-orphan"
    )


class AIAssessment(Base):
    __tablename__ = "ai_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id"), unique=True)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    missing_fields: Mapped[list] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(SAEnum(SeverityLevel), default=SeverityLevel.MINOR)
    risk_rationale: Mapped[str] = mapped_column(Text, default="")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[str] = mapped_column(String(36), nullable=True)
    duplicate_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    root_cause_suggestion: Mapped[str] = mapped_column(Text, default="")
    capa_suggestion: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    raw_model_output: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    complaint: Mapped["Complaint"] = relationship(back_populates="assessment")
