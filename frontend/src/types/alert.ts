export interface Alert {
  id: number;
  device_id: string;
  device_type: string;
  value: number;
  severity: string;
  status: "open" | "acknowledged" | "resolved";
  message: string;
  created_at: string;
}
