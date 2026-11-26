export interface DeviceCommand {
  id: string;
  device_id: string;
  command: string;
  parameters: string | null;
  status: string;
  result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface CommandCreate {
  device_id: string;
  command: string;
  parameters?: string | null;
}
