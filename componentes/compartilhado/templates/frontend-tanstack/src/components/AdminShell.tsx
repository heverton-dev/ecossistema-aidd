import React from "react";
import { Link } from "@tanstack/react-router";
import {
  Code2,
  Webhook,
  Boxes,
  BookOpen,
  LayoutDashboard,
  ShieldCheck,
  Wifi,
  WifiOff
} from "lucide-react";
import { OfflineSyncQueue } from "../lib/offline/sync-queue";

interface AdminShellProps {
  children: React.ReactNode;
  titulo?: string;
}

export function AdminShell({ children, titulo = "Painel AIDD" }: AdminShellProps) {
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
    <div className="flex h-screen w-screen bg-[oklch(0.975_0.002_285)] text-[oklch(0.19_0.003_285)] antialiased font-[Public_Sans]">
      {/* Sidebar Desktop Impeccable */}
      <aside className="w-64 border-r border-[oklch(0.905_0.003_285)] bg-[oklch(1_0_0)] flex flex-col justify-between">
        <div>
          <div className="p-6 border-b border-[oklch(0.905_0.003_285)] flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[oklch(0.555_0.215_27.5)] text-white flex items-center justify-center font-bold">
              A
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-tight">{titulo}</h1>
              <span className="text-[10px] text-[oklch(0.46_0.006_285)] uppercase tracking-wider font-semibold">
                TanStack Padrão-Ouro
              </span>
            </div>
          </div>

          <nav className="p-4 space-y-1">
            <Link
              to="/"
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-[oklch(0.955_0.002_285)] transition-colors"
            >
              <LayoutDashboard className="w-4 h-4 text-[oklch(0.555_0.215_27.5)]" />
              <span>Visão Geral</span>
            </Link>

            {/* Quarteto Sine Qua Non Dinâmico (Lei #10) */}
            <div className="pt-4 pb-2 px-3">
              <span className="text-[10px] font-bold tracking-wider uppercase text-[oklch(0.46_0.006_285)]">
                Quarteto Sine Qua Non
              </span>
            </div>

            <Link
              to="/api"
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-[oklch(0.955_0.002_285)] transition-colors"
            >
              <Code2 className="w-4 h-4 text-[oklch(0.5_0.12_250)]" />
              <span>OpenAPI Studio</span>
            </Link>

            <Link
              to="/webhook"
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-[oklch(0.955_0.002_285)] transition-colors"
            >
              <Webhook className="w-4 h-4 text-[oklch(0.76_0.15_75)]" />
              <span>Webhook Studio</span>
            </Link>

            <Link
              to="/mcp"
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-[oklch(0.955_0.002_285)] transition-colors"
            >
              <Boxes className="w-4 h-4 text-[oklch(0.47_0.12_150)]" />
              <span>MCP Studio</span>
            </Link>

            <Link
              to="/docs"
              className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium hover:bg-[oklch(0.955_0.002_285)] transition-colors"
            >
              <BookOpen className="w-4 h-4 text-[oklch(0.555_0.215_27.5)]" />
              <span>Docs & Guia</span>
            </Link>
          </nav>
        </div>

        {/* Status de Conexão e Fila Offline */}
        <div className="p-4 border-t border-[oklch(0.905_0.003_285)] bg-[oklch(0.975_0.002_285)] m-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold">
            {online ? (
              <>
                <Wifi className="w-4 h-4 text-[oklch(0.47_0.12_150)]" />
                <span>Online</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-[oklch(0.52_0.19_20)]" />
                <span>Modo Offline</span>
              </>
            )}
          </div>
          {filaCount > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[oklch(0.76_0.15_75)] text-white font-bold">
              {filaCount} sync
            </span>
          )}
        </div>
      </aside>

      {/* Conteúdo Central */}
      <main className="flex-1 flex flex-col overflow-auto">
        <header className="h-16 border-b border-[oklch(0.905_0.003_285)] bg-[oklch(1_0_0)] px-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[oklch(0.47_0.12_150)]" />
            <span className="text-xs font-medium text-[oklch(0.46_0.006_285)]">
              Blindagem HMAC & Determinismo
            </span>
          </div>
        </header>
        <section className="p-8 flex-1">{children}</section>
      </main>
    </div>
  );
}
