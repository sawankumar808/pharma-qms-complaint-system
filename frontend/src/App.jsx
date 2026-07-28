import { useState } from "react";
import Header from "./components/Header";
import ComplaintIntake from "./components/ComplaintIntake";
import LogComplaintForm from "./components/LogComplaintForm";
import AICopilotPanel from "./components/AICopilotPanel";
import ComplaintsDashboard from "./components/ComplaintsDashboard";
import "./styles/app.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("intake");

  return (
    <div className="shell">
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="page">
        {activeTab === "intake" ? (
          <div className="workspace">
            <div>
              <ComplaintIntake />
              <LogComplaintForm />
            </div>
            <AICopilotPanel />
          </div>
        ) : (
          <ComplaintsDashboard />
        )}
      </main>
    </div>
  );
}
