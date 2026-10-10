/**
 * QUADRO AIDD · MOTOR INTERATIVO JAVASCRIPT AVANÇADO
 * Padrão Impeccable (Craft Floor) | Vanilla JS Seguro (Zero Deps, Zero XSS)
 * Recursos Operacionais:
 * 1. Copiar Rápido no Hover (Direct Card Action)
 * 2. Cronômetro Vivo no Card (Live Elapsed Time)
 * 3. Busca Rápida por Tecla '/' (Instant Query Filter)
 * 4. Notificações Desktop Nativas (Web Notifications API)
 * 5. Telemetria de Custos & Tokens (Factual Token Metrics)
 */

const ESTADO_GLOBAL = {
  abaAtiva: "pipelines",
  pipelineSelecionado: null,
  cartaoSelecionado: null,
  dadosPipelines: {},
  tema: localStorage.getItem("aidd_quadro_tema") || "escuro",
  cachePipelinesJson: "",
  cacheKanbanJson: "",
  filtroPipelines: "",
  filtroKanban: "",
  notificacoesAtivas: localStorage.getItem("aidd_quadro_notificacoes") === "1",
  notificacoesEmitidas: new Set(),
  somAtivo: localStorage.getItem("aidd_quadro_som") === "1",
  intervaloLogtail: null,
  logtailOffset: 0,
  logtailRunId: null,
  logtailAutoScroll: true,
  dadosGates: [],
  dadosWorktrees: []
};

// ==========================================
// 1. GESTÃO DE TEMA (DARK / LIGHT)
// ==========================================
function aplicarTema(tema) {
  ESTADO_GLOBAL.tema = tema;
  localStorage.setItem("aidd_quadro_tema", tema);
  if (tema === "claro") {
    document.documentElement.setAttribute("data-tema", "claro");
  } else {
    document.documentElement.removeAttribute("data-tema");
  }
}

function alternarTema() {
  const novo = ESTADO_GLOBAL.tema === "claro" ? "escuro" : "claro";
  aplicarTema(novo);
  tocarSom("clique");
}

// ==========================================
// 1.1 SÍNTESE DE ÁUDIO NATIVA (WEB AUDIO API)
// ==========================================
let _audioCtx = null;
function obterAudioContext() {
  if (!_audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) _audioCtx = new AudioContextClass();
  }
  if (_audioCtx && _audioCtx.state === "suspended") {
    _audioCtx.resume();
  }
  return _audioCtx;
}

function tocarSom(tipo) {
  if (!ESTADO_GLOBAL.somAtivo) return;
  try {
    const ctx = obterAudioContext();
    if (!ctx) return;
    const t = ctx.currentTime;

    if (tipo === "sucesso") {
      // Acorde suave C5 -> E5 -> G5
      [523.25, 659.25, 783.99].forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, t + idx * 0.08);
        gain.gain.setValueAtTime(0.08, t + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, t + idx * 0.08 + 0.45);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t + idx * 0.08);
        osc.stop(t + idx * 0.08 + 0.5);
      });
    } else if (tipo === "falha") {
      // Tom grave descendente de alerta
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(220, t);
      osc.frequency.exponentialRampToValueAtTime(110, t + 0.35);
      gain.gain.setValueAtTime(0.12, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.45);
    } else if (tipo === "clique") {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(600, t);
      gain.gain.setValueAtTime(0.04, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.06);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.07);
    }
  } catch (e) {
    // Silencioso em caso de restrição do navegador
  }
}

function alternarSom() {
  ESTADO_GLOBAL.somAtivo = !ESTADO_GLOBAL.somAtivo;
  localStorage.setItem("aidd_quadro_som", ESTADO_GLOBAL.somAtivo ? "1" : "0");
  atualizarIconeSom();
  if (ESTADO_GLOBAL.somAtivo) tocarSom("sucesso");
}

function atualizarIconeSom() {
  const btn = document.getElementById("btn-som");
  if (!btn) return;
  btn.style.opacity = ESTADO_GLOBAL.somAtivo ? "1" : "0.5";
  btn.title = ESTADO_GLOBAL.somAtivo ? "Som ativado (clique para mutar)" : "Som desativado (clique para ativar)";
}

// ==========================================
// 2. NOTIFICAÇÕES DESKTOP NATIVAS (RECURSO #4)
// ==========================================
async function alternarNotificacoes() {
  if (!("Notification" in window)) {
    alert("Seu navegador não suporta notificações de desktop.");
    return;
  }

  if (Notification.permission === "granted") {
    ESTADO_GLOBAL.notificacoesAtivas = !ESTADO_GLOBAL.notificacoesAtivas;
  } else if (Notification.permission !== "denied") {
    const perm = await Notification.requestPermission();
    ESTADO_GLOBAL.notificacoesAtivas = (perm === "granted");
  } else {
    alert("Notificações estão bloqueadas no navegador. Permita nas configurações de site.");
    ESTADO_GLOBAL.notificacoesAtivas = false;
  }

  localStorage.setItem("aidd_quadro_notificacoes", ESTADO_GLOBAL.notificacoesAtivas ? "1" : "0");
  atualizarIconeNotificacao();
  tocarSom("clique");
}

function atualizarIconeNotificacao() {
  const btn = document.getElementById("btn-notificacao");
  if (!btn) return;
  const ativa = ESTADO_GLOBAL.notificacoesAtivas && Notification.permission === "granted";
  btn.classList.toggle("notificacao-ativa", ativa);
  btn.title = ativa ? "Notificações ativas (alertas para aprovação e falhas)" : "Ativar notificações desktop";
}

function emitirNotificacaoSeNecessario(titulo, corpo, idUnico) {
  if (!ESTADO_GLOBAL.notificacoesAtivas || Notification.permission !== "granted") return;
  if (ESTADO_GLOBAL.notificacoesEmitidas.has(idUnico)) return;

  ESTADO_GLOBAL.notificacoesEmitidas.add(idUnico);
  try {
    new Notification(titulo, {
      body: corpo,
      tag: idUnico
    });
    tocarSom("falha");
  } catch (e) {
    console.warn("Falha ao emitir notificação desktop:", e);
  }
}

// ==========================================
// 3. NAVEGAÇÃO DE ABAS
// ==========================================
function mudarAba(aba) {
  ESTADO_GLOBAL.abaAtiva = aba;
  tocarSom("clique");
  
  const abas = ["pipelines", "gates", "worktrees", "arquivo"];
  abas.forEach(nome => {
    const btn = document.getElementById(`aba-${nome}`);
    const sec = document.getElementById(`secao-${nome}`);
    if (btn) btn.classList.toggle("ativa", aba === nome);
    if (sec) sec.classList.toggle("escondido", aba !== nome);
  });

  if (aba === "arquivo") {
    carregarArquivo();
    preencherFiltrosArquivo();
  } else if (aba === "gates") {
    carregarGates();
  } else if (aba === "worktrees") {
    carregarWorktrees();
  }
}

// ==========================================
// 4. SINCRONIZAÇÃO E BUSCA DE DADOS
// ==========================================
async function atualizarDados() {
  const indicadorPulso = document.getElementById("indicador-pulso");
  const textoAtualizacao = document.getElementById("texto-atualizacao");
  const badgeContagem = document.getElementById("contagem-pipelines-ativos");

  try {
    const res = await fetch("/api/pipelines");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const json = await res.json();
    ESTADO_GLOBAL.dadosPipelines = json.pipelines || {};

    let totalAtivos = 0;
    for (const [idPipe, info] of Object.entries(ESTADO_GLOBAL.dadosPipelines)) {
      if ((info.executando || 0) > 0) totalAtivos++;
      if ((info.precisa_humano || 0) > 0) {
        emitirNotificacaoSeNecessario(
          "AIDD · Ação Humana Necessária",
          `O pipeline "${info.nome || idPipe}" está aguardando sua intervenção.`,
          `humano-${idPipe}-${info.precisa_humano}`
        );
      }
    }
    if (badgeContagem) badgeContagem.textContent = totalAtivos;

    renderizarPipelines();

    if (ESTADO_GLOBAL.pipelineSelecionado) {
      await carregarKanban(ESTADO_GLOBAL.pipelineSelecionado);
    }

    if (textoAtualizacao) textoAtualizacao.textContent = "Ao vivo";
    if (indicadorPulso) {
      indicadorPulso.classList.remove("desconectado");
      indicadorPulso.style.opacity = "1";
    }
  } catch (e) {
    if (textoAtualizacao) textoAtualizacao.textContent = "Desconectado";
    if (indicadorPulso) {
      indicadorPulso.classList.add("desconectado");
      indicadorPulso.style.opacity = "0.7";
    }
  }
}

// ==========================================
// 5. RENDERIZAÇÃO DA GRADE DE PIPELINES
// ==========================================
function renderizarPipelines() {
  const container = document.getElementById("grade-pipelines");
  if (!container || ESTADO_GLOBAL.pipelineSelecionado) return;

  const strDados = JSON.stringify(ESTADO_GLOBAL.dadosPipelines);
  if (strDados === ESTADO_GLOBAL.cachePipelinesJson && !ESTADO_GLOBAL.filtroPipelines) return;
  ESTADO_GLOBAL.cachePipelinesJson = strDados;

  container.replaceChildren();

  const termo = (ESTADO_GLOBAL.filtroPipelines || "").trim().toLowerCase();
  let encontrados = 0;

  for (const [id, info] of Object.entries(ESTADO_GLOBAL.dadosPipelines)) {
    const nome = (info.nome || id).toLowerCase();
    const cmd = (info.comando || "").toLowerCase();
    if (termo && !nome.includes(termo) && !id.toLowerCase().includes(termo) && !cmd.includes(termo)) {
      continue;
    }
    encontrados++;

    const card = document.createElement("article");
    const temExecutando = (info.executando || 0) > 0;
    const temFalha = (info.falhou || 0) > 0;
    card.className = "card-pipeline" + (temExecutando ? " card-ativo" : "") + (temFalha ? " card-falha" : "");
    card.tabIndex = 0;
    card.onclick = () => abrirKanban(id);
    card.onkeydown = (e) => { if (e.key === "Enter") abrirKanban(id); };

    const topo = document.createElement("div");
    topo.className = "card-pipeline-topo";

    const tit = document.createElement("h3");
    tit.className = "card-pipeline-titulo";
    tit.textContent = info.nome || id;
    topo.appendChild(tit);

    // Destaque sutil da Tríade Canônica
    if (["pure", "open", "freedom"].includes(id)) {
      const tagTriade = document.createElement("span");
      tagTriade.className = "badge-triade";
      tagTriade.textContent = id === "pure" ? "Tríade #1" : (id === "open" ? "Tríade #2" : "Tríade #3");
      topo.appendChild(tagTriade);
    }

    if (info.precisa_humano > 0) {
      const alerta = document.createElement("span");
      alerta.className = "badge-alerta";
      alerta.textContent = `⚠ ${info.precisa_humano} precisa de você`;
      topo.appendChild(alerta);
    }
    card.appendChild(topo);

    // CENTRO DO CARD: ETAPA ATUAL & BARRA DE PROGRESSO
    const centro = document.createElement("div");
    centro.className = "card-pipeline-centro";

    const etapaInfo = document.createElement("div");
    etapaInfo.className = "card-etapa-info";

    const etapaRotulo = document.createElement("span");
    etapaRotulo.className = "card-etapa-rotulo";
    etapaRotulo.textContent = "Etapa:";
    etapaInfo.appendChild(etapaRotulo);

    const etapaNome = document.createElement("span");
    etapaNome.className = "card-etapa-nome";

    const listaEtapas = Object.keys(info.etapas_contagem || {});
    const totalEtapas = listaEtapas.length || 7;
    let pctProgresso = 0;
    let estiloBarra = "neutro";

    if (info.executando > 0) {
      if (info.gate_atual) {
        etapaNome.textContent = `Gate: ${info.gate_atual} ${info.progresso_gates ? '(' + info.progresso_gates + ')' : ''}`;
        etapaNome.classList.add("executando");
        pctProgresso = info.percentual !== undefined ? info.percentual : 50;
        estiloBarra = "executando";
      } else {
        let etapaAtiva = null;
        let idxEtapa = -1;
        for (let i = 0; i < listaEtapas.length; i++) {
          const k = listaEtapas[i];
          if ((info.etapas_contagem[k] || 0) > 0) {
            etapaAtiva = k;
            idxEtapa = i;
          }
        }
        const nomeEtapaFormatado = etapaAtiva 
          ? (etapaAtiva.charAt(0).toUpperCase() + etapaAtiva.slice(1)).replace(/-/g, " ")
          : "Em andamento";
        etapaNome.textContent = nomeEtapaFormatado;
        etapaNome.classList.add("executando");
        pctProgresso = idxEtapa >= 0 ? Math.round(((idxEtapa + 1) / totalEtapas) * 100) : 50;
        estiloBarra = "executando";
      }
    } else if (info.falhou > 0) {
      etapaNome.textContent = "Falha detectada";
      etapaNome.classList.add("falhou");
      pctProgresso = 100;
      estiloBarra = "falhou";
    } else if (info.concluido > 0) {
      etapaNome.textContent = "Todas concluídas";
      etapaNome.classList.add("concluido");
      pctProgresso = 100;
      estiloBarra = "concluido";
    } else {
      etapaNome.textContent = "Aguardando disparo";
      pctProgresso = 0;
      estiloBarra = "neutro";
    }
    etapaInfo.appendChild(etapaNome);
    centro.appendChild(etapaInfo);

    const trilhaProg = document.createElement("div");
    trilhaProg.className = "card-progresso-trilha";
    const barraProg = document.createElement("div");
    barraProg.className = `card-progresso-barra ${estiloBarra}`;
    barraProg.style.width = `${pctProgresso}%`;
    trilhaProg.appendChild(barraProg);
    centro.appendChild(trilhaProg);

    card.appendChild(centro);

    // RODAPÉ: RODANDO -> CONCLUÍDOS -> FALHAS
    const metricas = document.createElement("div");
    metricas.className = "pipeline-metricas";

    const spanExec = document.createElement("span");
    spanExec.className = "metrica-tag" + (info.executando > 0 ? " executando" : "");
    spanExec.textContent = `${info.executando || 0} rodando`;

    const spanConc = document.createElement("span");
    spanConc.className = "metrica-tag" + (info.concluido > 0 ? " concluido" : "");
    spanConc.textContent = `${info.concluido || 0} concluídos`;

    const spanFalha = document.createElement("span");
    spanFalha.className = "metrica-tag" + (info.falhou > 0 ? " falha" : "");
    spanFalha.textContent = `${info.falhou || 0} falhas`;

    metricas.appendChild(spanExec);
    metricas.appendChild(spanConc);
    metricas.appendChild(spanFalha);
    card.appendChild(metricas);

    container.appendChild(card);
  }

  if (encontrados === 0 && termo) {
    const vazio = document.createElement("div");
    vazio.className = "estado-vazio-tabela";
    vazio.style.gridColumn = "1 / -1";
    vazio.textContent = `Nenhum pipeline encontrado para "${ESTADO_GLOBAL.filtroPipelines}".`;
    container.appendChild(vazio);
  }
}

// ==========================================
// 6. KANBAN DA EXECUÇÃO ESPECÍFICA
// ==========================================
async function abrirKanban(pipeId) {
  ESTADO_GLOBAL.pipelineSelecionado = pipeId;
  ESTADO_GLOBAL.filtroKanban = "";
  ESTADO_GLOBAL.cacheKanbanJson = "";
  
  const cKanban = document.getElementById("campo-busca-kanban");
  if (cKanban) cKanban.value = "";

  const grade = document.getElementById("grade-pipelines");
  const kanban = document.getElementById("kanban-container");
  
  if (grade) grade.classList.add("escondido");
  if (kanban) kanban.classList.remove("escondido");

  const bannerTexto = document.getElementById("texto-fluxo-ativo");
  const bannerEl = document.getElementById("banner-fluxo-ativo");
  if (bannerTexto) bannerTexto.textContent = `FLUXO ATIVO: ${pipeId.toUpperCase()}`;
  if (bannerEl) bannerEl.classList.add("executando");
  
  await carregarKanban(pipeId);
}

function fecharKanban() {
  ESTADO_GLOBAL.pipelineSelecionado = null;
  ESTADO_GLOBAL.filtroKanban = "";
  ESTADO_GLOBAL.cacheKanbanJson = "";

  const cKanban = document.getElementById("campo-busca-kanban");
  if (cKanban) cKanban.value = "";

  const grade = document.getElementById("grade-pipelines");
  const kanban = document.getElementById("kanban-container");
  
  if (kanban) kanban.classList.add("escondido");
  if (grade) grade.classList.remove("escondido");

  const bannerTexto = document.getElementById("texto-fluxo-ativo");
  const bannerEl = document.getElementById("banner-fluxo-ativo");
  if (bannerTexto) bannerTexto.textContent = "TODOS OS PIPELINES";
  if (bannerEl) bannerEl.classList.remove("executando");
  
  renderizarPipelines();
}

async function carregarKanban(pipeId) {
  try {
    const res = await fetch(`/api/pipeline/${pipeId}`);
    if (!res.ok) return;
    const dados = await res.json();

    const bannerTexto = document.getElementById("texto-fluxo-ativo");
    const badgeStatus = document.getElementById("kanban-badge-status");
    if (bannerTexto) bannerTexto.textContent = `FLUXO ATIVO: ${(dados.nome || pipeId).toUpperCase()}`;
    if (badgeStatus) badgeStatus.textContent = `● FLUXO ATIVO: ${(dados.nome || pipeId).toUpperCase()}`;

    // Atualizar iluminação da esteira topológica visual de 7 etapas
    const passosEsteira = document.querySelectorAll(".passo-esteira[data-passo]");
    const etapasAtivas = new Set((dados.execucoes || []).filter(e => e.status === "executando").map(e => e.etapa_atual));
    passosEsteira.forEach(p => {
      const passoId = p.getAttribute("data-passo");
      if (etapasAtivas.has(passoId)) {
        p.classList.add("passo-ativo");
      } else {
        p.classList.remove("passo-ativo");
      }
    });

    // Cache inteligente de dados
    const strDados = JSON.stringify(dados);
    if (strDados === ESTADO_GLOBAL.cacheKanbanJson && !ESTADO_GLOBAL.filtroKanban) {
      atualizarCronometros();
      return;
    }

    const titEl = document.getElementById("kanban-titulo");
    const cmdEl = document.getElementById("kanban-comando");
    if (titEl) titEl.textContent = dados.nome || pipeId;
    if (cmdEl) cmdEl.textContent = dados.comando || "-";

    const trilha = document.getElementById("kanban-colunas");
    if (!trilha) return;

    // Preservar posições de rolagem
    const posicoesScroll = {};
    const corposAtuais = trilha.querySelectorAll(".coluna-corpo[data-coluna-id]");
    corposAtuais.forEach(c => {
      posicoesScroll[c.getAttribute("data-coluna-id")] = c.scrollTop;
    });
    const scrollTrilhaX = trilha.scrollLeft;

    trilha.replaceChildren();

    // Etapas contratuais + dinâmicas
    const etapasDeclaradas = [...(dados.etapas || [])];
    const idsEtapas = new Set(etapasDeclaradas.map(e => e.id));

    for (const ex of dados.execucoes || []) {
      const etId = ex.etapa_atual;
      if (etId && !idsEtapas.has(etId) && !["fila", "concluido", "falhou", "cancelado", "interrompido"].includes(etId)) {
        etapasDeclaradas.push({ id: etId, titulo: etId.charAt(0).toUpperCase() + etId.slice(1) });
        idsEtapas.add(etId);
      }
    }

    if (etapasDeclaradas.length === 0) {
      etapasDeclaradas.push({ id: "executando", titulo: "Em Execução" });
    }

    const colunasDef = [
      { id: "fila", titulo: "Fila" },
      ...etapasDeclaradas.map(et => ({ id: et.id, titulo: et.titulo || et.id })),
      { id: "concluido", titulo: "Concluído" },
      { id: "parado", titulo: "Parado" }
    ];

    const barraAtalhos = document.getElementById("kanban-atalhos-colunas");
    if (barraAtalhos) barraAtalhos.replaceChildren();

    const termoBusca = (ESTADO_GLOBAL.filtroKanban || "").trim().toLowerCase();
    let colunaComFoco = null;

    for (const col of colunasDef) {
      const elCol = document.createElement("div");
      elCol.className = "kanban-coluna";
      elCol.id = `coluna-alvo-${col.id}`;

      // Filtrar cartões pertencentes à coluna
      const cartoes = (dados.execucoes || []).filter(ex => {
        let pertence = false;
        if (col.id === "fila") pertence = (ex.status === "fila");
        else if (col.id === "concluido") pertence = (ex.status === "concluido");
        else if (col.id === "parado") pertence = ["falhou", "cancelado", "interrompido"].includes(ex.status);
        else if (col.id === "executando" && (!ex.etapa_atual || ex.etapa_atual === "executando")) pertence = (ex.status === "executando");
        else pertence = (ex.etapa_atual === col.id && ex.status === "executando");

        if (!pertence) return false;

        if (termoBusca) {
          const tit = (ex.titulo || "").toLowerCase();
          const chv = (ex.chave || "").toLowerCase();
          const pid = String(ex.processo?.pid || "");
          return tit.includes(termoBusca) || chv.includes(termoBusca) || pid.includes(termoBusca);
        }
        return true;
      });

      // Adicionar chip na barra de atalhos rápidos
      if (barraAtalhos) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip-coluna-atalho" + 
          (cartoes.length > 0 ? " com-cartoes" : "") + 
          (col.id === "concluido" && cartoes.length > 0 ? " concluidos-destaque" : "");
        chip.title = `Rolar até a coluna ${col.titulo} (${cartoes.length} execuções)`;
        chip.onclick = () => {
          elCol.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
        };

        const chipTxt = document.createElement("span");
        chipTxt.textContent = col.titulo;
        chip.appendChild(chipTxt);

        const chipBadge = document.createElement("span");
        chipBadge.className = "chip-badge";
        chipBadge.textContent = cartoes.length;
        chip.appendChild(chipBadge);

        barraAtalhos.appendChild(chip);
      }

      if (cartoes.length > 0 && !colunaComFoco) {
        colunaComFoco = elCol;
      }

      const topo = document.createElement("div");
      topo.className = "coluna-topo";

      const titCol = document.createElement("span");
      titCol.className = "coluna-titulo-texto";
      titCol.textContent = col.titulo;
      titCol.title = col.titulo;
      topo.appendChild(titCol);

      const contador = document.createElement("span");
      contador.className = "coluna-contador";
      contador.textContent = cartoes.length;
      topo.appendChild(contador);

      elCol.appendChild(topo);

      const corpo = document.createElement("div");
      corpo.className = "coluna-corpo";
      corpo.setAttribute("data-coluna-id", col.id);

      if (cartoes.length === 0) {
        const vazio = document.createElement("div");
        vazio.className = "coluna-vazia";
        vazio.textContent = termoBusca ? "Nenhum resultado" : "Sem execuções";
        corpo.appendChild(vazio);
      } else {
        for (const cartao of cartoes) {
          const elCard = document.createElement("div");
          elCard.className = "cartao-execucao";
          elCard.tabIndex = 0;
          elCard.onclick = () => abrirGaveta(cartao.run_id);
          elCard.onkeydown = (e) => { if (e.key === "Enter") abrirGaveta(cartao.run_id); };

          // RECURSO #1: COPIAR RÁPIDO NO HOVER
          if (cartao.humano?.comando) {
            const btnHover = document.createElement("button");
            btnHover.className = "btn-hover-copiar";
            btnHover.textContent = "Copiar";
            btnHover.title = `Copiar comando: ${cartao.humano.comando}`;
            btnHover.onclick = (e) => {
              e.stopPropagation();
              navigator.clipboard.writeText(cartao.humano.comando);
              btnHover.textContent = "✓ Copiado!";
              btnHover.classList.add("copiado");
              setTimeout(() => {
                btnHover.textContent = "Copiar";
                btnHover.classList.remove("copiado");
              }, 2000);
            };
            elCard.appendChild(btnHover);
          }

          if (cartao.status === "falhou" || cartao.status === "interrompido") {
            elCard.classList.add("cartao-falha-kanban");
          }

          const titCard = document.createElement("div");
          titCard.className = "cartao-titulo";
          titCard.textContent = cartao.titulo || cartao.chave;
          elCard.appendChild(titCard);

          if (cartao.gate_atual) {
            const gateTag = document.createElement("div");
            gateTag.className = "cartao-gate-tag";
            gateTag.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:4px;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>Gate: ${cartao.gate_atual} ${cartao.progresso_gates ? '(' + cartao.progresso_gates + ')' : ''}`;
            elCard.appendChild(gateTag);
          }

          const metaCard = document.createElement("div");
          metaCard.className = "cartao-metadados";

          const pidSpan = document.createElement("span");
          pidSpan.textContent = `PID ${cartao.processo?.pid || "-"}`;
          metaCard.appendChild(pidSpan);

          // RECURSO #2: CRONÔMETRO VIVO NO CARD
          const tempoSpan = document.createElement("span");
          tempoSpan.className = "cartao-tempo" + (cartao.status === "executando" ? " em-execucao" : "");
          tempoSpan.setAttribute("data-inicio", cartao.processo?.inicio || cartao.atualizado_em || "");
          tempoSpan.setAttribute("data-fim", cartao.processo?.fim || "");
          tempoSpan.setAttribute("data-status", cartao.status);
          metaCard.appendChild(tempoSpan);

          const statusBadge = document.createElement("span");
          statusBadge.className = `cartao-status-tag status-${cartao.status}`;
          statusBadge.textContent = cartao.status;
          metaCard.appendChild(statusBadge);

          elCard.appendChild(metaCard);
          corpo.appendChild(elCard);
        }
      }

      elCol.appendChild(corpo);
      trilha.appendChild(elCol);
    }

    // Restaurar posições de rolagem ou focar na coluna com cartões
    const novosCorpos = trilha.querySelectorAll(".coluna-corpo[data-coluna-id]");
    novosCorpos.forEach(c => {
      const cid = c.getAttribute("data-coluna-id");
      if (posicoesScroll[cid] !== undefined) {
        c.scrollTop = posicoesScroll[cid];
      }
    });

    if (scrollTrilhaX === 0 && colunaComFoco && colunaComFoco.id !== "coluna-alvo-fila") {
      colunaComFoco.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    } else {
      trilha.scrollLeft = scrollTrilhaX;
    }

    ESTADO_GLOBAL.cacheKanbanJson = strDados;
    atualizarCronometros();
  } catch (e) {
    console.error("Erro ao carregar kanban:", e);
  }
}

// ==========================================
// 7. CRONÔMETRO VIVO EM TEMPO REAL (RECURSO #2)
// ==========================================
function formatarDuracao(segundos) {
  if (segundos < 0) segundos = 0;
  const m = Math.floor(segundos / 60);
  const s = Math.floor(segundos % 60);
  if (m === 0) return `${s}s`;
  const h = Math.floor(m / 60);
  if (h === 0) return `${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`;
  const mRest = m % 60;
  return `${h}h ${String(mRest).padStart(2, "0")}m`;
}

function atualizarCronometros() {
  const agoraMs = Date.now();
  const elementos = document.querySelectorAll(".cartao-tempo");

  elementos.forEach(el => {
    const inicioStr = el.getAttribute("data-inicio");
    const fimStr = el.getAttribute("data-fim");
    const status = el.getAttribute("data-status");

    if (!inicioStr) {
      el.textContent = "-";
      return;
    }

    const inicioMs = new Date(inicioStr).getTime();
    if (isNaN(inicioMs)) {
      el.textContent = "-";
      return;
    }

    if (status === "executando") {
      const seg = Math.max(0, Math.floor((agoraMs - inicioMs) / 1000));
      el.textContent = `⏱ ${formatarDuracao(seg)}`;
    } else if (fimStr) {
      const fimMs = new Date(fimStr).getTime();
      const seg = Math.max(0, Math.floor((fimMs - inicioMs) / 1000));
      el.textContent = formatarDuracao(seg);
    } else {
      el.textContent = "-";
    }
  });
}

// ==========================================
// 8. BUSCA RÁPIDA INDEPENDENTE (RECURSO #3)
// ==========================================
function filtrarPipelines(input) {
  const campo = input || document.getElementById("campo-busca");
  ESTADO_GLOBAL.filtroPipelines = (campo ? campo.value : "").trim();
  ESTADO_GLOBAL.cachePipelinesJson = "";
  renderizarPipelines();
}

function filtrarKanban(input) {
  const campo = input || document.getElementById("campo-busca-kanban");
  ESTADO_GLOBAL.filtroKanban = (campo ? campo.value : "").trim();
  ESTADO_GLOBAL.cacheKanbanJson = "";
  if (ESTADO_GLOBAL.pipelineSelecionado) {
    carregarKanban(ESTADO_GLOBAL.pipelineSelecionado);
  }
}

// Compatibilidade retroativa caso chamado por terceiros
function filtrarCards(elOrigem) {
  if (ESTADO_GLOBAL.pipelineSelecionado) {
    filtrarKanban(elOrigem);
  } else {
    filtrarPipelines(elOrigem);
  }
}

// ==========================================
// 9. GAVETA LATERAL & TELEMETRIA DE CUSTOS (RECURSO #5)
// ==========================================
async function abrirGaveta(runId) {
  try {
    const res = await fetch(`/api/execucao/${runId}`);
    if (!res.ok) return;
    const ex = await res.json();

    const titGaveta = document.getElementById("gaveta-titulo");
    if (titGaveta) titGaveta.textContent = ex.titulo || ex.run_id;

    const corpo = document.getElementById("gaveta-conteudo");
    if (!corpo) return;
    corpo.replaceChildren();

    // 1. Linha do Tempo
    const b1 = document.createElement("div");
    b1.className = "bloco-gaveta";
    const h1 = document.createElement("h4");
    h1.className = "bloco-gaveta-titulo";
    h1.textContent = "1. Linha do Tempo";
    b1.appendChild(h1);

    const listaTempo = document.createElement("ul");
    listaTempo.className = "linha-tempo-lista";
    for (const h of ex.historico || []) {
      const li = document.createElement("li");
      li.className = "linha-tempo-item";

      const hora = document.createElement("span");
      hora.className = "linha-tempo-hora";
      hora.textContent = (h.em || "").substring(11, 19);

      const evento = document.createElement("span");
      evento.className = "linha-tempo-evento";
      evento.textContent = h.evento + ":";

      const msg = document.createElement("span");
      msg.textContent = h.mensagem || "";

      li.appendChild(hora);
      li.appendChild(evento);
      li.appendChild(msg);
      listaTempo.appendChild(li);
    }
    b1.appendChild(listaTempo);
    corpo.appendChild(b1);

    // 2. O que foi feito
    const b2 = document.createElement("div");
    b2.className = "bloco-gaveta";
    const h2 = document.createElement("h4");
    h2.className = "bloco-gaveta-titulo";
    h2.textContent = "2. O Que Foi Feito";
    b2.appendChild(h2);

    if (!ex.etapas || ex.etapas.length === 0) {
      const p = document.createElement("p");
      p.style.fontSize = "0.785rem";
      p.style.color = "var(--texto-mutado)";
      p.textContent = "Nenhuma etapa concluída registrada.";
      b2.appendChild(p);
    } else {
      for (const et of ex.etapas) {
        const p = document.createElement("p");
        p.style.fontSize = "0.785rem";
        p.style.marginBottom = "0.3rem";
        p.textContent = `Etapa ${et.id} — Status: ${et.status}`;
        b2.appendChild(p);
      }
    }
    corpo.appendChild(b2);

    // 3. Por que parou
    if (ex.parada) {
      const b3 = document.createElement("div");
      b3.className = "bloco-gaveta";
      const h3 = document.createElement("h4");
      h3.className = "bloco-gaveta-titulo";
      h3.textContent = "3. Por Que Parou";
      b3.appendChild(h3);

      const motivo = document.createElement("p");
      motivo.style.fontSize = "0.825rem";
      motivo.style.color = "var(--c-falha)";
      motivo.textContent = ex.parada.motivo || "Parada sem motivo especificado.";
      b3.appendChild(motivo);
      corpo.appendChild(b3);
    }

    // BLOCO DE AÇÃO & REMEDIAÇÃO AGÊNTICA (QUANDO HÁ FALHA OU PARADA)
    if (ex.status === "falhou" || ex.status === "interrompido" || ex.parada) {
      const bRemed = document.createElement("div");
      bRemed.className = "bloco-gaveta bloco-remediacao-ativa";

      const hRemed = document.createElement("h4");
      hRemed.className = "bloco-gaveta-titulo titulo-remediacao";
      hRemed.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Central de Ação & Remediação Agêntica`;
      bRemed.appendChild(hRemed);

      const pDesc = document.createElement("p");
      pDesc.className = "remediacao-desc";
      pDesc.textContent = "Falha operacional detectada. Dispare remediações ou gere o relatório pronto para o agente:";
      bRemed.appendChild(pDesc);

      const gradeBotoes = document.createElement("div");
      gradeBotoes.className = "grade-botoes-remediacao";

      const svgDoc = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:6px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`;
      const svgRocket = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:6px;"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>`;
      const svgBolt = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;
      const svgWrench = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:6px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`;

      // 1. Botão Copiar Reporte Completo para Agente
      const btnReporte = document.createElement("button");
      btnReporte.className = "btn-remediacao btn-copiar-reporte";
      btnReporte.innerHTML = `${svgDoc}<span>Copiar Reporte para Agente</span>`;
      btnReporte.onclick = () => {
        const promptAgente = [
          "## REPORT DE FALHA OPERACIONAL (DASHBOARD AIDD)",
          `- Pipeline: \`${ex.pipeline || 'desconhecido'}\``,
          `- Run ID: \`${ex.run_id}\``,
          `- Status: ${ex.status}`,
          `- Etapa da Falha: ${ex.etapa_atual || 'não identificada'}`,
          `- Comando Executado: \`${ex.comando || ''}\``,
          `- Motivo da Parada: ${ex.parada?.motivo || 'Erro reportado pelo pipeline'}`,
          "",
          "### Instrução para o Agente:",
          "1. Analise o erro factual acima e investigue a causa raiz no código.",
          "2. Corrija o problema seguindo as 13 Leis do ecossistema (Zero Stubs, Determinismo).",
          "3. Execute os testes/gates correspondentes para assegurar que a falha foi sanada."
        ].join("\n");
        navigator.clipboard.writeText(promptAgente);
        btnReporte.innerHTML = `<span>✓ Reporte Copiado! Cole no Agente</span>`;
        btnReporte.classList.add("sucesso");
        setTimeout(() => {
          btnReporte.innerHTML = `${svgDoc}<span>Copiar Reporte para Agente</span>`;
          btnReporte.classList.remove("sucesso");
        }, 3000);
      };
      gradeBotoes.appendChild(btnReporte);

      // 2. Botão Disparar Pipeline Audit-4F
      const btnAudit4f = document.createElement("button");
      btnAudit4f.className = "btn-remediacao btn-disparar-audit";
      btnAudit4f.innerHTML = `${svgRocket}<span>Disparar Auditoria 4F (audit-4f)</span>`;
      btnAudit4f.onclick = async () => {
        btnAudit4f.disabled = true;
        btnAudit4f.textContent = "Disparando...";
        try {
          const r = await fetch("/api/acao/disparar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({acao: "audit-4f", alvo: ex.pipeline, run_id: ex.run_id})
          });
          const d = await r.json();
          if (r.ok) {
            btnAudit4f.textContent = `✓ Audit-4F em execução (PID ${d.pid || ''})`;
            btnAudit4f.classList.add("sucesso");
            setTimeout(() => carregarPipelines(), 1000);
          } else {
            btnAudit4f.textContent = `Erro: ${d.erro || 'Falha ao disparar'}`;
            btnAudit4f.disabled = false;
          }
        } catch (err) {
          btnAudit4f.textContent = "Erro de conexão";
          btnAudit4f.disabled = false;
        }
      };
      gradeBotoes.appendChild(btnAudit4f);

      // 3. Botão Disparar Pipeline Evolução
      const btnEvolucao = document.createElement("button");
      btnEvolucao.className = "btn-remediacao btn-disparar-evolucao";
      btnEvolucao.innerHTML = `${svgBolt}<span>Disparar Evolução Técnica (evolucao)</span>`;
      btnEvolucao.onclick = async () => {
        btnEvolucao.disabled = true;
        btnEvolucao.textContent = "Disparando...";
        try {
          const r = await fetch("/api/acao/disparar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({acao: "evolucao", alvo: ex.pipeline, run_id: ex.run_id})
          });
          const d = await r.json();
          if (r.ok) {
            btnEvolucao.textContent = `✓ Evolução em execução (PID ${d.pid || ''})`;
            btnEvolucao.classList.add("sucesso");
            setTimeout(() => carregarPipelines(), 1000);
          } else {
            btnEvolucao.textContent = `Erro: ${d.erro || 'Falha ao disparar'}`;
            btnEvolucao.disabled = false;
          }
        } catch (err) {
          btnEvolucao.textContent = "Erro de conexão";
          btnEvolucao.disabled = false;
        }
      };
      gradeBotoes.appendChild(btnEvolucao);

      // 4. Botão Reexecutar Gates
      const btnGates = document.createElement("button");
      btnGates.className = "btn-remediacao btn-disparar-gates";
      btnGates.innerHTML = `${svgWrench}<span>Reexecutar Gates (audit)</span>`;
      btnGates.onclick = async () => {
        btnGates.disabled = true;
        btnGates.textContent = "Disparando...";
        try {
          const r = await fetch("/api/acao/disparar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({acao: "audit"})
          });
          const d = await r.json();
          if (r.ok) {
            btnGates.textContent = `✓ Gates em execução (PID ${d.pid || ''})`;
            btnGates.classList.add("sucesso");
            setTimeout(() => carregarPipelines(), 1000);
          } else {
            btnGates.textContent = `Erro: ${d.erro || 'Falha ao disparar'}`;
            btnGates.disabled = false;
          }
        } catch (err) {
          btnGates.textContent = "Erro de conexão";
          btnGates.disabled = false;
        }
      };
      gradeBotoes.appendChild(btnGates);

      bRemed.appendChild(gradeBotoes);
      corpo.appendChild(bRemed);
    }

    // 4. Precisa de Você
    if (ex.humano) {
      const b4 = document.createElement("div");
      b4.className = "bloco-gaveta";
      const h4 = document.createElement("h4");
      h4.className = "bloco-gaveta-titulo";
      h4.textContent = "4. Precisa de Você (Ação Humana)";
      b4.appendChild(h4);

      const msgHumano = document.createElement("p");
      msgHumano.style.fontSize = "0.8rem";
      msgHumano.style.marginBottom = "0.5rem";
      msgHumano.textContent = ex.humano.mensagem || "Comando para intervenção rápida:";
      b4.appendChild(msgHumano);

      const caixa = document.createElement("div");
      caixa.className = "caixa-comando";

      const cmdText = document.createElement("code");
      cmdText.textContent = ex.humano.comando;

      const btnCopiar = document.createElement("button");
      btnCopiar.className = "btn-copiar";
      btnCopiar.textContent = "Copiar Comando";
      btnCopiar.onclick = () => {
        navigator.clipboard.writeText(ex.humano.comando);
        btnCopiar.textContent = "✓ Copiado!";
        btnCopiar.classList.add("copiado");
        setTimeout(() => {
          btnCopiar.textContent = "Copiar Comando";
          btnCopiar.classList.remove("copiado");
        }, 2000);
      };

      caixa.appendChild(cmdText);
      caixa.appendChild(btnCopiar);
      b4.appendChild(caixa);
      corpo.appendChild(b4);
    }

    // 5. RECURSO #5: TELEMETRIA FACTUAL DE CUSTOS & TOKENS (LEI #8)
    const b5 = document.createElement("div");
    b5.className = "bloco-gaveta";
    const h5 = document.createElement("h4");
    h5.className = "bloco-gaveta-titulo";
    h5.textContent = "5. Telemetria de Custos & Tokens";
    b5.appendChild(h5);

    const custos = ex.custos;
    if (custos && typeof custos === "object" && custos.tokens_in !== undefined) {
      const grid = document.createElement("div");
      grid.className = "bloco-custos-grid";

      const cardIn = document.createElement("div");
      cardIn.className = "custo-card";
      cardIn.innerHTML = `
        <span class="custo-card-label">Tokens Input</span>
        <span class="custo-card-valor destaque-vivo">${custos.tokens_in.toLocaleString()}</span>
      `;

      const cardOut = document.createElement("div");
      cardOut.className = "custo-card";
      cardOut.innerHTML = `
        <span class="custo-card-label">Tokens Output</span>
        <span class="custo-card-valor destaque-sucesso">${custos.tokens_out.toLocaleString()}</span>
      `;

      const totalTokens = (custos.tokens_in || 0) + (custos.tokens_out || 0);
      const cardTotal = document.createElement("div");
      cardTotal.className = "custo-card";
      cardTotal.innerHTML = `
        <span class="custo-card-label">Total de Tokens</span>
        <span class="custo-card-valor">${totalTokens.toLocaleString()}</span>
      `;

      const cardFerramentas = document.createElement("div");
      cardFerramentas.className = "custo-card";
      const totalTools = (custos.skills?.length || 0) + (custos.mcps?.length || 0);
      cardFerramentas.innerHTML = `
        <span class="custo-card-label">Skills & MCPs</span>
        <span class="custo-card-valor">${totalTools} ativos</span>
      `;

      grid.appendChild(cardIn);
      grid.appendChild(cardOut);
      grid.appendChild(cardTotal);
      grid.appendChild(cardFerramentas);
      b5.appendChild(grid);
    } else {
      const badgeHonesto = document.createElement("div");
      badgeHonesto.className = "custo-nao-medido-badge";
      badgeHonesto.textContent = "ℹ Rótulo Honesto (Lei #8): Telemetria não-medida (sem logs JSONL anexados).";
      b5.appendChild(badgeHonesto);
    }
    corpo.appendChild(b5);

    // 6. Dados Brutos
    const b6 = document.createElement("div");
    b6.className = "bloco-gaveta";
    const h6 = document.createElement("h4");
    h6.className = "bloco-gaveta-titulo";
    h6.textContent = "6. Dados Brutos (Auditoria Factual)";
    b6.appendChild(h6);

    const pre = document.createElement("pre");
    pre.className = "pre-dados-brutos";
    pre.textContent = JSON.stringify(ex, null, 2);
    b6.appendChild(pre);
    corpo.appendChild(b6);

    // Abrir drawer e backdrop
    const gavetaEl = document.getElementById("gaveta-detalhes");
    const backdropEl = document.getElementById("gaveta-backdrop");
    if (gavetaEl) {
      gavetaEl.classList.remove("escondido");
      gavetaEl.setAttribute("aria-hidden", "false");
    }
    if (backdropEl) backdropEl.classList.remove("escondido");

    // Iniciar Logtail em streaming para a execução aberta
    iniciarLogtail(runId);
  } catch (e) {
    console.error("Erro ao carregar detalhes:", e);
  }
}

function fecharGaveta() {
  pararLogtail();
  const gavetaEl = document.getElementById("gaveta-detalhes");
  const backdropEl = document.getElementById("gaveta-backdrop");
  if (gavetaEl) {
    gavetaEl.classList.add("escondido");
    gavetaEl.setAttribute("aria-hidden", "true");
  }
  if (backdropEl) backdropEl.classList.add("escondido");
}

// ==========================================
// 10. ABA ARQUIVO HISTÓRICO
// ==========================================
function preencherFiltrosArquivo() {
  const selectPipe = document.getElementById("filtro-pipeline");
  if (!selectPipe || selectPipe.options.length > 1) return;

  for (const [id, info] of Object.entries(ESTADO_GLOBAL.dadosPipelines)) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = info.nome || id;
    selectPipe.appendChild(opt);
  }
}

async function carregarArquivo() {
  const container = document.getElementById("tabela-arquivo");
  if (!container) return;

  const selectPipe = document.getElementById("filtro-pipeline");
  const selectStatus = document.getElementById("filtro-status");
  const pipe = selectPipe ? selectPipe.value : "";
  const status = selectStatus ? selectStatus.value : "";

  let url = "/api/arquivo?";
  if (pipe) url += `pipeline=${encodeURIComponent(pipe)}&`;
  if (status) url += `status=${encodeURIComponent(status)}&`;

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    const json = await res.json();

    container.replaceChildren();

    if (!json.execucoes || json.execucoes.length === 0) {
      const vazio = document.createElement("div");
      vazio.className = "estado-vazio-tabela";
      vazio.textContent = "Nenhuma execução arquivada com os filtros selecionados.";
      container.appendChild(vazio);
      return;
    }

    const tabela = document.createElement("table");
    tabela.className = "tabela-arquivo";

    const thead = document.createElement("thead");
    const trHead = document.createElement("tr");
    for (const h of ["Pipeline", "Título / Chave", "Status", "Início", "Ações"]) {
      const th = document.createElement("th");
      th.textContent = h;
      trHead.appendChild(th);
    }
    thead.appendChild(trHead);
    tabela.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (const ex of json.execucoes) {
      const tr = document.createElement("tr");

      const tdPipe = document.createElement("td");
      tdPipe.className = "td-destaque";
      tdPipe.textContent = ex.pipeline;
      tr.appendChild(tdPipe);

      const tdTit = document.createElement("td");
      tdTit.textContent = ex.titulo || ex.chave;
      tr.appendChild(tdTit);

      const tdStatus = document.createElement("td");
      const spanStatus = document.createElement("span");
      spanStatus.className = `cartao-status-tag status-${ex.status}`;
      spanStatus.textContent = ex.status;
      tdStatus.appendChild(spanStatus);
      tr.appendChild(tdStatus);

      const tdInicio = document.createElement("td");
      tdInicio.className = "td-mono";
      tdInicio.textContent = ex.processo?.inicio || "-";
      tr.appendChild(tdInicio);

      const tdAcao = document.createElement("td");
      const btn = document.createElement("button");
      btn.className = "btn-acao-tabela";
      btn.textContent = "Ver Detalhes";
      btn.onclick = () => abrirGaveta(ex.run_id);
      tdAcao.appendChild(btn);
      tr.appendChild(tdAcao);

      tbody.appendChild(tr);
    }
    tabela.appendChild(tbody);
    container.appendChild(tabela);
  } catch (e) {
    console.error("Erro ao carregar arquivo histórico:", e);
  }
}

// ==========================================
// 11. ATALHOS DE TECLADO
// ==========================================
window.addEventListener("keydown", (e) => {
  const tag = (e.target.tagName || "").toUpperCase();
  const editavel = tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA";

  if (e.key === "Escape") {
    const gaveta = document.getElementById("gaveta-detalhes");
    if (gaveta && !gaveta.classList.contains("escondido")) {
      fecharGaveta();
    } else if (ESTADO_GLOBAL.pipelineSelecionado) {
      fecharKanban();
    }
    return;
  }

  // ATALHO '/' PARA FOCAR BUSCA
  if (e.key === "/" && !editavel) {
    e.preventDefault();
    const campo = ESTADO_GLOBAL.pipelineSelecionado
      ? document.getElementById("campo-busca-kanban")
      : document.getElementById("campo-busca");
    if (campo) {
      campo.focus();
      campo.select();
    }
    return;
  }

  if (editavel) return;

  if (e.key === "t" || e.key === "T") {
    alternarTema();
  } else if (e.key === "s" || e.key === "S") {
    alternarSom();
  } else if (e.key === "1") {
    mudarAba("pipelines");
  } else if (e.key === "2") {
    mudarAba("gates");
  } else if (e.key === "3") {
    mudarAba("worktrees");
  } else if (e.key === "4") {
    mudarAba("arquivo");
  }
});

// ==========================================
// 12. LOGTAIL / STREAMING DE LOGS NA GAVETA
// ==========================================
function alternarAbaGaveta(aba) {
  const btnDet = document.getElementById("gaveta-aba-detalhes");
  const btnTerm = document.getElementById("gaveta-aba-terminal");
  const conDet = document.getElementById("gaveta-conteudo");
  const conTerm = document.getElementById("gaveta-terminal-conteudo");

  if (btnDet) btnDet.classList.toggle("ativa", aba === "detalhes");
  if (btnTerm) btnTerm.classList.toggle("ativa", aba === "terminal");
  if (conDet) conDet.classList.toggle("escondido", aba !== "detalhes");
  if (conTerm) conTerm.classList.toggle("escondido", aba !== "terminal");
  tocarSom("clique");
}

function iniciarLogtail(runId) {
  pararLogtail();
  ESTADO_GLOBAL.logtailRunId = runId;
  ESTADO_GLOBAL.logtailOffset = 0;
  
  const elTerm = document.getElementById("terminal-log-texto");
  if (elTerm) elTerm.textContent = `[aidd-logtail] Conectando ao fluxo de logs da execução ${runId}...\n`;

  // Consulta imediata e depois intervalo
  consultarChunkLog();
  ESTADO_GLOBAL.intervaloLogtail = setInterval(consultarChunkLog, 1500);
}

function pararLogtail() {
  if (ESTADO_GLOBAL.intervaloLogtail) {
    clearInterval(ESTADO_GLOBAL.intervaloLogtail);
    ESTADO_GLOBAL.intervaloLogtail = null;
  }
  ESTADO_GLOBAL.logtailRunId = null;
}

async function consultarChunkLog() {
  if (!ESTADO_GLOBAL.logtailRunId) return;
  try {
    const res = await fetch(`/api/logs/${ESTADO_GLOBAL.logtailRunId}?offset=${ESTADO_GLOBAL.logtailOffset}`);
    if (!res.ok) return;
    const dados = await res.json();
    if (dados.log) {
      const elTerm = document.getElementById("terminal-log-texto");
      if (elTerm) {
        elTerm.textContent += dados.log;
        if (ESTADO_GLOBAL.logtailAutoScroll) {
          elTerm.scrollTop = elTerm.scrollHeight;
        }
      }
    }
    ESTADO_GLOBAL.logtailOffset = dados.offset || ESTADO_GLOBAL.logtailOffset;
    if (dados.fim) {
      pararLogtail();
      const elTerm = document.getElementById("terminal-log-texto");
      if (elTerm) elTerm.textContent += "\n[aidd-logtail] Fim da execução registrado.\n";
    }
  } catch (e) {
    // Silencioso em caso de corte
  }
}

function limparTerminalGaveta() {
  const elTerm = document.getElementById("terminal-log-texto");
  if (elTerm) elTerm.textContent = "";
}

function alternarAutoScrollTerminal() {
  ESTADO_GLOBAL.logtailAutoScroll = !ESTADO_GLOBAL.logtailAutoScroll;
  const btn = document.getElementById("btn-terminal-pausa");
  if (btn) btn.textContent = `Auto-scroll: ${ESTADO_GLOBAL.logtailAutoScroll ? 'ON' : 'OFF'}`;
}

// ==========================================
// 13. MATRIZ DE GATES (GRADE DE 72 LEDS)
// ==========================================
async function carregarGates() {
  const container = document.getElementById("grade-leds-gates");
  if (!container) return;

  try {
    const res = await fetch("/api/gates");
    if (!res.ok) return;
    const dados = await res.json();
    ESTADO_GLOBAL.dadosGates = dados.gates || [];

    let passou = 0;
    let falhou = 0;
    let pendente = 0;

    for (const g of ESTADO_GLOBAL.dadosGates) {
      if (g.status === "passou") passou++;
      else if (g.status === "falhou") falhou++;
      else pendente++;
    }

    const elPassou = document.getElementById("contagem-gates-passou");
    const elFalhou = document.getElementById("contagem-gates-falhou");
    const elPendente = document.getElementById("contagem-gates-pendente");
    const badgeTopo = document.getElementById("contagem-gates-leds");

    if (elPassou) elPassou.textContent = passou;
    if (elFalhou) elFalhou.textContent = falhou;
    if (elPendente) elPendente.textContent = pendente;
    if (badgeTopo) badgeTopo.textContent = `${passou}/${ESTADO_GLOBAL.dadosGates.length}`;

    renderizarGradeGates(ESTADO_GLOBAL.dadosGates);
  } catch (e) {
    console.error("Erro ao carregar gates:", e);
  }
}

function renderizarGradeGates(gates) {
  const container = document.getElementById("grade-leds-gates");
  if (!container) return;
  container.replaceChildren();

  for (const g of gates) {
    const item = document.createElement("div");
    item.className = "led-gate-item";
    item.title = `${g.id}\nMódulo: ${g.modulo}\nLei: ${g.lei || 'Canônica'}\nStatus: ${g.status}`;

    const led = document.createElement("span");
    led.className = `led-indicador ${g.status}`;
    item.appendChild(led);

    const nome = document.createElement("span");
    nome.className = "led-gate-nome";
    nome.textContent = g.nome;
    item.appendChild(nome);

    if (g.lei) {
      const lei = document.createElement("span");
      lei.className = "led-gate-lei";
      lei.textContent = `L#${g.lei}`;
      item.appendChild(lei);
    }

    container.appendChild(item);
  }
}

function filtrarGates(input) {
  const termo = (input.value || "").trim().toLowerCase();
  if (!termo) {
    renderizarGradeGates(ESTADO_GLOBAL.dadosGates);
    return;
  }
  const filtrados = ESTADO_GLOBAL.dadosGates.filter(g => 
    g.nome.toLowerCase().includes(termo) || 
    g.id.toLowerCase().includes(termo) ||
    (g.lei && g.lei.toString().includes(termo))
  );
  renderizarGradeGates(filtrados);
}

// ==========================================
// 14. WORKTREES VSA & DIFF VIEWER
// ==========================================
async function carregarWorktrees() {
  const container = document.getElementById("lista-worktrees-container");
  const badgeCont = document.getElementById("contagem-worktrees");
  if (!container) return;

  try {
    const res = await fetch("/api/worktrees");
    if (!res.ok) return;
    const dados = await res.json();
    ESTADO_GLOBAL.dadosWorktrees = dados.worktrees || [];
    if (badgeCont) badgeCont.textContent = ESTADO_GLOBAL.dadosWorktrees.length;

    container.replaceChildren();

    if (ESTADO_GLOBAL.dadosWorktrees.length === 0) {
      const vazio = document.createElement("div");
      vazio.className = "estado-vazio-tabela";
      vazio.style.gridColumn = "1 / -1";
      vazio.textContent = "Nenhuma git worktree efêmera ativa no momento. Todas convergiram ou foram limpas.";
      container.appendChild(vazio);
      return;
    }

    for (const wt of ESTADO_GLOBAL.dadosWorktrees) {
      const card = document.createElement("div");
      card.className = "card-worktree";

      const topo = document.createElement("div");
      topo.className = "worktree-topo";

      const tit = document.createElement("span");
      tit.className = "worktree-nome";
      tit.textContent = wt.nome || "worktree";
      topo.appendChild(tit);

      if (wt.branch) {
        const br = document.createElement("span");
        br.className = "worktree-branch";
        br.textContent = wt.branch;
        topo.appendChild(br);
      }
      card.appendChild(topo);

      const pathEl = document.createElement("span");
      pathEl.className = "worktree-caminho";
      pathEl.textContent = wt.caminho;
      card.appendChild(pathEl);

      const acoes = document.createElement("div");
      acoes.className = "worktree-acoes";

      const btnDiff = document.createElement("button");
      btnDiff.className = "btn-worktree-diff";
      btnDiff.textContent = "🔍 Inspecionar Diff";
      btnDiff.onclick = () => abrirModalDiff(wt.caminho);
      acoes.appendChild(btnDiff);

      card.appendChild(acoes);
      container.appendChild(card);
    }
  } catch (e) {
    console.error("Erro ao carregar worktrees:", e);
  }
}

async function abrirModalDiff(caminho) {
  const modal = document.getElementById("modal-diff");
  const pre = document.getElementById("modal-diff-conteudo");
  const tit = document.getElementById("modal-diff-titulo");
  if (!modal || !pre) return;

  if (tit) tit.textContent = `Diff da Worktree: ${caminho}`;
  pre.textContent = "Coletando diff git...";
  modal.classList.remove("escondido");
  tocarSom("clique");

  try {
    const res = await fetch(`/api/worktree/diff?caminho=${encodeURIComponent(caminho)}`);
    if (!res.ok) {
      pre.textContent = "Falha ao obter diff.";
      return;
    }
    const dados = await res.json();
    pre.textContent = dados.diff || "Nenhuma alteração pendente (working tree clean).";
  } catch (e) {
    pre.textContent = `Erro: ${e.message}`;
  }
}

function fecharModalDiff(event) {
  const modal = document.getElementById("modal-diff");
  if (modal) modal.classList.add("escondido");
}

// ==========================================
// 15. LAUNCHPAD MODAL (NOVO DISPARO COM 1 CLIQUE)
// ==========================================
function abrirLaunchpad() {
  const modal = document.getElementById("modal-launchpad");
  const status = document.getElementById("status-disparo-launchpad");
  if (status) status.classList.add("escondido");
  if (modal) modal.classList.remove("escondido");
  tocarSom("clique");
}

function fecharLaunchpad(event) {
  const modal = document.getElementById("modal-launchpad");
  if (modal) modal.classList.add("escondido");
}

async function dispararFluxo(tipo) {
  const status = document.getElementById("status-disparo-launchpad");
  if (status) {
    status.classList.remove("escondido");
    status.textContent = `Disparando fluxo '${tipo}'...`;
  }
  tocarSom("clique");

  try {
    const res = await fetch("/api/acao/disparar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ acao: tipo })
    });
    const dados = await res.json();
    if (res.ok) {
      if (status) status.textContent = `✓ Sucesso! ${dados.mensagem || 'Fluxo iniciado'} (PID ${dados.pid || ''})`;
      tocarSom("sucesso");
      setTimeout(() => {
        fecharLaunchpad();
        atualizarDados();
      }, 1500);
    } else {
      if (status) status.textContent = `Erro: ${dados.erro || 'Falha ao acionar'}`;
      tocarSom("falha");
    }
  } catch (e) {
    if (status) status.textContent = `Erro de conexão: ${e.message}`;
    tocarSom("falha");
  }
}

// ==========================================
// 16. TELEMETRIA FACTUAL DE TOKENS (SPARKLINE)
// ==========================================
async function carregarTelemetriaTokens() {
  try {
    const res = await fetch("/api/telemetria/tokens");
    if (!res.ok) return;
    const dados = await res.json();

    const elTaxa = document.getElementById("tokens-taxa-texto");
    const elCusto = document.getElementById("tokens-custo-texto");
    if (elTaxa) elTaxa.textContent = `${(dados.taxa_atual_tpm / 1000).toFixed(1)}k TPM`;
    if (elCusto) elCusto.textContent = `$${dados.custo_sessao_usd.toFixed(2)}`;

    // Atualiza pontos do Sparkline SVG se houver histórico
    const spark = document.getElementById("sparkline-tokens");
    if (spark && dados.historico && dados.historico.length > 1) {
      const maxT = Math.max(...dados.historico.map(p => p.tokens), 1);
      const w = 48;
      const h = 18;
      const step = w / (dados.historico.length - 1);
      const pontos = dados.historico.map((p, idx) => {
        const x = Math.round(idx * step);
        const y = Math.round(h - (p.tokens / maxT) * (h - 4)) - 2;
        return `${x},${y}`;
      }).join(" ");
      const poly = spark.querySelector("polyline");
      if (poly) poly.setAttribute("points", pontos);
    }
  } catch (e) {
    // Silencioso
  }
}

// Inicialização
aplicarTema(ESTADO_GLOBAL.tema);
atualizarIconeNotificacao();
atualizarIconeSom();
setInterval(atualizarDados, 2000);
setInterval(atualizarCronometros, 1000);
setInterval(carregarTelemetriaTokens, 5000);
atualizarDados();
carregarTelemetriaTokens();

// Recarga instantânea ao retornar à aba ou focar na janela
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    atualizarDados();
    carregarTelemetriaTokens();
  }
});
window.addEventListener("focus", () => {
  atualizarDados();
  carregarTelemetriaTokens();
});

