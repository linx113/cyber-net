export interface Device {
  id: string;
  type: string;
  location: string;
  status: string;
  value?: number | null;
  unit?: string | null;
  last_updated?: string | null;
  brightness: number | null;
  is_on: boolean | null;
}

export interface DevicesResponse {
  total: number;
  devices: Device[];
}
