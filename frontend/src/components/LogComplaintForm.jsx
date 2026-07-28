import { useDispatch, useSelector } from "react-redux";
import { updateFormField, persistComplaint, resetIntake } from "../store/complaintsSlice";

const FIELDS = [
  { key: "product_name", label: "Product name", mono: false },
  { key: "batch_number", label: "Batch number", mono: true },
  { key: "complainant_name", label: "Complainant name", mono: false },
  { key: "complainant_email", label: "Complainant email", mono: true },
  { key: "date_of_incident", label: "Date of incident", mono: true },
];

export default function LogComplaintForm() {
  const dispatch = useDispatch();
  const { form, assessment, extractStatus, saveStatus, saveError } = useSelector((s) => s.complaints);

  const hasResult = extractStatus === "succeeded";

  const handleChange = (field, value) => dispatch(updateFormField({ field, value }));

  return (
    <div className="card">
      <div className="card__eyebrow">Step 2</div>
      <h2 className="card__title">Log Customer Complaint</h2>
      <p className="card__desc">
        Auto-populated from the AI extraction above — review and correct anything before saving.
      </p>

      {assessment && (
        <div className={`completeness-note ${assessment.missing_fields.length ? "is-missing" : ""}`}>
          {assessment.missing_fields.length
            ? `⚠ ${assessment.missing_fields.length} field(s) need your attention before this complaint is complete.`
            : "✓ All mandatory fields were found by the AI Copilot."}
        </div>
      )}

      <div className="form-grid">
        {FIELDS.map((f) => (
          <div className="field" key={f.key}>
            <label htmlFor={f.key}>{f.label}</label>
            <input
              id={f.key}
              className={f.mono ? "mono" : ""}
              value={form[f.key]}
              onChange={(e) => handleChange(f.key, e.target.value)}
              disabled={!hasResult}
            />
          </div>
        ))}

        <div className="field form-grid--full">
          <label htmlFor="complaint_description">Complaint description</label>
          <textarea
            id="complaint_description"
            value={form.complaint_description}
            onChange={(e) => handleChange("complaint_description", e.target.value)}
            disabled={!hasResult}
          />
        </div>
      </div>

      <div className="form-actions">
        <button
          className="btn btn--primary"
          disabled={!hasResult || saveStatus === "loading"}
          onClick={() => dispatch(persistComplaint())}
        >
          {saveStatus === "loading" ? "Saving…" : "Save to Complaint Log"}
        </button>
        <button className="btn btn--ghost" onClick={() => dispatch(resetIntake())}>
          Clear
        </button>
      </div>

      {saveStatus === "succeeded" && (
        <div className="completeness-note" style={{ marginTop: 12 }}>
          ✓ Saved. View it in the Complaint Log tab.
        </div>
      )}
      {saveError && <div className="error-banner">{saveError}</div>}
    </div>
  );
}
