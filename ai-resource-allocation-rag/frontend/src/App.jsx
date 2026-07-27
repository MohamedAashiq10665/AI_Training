import React from "react";
import { CssBaseline } from "@mui/material";
import { clearSession, getStoredRole, getStoredToken } from "./services/api";
import Dashboard from "./components/Dashboard";
import EmployeesPage from "./components/EmployeesPage";
import LoginPage from "./components/LoginPage";

export default function App() {
  const [token, setToken] = React.useState(getStoredToken());
  const [role, setRole] = React.useState(getStoredRole() || "viewer");
  const [page, setPage] = React.useState("dashboard");

  const handleLoginSuccess = () => {
    setToken(getStoredToken());
    setRole(getStoredRole() || "viewer");
    setPage("dashboard");
  };

  const handleLogout = () => {
    clearSession();
    setToken(null);
    setRole("viewer");
    setPage("dashboard");
  };

  const handleShowEmployees = () => setPage("employees");
  const handleShowDashboard = () => setPage("dashboard");

  return (
    <>
      <CssBaseline />
      {token ? (
        page === "employees" ? (
          <EmployeesPage role={role} onBackToDashboard={handleShowDashboard} onLogout={handleLogout} />
        ) : (
          <Dashboard role={role} onLogout={handleLogout} onShowEmployees={handleShowEmployees} />
        )
      ) : (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}
