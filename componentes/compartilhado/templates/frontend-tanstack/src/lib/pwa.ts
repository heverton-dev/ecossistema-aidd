import { useEffect, useState } from "react";

export function registrarServiceWorker(swPath = "/sw.js"): void {
  if (typeof window !== "undefined" && "serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register(swPath)
        .then((reg) => {
          console.debug("[AIDD-PWA] Service Worker registrado:", reg.scope);
        })
        .catch((err) => {
          console.debug("[AIDD-PWA] Erro ao registrar Service Worker:", err);
        });
    });
  }
}

export function usePwaInstalacao() {
  const [instalavel, setInstalavel] = useState(false);
  const [instalado, setInstalado] = useState(false);
  const [promptDeferred, setPromptDeferred] = useState<any>(null);

  useEffect(() => {
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setPromptDeferred(e);
      setInstalavel(true);
    };

    const handleAppInstalled = () => {
      setPromptDeferred(null);
      setInstalavel(false);
      setInstalado(true);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const instalar = async () => {
    if (!promptDeferred) return false;
    promptDeferred.prompt();
    const { outcome } = await promptDeferred.userChoice;
    setPromptDeferred(null);
    setInstalavel(false);
    return outcome === "accepted";
  };

  return { instalavel, instalado, instalar };
}
