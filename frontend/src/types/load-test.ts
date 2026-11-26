export interface LoadTestResult {
  created_at: string;
  concurrency: number;
  requests: number;
  successes: number;
  errors: number;
  average_response_ms: number;
  max_response_ms: number;
  requests_per_second: number;
  duration_seconds: number;
  instance_distribution: string;
}

export interface LoadTestReport {
  running: boolean;
  last_error: string | null;
  results: LoadTestResult[];
}
