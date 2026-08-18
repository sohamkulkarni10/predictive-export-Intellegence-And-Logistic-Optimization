import { Navigate } from "react-router-dom";
import LoginPage from "../components/LoginPage";
import { useApp } from "../context/AppContext";

export default function LoginRoute() {
  const { user, signIn, loginError, loginLoading } = useApp();
  if (user) return <Navigate to="/dashboard" replace />;
  return <LoginPage onLogin={signIn} error={loginError} loading={loginLoading} />;
}
