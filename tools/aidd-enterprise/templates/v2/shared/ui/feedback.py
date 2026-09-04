"""
Design System & Feedback Components (Toast, Confirm Dialog, Modal)
Garante que nenhuma aplicação gerada utilize alerts/confirms nativos do sistema operacional ou do navegador.
"""

def get_feedback_css() -> str:
    return """
/* =========================================================================
   DESIGN SYSTEM UNIVERSAL (SCROLLBAR 4PX & BUTTON WRAP PROTECTION)
   ========================================================================= */
* {
    scrollbar-width: thin;
    scrollbar-color: rgba(59, 130, 246, 0.4) transparent;
}

::-webkit-scrollbar {
    width: 4px !important;
    height: 4px !important;
}

::-webkit-scrollbar-track {
    background: transparent !important;
}

::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.35) !important;
    border-radius: 9999px !important;
    transition: background 0.2s ease !important;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.75) !important;
}

/* Proteção de Quebra de Linha em Todos os Botões */
button, .btn, .btn-primary, .btn-secondary, .btn-gold, .btn-danger,
.tab-btn, .resp-status-btn, .lang-tab, .endpoint-link {
    white-space: nowrap !important;
    text-overflow: ellipsis;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    line-height: 1.2 !important;
}

/* =========================================================================
   TOAST NOTIFICATION CONTAINER (HIGH-END GLASSMORPHISM)
   ========================================================================= */
#aidd-toast-container {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    z-index: 99999;
    pointer-events: none;
}

.aidd-toast {
    pointer-events: auto;
    min-width: 280px;
    max-width: 420px;
    background: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    color: #f8fafc;
    font-size: 0.86rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6);
    transform: translateY(20px) scale(0.95);
    opacity: 0;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.aidd-toast.show {
    transform: translateY(0) scale(1);
    opacity: 1;
}

.aidd-toast-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.aidd-toast.toast-success { border-color: rgba(16, 185, 129, 0.4); }
.aidd-toast.toast-success .aidd-toast-icon { color: #34d399; }

.aidd-toast.toast-error { border-color: rgba(239, 68, 68, 0.4); }
.aidd-toast.toast-error .aidd-toast-icon { color: #f87171; }

.aidd-toast.toast-warning { border-color: rgba(245, 158, 11, 0.4); }
.aidd-toast.toast-warning .aidd-toast-icon { color: #fbbf24; }

.aidd-toast.toast-info { border-color: rgba(59, 130, 246, 0.4); }
.aidd-toast.toast-info .aidd-toast-icon { color: #60a5fa; }

/* =========================================================================
   CUSTOM CONFIRM & ALERT MODAL (DESIGN SYSTEM INTEGRATED)
   ========================================================================= */
#aidd-dialog-overlay {
    position: fixed;
    inset: 0;
    background: rgba(3, 7, 18, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 99998;
    opacity: 0;
    transition: opacity 0.2s ease;
}

#aidd-dialog-overlay.show {
    display: flex;
    opacity: 1;
}

.aidd-dialog-card {
    background: #0b1329;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    width: 100%;
    max-width: 440px;
    padding: 1.8rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    transform: scale(0.95);
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

#aidd-dialog-overlay.show .aidd-dialog-card {
    transform: scale(1);
}

.aidd-dialog-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.aidd-dialog-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #fff;
}

.aidd-dialog-msg {
    font-size: 0.9rem;
    color: #94a3b8;
    line-height: 1.6;
}

.aidd-dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 0.5rem;
}
"""

def get_feedback_js() -> str:
    return """
// =========================================================================
// FEEDBACK UI ENGINE (TOASTS, MODAL CONFIRM & OS DIALOG OVERRIDES)
// =========================================================================
(function() {
    // 1. Criar container de Toasts se não existir
    let toastContainer = document.getElementById('aidd-toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'aidd-toast-container';
        document.body.appendChild(toastContainer);
    }

    // 2. Criar overlay de Diálogo Customizado se não existir
    let dialogOverlay = document.getElementById('aidd-dialog-overlay');
    if (!dialogOverlay) {
        dialogOverlay = document.createElement('div');
        dialogOverlay.id = 'aidd-dialog-overlay';
        dialogOverlay.innerHTML = `
            <div class="aidd-dialog-card">
                <div class="aidd-dialog-header">
                    <div id="aidd-dialog-icon"></div>
                    <div class="aidd-dialog-title" id="aidd-dialog-title">Confirmação</div>
                </div>
                <div class="aidd-dialog-msg" id="aidd-dialog-msg">Deseja prosseguir com esta ação?</div>
                <div class="aidd-dialog-actions">
                    <button class="btn" id="aidd-dialog-btn-cancel" style="background: rgba(255,255,255,0.05); color: #cbd5e1;">Cancelar</button>
                    <button class="btn btn-primary" id="aidd-dialog-btn-confirm" style="background: #3b82f6; border-color: #3b82f6;">Confirmar</button>
                </div>
            </div>
        `;
        document.body.appendChild(dialogOverlay);
    }

    const ICONS_MAP = {
        success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`,
        error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
        warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
        info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`
    };

    // Função Global de Toast
    window.showToast = function(message, type = 'info', duration = 3500) {
        const toast = document.createElement('div');
        toast.className = `aidd-toast toast-${type}`;
        
        const iconDiv = document.createElement('div');
        iconDiv.className = 'aidd-toast-icon';
        iconDiv.innerHTML = ICONS_MAP[type] || ICONS_MAP.info;

        const textSpan = document.createElement('span');
        textSpan.textContent = message;

        toast.appendChild(iconDiv);
        toast.appendChild(textSpan);
        toastContainer.appendChild(toast);

        // Animação de Entrada
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto dismiss
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 300);
        }, duration);
    };

    // Função Global de Diálogo / Confirmação Promise-based
    window.showConfirm = function(title, message, isDanger = false) {
        return new Promise((resolve) => {
            const overlay = document.getElementById('aidd-dialog-overlay');
            const titleEl = document.getElementById('aidd-dialog-title');
            const msgEl = document.getElementById('aidd-dialog-msg');
            const iconEl = document.getElementById('aidd-dialog-icon');
            const btnCancel = document.getElementById('aidd-dialog-btn-cancel');
            const btnConfirm = document.getElementById('aidd-dialog-btn-confirm');

            titleEl.textContent = title || 'Confirmação';
            msgEl.textContent = message || 'Deseja confirmar esta operação?';
            
            iconEl.innerHTML = isDanger ? ICONS_MAP.warning : ICONS_MAP.info;
            iconEl.style.color = isDanger ? '#f87171' : '#60a5fa';

            if (isDanger) {
                btnConfirm.style.background = '#ef4444';
                btnConfirm.style.borderColor = '#ef4444';
            } else {
                btnConfirm.style.background = '#3b82f6';
                btnConfirm.style.borderColor = '#3b82f6';
            }

            overlay.style.display = 'flex';
            requestAnimationFrame(() => overlay.classList.add('show'));

            function cleanup() {
                overlay.classList.remove('show');
                setTimeout(() => { overlay.style.display = 'none'; }, 200);
                btnConfirm.onclick = null;
                btnCancel.onclick = null;
            }

            btnConfirm.onclick = () => { cleanup(); resolve(true); };
            btnCancel.onclick = () => { cleanup(); resolve(false); };
        });
    };

    // Substituição Total de alert() do navegador
    window.alert = function(msg) {
        window.showToast(msg, 'info');
    };
})();
"""
