/**
 * UI Dialogs & Alerts - Componentes Nativos Compartilhados (Share)
 * Ecossistema AIDD - Substitui completamente alerts, confirms e dialogs do SO/Browser.
 */

(function () {
  // Injeta o container de Toast e o container de Modal no DOM caso nao existam
  function ensureDOMContainers() {
    if (!document.getElementById('aidd-toast-container')) {
      const toastContainer = document.createElement('div');
      toastContainer.id = 'aidd-toast-container';
      toastContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
        max-width: 380px;
        width: 100%;
      `;
      document.body.appendChild(toastContainer);
    }

    if (!document.getElementById('aidd-modal-container')) {
      const modalContainer = document.createElement('div');
      modalContainer.id = 'aidd-modal-container';
      modalContainer.style.cssText = `
        position: fixed;
        inset: 0;
        z-index: 99998;
        display: none;
        align-items: center;
        justify-content: center;
        background: rgba(2, 6, 23, 0.75);
        backdrop-filter: blur(8px);
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
      `;
      document.body.appendChild(modalContainer);
    }
  }

  const UIDialogs = {
    /**
     * Exibe notificacao Toast temporaria
     */
    toast: function ({ message, type = 'info', duration = 3500 }) {
      ensureDOMContainers();
      const container = document.getElementById('aidd-toast-container');
      const toast = document.createElement('div');

      const icons = {
        success: 'fa-circle-check text-emerald-400',
        error: 'fa-circle-xmark text-rose-400',
        warning: 'fa-triangle-exclamation text-amber-400',
        info: 'fa-circle-info text-indigo-400'
      };

      const borders = {
        success: 'border-emerald-500/30 bg-slate-900/95 text-slate-100',
        error: 'border-rose-500/30 bg-slate-900/95 text-slate-100',
        warning: 'border-amber-500/30 bg-slate-900/95 text-slate-100',
        info: 'border-indigo-500/30 bg-slate-900/95 text-slate-100'
      };

      toast.className = `p-4 rounded-xl border shadow-2xl flex items-center gap-3 transform translate-y-2 opacity-0 transition-all duration-300 pointer-events-auto ${borders[type] || borders.info}`;
      toast.innerHTML = `
        <i class="fa-solid ${icons[type] || icons.info} text-lg"></i>
        <div class="flex-1 text-xs font-medium leading-relaxed">${message}</div>
        <button class="text-slate-500 hover:text-slate-300 transition" onclick="this.parentElement.remove()">
          <i class="fa-solid fa-xmark text-xs"></i>
        </button>
      `;

      container.appendChild(toast);

      // Trigger animation
      requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
      });

      // Auto remove
      setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-2', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
      }, duration);
    },

    /**
     * Exibe Modal de Confirmacao nativo estilizado (Promise)
     */
    confirm: function ({
      title = 'Confirmar Ação',
      message = 'Você tem certeza que deseja prosseguir?',
      confirmText = 'Confirmar',
      cancelText = 'Cancelar',
      type = 'danger'
    }) {
      ensureDOMContainers();
      return new Promise((resolve) => {
        const container = document.getElementById('aidd-modal-container');

        const btnColors = {
          danger: 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30',
          primary: 'bg-brand-600 hover:bg-brand-500 text-white shadow-brand-600/30'
        };

        const iconHeader = {
          danger: '<div class="w-10 h-10 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center text-lg"><i class="fa-solid fa-triangle-exclamation"></i></div>',
          primary: '<div class="w-10 h-10 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 flex items-center justify-center text-lg"><i class="fa-solid fa-circle-question"></i></div>'
        };

        container.innerHTML = `
          <div class="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl transform scale-95 transition-all duration-200" id="aidd-modal-box">
            <div class="flex items-start gap-4 mb-4">
              ${iconHeader[type] || iconHeader.primary}
              <div class="flex-1">
                <h3 class="text-base font-bold text-white mb-1">${title}</h3>
                <p class="text-xs text-slate-400 leading-relaxed">${message}</p>
              </div>
            </div>
            <div class="flex items-center justify-end gap-3 mt-6">
              <button id="aidd-modal-cancel" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
                ${cancelText}
              </button>
              <button id="aidd-modal-confirm" class="px-4 py-2 text-xs font-semibold rounded-xl ${btnColors[type] || btnColors.primary} shadow-lg transition">
                ${confirmText}
              </button>
            </div>
          </div>
        `;

        container.style.display = 'flex';
        requestAnimationFrame(() => {
          container.style.opacity = '1';
          const box = document.getElementById('aidd-modal-box');
          if (box) box.classList.remove('scale-95');
        });

        function fechar(resultado) {
          container.style.opacity = '0';
          const box = document.getElementById('aidd-modal-box');
          if (box) box.classList.add('scale-95');
          setTimeout(() => {
            container.style.display = 'none';
            container.innerHTML = '';
            document.removeEventListener('keydown', onKeyDown);
            resolve(resultado);
          }, 200);
        }

        function onKeyDown(e) {
          if (e.key === 'Escape') fechar(false);
        }

        document.getElementById('aidd-modal-cancel').onclick = () => fechar(false);
        document.getElementById('aidd-modal-confirm').onclick = () => fechar(true);
        document.addEventListener('keydown', onKeyDown);
      });
    }
  };

  window.UIDialogs = UIDialogs;
})();
