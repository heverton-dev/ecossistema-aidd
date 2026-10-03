import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { usePaginacao, type TamanhoPagina } from "../hooks/usePaginacao";
import { Paginacao } from "./Paginacao";
import { EmptyState } from "./Section";
import { ListSkeleton } from "./Skeletons";

export type Coluna<T> = {
  id: string;
  titulo: ReactNode;
  /** Conteúdo da célula. */
  celula: (linha: T) => ReactNode;
  /** Classe adicional (alinhamento, largura). */
  className?: string | undefined;
  /** Esconde a coluna em ecrãs pequenos. */
  ocultarEmMobile?: boolean | undefined;
  alinhar?: "esquerda" | "direita" | "centro" | undefined;
};

type Props<T> = {
  colunas: Coluna<T>[];
  linhas: readonly T[];
  chave: (linha: T) => string;
  aCarregar?: boolean | undefined;
  vazio?: { titulo: string; descricao?: string | undefined; acao?: ReactNode } | undefined;
  onLinha?: ((linha: T) => void) | undefined;
  tamanhoInicial?: TamanhoPagina | undefined;
  /** Sem paginação (listas curtas). */
  semPaginacao?: boolean | undefined;
  className?: string | undefined;
  /** Rodapé opcional (totais) renderizado sob as linhas. */
  rodape?: ReactNode;
};

const alinhamento = {
  esquerda: "text-left",
  direita: "text-right",
  centro: "text-center",
} as const;

/** Tabela paginada padrão da aplicação (10/25/50 por página, estados vazio e a carregar). */
export function DataTable<T>({
  colunas,
  linhas,
  chave,
  aCarregar,
  vazio,
  onLinha,
  tamanhoInicial = 10,
  semPaginacao,
  className,
  rodape,
}: Props<T>) {
  const estado = usePaginacao(linhas, tamanhoInicial);
  const visiveis = semPaginacao ? linhas : estado.visiveis;

  if (aCarregar) return <ListSkeleton linhas={5} />;
  if (linhas.length === 0)
    return (
      <div className="p-4">
        <EmptyState
          titulo={vazio?.titulo ?? "Sem registos"}
          descricao={vazio?.descricao}
          acao={vazio?.acao}
        />
      </div>
    );

  return (
    <div className={cn("flex flex-col", className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              {colunas.map((c) => (
                <th
                  key={c.id}
                  scope="col"
                  className={cn(
                    "eyebrow px-4 py-2.5 font-semibold text-muted-foreground",
                    c.alinhar ? alinhamento[c.alinhar] : "text-left",
                    c.ocultarEmMobile && "hidden md:table-cell",
                    c.className,
                  )}
                >
                  {c.titulo}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {visiveis.map((linha) => (
              <tr
                key={chave(linha)}
                onClick={onLinha ? () => onLinha(linha) : undefined}
                onKeyDown={
                  onLinha
                    ? (e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onLinha(linha);
                        }
                      }
                    : undefined
                }
                tabIndex={onLinha ? 0 : undefined}
                className={cn(
                  "transition-colors",
                  onLinha &&
                    "cursor-pointer hover:bg-accent/60 focus-visible:bg-accent/60 focus-visible:outline-none",
                )}
              >
                {colunas.map((c) => (
                  <td
                    key={c.id}
                    className={cn(
                      "px-4 py-3 align-middle",
                      c.alinhar ? alinhamento[c.alinhar] : "text-left",
                      c.ocultarEmMobile && "hidden md:table-cell",
                      c.className,
                    )}
                  >
                    {c.celula(linha)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          {rodape ? (
            <tfoot className="border-t border-border bg-muted/40 font-semibold">{rodape}</tfoot>
          ) : null}
        </table>
      </div>
      {semPaginacao ? null : <Paginacao estado={estado} />}
    </div>
  );
}
