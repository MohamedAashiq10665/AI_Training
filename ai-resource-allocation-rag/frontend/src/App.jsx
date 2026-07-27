import React from "react";
import { CssBaseline } from "@mui/material";
import { clearSession, getStoredToken } from "./services/api";
import Dashboard from "./components/Dashboard";
import EmployeesPage from "./components/EmployeesPage";
import LoginPage from "./components/LoginPage";

export default function App() {
  const [token, setToken] = React.useState(getStoredToken());
  const [page, setPage] = React.useState("dashboard");

  const handleLoginSuccess = () => {
    setToken(getStoredToken());
    setPage("dashboard");
  };

  const handleLogout = () => {
    clearSession();
    setToken(null);
    setPage("dashboard");
  };

  const handleShowEmployees = () => setPage("employees");
  const handleShowDashboard = () => setPage("dashboard");

  return (
    <>
      <CssBaseline />
      {token ? (
        page === "employees" ? (
          <EmployeesPage onBackToDashboard={handleShowDashboard} onLogout={handleLogout} />
        ) : (
          <Dashboard onLogout={handleLogout} onShowEmployees={handleShowEmployees} />
        )
      ) : (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}
