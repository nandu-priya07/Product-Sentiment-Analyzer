import { NavLink } from "react-router-dom";
import { ChartNoAxesColumn, History, House, LayoutDashboard } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <NavLink to="/" className="navbar-logo">
          <div className="logo-icon">
            <ChartNoAxesColumn size={20} color="#fff" />
          </div>
          <span>SentiScope</span>
        </NavLink>

        <div className="navbar-links">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <House size={16} />
            <span>Home</span>
          </NavLink>
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <LayoutDashboard size={16} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <History size={16} />
            <span>History</span>
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
