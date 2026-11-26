import Filters from "@/components/filters";
import { Skeleton } from "@/components/ui/skeleton";
import { getDevices } from "@/services/devices";
import type { Device } from "@/types/device";
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

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedType, setSelectedType] = useState("all");

  async function loadDevices(showSkeleton = false) {
    try {
      const [data] = await Promise.all([
        getDevices(),
        showSkeleton
          ? new Promise((resolve) => setTimeout(resolve, 600))
          : Promise.resolve(),
      ]);

      setError("");
      setDevices(data.devices);
    } catch {
      setError("Failed to load devices");
    } finally {
      if (showSkeleton) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    const initialLoad = window.setTimeout(() => loadDevices(true), 0);
    const interval = setInterval(() => loadDevices(), 5000);
    return () => {
      window.clearTimeout(initialLoad);
      clearInterval(interval);
    };
  }, []);

  const activeCount = devices.filter(
    (device) => device.status === "active",
  ).length;

  const filteredDevices =
    selectedType === "all"
      ? devices
      : devices.filter((device) => device.type === selectedType);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">Devices</h1>
          <p className="text-sm text-muted-foreground">
            Virtual devices connected
          </p>

          <Filters
            options={deviceTypes}
            selectedType={selectedType}
            setSelectedType={setSelectedType}
          />
        </div>

        <button
          onClick={() => loadDevices()}
          disabled={loading}
          className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-accent disabled:opacity-50"
        >
          <RefreshCw className="size-4" />
          Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total devices</p>
          <p className="mt-2 text-2xl font-semibold">
            {loading ? <Skeleton className="h-6 w-16" /> : devices.length}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Active devices</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-400">
            {loading ? <Skeleton className="h-6 w-16" /> : activeCount}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="divide-y divide-border">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="flex items-center justify-between gap-4 p-4"
            >
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
                <Skeleton className="h-3 w-64 max-w-full" />
              </div>
              <Skeleton className="h-5 w-16 rounded-md" />
            </div>
          ))}
        </div>
      ) : filteredDevices.length === 0 ? (
        <p className="p-4 text-sm text-muted-foreground">No devices found</p>
      ) : (
        <div className="divide-y divide-border">
          {filteredDevices.map((device) => (
            <div
              key={device.id}
              className="flex flex-wrap items-center justify-between gap-3 p-4"
            >
              <div className="min-w-0">
                <p className="font-medium">{device.type}</p>
                <p className="truncate text-sm text-muted-foreground">
                  {device.location}
                </p>
                <p className="text-sm text-muted-foreground">
                  Latest reading:{" "}
                  {device.value === null || device.value === undefined
                    ? "Waiting for telemetry"
                    : `${device.value} ${device.unit ?? ""}`}
                </p>
                {device.last_updated && (
                  <p className="text-xs text-muted-foreground">
                    Updated {new Date(device.last_updated).toLocaleTimeString()}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">ID: {device.id}</p>
              </div>

              <div className="flex items-center gap-2">
                <Activity className="size-4 text-muted-foreground" />
                <span
                  className={
                    device.status === "active"
                      ? "text-sm text-emerald-400"
                      : "text-sm text-red-400"
                  }
                >
                  {device.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
