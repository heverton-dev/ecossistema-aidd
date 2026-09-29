import { gerarAssinaturaHMAC, validarAssinaturaHMAC } from "../seguranca";

export interface ItemFilaPendente {
  id: string;
  kind: string;
  payload: Record<string, unknown>;
  criadoEm: string;
  signature?: string;
}

const CHAVE_STORAGE = "aidd.sync-queue";

export class OfflineSyncQueue {
  private static ler(): ItemFilaPendente[] {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(window.localStorage.getItem(CHAVE_STORAGE) ?? "[]") as ItemFilaPendente[];
    } catch {
      return [];
    }
  }

  private static escrever(fila: ItemFilaPendente[]): void {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(CHAVE_STORAGE, JSON.stringify(fila));
    window.dispatchEvent(new CustomEvent("aidd-sync-queue-updated", { detail: { count: fila.length } }));
  }

  public static tamanho(): number {
    return this.ler().length;
  }

  public static async enfileirar(itemSemAssinatura: Omit<ItemFilaPendente, "signature">): Promise<ItemFilaPendente> {
    const signature = await gerarAssinaturaHMAC(itemSemAssinatura.payload);
    const item: ItemFilaPendente = {
      ...itemSemAssinatura,
      signature,
    };
    const fila = this.ler();
    fila.push(item);
    this.escrever(fila);
    return item;
  }

  public static async processarFila(
    despachante: (item: ItemFilaPendente) => Promise<boolean>
  ): Promise<{ processados: number; falhas: number; corrompidos: number }> {
    const fila = this.ler();
    const restantes: ItemFilaPendente[] = [];
    let processados = 0;
    let falhas = 0;
    let corrompidos = 0;

    for (const item of fila) {
      if (!item.signature) {
        corrompidos++;
        continue;
      }

      const valida = await validarAssinaturaHMAC(item.payload, item.signature);
      if (!valida) {
        corrompidos++;
        continue;
      }

      try {
        const sucesso = await despachante(item);
        if (sucesso) {
          processados++;
        } else {
          falhas++;
          restantes.push(item);
        }
      } catch {
        falhas++;
        restantes.push(item);
      }
    }

    this.escrever(restantes);
    return { processados, falhas, corrompidos };
  }

  public static limpar(): void {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(CHAVE_STORAGE);
    window.dispatchEvent(new CustomEvent("aidd-sync-queue-updated", { detail: { count: 0 } }));
  }
}
