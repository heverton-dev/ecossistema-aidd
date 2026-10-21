import React from "react";
import { Plus, MoreHorizontal, Calendar, Tag } from "lucide-react";

export interface KanbanItem {
  id: string;
  title: string;
  status: string;
  priority?: "low" | "medium" | "high";
  due_date?: string;
  tags?: string[];
  notes?: string;
}

export interface KanbanColumn {
  id: string;
  title: string;
  color?: string;
}

interface KanbanBoardProps {
  columns: KanbanColumn[];
  items: KanbanItem[];
  onItemMove?: (itemId: string, targetStatus: string) => void;
  onItemClick?: (item: KanbanItem) => void;
  onAddItem?: (columnId: string) => void;
}

export function KanbanBoard({
  columns,
  items,
  onItemMove,
  onItemClick,
  onAddItem,
}: KanbanBoardProps) {
  const getPriorityBadge = (priority?: string) => {
    switch (priority) {
      case "high":
        return (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-rose-500/30 bg-rose-500/10 text-rose-400">
            Alta
          </span>
        );
      case "medium":
        return (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-amber-500/30 bg-amber-500/10 text-amber-400">
            Média
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-slate-700 bg-slate-800 text-slate-400">
            Baixa
          </span>
        );
    }
  };

  return (
    <div className="w-full flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
      {columns.map((col) => {
        const colItems = items.filter((item) => item.status === col.id);

        return (
          <div
            key={col.id}
            className="flex flex-col rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 min-h-[500px]"
          >
            {/* Header da Coluna */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/60">
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: col.color || "#6366f1" }}
                />
                <h3 className="text-xs font-semibold text-slate-200 tracking-tight uppercase">
                  {col.title}
                </h3>
                <span className="text-[11px] px-2 py-0.2 rounded-full font-medium bg-slate-800 text-slate-400">
                  {colItems.length}
                </span>
              </div>

              {onAddItem && (
                <button
                  type="button"
                  onClick={() => onAddItem(col.id)}
                  className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                  aria-label="Adicionar item"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Lista de Cards */}
            <div className="flex flex-col gap-3 flex-1 overflow-y-auto">
              {colItems.length === 0 ? (
                <div className="flex-1 flex items-center justify-center p-6 border border-dashed border-slate-800/60 rounded-lg text-slate-500 text-xs text-center">
                  Nenhum item nesta coluna
                </div>
              ) : (
                colItems.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => onItemClick?.(item)}
                    className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/90 hover:border-slate-700 hover:bg-slate-800/60 transition-all cursor-pointer shadow-sm group"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className="text-xs font-semibold text-slate-200 group-hover:text-white transition-colors leading-relaxed">
                        {item.title}
                      </h4>
                      {item.priority && getPriorityBadge(item.priority)}
                    </div>

                    {item.notes && (
                      <p className="text-[11px] text-slate-400 line-clamp-2 mb-3">
                        {item.notes}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800/60">
                      <div className="flex items-center gap-2">
                        {item.due_date && (
                          <span className="flex items-center gap-1 text-slate-400">
                            <Calendar className="w-3 h-3" />
                            {item.due_date}
                          </span>
                        )}
                        {item.tags && item.tags.length > 0 && (
                          <span className="flex items-center gap-1 text-slate-400">
                            <Tag className="w-3 h-3" />
                            {item.tags[0]}
                          </span>
                        )}
                      </div>

                      {onItemMove && (
                        <select
                          value={item.status}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => onItemMove(item.id, e.target.value)}
                          className="bg-slate-950/80 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none"
                        >
                          {columns.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.title}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
