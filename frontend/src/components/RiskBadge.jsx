const CLASS_BY_LEVEL = {
  Critical: "badge--critical",
  Major: "badge--major",
  Minor: "badge--minor",
};

export default function RiskBadge({ level }) {
  const cls = CLASS_BY_LEVEL[level] || "badge--minor";
  return <span className={`badge ${cls}`}>{level || "Minor"}</span>;
}
