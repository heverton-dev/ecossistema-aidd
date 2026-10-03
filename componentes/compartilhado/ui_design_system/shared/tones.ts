/** Tons semânticos partilhados (mapeiam para tokens em src/styles.css). */
export type Tone = "muted" | "info" | "success" | "warning" | "destructive" | "primary";

export const toneText: Record<Tone, string> = {
  muted: "text-muted-foreground",
  info: "text-info",
  success: "text-success",
  warning: "text-warning-foreground dark:text-warning",
  destructive: "text-destructive",
  primary: "text-primary-text",
};

export const toneSoft: Record<Tone, string> = {
  muted: "bg-muted text-muted-foreground",
  info: "bg-info/12 text-info",
  success: "bg-success/12 text-success",
  warning: "bg-warning/18 text-warning-foreground dark:text-warning",
  destructive: "bg-destructive/12 text-destructive",
  primary: "bg-primary/12 text-primary-text",
};

/**
 * Cores para elementos gráficos (Leaflet / Canvas / SVG). São referências a tokens de
 * src/styles.css; resolva-as com `resolverCor` no momento de desenhar para seguir o tema.
 */
export const MAP_COLORS = {
  polyline: "var(--foreground)",
  estafeta: "var(--foreground)",
  pendente: "var(--muted-foreground)",
  em_curso: "var(--info)",
  concluida: "var(--success)",
  insucesso: "var(--destructive)",
  reversa: "var(--warning)",
} as const;

/** Cor do marcador de cada estado de parada. */
export const CORES_ESTADO: Record<string, string> = {
  pendente: MAP_COLORS.pendente,
  em_curso: MAP_COLORS.em_curso,
  concluida: MAP_COLORS.concluida,
  insucesso: MAP_COLORS.insucesso,
  reversa: MAP_COLORS.reversa,
};

export function corDoEstado(estado: string): string {
  return CORES_ESTADO[estado] ?? MAP_COLORS.pendente;
}

/** Converte `var(--token)` no valor calculado; outras cores passam inalteradas. */
export function resolverCor(cor: string): string {
  const m = /^var\((--[\w-]+)\)$/.exec(cor);
  if (!m || typeof document === "undefined") return cor;
  return getComputedStyle(document.documentElement).getPropertyValue(m[1]!).trim() || cor;
}
