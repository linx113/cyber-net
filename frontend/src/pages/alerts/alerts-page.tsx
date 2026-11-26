import Filters from "@/components/filters";
import { Skeleton } from "@/components/ui/skeleton";
import { getAlerts, updateAlertStatus } from "@/services/alerts";
import type { Alert } from "@/types/alert";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

const severityLevels = [
  { value: "all", label: "All" },
  { value: "critical", label: "Critical" },
  { value: "warning", label: "Warning" },
  { value: "info", label: "Info" },
];

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("all");

  async function loadAlerts(showSkeleton = false) {
    try {
      const [data] = await Promise.all([
        getAlerts(100),
        showSkeleton
          ? new Promise((resolve) => setTimeout(resolve, 600))
          : Promise.resolve(),
      ]);

      setAlerts(data);
      setError("");
    } catch {
      setError("Failed to load alerts");
    } finally {
      if (showSkeleton) {
        setLoading(false);
      }
    }
  }

  async function changeStatus(alert: Alert, status: "acknowledged" | "resolved") {
    try {
      const updated = await updateAlertStatus(alert.id, status);
      setAlerts((current) =>
        current.map((item) => item.id === updated.id ? updated : item),
      );
      setError("");
    } catch {
      setError("Failed to update alert status");
    }
  }

  useEffect(() => {
    const initialLoad = window.setTimeout(() => loadAlerts(true), 0);
    const interval = setInterval(() => loadAlerts(), 5000);

    return () => {
      window.clearTimeout(initialLoad);
      clearInterval(interval);
    };
  }, []);

  const filteredAlerts =
    selectedSeverity === "all"
      ? alerts
      : alerts.filter((alert) => alert.severity === selectedSeverity);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">Alerts</h1>
          <p className="text-sm text-muted-foreground">
            Detected events and device warnings.
          </p>
          <Filters
            selectedType={selectedSeverity}
            setSelectedType={setSelectedSeverity}
            options={severityLevels}
          />
        </div>

        <button
          type="button"
          onClick={() => loadAlerts()}
          className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-muted"
        >
          <RefreshCw className="size-4" />
          Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-hidden rounded-lg border">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-4 text-muted-foreground" />
            <span className="text-sm font-medium">Alert records</span>
          </div>

          <span className="text-sm text-muted-foreground">
            {filteredAlerts.length} alerts
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-muted-foreground">
              <tr className="border-b text-left">
                <th className="px-4 py-3 font-medium">Severity</th>
                <th className="px-4 py-3 font-medium">Device</th>
                <th className="px-4 py-3 font-medium">Message</th>
                <th className="px-4 py-3 font-medium">Value</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Timestamp</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, index) => (
                  <tr key={index} className="border-b">
                    {Array.from({ length: 5 }).map((_, cell) => (
                      <td key={cell} className="px-4 py-4">
                        <Skeleton className="h-4 w-24" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : filteredAlerts.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-10 text-center text-muted-foreground"
                  >
                    No alerts found.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className="border-b last:border-0 hover:bg-muted/20"
                  >
                    <td className="px-4 py-3">
                      <span
                        className={
                          alert.severity === "critical"
                            ? "text-red-400"
                            : alert.severity === "warning"
                              ? "text-amber-400"
                              : "text-emerald-400"
                        }
                      >
                        {alert.severity}
                      </span>
                    </td>

                    <td className="px-4 py-3 font-medium">
                      {alert.device_type.replace("_", " ")}
                    </td>

                    <td className="px-4 py-3 text-muted-foreground">
                      {alert.message}
                    </td>

                    <td className="px-4 py-3 tabular-nums">{alert.value}</td>
                    <td className="px-4 py-3 capitalize">{alert.status}</td>

                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                      {new Date(alert.created_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      {alert.status === "open" && (
                        <button
                          type="button"
                          onClick={() => void changeStatus(alert, "acknowledged")}
                          className="text-primary hover:underline"
                        >
                          Acknowledge
                        </button>
                      )}
                      {alert.status === "acknowledged" && (
                        <button
                          type="button"
                          onClick={() => void changeStatus(alert, "resolved")}
                          className="text-primary hover:underline"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
