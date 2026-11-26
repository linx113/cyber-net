import type { LoadTestReport } from "@/types/load-test";

const API_URL = import.meta.env.VITE_API_URL || "";

export async function getLoadTests(): Promise<LoadTestReport> {
  const response = await fetch(`${API_URL}/api/load-tests`);
  if (!response.ok) {
    throw new Error("Failed to load load-test results");
  }
  const report = await response.json();
  return {
    ...report,
    results: report.results.map((row: Record<string, string>) => ({
      created_at: row.created_at,
      concurrency: Number(row.concurrency),
      requests: Number(row.requests),
      successes: Number(row.successes),
      errors: Number(row.errors),
      average_response_ms: Number(row.average_response_ms),
      max_response_ms: Number(row.max_response_ms),
      requests_per_second: Number(row.requests_per_second),
      duration_seconds: Number(row.duration_seconds),
      instance_distribution: row.instance_distribution,
    })),
  };
}

export async function startLoadTest(): Promise<void> {
  const response = await fetch(`${API_URL}/api/load-tests/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      concurrency_levels: [100, 500, 1000],
      requests_per_client: 1,
    }),
  });
  if (!response.ok) {
    const result = await response.json();
    throw new Error(result.detail || "Failed to start load test");
  }
}
