import { getAlertsCount } from "@/services/alerts";
import {
  Activity,
  AlertTriangle,
  Cpu,
  LayoutDashboard,
  Settings,
  Terminal,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

const navigation = [
  {
    title: "OVERVIEW",
    items: [{ label: "Dashboard", path: "/", icon: LayoutDashboard }],
  },
  {
    title: "CITY MONITORING",
    items: [
      { label: "Devices", path: "/devices", icon: Cpu },
      { label: "Telemetry", path: "/telemetry", icon: Activity },
      { label: "Alerts", path: "/alerts", icon: AlertTriangle },
    ],
  },
  {
    title: "MANAGEMENT",
    items: [{ label: "Commands", path: "/commands", icon: Terminal }],
  },
];

export function AppSidebar() {
  const [alertsCount, setAlertsCount] = useState(0);
  useEffect(() => {
    async function loadAlertsCount() {
      try {
        const count = await getAlertsCount();
        setAlertsCount(count);
      } catch (error) {
        console.error("Failed to load alerts count:", error);
      }
    }

    loadAlertsCount();

    const interval = setInterval(loadAlertsCount, 10000);

    return () => clearInterval(interval);
  }, []);
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
      <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-6">
        <div>
          <h1 className="text-base font-bold tracking-wide text-sidebar-foreground">
            CyberNet
          </h1>
        </div>
      </div>

      <nav className="flex-1 space-y-8 overflow-y-auto px-3 py-6">
        {navigation.map((group) => (
          <div key={group.title} className="space-y-2">
            <p className="px-3 text-[10px] font-semibold tracking-[0.15em] text-muted-foreground">
              {group.title}
            </p>

            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === "/"}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                        isActive
                          ? "bg-primary/10 font-medium text-primary"
                          : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                      }`
                    }
                  >
                    <Icon size={18} />
                    <span>{item.label}</span>

                    {item.label === "Alerts" && alertsCount > 0 && (
                      <span className="ml-auto flex size-5 items-center justify-center rounded-full bg-destructive/15 text-[8px] font-semibold text-destructive p-2">
                        {alertsCount > 99 ? "99+" : alertsCount}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
              isActive
                ? "bg-sidebar-accent text-sidebar-foreground"
                : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
            }`
          }
        >
          <Settings size={18} />
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
