(function () {
  "use strict";

  function copyIconSVG() {
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
  }

  function checkIconSVG() {
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  }

  function attachCopyButtons() {
    var blocks = document.querySelectorAll("pre > code");
    blocks.forEach(function (codeEl) {
      var pre = codeEl.parentElement;
      if (!pre || pre.dataset.copyReady === "1") return;
      pre.dataset.copyReady = "1";

      var wrapper = document.createElement("div");
      wrapper.className = "code-block";
      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(pre);

      var button = document.createElement("button");
      button.type = "button";
      button.className = "copy-btn";
      button.setAttribute("aria-label", "Copiar comando");
      button.innerHTML = copyIconSVG() + "<span>Copiar</span>";

      button.addEventListener("click", function () {
        var text = codeEl.textContent || "";
        var restore = function () {
          setTimeout(function () {
            button.classList.remove("copied");
            button.innerHTML = copyIconSVG() + "<span>Copiar</span>";
          }, 1600);
        };
        var markCopied = function () {
          button.classList.add("copied");
          button.innerHTML = checkIconSVG() + "<span>Copiado</span>";
          restore();
        };

        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(text).then(markCopied).catch(function () {
            fallbackCopy(text, markCopied);
          });
        } else {
          fallbackCopy(text, markCopied);
        }
      });

      wrapper.insertBefore(button, pre);
    });
  }

  function fallbackCopy(text, onDone) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand("copy");
      onDone();
    } catch (err) {
      /* Falha silenciosa: comando permanece selecionável manualmente. */
    }
    document.body.removeChild(textarea);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachCopyButtons);
  } else {
    attachCopyButtons();
  }
})();
