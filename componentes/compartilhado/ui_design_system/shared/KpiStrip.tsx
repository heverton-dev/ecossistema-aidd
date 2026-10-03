import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { toneText, type Tone } from "../tones";

export type Kpi = {
  label: string;
  valor: ReactNode;
  /** Linha de contexto real (ex.: "59% das paradas"). */
  contexto?: ReactNode | undefined;
  /** Tom semântico do contexto. */
  tone?: Tone | undefined;
};

const colunasLg: Record<number, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-4",
  5: "lg:grid-cols-5",
  6: "lg:grid-cols-6",
};

const colunasCompacto: Record<number, string> = {
  2: "grid-cols-2",
  3: "grid-cols-3",
  4: "grid-cols-2 sm:grid-cols-4",
  5: "grid-cols-2 sm:grid-cols-5",
  6: "grid-cols-3 sm:grid-cols-6",
};

/**
 * Faixa de indicadores (KPIs): um único cartão dividido por linhas finas.
 * `compacto` mantém tudo numa linha, para a app do estafeta.
 */
export function KpiStrip({
  itens,
  compacto,
  ariaLabel = "Indicadores",
  className,
}: {
  itens: Kpi[];
  compacto?: boolean;
  ariaLabel?: string;
  className?: string;
}) {
  const n = Math.min(Math.max(itens.length, 2), 6);
  return (
    <section
      aria-label={ariaLabel}
      className={cn(
        "overflow-hidden rounded-lg border border-border bg-border shadow-elev-1",
        className,
      )}
    >
      <dl
        className={cn(
          "grid gap-px",
          compacto
            ? (colunasCompacto[n] ?? "grid-cols-3")
            : cn(
                "grid-cols-2 [&>*:last-child:nth-child(odd)]:col-span-2 lg:[&>*:last-child:nth-child(odd)]:col-span-1",
                colunasLg[n],
              ),
        )}
      >
        {itens.map((k) => (
          <div
            key={k.label}
            className={cn("min-w-0 bg-card", compacto ? "px-2 sm:px-3 py-2 sm:py-2.5" : "px-4 py-3.5")}
          >
            <dt className="truncate text-xs text-muted-foreground">{k.label}</dt>
            <dd className={cn("numeric-data mt-0.5 truncate font-semibold", compacto ? "text-base sm:text-lg" : "text-2xl font-normal")}>
              {k.valor}
            </dd>
            {k.contexto ? (
              <dd
                className={cn(
                  "mt-0.5 truncate text-[11px] sm:text-xs",
                  k.tone ? toneText[k.tone] : "text-muted-foreground",
                )}
              >
                {k.contexto}
              </dd>
            ) : null}
          </div>
        ))}
      </dl>
    </section>
  );
}
