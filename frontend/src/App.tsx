import { AppLayout } from "@/components/layout/app-layout";
import { DashboardPage } from "@/pages/dashboard/dashboard-page";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { DevicesPage } from "./pages/devices/devices-page";
import { TelemetryPage } from "./pages/telemetry/telemetry-page";
import { AlertsPage } from "./pages/alerts/alerts-page";
import { CommandsPage } from "./pages/commands/commands-page";

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-sm text-muted-foreground">
        This section is under development.
      </p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/devices" element={<DevicesPage />} />
          <Route path="/telemetry" element={<TelemetryPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/commands" element={<CommandsPage />} />
          <Route
            path="/settings"
            element={<PlaceholderPage title="Settings" />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
