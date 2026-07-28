import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { loadComplaints } from "../store/complaintsSlice";
import RiskBadge from "./RiskBadge";

export default function ComplaintsDashboard() {
  const dispatch = useDispatch();
  const { list, listStatus } = useSelector((s) => s.complaints);

  useEffect(() => {
    dispatch(loadComplaints());
  }, [dispatch]);

  if (listStatus === "loading" && list.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">Loading complaint log…</div>
      </div>
    );
  }

  if (list.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">
          <div className="empty-state__title">No complaints logged yet</div>
          <div>Analyze and save a complaint from the "Log Complaint" tab to see it here.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card__eyebrow">Complaint Log</div>
      <h2 className="card__title">{list.length} complaint{list.length === 1 ? "" : "s"} on record</h2>

      <div className="table-wrap">
        <table className="complaints-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Product / Batch</th>
              <th>Complainant</th>
              <th>Risk</th>
              <th>Status</th>
              <th>AI Summary</th>
            </tr>
          </thead>
          <tbody>
            {list.map((c) => (
              <tr key={c.id}>
                <td className="mono-id">{c.id.slice(0, 8)}</td>
                <td>
                  <div>{c.product_name || "—"}</div>
                  <div className="mono-id">{c.batch_number || "—"}</div>
                </td>
                <td>
                  <div>{c.complainant_name || "—"}</div>
                  <div className="mono-id">{c.complainant_email || "—"}</div>
                </td>
                <td>
                  <RiskBadge level={c.severity} />
                  {c.assessment?.is_duplicate && (
                    <div style={{ marginTop: 6 }}>
                      <span className="badge badge--duplicate">Duplicate</span>
                    </div>
                  )}
                </td>
                <td>{c.status}</td>
                <td style={{ maxWidth: 320 }}>{c.assessment?.summary || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
