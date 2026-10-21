import React, { useState } from "react";
import { Search, Filter, ArrowUpDown, MoreHorizontal, CheckCircle2, Clock, AlertCircle } from "lucide-react";

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
  width?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  title?: string;
  searchPlaceholder?: string;
  onRowClick?: (item: T) => void;
}

export function DataTable<T extends { id: string | number }>({
  data,
  columns,
  title,
  searchPlaceholder = "Filtrar registros...",
  onRowClick,
}: DataTableProps<T>) {
  const [query, setQuery] = useState("");

  const filtered = data.filter((item) => {
    if (!query.trim()) return true;
    return Object.values(item).some((val) =>
      String(val).toLowerCase().includes(query.toLowerCase())
    );
  });

  return (
    <div className="w-full rounded-xl border border-slate-800/80 bg-slate-900/60 backdrop-blur shadow-sm overflow-hidden flex flex-col">
      {/* Topo / Barra de Ferramentas */}
      <div className="p-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 bg-slate-900/40">
        <div className="flex items-center gap-3">
          {title && <h2 className="text-sm font-semibold text-slate-100 tracking-tight">{title}</h2>}
          <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-slate-800 text-slate-400">
            {filtered.length} {filtered.length === 1 ? "registro" : "registros"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={searchPlaceholder}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-800 bg-slate-950/80 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 w-56 transition-all"
            />
          </div>
        </div>
      </div>

      {/* Tabela de Dados */}
      <div className="overflow-x-auto w-full">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              {columns.map((col, idx) => (
                <th key={String(col.key) + idx} style={{ width: col.width }} className="py-3 px-4">
                  <div className="flex items-center gap-1.5">
                    <span>{col.header}</span>
                  </div>
                </th>
              ))}
              <th className="py-3 px-4 text-right w-12">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="py-12 text-center text-slate-500">
                  Nenhum registro encontrado.
                </td>
              </tr>
            ) : (
              filtered.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => onRowClick?.(item)}
                  className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                >
                  {columns.map((col, idx) => (
                    <td key={String(col.key) + idx} className="py-3 px-4">
                      {col.render ? col.render(item) : String((item as any)[col.key] ?? "-")}
                    </td>
                  ))}
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      aria-label="Opções"
                      className="p-1 rounded hover:bg-slate-700/60 text-slate-400 hover:text-slate-200 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <MoreHorizontal className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
