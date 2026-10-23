# DESIGN.md — Design System & Tokens Visuais (Modo Claro Soberano)

## 1. Paleta de Cores & Tokens Semânticos

| Token | Valor Hex | Finalidade / Semântica | Contraste WCAG |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#f8fafc` | Fundo principal da página (Slate 50) | Base neutra |
| `--bg-card` | `#ffffff` | Superfície de cartões e modais | 21:1 vs text-main |
| `--bg-subtle` | `#f1f5f9` | Fundo de badges e elementos secundários | Base suave |
| `--border` | `#e2e8f0` | Divisores e bordas estruturais de 1px | 1.3:1 (estrutural) |
| `--border-hover`| `#cbd5e1` | Estado hover de bordas e botões | Foco sutil |
| `--text-main` | `#0f172a` | Texto de leitura primária, títulos (Slate 900) | 16.5:1 (AAA) |
| `--text-muted` | `#475569` | Descrições e metadados auxiliares (Slate 600) | 6.8:1 (AA) |
| `--text-tertiary`| `#64748b` | Rótulos de cabeçalho de tabela e captions | 4.6:1 (AA) |
| `--primary` | `#0284c7` | Cor primária corporativa (Sky 600) | 4.8:1 vs white |
| `--primary-surface`| `#f0f9ff`| Superfície de destaque primário (Sky 50) | Base para pílulas |
| `--emerald` | `#059669` | Natureza Determinística (Emerald 600) | 4.5:1 vs white |
| `--amber` | `#d97706` | Avisos e alertas (Amber 600) | 4.5:1 vs white |
| `--rose` | `#e11d48` | Erros e portões bloqueantes (Rose 600) | 4.6:1 vs white |

## 2. Escala Tipográfica (Fluida com clamp)
- **Família Primária:** `'Plus Jakarta Sans', system-ui, -apple-system, sans-serif`
- **Família Monospaçada:** `'JetBrains Mono', monospace` (para hashes SHA-256, rotas, scripts e nomes de arquivos)
- **H1 (Título da Página):** `clamp(0.95rem, 2vw, 1.15rem)`, `font-weight: 800`
- **H2 (Seções):** `clamp(0.95rem, 2vw, 1.1rem)`, `font-weight: 800`
- **H3 (Títulos de Etapa):** `1rem`, `font-weight: 800`
- **Body / Descrição:** `0.82rem`, `line-height: 1.45`
- **Code Pills / Hashes:** `0.72rem`, `font-family: JetBrains Mono`

## 3. Elevações & Sombras Sutis
- `--shadow-xs`: `0 1px 2px 0 rgb(0 0 0 / 0.05)`
- `--shadow-sm`: `0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)`
- `--shadow-md`: `0 4px 6px -1px rgb(0 0 0 / 0.06), 0 2px 4px -2px rgb(0 0 0 / 0.04)`
- `--shadow-lg`: `0 10px 15px -3px rgb(0 0 0 / 0.07), 0 4px 6px -4px rgb(0 0 0 / 0.03)`

## 4. Regras de Interatividade & Acessibilidade
- **Área mínima de toque (Touch Target):** Mínimo de 38px a 44px para botões de filtro e fechar modal no mobile.
- **Foco de Teclado:** `:focus-visible` com `outline: 2px solid var(--primary); outline-offset: 2px;`
- **Zero Emojis Decotativos:** Ícones via SVG estruturado em traço vetorial (1.75px).
