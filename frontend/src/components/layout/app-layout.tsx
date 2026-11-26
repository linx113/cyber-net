import { Outlet } from "react-router-dom";
import { AppHeader } from "./app-header";
import { AppSidebar } from "./app-sidebar";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <AppSidebar />

      <div className="min-h-screen lg:pl-64">
        <AppHeader />

        <main className="mx-auto w-full max-w-[1800px] p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
