# PRODUCT.md — Atlas da Esteira Canônica AIDD (11 Etapas)

## 1. Visão do Produto & Superfície
O **Atlas da Esteira Canônica AIDD** (`mapa-11-passos-esteira.html`) é a interface visual interativa para inspeção, governança e navegação arquitetural fractal de todo o ecossistema AIDD. Ele traduz a especificação técnica viva de [DISSECACAO-ESTEIRA-11-PASSOS-AIDD.md](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/docs/manuais/DISSECACAO-ESTEIRA-11-PASSOS-AIDD.md) em uma experiência navegável sem atrito.

## 2. Personas de Uso
1. **Engenheiro de Software & Desenvolvedor de Módulos:** Consulta rápida dos contratos de entrada e saída (Handoffs JSON com hash SHA-256) e ferramentas acionadas em cada etapa.
2. **Arquiteto de Sistemas & Guardião de Governança:** Auditoria visual dos 69 Quality Gates ativos, separação estrita de responsabilidades entre fatias VSA e integridade da barreira de rebase.
3. **Auditor 4F / Gestor Técnico:** Acompanhamento do pipeline linear com comprovação de "portões que mordem" (exit 1 em violação) e zero stubs (Lei #5).

## 3. Requisitos Invioláveis da Interface
- **Soberania do Modo Claro (Light Mode Sovereign):** Superfícies limpas (`#ffffff`, `#f8fafc`, `#f1f5f9`), contraste tipográfico estrito (WCAG 2.2 AA/AAA), bordas de 1px em ardósia neutra e elevação sutil.
- **Responsividade Total (Viewport Universal):** Funcionamento perfeito em qualquer resolução (Mobile 320px-480px, Tablet 768px-1024px e Desktop 1440px+).
- **Zero Layout Shift (CLS = 0):** Carregamento sem saltos de elementos, caixas dimensionadas com aspect-ratio ou min-height definidos.
- **5 Estados de UI:**
  - *Idle:* Cards navegáveis com indicação visual clara de clique.
  - *Filtrado:* Transições instantâneas entre categorias sem perda de contexto.
  - *Vazio:* Feedback explícito caso nenhum card atenda a um critério de busca/filtro.
  - *Inspecionando (Modal):* Diálogo focado com rolagem interna independente e tecla ESC / clique externo para fechar.
  - *Foco/Acessibilidade:* Indicadores de foco visíveis (`outline: 2px solid var(--primary)` com offset).
