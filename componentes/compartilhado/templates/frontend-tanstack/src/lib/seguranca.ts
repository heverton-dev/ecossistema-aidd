/**
 * Utilidades criptográficas para garantia de integridade da fila offline
 * Usa Web Crypto API nativa, sem dependências proprietárias.
 */

const SEGREDO_HMAC_DEFAULT = "aidd-offline-integrity-secret";

export async function gerarAssinaturaHMAC(payload: unknown, secret: string = SEGREDO_HMAC_DEFAULT): Promise<string> {
  const enc = new TextEncoder();
  const dados = enc.encode(typeof payload === "string" ? payload : JSON.stringify(payload));
  const keyData = enc.encode(secret);

  if (typeof crypto !== "undefined" && crypto.subtle) {
    const key = await crypto.subtle.importKey(
      "raw",
      keyData,
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const signature = await crypto.subtle.sign("HMAC", key, dados);
    return Array.from(new Uint8Array(signature))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  // Fallback determinístico caso Web Crypto não esteja disponível
  let hash = 0;
  const str = JSON.stringify(payload) + secret;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return "fallback-" + Math.abs(hash).toString(16);
}

export async function validarAssinaturaHMAC(
  payload: unknown,
  assinatura: string,
  secret: string = SEGREDO_HMAC_DEFAULT
): Promise<boolean> {
  const esperada = await gerarAssinaturaHMAC(payload, secret);
  return esperada === assinatura;
}
