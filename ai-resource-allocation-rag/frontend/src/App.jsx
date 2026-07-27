import React from "react";
import { CssBaseline } from "@mui/material";
import { clearSession, getStoredToken } from "./services/api";
import Dashboard from "./components/Dashboard";
import LoginPage from "./components/LoginPage";

export default function App() {
  const [token, setToken] = React.useState(getStoredToken());

  const handleLoginSuccess = () => {
    setToken(getStoredToken());
  };

  const handleLogout = () => {
    clearSession();
    setToken(null);
  };

  return (
    <>
      <CssBaseline />
      {token ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}
