# 💎 Impeccable Design System & Frontend Standards (AIDD v4)

O padrão **Impeccable** estabelece os requisitos inegociáveis de Engenharia de Interface e Experiência do Usuário (UI/UX) para todas as aplicações geradas pelo AIDD v4.

---

## 🏛️ 1. Regras Fundamentais de UI/UX

1. **Regra Zero Emojis:** Nunca utilize emojis em botões, títulos, cards, modais ou badges de interface. Utilize **exclusivamente ícones vetoriais SVG** (padrão Lucide / Heroicons) e tipografia pura.
2. **Zero Alertas Nativos do SO:** Nenhuma aplicação deve chamar `window.alert()`, `window.confirm()` ou diálogos do Windows. Utilize o subsistema de feedback nativo (`showToast()`, `showConfirm()`) do shared kernel.
3. **Header Imutável de Linha Única:** O header da aplicação jamais pode quebrar em duas linhas ou sobrepor elementos. Deve possuir `white-space: nowrap`, `min-height: 56px`/`60px`, `overflow-x: auto` e `flex-shrink: 0` para todos os componentes internos (Brand, App Switcher e Action Buttons).
4. **Scrollbars Padronizadas de 4px:** Todas as barras de rolagem da aplicação (janela, tabelas, modais, sidebar) devem possuir no máximo 4 pixels de largura/altura e utilizar a cor do design system (`rgba(59, 130, 246, 0.35)`).
5. **Botões em Linha Única:** Todo botão, link de navegação ou aba de status possui `white-space: nowrap !important; line-height: 1.2; display: inline-flex; align-items: center; justify-content: center;` impedindo quebra de texto.
6. **Responsividade Fluida:** Todas as tabelas e grids de dados são envolvidos em containers com rolagem horizontal de 4px, garantindo visualização impecável de telas móveis a monitores ultrawide.

---

## 📐 2. Escala Tipográfica Padronizada

| Nível | Tamanho | Peso | Uso Obrigatório |
| :--- | :--- | :--- | :--- |
| **`--text-2xl`** | `1.85rem` (29.6px) | 800 | Título da página principal, valores de KPI Cards |
| **`--text-xl`** | `1.45rem` (23.2px) | 800 | Títulos H2 de fatias verticais e módulos |
| **`--text-lg`** | `1.15rem` (18.4px) | 800 | Cabeçalhos de Cards e Modais |
| **`--text-md`** | `0.98rem` (15.6px) | 700 / 600 | Subtítulos e descrições de seção |
| **`--text-base`** | `0.88rem` (14.0px) | 500 / 600 | Texto de células de tabelas e corpo de parágrafos |
| **`--text-sm`** | `0.82rem` (13.1px) | 700 / 600 | Botões (`.btn`), inputs de formulário, breadcrumbs |
| **`--text-xs`** | `0.72rem` (11.5px) | 800 | Badges de status, tags de categorias, labels de apoio |
| **`--font-mono`** | `0.80rem` (12.8px) | 600 | Códigos de rastreio, JSON, endpoints e dados técnicos |

---

## 🎨 3. Paleta de Cores & Glassmorphism

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
