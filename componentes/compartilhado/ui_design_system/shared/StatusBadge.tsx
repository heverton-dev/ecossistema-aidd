import { cn } from "@/lib/utils";
import { toneSoft, type Tone } from "../tones";

/** Etiqueta de estado padrão (rotas, paradas, carrinhas, ocorrências). */
export function StatusBadge({
  label,
  tone = "muted",
  className,
}: {
  label: string;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold whitespace-nowrap",
        toneSoft[tone],
        className,
      )}
    >
      {label}
    </span>
  );
}
