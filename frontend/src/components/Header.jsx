export default function Header({ activeTab, onTabChange }) {
  return (
    <header className="header">
      <div className="header__brand">
        <div className="header__mark">AI</div>
        <div>
          <div className="header__title">AIVOA · Complaint Management</div>
          <div className="header__subtitle">AI-Powered Customer Complaint Management System</div>
        </div>
      </div>

      <nav className="header__nav">
        <button
          className={`header__nav-btn ${activeTab === "intake" ? "is-active" : ""}`}
          onClick={() => onTabChange("intake")}
        >
          Log Complaint
        </button>
        <button
          className={`header__nav-btn ${activeTab === "dashboard" ? "is-active" : ""}`}
          onClick={() => onTabChange("dashboard")}
        >
          Complaint Log
        </button>
      </nav>
    </header>
  );
}
