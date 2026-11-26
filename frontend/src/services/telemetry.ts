import type { TelemetryRecord } from "@/types/telemetry";

const API_URL = import.meta.env.VITE_API_URL || "";

export async function getTelemetry(limit = 100): Promise<TelemetryRecord[]> {
  const response = await fetch(`${API_URL}/api/telemetry?limit=${limit}`);

  if (!response.ok) {
    throw new Error("Failed to load telemetry");
  }

  return response.json();
}
