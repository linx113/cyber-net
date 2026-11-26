import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getAlerts, getAlertsCount } from "@/services/alerts";
import { getDevices } from "@/services/devices";
import { getLoadTests, startLoadTest } from "@/services/load-tests";
import { getTelemetry } from "@/services/telemetry";
import type { Alert } from "@/types/alert";
import type { Device } from "@/types/device";
import type { TelemetryRecord } from "@/types/telemetry";
import type { LoadTestResult } from "@/types/load-test";
import { Activity, AlertTriangle, Cpu, Radio } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function getActivity(records: TelemetryRecord[]) {
  const buckets = new Map<string, number>();

  for (const record of records) {
    const time = new Date(record.timestamp);
    if (Number.isNaN(time.getTime())) continue;
    const label = time.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    buckets.set(label, (buckets.get(label) ?? 0) + 1);
  }

  return Array.from(buckets, ([time, events]) => ({ time, events })).reverse();
}

export function DashboardPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryRecord[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertCount, setAlertCount] = useState(0);
  const [loadResults, setLoadResults] = useState<LoadTestResult[]>([]);
  const [loadTestRunning, setLoadTestRunning] = useState(false);
  const [loadTestError, setLoadTestError] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const loadTestsPromise = getLoadTests().catch(() => null);

    try {
      const [deviceData, telemetryData, recentAlerts, totalAlerts] = await Promise.all([
        getDevices(),
        getTelemetry(500),
        getAlerts(5),
        getAlertsCount(),
      ]);
      setDevices(deviceData.devices);
      setTelemetry(telemetryData);
      setAlerts(recentAlerts);
      setAlertCount(totalAlerts);

      const loadTests = await loadTestsPromise;
      if (loadTests) {
        setLoadResults(loadTests.results);
        setLoadTestRunning(loadTests.running);
        setLoadTestError(loadTests.last_error ?? "");
      } else {
        setLoadTestError("Load-test service is unavailable.");
      }
      setError("");
    } catch {
      setError("Some dashboard data could not be refreshed.");
    }
  }, []);

  async function runLoadTest() {
    try {
      await startLoadTest();
      setLoadTestRunning(true);
      setLoadTestError("");
    } catch (loadError) {
      setLoadTestError(
        loadError instanceof Error ? loadError.message : "Could not start load test",
      );
    }
  }

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void refresh(), 0);
    const interval = window.setInterval(() => void refresh(), 5000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [refresh]);

  const activeCount = devices.filter((device) => device.status === "active").length;
  const inactiveCount = devices.filter((device) => device.status === "inactive").length;
  const maintenanceCount = devices.filter((device) => device.status === "maintenance").length;
  const activity = useMemo(() => getActivity(telemetry), [telemetry]);
  const sectorSummary = useMemo(
    () => ["Sector-A", "Sector-B", "Sector-C", "Sector-D"].map((location) => {
      const sectorDevices = devices.filter((device) => device.location === location);
      return {
        location,
        total: sectorDevices.length,
        active: sectorDevices.filter((device) => device.status === "active").length,
      };
    }),
    [devices],
  );
  const metrics = [
    {
      title: "Total devices",
      value: devices.length.toLocaleString(),
      detail: `${inactiveCount.toLocaleString()} inactive`,
      icon: Cpu,
      color: "text-primary",
    },
    {
      title: "Online devices",
      value: activeCount.toLocaleString(),
      detail: devices.length
        ? `${Math.round((activeCount / devices.length) * 100)}% available`
        : "Waiting for devices",
      icon: Radio,
      color: "text-emerald-400",
    },
    {
      title: "Alerts recorded",
      value: alertCount.toLocaleString(),
      detail: `${alerts.filter((alert) => alert.severity === "critical").length} critical in latest 5`,
      icon: AlertTriangle,
      color: "text-amber-400",
    },
    {
      title: "Recent telemetry",
      value: telemetry.length.toLocaleString(),
      detail: "Latest 500 records",
      icon: Activity,
      color: "text-sky-400",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm text-muted-foreground">
            City infrastructure overview
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            Dashboard
          </h1>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span
            className={`size-2 rounded-full ${error ? "bg-red-400" : "bg-emerald-400"}`}
          />
          {error ? "Data refresh failed" : "Live data · Refreshes every 5 seconds"}
        </div>
      </div>

      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.title} className="border-border bg-card">
              <CardContent className="flex items-start justify-between p-5">
                <div>
                  <p className="text-sm text-muted-foreground">{metric.title}</p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight">
                    {metric.value}
                  </p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {metric.detail}
                  </p>
                </div>
                <div className={`rounded-lg bg-muted p-2.5 ${metric.color}`}>
                  <Icon size={20} />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,1fr)]">
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-base">Recent telemetry activity</CardTitle>
            <CardDescription>
              Events per timestamp in the latest 500 records
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={activity}
                  margin={{ top: 10, right: 10, left: -15, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="telemetryGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickMargin={10}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickMargin={8}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--popover)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                      color: "var(--popover-foreground)",
                      fontSize: "12px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="events"
                    name="Telemetry events"
                    stroke="var(--primary)"
                    strokeWidth={2}
                    fill="url(#telemetryGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-base">Device status</CardTitle>
            <CardDescription>Latest status reported by the simulator</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Active</span>
              <span className="text-emerald-400">{activeCount}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Inactive</span>
              <span className="text-red-400">{inactiveCount}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Maintenance</span>
              <span>{maintenanceCount}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Device types</span>
              <span>{new Set(devices.map((device) => device.type)).size}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Latest telemetry</span>
              <span>{telemetry.length ? new Date(telemetry[0].timestamp).toLocaleTimeString() : "No data"}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-base">City schematic</CardTitle>
          <CardDescription>
            Device coverage across the four connected city sectors
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            role="group"
            aria-label="Schematic map of device counts by city sector"
            className="grid grid-cols-2 gap-2 rounded-lg bg-border p-2"
          >
            {sectorSummary.map((sector) => (
              <div
                key={sector.location}
                className="min-h-24 rounded-md bg-card p-4"
              >
                <p className="text-sm font-medium">{sector.location}</p>
                <p className="mt-2 text-2xl font-semibold">
                  {sector.total.toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground">
                  {sector.active.toLocaleString()} active
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div>
            <CardTitle className="text-base">Load test results</CardTitle>
            <CardDescription>
              Throughput, response times, and request distribution across service instances
            </CardDescription>
          </div>
          <button
            type="button"
            onClick={() => void runLoadTest()}
            disabled={loadTestRunning}
            className="shrink-0 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {loadTestRunning ? "Test running…" : "Run 100 / 500 / 1000"}
          </button>
        </CardHeader>
        <CardContent className="space-y-4">
          {loadTestError && (
            <p role="alert" className="text-sm text-red-400">{loadTestError}</p>
          )}
          <div className="h-[220px] w-full">
            {loadResults.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={loadResults.slice(-10)}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="concurrency" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <YAxis yAxisId="left" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="requests_per_second" name="Requests/s" fill="var(--primary)" />
                  <Bar yAxisId="right" dataKey="average_response_ms" name="Average ms" fill="#38bdf8" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No load-test results yet. Start a test to populate this chart.
              </div>
            )}
          </div>
          {loadResults.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Clients</th>
                    <th className="px-3 py-2 font-medium">Success</th>
                    <th className="px-3 py-2 font-medium">Errors</th>
                    <th className="px-3 py-2 font-medium">Avg ms</th>
                    <th className="px-3 py-2 font-medium">Requests/s</th>
                    <th className="px-3 py-2 font-medium">Instances</th>
                  </tr>
                </thead>
                <tbody>
                  {loadResults.slice(-5).reverse().map((result, index) => (
                    <tr key={`${result.created_at}-${result.concurrency}-${index}`} className="border-t border-border">
                      <td className="px-3 py-2">{result.concurrency}</td>
                      <td className="px-3 py-2">{result.successes}/{result.requests}</td>
                      <td className="px-3 py-2">{result.errors}</td>
                      <td className="px-3 py-2">{result.average_response_ms}</td>
                      <td className="px-3 py-2">{result.requests_per_second}</td>
                      <td className="px-3 py-2 font-mono text-xs">{result.instance_distribution}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-base">Recent alerts</CardTitle>
          <CardDescription>Latest incidents reported by analytics</CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="py-4 text-sm text-muted-foreground">No alerts recorded.</p>
          ) : (
            <div className="space-y-1">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex flex-col gap-3 rounded-lg px-3 py-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="mt-1 truncate text-xs text-muted-foreground">
                      {alert.device_type.replace("_", " ")} · {alert.device_id} · {alert.value}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={
                        alert.severity === "critical"
                          ? "rounded-md bg-destructive/10 px-2 py-1 text-xs text-destructive"
                          : "rounded-md bg-amber-400/10 px-2 py-1 text-xs text-amber-400"
                      }
                    >
                      {alert.severity}
                    </span>
                    <span className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
