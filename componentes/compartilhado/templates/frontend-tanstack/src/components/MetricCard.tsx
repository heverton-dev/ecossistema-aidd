import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, change, trend = "neutral", icon }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 backdrop-blur p-5 shadow-sm flex flex-col justify-between">
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="text-xs font-medium text-slate-400">{label}</span>
        {icon && <div className="p-2 rounded-lg bg-slate-800/80 text-slate-300">{icon}</div>}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>

        {change && (
          <div
            className={`flex items-center gap-1 text-xs font-semibold ${
              trend === "up"
                ? "text-emerald-400"
                : trend === "down"
                ? "text-rose-400"
                : "text-slate-400"
            }`}
          >
            {trend === "up" ? (
              <TrendingUp className="w-3.5 h-3.5" />
            ) : trend === "down" ? (
              <TrendingDown className="w-3.5 h-3.5" />
            ) : null}
            <span>{change}</span>
          </div>
        )}
      </div>
    </div>
  );
}
