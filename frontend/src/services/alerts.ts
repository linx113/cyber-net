import type { Alert } from "@/types/alert";

const API_URL = import.meta.env.VITE_API_URL || "";

export async function getAlerts(limit = 100): Promise<Alert[]> {
  const response = await fetch(`${API_URL}/api/alerts?limit=${limit}`);

  if (!response.ok) {
    throw new Error("Failed to load alerts");
  }

  return response.json();
}

export async function getAlertsCount(): Promise<number> {
  const response = await fetch(`${API_URL}/api/alerts/count`);

  if (!response.ok) throw new Error("Failed to load alerts count");

  const data = await response.json();
  return data.count;
}

export async function updateAlertStatus(
  alertId: number,
  status: "acknowledged" | "resolved",
): Promise<Alert> {
  const response = await fetch(
    `${API_URL}/api/alerts/${alertId}/status`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    },
  );
  if (!response.ok) {
    throw new Error("Failed to update alert status");
  }
  return response.json();
}
