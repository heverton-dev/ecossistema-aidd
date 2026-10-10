# DESIGN.md · Sistema de Design do Quadro AIDD

> **Padrão Impeccable (Craft Floor)**  
> **Modo de Aplicação:** Operate (Console Operacional de Missão Crítica)  
> **Stack:** Vanilla HTML5, CSS3 Moderno (Custom Properties + OKLCH), Vanilla JS (Zero external dependencies)

---

## 1. Princípios Visuais & Arquitetura

1. **Densidade Operacional Limpa:**
   - Projetado para desenvolvedores e operadores de IA monitorando múltiplos pipelines concorrentes.
   - Informações prioritárias visíveis de imediato: status do processo (PID), tempo em execução, gargalo atual e necessidade de intervenção humana.
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
## 3. Recursos Operacionais de Alta Produtividade

1. **Hover Copy (Ação Direta no Card):**
   - Botão rápido de copiar comando acoplado ao canto do card no estado *"Precisa de você"*, disparável com 1 clique (`e.stopPropagation()` impede abertura involuntária da gaveta).
2. **Cronômetro Vivo no Card:**
   - Duração calculada ao vivo a cada segundo (`⏱ 01m 24s`) nos cards com status ativo, e duração estática consolidada nos concluídos.
3. **Busca Rápida por Tecla (`/`):**
   - Input de busca compacto com captura do atalho `/` no teclado; filtra instantaneamente por nome do pipeline, chave, ticket ou PID sem recarregar página.
4. **Notificações Desktop Nativas:**
   - Integração com a Web Notifications API com ativação via botão discreto no header; emite alerta no Windows quando um fluxo requer intervenção humana ou falha.
5. **Telemetria de Custos & Tokens (Factual - Lei #8):**
   - Painel na gaveta lateral exibindo contagem factual de tokens de entrada, saída, total e ferramentas/MCPs utilizadas, ou selo de não-medido quando ausentes os logs.
