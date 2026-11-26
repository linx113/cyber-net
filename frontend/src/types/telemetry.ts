export interface TelemetryRecord {
  id: number;
  device_id: string;
  device_type: string;
  location: string;
  value: number;
  unit: string;
  status: string;
  timestamp: string;
  received_at: string;
}
