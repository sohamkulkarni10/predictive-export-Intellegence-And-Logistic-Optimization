import { Navigate, Route, Routes } from "react-router-dom";
import { AppProvider, useApp } from "./context/AppContext";
import DashboardShell from "./components/layout/DashboardShell";
import LandingPage from "./pages/LandingPage";
import LoginRoute from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import DemandPage from "./pages/DemandPage";
import PricePage from "./pages/PricePage";
import LogisticsPage from "./pages/LogisticsPage";
import ContainersPage from "./pages/ContainersPage";
import AssistantPage from "./pages/AssistantPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import AgentsPage from "./pages/AgentsPage";

function ProtectedRoute() {
  const { user } = useApp();
  return user ? <DashboardShell /> : <Navigate to="/login" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginRoute />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/demand" element={<DemandPage />} />
        <Route path="/price" element={<PricePage />} />
        <Route path="/logistics" element={<LogisticsPage />} />
        <Route path="/containers" element={<ContainersPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/global-trade" element={<AnalyticsPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/analytics" element={<Navigate to="/global-trade" replace />} />
        <Route path="/knowledge" element={<Navigate to="/assistant" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppRoutes />
    </AppProvider>
  );
}
