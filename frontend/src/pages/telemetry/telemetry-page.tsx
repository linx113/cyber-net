import Filters from "@/components/filters";
import { Skeleton } from "@/components/ui/skeleton";
import { getTelemetry } from "@/services/telemetry";
import type { TelemetryRecord } from "@/types/telemetry";
import { Activity, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

const deviceTypes = [
  { value: "all", label: "All" },
  { value: "temperature", label: "Temperature" },
  { value: "humidity", label: "Humidity" },
  { value: "street_light", label: "Street light" },
  { value: "air_quality", label: "Air quality" },
  { value: "traffic_sensor", label: "Traffic sensor" },
  { value: "traffic_light", label: "Traffic light" },
];

export function TelemetryPage() {
  const [records, setRecords] = useState<TelemetryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedType, setSelectedType] = useState("all");

  async function loadTelemetry(showSkeleton = false) {
    try {
      const [data] = await Promise.all([
        getTelemetry(100),
        showSkeleton
          ? new Promise((resolve) => setTimeout(resolve, 600))
          : Promise.resolve(),
      ]);

      setError("");
      setRecords(data);
    } catch {
      setError("Failed to load telemetry");
    } finally {
      if (showSkeleton) {
        setLoading(false);
      }
    }
  }
  useEffect(() => {
    const initialLoad = window.setTimeout(() => loadTelemetry(true), 0);
    const interval = setInterval(() => loadTelemetry(), 5000);

    return () => {
      window.clearTimeout(initialLoad);
      clearInterval(interval);
    };
  }, []);

  const filteredRecords =
    selectedType === "all"
      ? records
      : records.filter((record) => record.device_type === selectedType);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">Telemetry</h1>
          <p className="text-sm text-muted-foreground">
            Real-time data received from devices.
          </p>

          <Filters
            options={deviceTypes}
            selectedType={selectedType}
            setSelectedType={setSelectedType}
          />
        </div>

        <button
          type="button"
          onClick={() => loadTelemetry()}
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
            <Activity className="size-4 text-muted-foreground" />
            <span className="text-sm font-medium">Telemetry records</span>
          </div>

          <span className="text-sm text-muted-foreground">
            {filteredRecords.length} records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-muted-foreground">
              <tr className="border-b text-left">
                <th className="px-4 py-3 font-medium">Device</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Value</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Timestamp</th>
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
              ) : filteredRecords.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-10 text-center text-muted-foreground"
                  >
                    No telemetry records found.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((record) => (
                  <tr
                    key={record.id}
                    className="border-b last:border-0 hover:bg-muted/20"
                  >
                    <td className="px-4 py-3 font-medium">
                      {record.device_type.replace("_", " ")}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {record.location}
                    </td>
                    <td className="px-4 py-3 tabular-nums">
                      {record.value} {record.unit}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={
                          record.status === "active"
                            ? "text-emerald-400"
                            : "text-red-400"
                        }
                      >
                        {record.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                      {new Date(record.timestamp).toLocaleString()}
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
