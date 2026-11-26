import type { CommandCreate, DeviceCommand } from "@/types/command";

const API_URL = import.meta.env.VITE_API_URL || "";

export async function getCommands(): Promise<DeviceCommand[]> {
  const response = await fetch(`${API_URL}/api/commands`);

  if (!response.ok) {
    throw new Error("Failed to load commands");
  }

  return response.json();
}

export async function createCommand(
  command: CommandCreate,
): Promise<DeviceCommand> {
  const response = await fetch(`${API_URL}/api/commands`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(command),
  });

  if (!response.ok) {
    throw new Error("Failed to send command");
  }

  return response.json();
}
