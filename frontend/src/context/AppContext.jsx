import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearAuthStorage, getStoredSession, login, logout } from "../api";
import { useAnalysis } from "../hooks/useAnalysis";
import { USE_MOCK } from "../mock";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const navigate = useNavigate();
  const stored = getStoredSession();
  const [user, setUser] = useState(stored?.user || null);
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  const forceLogin = useCallback(
    (message) => {
      clearAuthStorage();
      setUser(null);
      setLoginError(message || "Your session expired. Please sign in again.");
      navigate("/login", { replace: true });
    },
    [navigate],
  );

  const analysis = useAnalysis({ onAuthExpired: forceLogin });

  const signIn = useCallback(
    async (username, password, remember = false) => {
      setLoginLoading(true);
      setLoginError("");
      try {
        if (USE_MOCK) {
          const storage = remember ? localStorage : sessionStorage;
          storage.setItem("export_ai_token", "mock");
          storage.setItem("export_ai_user", username);
          setUser(username);
        } else {
          const data = await login(username, password);
          const storage = remember ? localStorage : sessionStorage;
          clearAuthStorage();
          storage.setItem("export_ai_token", data.token);
          storage.setItem("export_ai_user", data.username);
          setUser(data.username);
        }
        navigate("/dashboard", { replace: true });
        return true;
      } catch (error) {
        clearAuthStorage();
        setUser(null);
        setLoginError(error.message || "Login failed");
        return false;
      } finally {
        setLoginLoading(false);
      }
    },
    [navigate],
  );

  const signOut = useCallback(async () => {
    await logout();
    sessionStorage.removeItem("export_ai_token");
    sessionStorage.removeItem("export_ai_user");
    setUser(null);
    setLoginError("");
    navigate("/", { replace: true });
  }, [navigate]);

  const value = useMemo(
    () => ({
      user,
      loginError,
      loginLoading,
      signIn,
      signOut,
      analysis,
    }),
    [user, loginError, loginLoading, signIn, signOut, analysis],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used inside AppProvider");
  return context;
}
