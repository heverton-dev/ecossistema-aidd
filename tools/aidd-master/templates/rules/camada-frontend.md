# Camada Frontend — Regras de Interface & UX

> **Escopo:** Toda interface visual em `src/static/`, componentes HTML e Super-App SPA.
> **Referencia:** `templates/rules/03_impeccable.md`, `templates/core/index.html`, `templates/core/docs.html`.

---

## 1. Tailwind CSS com Impeccable UI

- Framework CSS: Tailwind CSS com configuracao do design system.
- Paleta base: Slate (neutros) + Indigo/Blue (primario).
- Dark mode como padrao (`class="dark"` no `<html>`).
- Bordas sutis: `border-white/8` (rgba 255,255,255,0.08).
- Sombras: `shadow-lg` com `backdrop-filter: blur(20px)` para glassmorphism.
- Background: `#020617` (body), `#050b18` (surface), `#030712` (sidebar).

### Variaveis CSS Obrigatorias

```css
:root {
    --bg-body: #020617;
    --bg-surface: #050b18;
    --bg-surface-hover: #081226;
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.16);
    --primary: #3b82f6;
    --primary-light: #60a5fa;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --purple: #a855f7;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
}
```

### Tipografia Padronizada

| Nivel | Tamanho | Peso | Uso |
|-------|---------|------|-----|
| `--text-2xl` | 1.85rem | 800 | Titulo principal, KPI Cards |
| `--text-xl` | 1.45rem | 800 | Titulos H2 de modulos |
| `--text-lg` | 1.15rem | 800 | Cabecalhos de Cards/Modais |
| `--text-md` | 0.98rem | 700/600 | Subtitulos |
| `--text-base` | 0.88rem | 500/600 | Corpo de texto, tabelas |
| `--text-sm` | 0.82rem | 700/600 | Botoes, inputs, breadcrumbs |
| `--text-xs` | 0.72rem | 800 | Badges, tags, labels |
| `--font-mono` | 0.80rem | 600 | Codigos, JSON, endpoints |

---

## 2. WCAG 2.1 Accessibility Compliance

Regras obrigatorias de acessibilidade:

- Todo `<button>` DEVE ter `type="button"` (evitar submit acidental).
- Todo elemento interativo DEVE ter `aria-label` ou texto visivel.
- Foco visivel: `outline: 2px solid var(--primary)` em `:focus-visible`.
- Contraste minimo: 4.5:1 para texto normal, 3:1 para texto grande.
- Navegacao por teclado: `Tab`, `Enter`, `Escape` funcionais em todos os componentes.
- `role` ARIA em componentes customizados: `dialog`, `menu`, `tablist`, `alert`.
- Imagens com `alt` descritivo. Icones SVG com `aria-hidden="true"` quando decorativos.
- Skip links: `<a href="#main-content" class="sr-only focus:not-sr-only">Pular para conteudo</a>`.
- Formularios com `<label>` associado via `for`/`id`.

---

## 3. Chrome DevTools MCP Integration

- Performance: Largest Contentful Paint (LCP) < 2.5s.
- First Input Delay (FID) < 100ms.
- Cumulative Layout Shift (CLS) < 0.1.
- Auditar com Lighthouse score >= 90 em todas as categorias.
- Network: minimizar requests, lazy loading de componentes pesados.
- Memory: evitar memory leaks em event listeners (remover no `onUnmount`).
- Accessibility audit: zero violations criticas no axe-core.

---

## 4. Design System Variables

### Scrollbars Padronizadas (4px)

```css
* {
    scrollbar-width: thin;
    scrollbar-color: rgba(59, 130, 246, 0.4) transparent;
}
::-webkit-scrollbar { width: 4px !important; height: 4px !important; }
::-webkit-scrollbar-track { background: transparent !important; }
::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.35) !important;
    border-radius: 9999px !important;
}
```

### Header Imutavel de Linha Unica

```css
header {
    min-height: 56px;
    white-space: nowrap;
    overflow-x: auto;
    flex-shrink: 0;
}
```

### Botoes em Linha Unica

```css
button, .btn {
    white-space: nowrap !important;
    line-height: 1.2;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
```

### Zero Emojis, Apenas SVG

- Usar exclusivamente icones vetoriais SVG (Lucide / Heroicons).
- Proibicao total de emojis em botoes, titulos, cards, badges.
- Icones inline com `<svg>` (nao `<img>` para icones de UI).

### Zero Alertas Nativos

- NUNCA usar `window.alert()`, `window.confirm()`, `window.prompt()`.
- Usar sistema de feedback: `showToast(mensagem, tipo)`.
- Confirmacoes: modal HTML customizado com `showConfirm(pergunta)`.
- Toast container fixo no canto inferior direito.

---

## 5. Responsive Breakpoints

| Breakpoint | Largura | Layout |
|------------|---------|--------|
| Mobile | < 640px | Stack vertical, sidebar colapsada |
| Tablet | 640px - 1024px | 2 colunas, sidebar compacta |
| Desktop | 1024px - 1440px | 3 colunas (sidebar + main + panel) |
| Ultrawide | > 1440px | 3 colunas com max-width container |

- Tabelas com scroll horizontal em containers responsivos.
- Grids com `minmax(0, 1fr)` para evitar overflow.
- Media queries mobile-first: `@media (min-width: ...)`.
- Touch targets: minimo 44x44px em dispositivos moveis.

---

## 6. Super-App SPA Architecture

- Single Page Application com `index.html` como entrypoint.
- Navegacao via `App Switcher` (abas de modulos no header).
- Carregamento de modulos via `fetch()` dinamico (code splitting).
- Estado global minimo: cada modulo gerencia seu proprio estado.
- Feedback de loading: skeleton screens, nao spinners genericos.
- Transicoes suaves: `transition: all 0.15s` em elementos interativos.

---

## 7. Formularios Reativos

- Inputs com validacao em tempo real (debounce 300ms).
- Mensagens de erro inline (nao apenas borda vermelha).
- Botao de submit desabilitado durante envio (prevenir duplo clique).
- Labels flutuantes ou placeholders claros.
- Campos obrigatorios marcados com asterisco vermelho.

---

## Checklist de Auditoria Frontend

| # | Criterio | Gate |
|---|----------|------|
| 1 | Tailwind CSS com variaveis do design system | G_QUALIDADE |
| 2 | WCAG 2.1 (aria-label, type="button", foco) | G_SEGURANCA |
| 3 | Scrollbars 4px em toda aplicacao | G_QUALIDADE |
| 4 | Header de linha unica (nowrap, overflow-x) | G_QUALIDADE |
| 5 | Zero emojis (apenas SVG Lucide) | G_CONTRACTS |
| 6 | Zero alertas nativos (toast/modal) | G_CONTRACTS |
| 7 | Botoes em linha unica | G_QUALIDADE |
| 8 | Responsividade fluida (mobile a ultrawide) | G_QUALIDADE |
| 9 | Lighthouse score >= 90 | G_TESTES |
| 10 | Formularios com validacao reativa | G_TESTES |
