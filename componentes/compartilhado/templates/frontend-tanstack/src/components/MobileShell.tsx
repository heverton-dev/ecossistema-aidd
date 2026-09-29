import React from "react";
import { Link } from "@tanstack/react-router";
import { LayoutDashboard, BookOpen, Boxes, Wifi, WifiOff } from "lucide-react";
import { OfflineSyncQueue } from "../lib/offline/sync-queue";

interface MobileShellProps {
  children: React.ReactNode;
  titulo?: string;
}

export function MobileShell({ children, titulo = "AIDD Mobile" }: MobileShellProps) {
  const [online, setOnline] = React.useState(typeof navigator !== "undefined" ? navigator.onLine : true);
  const [filaCount, setFilaCount] = React.useState(0);

  React.useEffect(() => {
    const handleStatus = () => setOnline(navigator.onLine);
    const handleFila = (e: any) => setFilaCount(e.detail?.count ?? OfflineSyncQueue.tamanho());

    window.addEventListener("online", handleStatus);
    window.addEventListener("offline", handleStatus);
    window.addEventListener("aidd-sync-queue-updated", handleFila);

    setFilaCount(OfflineSyncQueue.tamanho());

    return () => {
      window.removeEventListener("online", handleStatus);
      window.removeEventListener("offline", handleStatus);
      window.removeEventListener("aidd-sync-queue-updated", handleFila);
    };
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[oklch(0.975_0.002_285)] text-[oklch(0.19_0.003_285)] font-[Public_Sans] overflow-hidden">
      {/* Top Header Mobile */}
      <header className="h-14 border-b border-[oklch(0.905_0.003_285)] bg-[oklch(1_0_0)] px-4 flex items-center justify-between">
        <h1 className="font-bold text-sm">{titulo}</h1>
        <div className="flex items-center gap-2">
          {online ? (
            <Wifi className="w-4 h-4 text-[oklch(0.47_0.12_150)]" />
          ) : (
            <div className="flex items-center gap-1 text-[oklch(0.52_0.19_20)] text-xs font-bold">
              <WifiOff className="w-4 h-4" />
              <span>OFFLINE</span>
            </div>
          )}
          {filaCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[oklch(0.76_0.15_75)] text-white font-bold">
              {filaCount}
            </span>
          )}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 overflow-y-auto p-4">{children}</main>

      {/* Bottom Navigation */}
      <nav className="h-16 border-t border-[oklch(0.905_0.003_285)] bg-[oklch(1_0_0)] px-6 flex items-center justify-around">
        <Link to="/" className="flex flex-col items-center gap-1 text-xs">
          <LayoutDashboard className="w-5 h-5 text-[oklch(0.555_0.215_27.5)]" />
          <span>Início</span>
        </Link>
        <Link to="/mcp" className="flex flex-col items-center gap-1 text-xs">
          <Boxes className="w-5 h-5 text-[oklch(0.47_0.12_150)]" />
          <span>MCP</span>
        </Link>
        <Link to="/docs" className="flex flex-col items-center gap-1 text-xs">
          <BookOpen className="w-5 h-5 text-[oklch(0.5_0.12_250)]" />
          <span>Docs</span>
        </Link>
      </nav>
    </div>
  );
}
