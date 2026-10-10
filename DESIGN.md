---
colors:
  primary: "#38bdf8"
  primary-glow: "rgba(56, 189, 248, 0.25)"
  background: "#080b11"
  surface: "#0d121c"
  surface-elevated: "#141b27"
  surface-highlight: "#1e293b"
  text-primary: "#f1f5f9"
  text-secondary: "#94a3b8"
  text-muted: "#64748b"
  border-base: "rgba(255, 255, 255, 0.08)"
  border-subtle: "rgba(255, 255, 255, 0.04)"
  border-focus: "#38bdf8"
  status-success: "#10b981"
  status-warning: "#f59e0b"
  status-danger: "#f43f5e"
  status-neutral: "#64748b"
typography:
  font-family-sans: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
  font-family-mono: "'JetBrains Mono', 'SF Mono', Consolas, Monaco, monospace"
  scale:
    xs: "0.7rem"
    sm: "0.785rem"
    base: "0.875rem"
    lg: "1.05rem"
    xl: "1.25rem"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.5rem"
components:
  card:
    border: "1px solid var(--borda-base)"
    background: "var(--bg-superficie)"
    shadow: "0 4px 16px -2px rgba(0, 0, 0, 0.5)"
    active-scale: "scale(0.99)"
  button:
    touch-target-min: "44px"
    border-radius: "var(--raio-p)"
---

# DESIGN.md · Sistema de Design do Quadro AIDD

> **Padrão Impeccable (Craft Floor)**  
> **Modo de Aplicação:** Operate (Console Operacional de Missão Crítica)  
> **Target Devices:** Desktop (Operador) & Mobile Companion (Smartphones iOS/Android via Wi-Fi QR Code)  
> **Stack:** Vanilla HTML5, CSS3 Moderno (Custom Properties + OKLCH/Hex Semântico), Vanilla JS (Zero external dependencies)

---

## 1. Princípios Visuais & Arquitetura

1. **Densidade Operacional Limpa (Modo Operate):**
   - Projetado para desenvolvedores e operadores de IA monitorando múltiplos pipelines concorrentes.
   - Informações prioritárias visíveis de imediato: status do processo (PID), tempo em execução ao vivo, gargalo atual e necessidade de intervenção humana.
   - Eliminação de qualquer adorno superficial (zero gradient text, zero bordas grossas decorativas, zero sombras sem blur).

2. **Tema Dual Universal (Dark / Light):**
   - **Dark Mode (Padrão):** Fundo ardósia profundo (`#080b11`), superfícies elevadas (`#0d121c` e `#141b27`), bordas nítidas de 1px com baixa opacidade (`rgba(255, 255, 255, 0.08)`).
   - **Light Mode (Alternativo via tecla `T` ou botão):** Fundo neutro limpo (`#f8fafc`), cartões brancos puros (`#ffffff`), texto de alto contraste (`#0f172a`).

3. **Semântica Funcional de Cores (WCAG AAA/AA):**
   - **Executando (Ao Vivo):** Ciano elétrico (`#38bdf8`) com pulso sutil em taxa suave de 2s.
   - **Concluído:** Verde esmeralda (`#10b981`).
   - **Precisa de Você / Alerta:** Âmbar incandescente (`#f59e0b`) com contraste 5.8:1 sobre superfícies escuras.
   - **Falhou / Parado:** Carmesim vibrante (`#f43f5e`).
   - **Fila / Pendente:** Ardósia neutra (`#64748b`).

---

## 2. Craft Floor Compliance (Impeccable Reference)

- **Contraste & Profundidade:** Sombras suaves com blur e offset realistas (`0 4px 16px -2px rgba(0, 0, 0, 0.5)`), sem bordas grossas decorativas (`border-left > 1px` banido).
- **Tipografia:** Fonte do sistema moderno (`-apple-system`, `Segoe UI`, `Roboto`) para a interface humana; fonte mono estrita (`JetBrains Mono`, `Consolas`, `SF Mono`) restrita a PIDs, comandos, timestamps e identificadores de hash.
- **Superfícies Nativas:** Custom scrollbars integradas ao tema, `::selection` estilizada, anéis de foco acessíveis (`:focus-visible`).
- **Mobile Ergonomics (Alvo Touch):** Alvos de toque com dimensão mínima de 44x44px para o polegar, safe-areas de topo e base respeitadas (`env(safe-area-inset-top)` e `env(safe-area-inset-bottom)`), e scroll snap horizontal suave para navegação entre colunas e cartões.

---

## 3. Recursos Operacionais de Alta Produtividade

1. **Hover & Touch Copy (Ação Direta no Card):**
   - Botão rápido de copiar comando acoplado ao canto do card no estado *"Precisa de você"*, disparável com 1 toque/clique (`e.stopPropagation()` impede abertura involuntária da gaveta).
2. **Cronômetro Vivo no Card:**
   - Duração calculada ao vivo a cada segundo (`⏱ 01m 24s`) nos cards com status ativo, e duração estática consolidada nos concluídos.
3. **Busca Rápida por Tecla (`/`):**
   - Input de busca compacto com captura do atalho `/` no teclado; filtra instantaneamente por nome do pipeline, chave, ticket ou PID sem recarregar página.
4. **Notificações Desktop Nativas & Som de Alerta:**
   - Integração com a Web Notifications API com ativação via botão discreto no header; emite alerta no Windows quando um fluxo requer intervenção humana ou falha, com áudio opcional sintetizado por Web Audio API.
5. **Telemetria de Custos & Tokens (Factual - Lei #8):**
   - Painel na gaveta lateral exibindo contagem factual de tokens de entrada, saída, total e ferramentas/MCPs utilizadas, ou selo de não-medido quando ausentes os logs.
6. **QR Code Companion Mobile (Wi-Fi):**
   - Modal com QR Code determinístico gerado no cliente via matriz SVG sem dependência externa, permitindo leitura direta pela câmera do smartphone na mesma rede local.
