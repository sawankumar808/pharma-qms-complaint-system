from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from app.ai.groq_client import call_llm_json, call_llm_text
from app.core.config import get_settings

settings = get_settings()

REQUIRED_FIELDS = [
    "product_name",
    "batch_number",
    "complainant_name",
    "complainant_email",
    "date_of_incident",
    "complaint_description",
]


class ComplaintState(TypedDict, total=False):
    raw_text: str
    existing_complaints: list[dict] 

    extracted: dict
    completeness_score: float
    missing_fields: list[str]

    duplicate: dict
    risk: dict
    root_cause: str
    capa: str
    summary: str


def extract_fields_node(state: ComplaintState) -> ComplaintState:
    system = (
        "You are a data-extraction assistant for a pharmaceutical Quality Management "
        "System (QMS). Extract structured fields from a raw customer complaint "
        "(which may be free text, a pasted email, or text extracted from a PDF). "
        "Respond ONLY with a JSON object with exactly these keys: "
        "product_name, batch_number, complainant_name, complainant_email, "
        "date_of_incident, complaint_description. "
        "If a field is genuinely not present in the text, return an empty string for it. "
        "date_of_incident should be normalized to YYYY-MM-DD when a date is present."
    )
    data = call_llm_json(system, state["raw_text"])
    extracted = {field: str(data.get(field, "") or "") for field in REQUIRED_FIELDS}
    return {"extracted": extracted}


def completeness_node(state: ComplaintState) -> ComplaintState:
    """Bonus feature: Complaint Completeness Checker."""
    extracted = state["extracted"]
    missing = [f for f in REQUIRED_FIELDS if not extracted.get(f, "").strip()]
    score = round(1 - (len(missing) / len(REQUIRED_FIELDS)), 2)
    return {"completeness_score": score, "missing_fields": missing}


def duplicate_check_node(state: ComplaintState) -> ComplaintState:
    """Bonus feature: Duplicate Complaint Detection.

    Compares the new complaint against existing complaints already logged in
    the system (product + batch + description) and asks the model to judge
    similarity. Falls back to "not a duplicate" if there is nothing to compare
    against yet.
    """
    existing = state.get("existing_complaints") or []
    if not existing:
        return {"duplicate": {"is_duplicate": False, "duplicate_of_id": None, "similarity": 0.0, "reason": "No prior complaints logged yet."}}

    candidates = "\n".join(
        f"- id={c['id']} | product={c.get('product_name','')} | batch={c.get('batch_number','')} "
        f"| description={c.get('complaint_description','')[:300]}"
        for c in existing[-25:] 
    )
    system = (
        "You are a duplicate-detection assistant for a pharmaceutical QMS complaint log. "
        "Given a NEW complaint and a list of EXISTING complaints, decide if the new one is "
        "very likely describing the same underlying quality event as one of the existing ones "
        "(same product/batch and materially the same issue). "
        "Respond ONLY with JSON: {\"is_duplicate\": bool, \"duplicate_of_id\": string or null, "
        "\"similarity\": number between 0 and 1, \"reason\": string}."
    )
    user = (
        f"NEW COMPLAINT:\nproduct={state['extracted'].get('product_name','')} | "
        f"batch={state['extracted'].get('batch_number','')} | "
        f"description={state['extracted'].get('complaint_description','')}\n\n"
        f"EXISTING COMPLAINTS:\n{candidates}"
    )
    result = call_llm_json(system, user)
    is_dup = bool(result.get("is_duplicate", False))
    similarity = float(result.get("similarity", 0.0) or 0.0)
    # Respect the configured threshold even if the model is over-eager.
    if similarity < settings.duplicate_similarity_threshold:
        is_dup = False
    return {
        "duplicate": {
            "is_duplicate": is_dup,
            "duplicate_of_id": result.get("duplicate_of_id") if is_dup else None,
            "similarity": similarity,
            "reason": result.get("reason", ""),
        }
    }


def risk_classification_node(state: ComplaintState) -> ComplaintState:
    """Core mandatory feature: AI Risk Classification (also listed as a bonus example)."""
    system = (
        "You are an AI Copilot assisting a Quality Assurance reviewer at a pharmaceutical "
        "API/FDF manufacturer. Classify the RISK LEVEL of a customer complaint as one of: "
        "Critical, Major, Minor - using standard QMS severity logic "
        "(Critical = potential patient safety / GMP / regulatory impact e.g. contamination, "
        "wrong product, adverse reaction; Major = product quality defect without immediate "
        "safety impact e.g. packaging defect, potency deviation; Minor = cosmetic/documentation "
        "issue with no quality impact). "
        "Respond ONLY with JSON: {\"risk_level\": \"Critical|Major|Minor\", \"rationale\": string}."
    )
    result = call_llm_json(system, state["extracted"].get("complaint_description", state["raw_text"]))
    risk_level = result.get("risk_level", "Minor")
    if risk_level not in ("Critical", "Major", "Minor"):
        risk_level = "Minor"
    return {"risk": {"risk_level": risk_level, "rationale": result.get("rationale", "")}}


def root_cause_node(state: ComplaintState) -> ComplaintState:
    """Bonus feature: Root Cause Recommendation."""
    system = (
        "You are a QMS investigation assistant. Given a pharmaceutical customer complaint, "
        "suggest the most probable root cause CATEGORY (e.g. manufacturing deviation, "
        "raw material quality, packaging/labeling defect, cold-chain/storage excursion, "
        "transportation damage, documentation error) and a one-paragraph justification. "
        "This is a preliminary AI suggestion for the investigator, not a final determination. "
        "Respond as plain text, 2-4 sentences."
    )
    text = call_llm_text(system, state["extracted"].get("complaint_description", state["raw_text"]))
    return {"root_cause": text}


def capa_node(state: ComplaintState) -> ComplaintState:
    """Bonus feature: CAPA (Corrective and Preventive Action) Recommendation."""
    system = (
        "You are a QMS CAPA assistant. Given a complaint description and its likely root "
        "cause, propose a short draft CAPA: one Corrective Action (fixes this instance) and "
        "one Preventive Action (stops recurrence). Keep it concrete and specific to a "
        "pharmaceutical manufacturing (API/FDF) context. Respond as plain text with two "
        "labeled lines: 'Corrective Action:' and 'Preventive Action:'."
    )
    user = (
        f"Complaint: {state['extracted'].get('complaint_description', state['raw_text'])}\n"
        f"Likely root cause: {state.get('root_cause', '')}"
    )
    text = call_llm_text(system, user)
    return {"capa": text}


def summary_node(state: ComplaintState) -> ComplaintState:
    system = (
        "Summarize the following pharmaceutical customer complaint investigation in 2-3 "
        "concise sentences for a QA manager skimming a dashboard. Mention product, the "
        "issue, and the assessed risk level."
    )
    user = (
        f"Description: {state['extracted'].get('complaint_description', state['raw_text'])}\n"
        f"Risk level: {state.get('risk', {}).get('risk_level')}\n"
        f"Root cause: {state.get('root_cause', '')}"
    )
    text = call_llm_text(system, user, model=settings.groq_context_model)
    return {"summary": text}


def build_graph():
    graph = StateGraph(ComplaintState)

    
    graph.add_node("extract_fields", extract_fields_node)
    graph.add_node("completeness_check", completeness_node)
    graph.add_node("duplicate_check", duplicate_check_node)
    graph.add_node("risk_classification", risk_classification_node)
    graph.add_node("root_cause_analysis", root_cause_node)
    graph.add_node("capa_recommendation", capa_node)
    graph.add_node("summary_generation", summary_node)

    graph.set_entry_point("extract_fields")

    graph.add_edge("extract_fields", "completeness_check")
    graph.add_edge("completeness_check", "duplicate_check")
    graph.add_edge("duplicate_check", "risk_classification")
    graph.add_edge("risk_classification", "root_cause_analysis")
    graph.add_edge("root_cause_analysis", "capa_recommendation")
    graph.add_edge("capa_recommendation", "summary_generation")
    graph.add_edge("summary_generation", END)

    return graph.compile()


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_complaint_pipeline(raw_text: str, existing_complaints: Optional[list[dict]] = None) -> ComplaintState:
    graph = get_compiled_graph()
    initial_state: ComplaintState = {
        "raw_text": raw_text,
        "existing_complaints": existing_complaints or [],
    }
    return graph.invoke(initial_state)
