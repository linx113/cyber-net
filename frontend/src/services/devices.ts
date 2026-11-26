import type { DevicesResponse } from "@/types/device";

const API_URL = import.meta.env.VITE_API_URL || "";

export async function getDevices(): Promise<DevicesResponse> {
  const response = await fetch(`${API_URL}/api/devices`);

  if (!response.ok) {
    throw new Error("Failed to load devices");
  }

  return response.json();
}
