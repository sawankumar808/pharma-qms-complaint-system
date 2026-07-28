import { useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { runExtraction } from "../store/complaintsSlice";
import { SAMPLE_COMPLAINTS } from "../data/sampleComplaints";

export default function ComplaintIntake() {
  const dispatch = useDispatch();
  const { extractStatus, extractError } = useSelector((s) => s.complaints);
  const [mode, setMode] = useState("paste"); // paste | file
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const isLoading = extractStatus === "loading";

  const handleAnalyze = () => {
    if (mode === "file" && file) {
      dispatch(runExtraction({ file, sourceChannel: file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "Email" }));
    } else if (text.trim()) {
      dispatch(runExtraction({ rawText: text, sourceChannel: "Manual Entry" }));
    }
  };

  const handleSample = (sample) => {
    setMode("paste");
    setText(sample.text);
  };

  return (
    <div className="card">
      <div className="card__eyebrow">Step 1</div>
      <h2 className="card__title">Intake a complaint</h2>
      <p className="card__desc">
        Paste a customer email/complaint, or upload a PDF/text file. The AI Copilot will extract
        structured fields and run the full analysis pipeline below.
      </p>

      <div className="intake__tabs">
        <button className={`intake__tab ${mode === "paste" ? "is-active" : ""}`} onClick={() => setMode("paste")}>
          Paste text
        </button>
        <button className={`intake__tab ${mode === "file" ? "is-active" : ""}`} onClick={() => setMode("file")}>
          Upload file
        </button>
      </div>

      {mode === "paste" ? (
        <textarea
          className="intake__textarea"
          placeholder="Paste the customer complaint email, portal submission, or transcript here…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      ) : (
        <div className="intake__file" onClick={() => fileInputRef.current?.click()}>
          {file ? (
            <span>📄 {file.name}</span>
          ) : (
            <span>Click to choose a .pdf, .txt, or .eml file</span>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.eml"
            hidden
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
      )}

      <div className="intake__samples">
        {SAMPLE_COMPLAINTS.map((s) => (
          <button key={s.label} className="chip" onClick={() => handleSample(s)}>
            {s.label}
          </button>
        ))}
      </div>

      <button className="btn btn--primary btn--full" onClick={handleAnalyze} disabled={isLoading}>
        {isLoading ? "Running AI Copilot pipeline…" : "Run AI Analysis"}
      </button>

      {extractError && <div className="error-banner">{extractError}</div>}
    </div>
  );
}
