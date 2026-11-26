import { getDevices } from "@/services/devices";
import { createCommand, getCommands } from "@/services/commands";
import type { Device } from "@/types/device";
import type { DeviceCommand } from "@/types/command";
import { useEffect, useState } from "react";

export function CommandsPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [commands, setCommands] = useState<DeviceCommand[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [command, setCommand] = useState("turn_on");
  const [parameter, setParameter] = useState("true");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function refresh() {
    try {
      const [deviceResponse, commandResponse] = await Promise.all([
        getDevices(),
        getCommands(),
      ]);
      setDevices(deviceResponse.devices);
      setCommands(commandResponse);
      setDeviceId((current) =>
        deviceResponse.devices.some((device) => device.id === current)
          ? current
          : (deviceResponse.devices[0]?.id ?? ""),
      );
      setError("");
    } catch {
      setError("Could not load devices or command history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void refresh(), 0);
    const interval = window.setInterval(() => void refresh(), 5000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, []);

  const selectedDevice = devices.find((device) => device.id === deviceId);
  const availableCommands = [
    { value: "set_maintenance", label: "Set maintenance mode" },
    { value: "restart", label: "Restart device" },
    { value: "set_interval", label: "Change telemetry interval" },
    ...(selectedDevice?.type === "street_light"
      ? [
          { value: "turn_on", label: "Turn on lighting" },
          { value: "turn_off", label: "Turn off lighting" },
          { value: "set_lighting", label: "Set brightness" },
        ]
      : []),
    ...(selectedDevice?.type === "traffic_light"
      ? [{ value: "set_traffic_mode", label: "Change traffic-light mode" }]
      : []),
  ];

  async function submitCommand(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSending(true);
    setError("");
    setNotice("");

    try {
      await createCommand({
        device_id: deviceId,
        command,
        parameters: command === "set_lighting"
          ? `brightness=${parameter}`
          : command === "set_interval"
            ? `seconds=${parameter}`
            : command === "set_maintenance"
              ? `enabled=${parameter}`
              : command === "set_traffic_mode"
                ? `mode=${parameter}`
                : null,
      });
      setNotice("Command queued. Its status will update automatically.");
      await refresh();
    } catch {
      setError("Could not send the command. Check that the services are online.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Device commands</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Send supported device commands through RabbitMQ and track their execution status.
        </p>
      </header>

      <form
        onSubmit={submitCommand}
        className="grid gap-4 rounded-lg border border-border bg-card p-5 sm:grid-cols-2"
      >
        <label className="space-y-2 text-sm">
          <span className="block font-medium">Device</span>
          <select
            required
            value={deviceId}
            onChange={(event) => {
              const nextDevice = devices.find(
                (device) => device.id === event.target.value,
              );
              setDeviceId(event.target.value);
              const nextCommand = nextDevice?.type === "street_light"
                ? "turn_on"
                : nextDevice?.type === "traffic_light"
                  ? "set_traffic_mode"
                  : "set_maintenance";
              setCommand(nextCommand);
              setParameter(
                nextCommand === "set_traffic_mode"
                  ? "auto"
                  : nextCommand === "set_maintenance"
                    ? "true"
                    : "70",
              );
            }}
            disabled={loading || devices.length === 0}
            className="w-full rounded-md border border-border bg-background px-3 py-2"
          >
            {devices.length === 0 && <option value="">No devices available</option>}
            {devices.map((device) => (
              <option key={device.id} value={device.id}>
                {device.type.replace("_", " ")} · {device.location} · {device.id}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2 text-sm">
          <span className="block font-medium">Command</span>
          <select
            value={command}
            onChange={(event) => {
              const nextCommand = event.target.value;
              setCommand(nextCommand);
              setParameter(
                nextCommand === "set_maintenance"
                  ? "true"
                  : nextCommand === "set_traffic_mode"
                    ? "auto"
                    : nextCommand === "set_interval"
                      ? "5"
                      : "70",
              );
            }}
            className="w-full rounded-md border border-border bg-background px-3 py-2"
          >
            {availableCommands.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {["set_lighting", "set_interval", "set_maintenance", "set_traffic_mode"].includes(command) && (
          <label className="space-y-2 text-sm">
            <span className="block font-medium">
              {command === "set_lighting"
                ? "Brightness (0–100)"
                : command === "set_interval"
                  ? "Interval in seconds (1–3600)"
                  : command === "set_maintenance"
                    ? "Maintenance mode"
                    : "Traffic-light mode"}
            </span>
            {command === "set_maintenance" || command === "set_traffic_mode" ? (
              <select
                value={parameter}
                onChange={(event) => setParameter(event.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2"
              >
                {command === "set_maintenance" ? (
                  <>
                    <option value="true">Enabled</option>
                    <option value="false">Disabled</option>
                  </>
                ) : (
                  ["auto", "red", "yellow", "green"].map((mode) => (
                    <option key={mode} value={mode}>{mode}</option>
                  ))
                )}
              </select>
            ) : (
              <input
                type="number"
                max={command === "set_interval" ? "3600" : "100"}
                min={command === "set_interval" ? "1" : "0"}
                required
                value={parameter}
                onChange={(event) => setParameter(event.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2"
              />
            )}
          </label>
        )}

        <div className="flex items-end">
          <button
            type="submit"
            disabled={sending || loading || devices.length === 0}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
          >
            {sending ? "Sending…" : "Send command"}
          </button>
        </div>
      </form>

      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      {notice && <p role="status" className="text-sm text-emerald-400">{notice}</p>}

      <section className="overflow-hidden rounded-lg border border-border">
        <div className="border-b border-border px-4 py-3">
          <h2 className="font-medium">Recent commands</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/40 text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Device</th>
                <th className="px-4 py-3 font-medium">Command</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {commands.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                    {loading ? "Loading commands…" : "No commands have been sent."}
                  </td>
                </tr>
              ) : (
                commands.map((item) => (
                  <tr key={item.id} className="border-t border-border">
                    <td className="px-4 py-3 font-mono text-xs">{item.device_id}</td>
                    <td className="px-4 py-3">
                      {item.command}
                      {item.parameters ? ` (${item.parameters})` : ""}
                    </td>
                    <td className="px-4 py-3 capitalize">{item.status}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
