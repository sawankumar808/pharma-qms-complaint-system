import { useSelector } from "react-redux";
import RiskBadge from "./RiskBadge";

function Step({ index, label, done, children }) {
  return (
    <div className={`pipeline__step ${done ? "is-done" : ""}`}>
      <div className="pipeline__dot">{index}</div>
      <div className="pipeline__label">{label}</div>
      <div className="pipeline__body">
        {done ? children : <span className="pipeline__placeholder">Waiting for analysis…</span>}
      </div>
    </div>
  );
}

export default function AICopilotPanel() {
  const { assessment, extractStatus } = useSelector((s) => s.complaints);
  const done = extractStatus === "succeeded" && !!assessment;

  return (
    <div className="card">
      <div className="card__eyebrow">AI Copilot</div>
      <h2 className="card__title">Risk assessment pipeline</h2>
      <p className="card__desc">
        Each stage below is a distinct LangGraph node (Groq · gemma2-9b-it) — the same chain of
        custody a QA reviewer would walk through manually.
      </p>

      <div className="pipeline">
        <Step index="1" label="Completeness Checker" done={done}>
          {done && (
            <>
              Completeness score: <strong>{Math.round(assessment.completeness_score * 100)}%</strong>
              {assessment.missing_fields.length > 0 ? (
                <div style={{ marginTop: 6 }}>
                  Missing: {assessment.missing_fields.join(", ")}
                </div>
              ) : (
                <div style={{ marginTop: 6 }}>All mandatory fields present.</div>
              )}
            </>
          )}
        </Step>

        <Step index="2" label="Duplicate Complaint Detection" done={done}>
          {done &&
            (assessment.is_duplicate ? (
              <>
                <span className="badge badge--duplicate">Likely duplicate</span>
                <div style={{ marginTop: 6 }}>
                  Similarity {Math.round(assessment.duplicate_similarity * 100)}% with complaint{" "}
                  <span className="mono-id">{assessment.duplicate_of_id}</span>
                </div>
              </>
            ) : (
              <>No matching complaint found in the existing log.</>
            ))}
        </Step>

        <Step index="3" label="AI Risk Classification" done={done}>
          {done && (
            <>
              <RiskBadge level={assessment.risk_level} /> {assessment.risk_rationale}
            </>
          )}
        </Step>

        <Step index="4" label="Root Cause Recommendation" done={done}>
          {done && assessment.root_cause_suggestion}
        </Step>

        <Step index="5" label="CAPA Recommendation" done={done}>
          {done && (
            <div style={{ whiteSpace: "pre-line" }}>{assessment.capa_suggestion}</div>
          )}
        </Step>

        <Step index="6" label="Complaint Summary" done={done}>
          {done && assessment.summary}
        </Step>
      </div>
    </div>
  );
}
