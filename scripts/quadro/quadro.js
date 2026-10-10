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
    card.className = "card-pipeline";
    if (info.precisa_humano > 0) {
      card.classList.add("card-estado-humano");
    } else if (info.falhou > 0) {
      card.classList.add("card-estado-falhou");
    } else if (info.executando > 0) {
      card.classList.add("card-estado-executando");
    } else if (info.concluido > 0) {
      card.classList.add("card-estado-concluido");
    }

    card.tabIndex = 0;
    card.onclick = () => abrirKanban(id);
    card.onkeydown = (e) => { if (e.key === "Enter") abrirKanban(id); };

    const topo = document.createElement("div");
    topo.className = "card-pipeline-topo";

    const tit = document.createElement("h3");
    tit.className = "card-pipeline-titulo";
    tit.textContent = info.nome || id;
    topo.appendChild(tit);

    // Destaque corporativo da Tríade Canônica
    if (["pure", "open", "freedom"].includes(id)) {
      const tagTriade = document.createElement("span");
      tagTriade.className = "badge-corp vivo";
      tagTriade.textContent = id === "pure" ? "Tríade #1" : (id === "open" ? "Tríade #2" : "Tríade #3");
      topo.appendChild(tagTriade);
    }

    if (info.precisa_humano > 0) {
      const alerta = document.createElement("span");
      alerta.className = "badge-corp alerta";
      alerta.textContent = `⚠ ${info.precisa_humano} ação humana`;
      topo.appendChild(alerta);
    }
    card.appendChild(topo);

    // CENTRO DO CARD: ETAPA ATUAL & BARRA DE PROGRESSO & TIMER DA FASE
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

    // TIMER DEDICADO POR FASE / ETAPA
    if (info.executando > 0) {
      const timerEtapa = document.createElement("div");
      timerEtapa.className = "card-etapa-timer-linha";
      timerEtapa.innerHTML = `
        <span>Tempo na fase:</span>
        <span class="timer-etapa-badge cartao-tempo-etapa" data-inicio="${info.atualizado_em || ''}">00:00</span>
      `;
      centro.appendChild(timerEtapa);
    }

    card.appendChild(centro);

    // RODAPÉ: RODANDO -> CONCLUÍDOS -> FALHAS (ENTERPRISE BADGES)
    const metricas = document.createElement("div");
    metricas.className = "pipeline-metricas";

    const spanExec = document.createElement("span");
    spanExec.className = "metrica-tag badge-corp" + (info.executando > 0 ? " vivo" : "");
    spanExec.textContent = `${info.executando || 0} rodando`;

    const spanConc = document.createElement("span");
    spanConc.className = "metrica-tag badge-corp" + (info.concluido > 0 ? " sucesso" : "");
    spanConc.textContent = `${info.concluido || 0} concluídos`;

    const spanFalha = document.createElement("span");
    spanFalha.className = "metrica-tag badge-corp" + (info.falhou > 0 ? " falha" : "");
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
          if (cartao.status === "falhou" || cartao.status === "interrompido") {
            elCard.classList.add("card-estado-falhou");
          } else if (cartao.status === "precisa_humano" || cartao.humano) {
            elCard.classList.add("card-estado-humano");
          } else if (cartao.status === "executando") {
            elCard.classList.add("card-estado-executando");
          } else if (cartao.status === "concluido") {
            elCard.classList.add("card-estado-concluido");
          }
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

  // CRONÔMETRO DEDICADO POR FASE / ETAPA
  const elementosEtapa = document.querySelectorAll(".cartao-tempo-etapa");
  elementosEtapa.forEach(el => {
    const inicioStr = el.getAttribute("data-inicio");
    if (!inicioStr) return;
    const inicioMs = new Date(inicioStr).getTime();
    if (isNaN(inicioMs)) return;
    const seg = Math.max(0, Math.floor((agoraMs - inicioMs) / 1000));
    el.textContent = formatarDuracao(seg);
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
// 9. GAVETA LATERAL & TELEMETRIA DE CUSTOS (CORPORATE CLEAN DESIGN)
// ==========================================
async function abrirGaveta(runId) {
  try {
    const res = await fetch(`/api/execucao/${runId}`);
    if (!res.ok) return;
    const ex = await res.json();

    const titGaveta = document.getElementById("gaveta-titulo");
    if (titGaveta) {
      const st = ex.status || 'desconhecido';
      const classeBadge = st === 'concluido' ? 'sucesso' : (st === 'falhou' || st === 'interrompido' ? 'falha' : (st === 'executando' ? 'vivo' : 'alerta'));
      titGaveta.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
          <span>${ex.titulo || ex.run_id}</span>
          <span class="badge-corp ${classeBadge}">${st.toUpperCase()}</span>
        </div>
      `;
    }

    const corpo = document.getElementById("gaveta-conteudo");
    const corpoTimeline = document.getElementById("gaveta-timeline-conteudo");
    if (!corpo || !corpoTimeline) return;
    corpo.replaceChildren();
    corpoTimeline.replaceChildren();

    // 1. CARDS DE MÉTRICAS RÁPIDAS (RESUMO EXECUTIVO)
    const gradeResumo = document.createElement("div");
    gradeResumo.className = "gaveta-resumo-grid";
    gradeResumo.innerHTML = `
      <div class="resumo-item">
        <span class="resumo-label">Pipeline</span>
        <span class="resumo-valor">${ex.pipeline || '-'}</span>
      </div>
      <div class="resumo-item">
        <span class="resumo-label">PID / Processo</span>
        <span class="resumo-valor">${ex.processo?.pid || '-'}</span>
      </div>
      <div class="resumo-item">
        <span class="resumo-label">Início</span>
        <span class="resumo-valor">${ex.processo?.inicio ? (ex.processo.inicio).substring(11, 19) : '-'}</span>
      </div>
      <div class="resumo-item">
        <span class="resumo-label">Fase Atual</span>
        <span class="resumo-valor destaque-vivo">${ex.etapa_atual || '-'}</span>
      </div>
    `;
    corpo.appendChild(gradeResumo);

    // 2. BLOCO DE ALERTA & REMEDIAÇÃO (SOMENTE SE FALHA OU PARADA)
    if (ex.status === "falhou" || ex.status === "interrompido" || ex.parada) {
      const bAlerta = document.createElement("div");
      bAlerta.className = "bloco-remediacao-clean";
      bAlerta.innerHTML = `
        <div class="remediacao-topo-clean">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <h4>Falha Operacional Detectada</h4>
        </div>
        <p class="remediacao-motivo-texto">${ex.parada?.motivo || 'Execução interrompida sem sinal de sucesso.'}</p>
        <div class="grade-botoes-remediacao-clean"></div>
      `;
      const gradeBotoes = bAlerta.querySelector(".grade-botoes-remediacao-clean");

      const btnReporte = document.createElement("button");
      btnReporte.className = "btn-remediacao btn-copiar-reporte";
      btnReporte.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg><span>Copiar Reporte Agente</span>`;
      btnReporte.onclick = () => {
        const promptAgente = [
          "## REPORT DE FALHA OPERACIONAL (DASHBOARD AIDD)",
          `- Pipeline: \`${ex.pipeline || 'desconhecido'}\``,
          `- Run ID: \`${ex.run_id}\``,
          `- Status: ${ex.status}`,
          `- Etapa da Falha: ${ex.etapa_atual || 'não identificada'}`,
          `- Comando: \`${ex.comando || ''}\``,
          `- Motivo: ${ex.parada?.motivo || 'Erro no pipeline'}`
        ].join("\n");
        navigator.clipboard.writeText(promptAgente);
        btnReporte.innerHTML = "<span>✓ Reporte Copiado!</span>";
        setTimeout(() => { btnReporte.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg><span>Copiar Reporte Agente</span>`; }, 2500);
      };
      gradeBotoes.appendChild(btnReporte);

      const btnAudit = document.createElement("button");
      btnAudit.className = "btn-remediacao btn-disparar-audit";
      btnAudit.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg><span>Audit-4F</span>`;
      btnAudit.onclick = () => dispararAcao("audit-4f", ex.pipeline);
      gradeBotoes.appendChild(btnAudit);

      const btnEvolucao = document.createElement("button");
      btnEvolucao.className = "btn-remediacao btn-disparar-evolucao";
      btnEvolucao.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span>Evolução</span>`;
      btnEvolucao.onclick = () => dispararAcao("evolucao", ex.pipeline);
      gradeBotoes.appendChild(btnEvolucao);

      const btnGates = document.createElement("button");
      btnGates.className = "btn-remediacao btn-disparar-gates";
      btnGates.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg><span>Gates</span>`;
      btnGates.onclick = () => dispararAcao("audit");
      gradeBotoes.appendChild(btnGates);

      corpo.appendChild(bAlerta);
    }

    // 3. AÇÃO HUMANA (SE HOUVER)
    if (ex.humano) {
      const bHumano = document.createElement("div");
      bHumano.className = "bloco-humano-clean";
      bHumano.innerHTML = `
        <h4 class="bloco-gaveta-titulo"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Intervenção Manual Requerida</h4>
        <p style="font-size:0.785rem;color:var(--texto-secundario);margin:0.35rem 0;">${ex.humano.mensagem || 'Comando sugerido:'}</p>
        <div class="caixa-comando">
          <code>${ex.humano.comando}</code>
          <button class="btn-copiar" onclick="navigator.clipboard.writeText('${ex.humano.comando}');this.textContent='Copiado!';setTimeout(()=>this.textContent='Copiar',2000);">Copiar</button>
        </div>
      `;
      corpo.appendChild(bHumano);
    }

    // 4. ETAPAS CONCLUÍDAS (LISTA LIMPA COM BULLETS)
    const bEtapas = document.createElement("div");
    bEtapas.className = "bloco-gaveta";
    bEtapas.innerHTML = `<h4 class="bloco-gaveta-titulo">Etapas da Execução</h4>`;
    if (!ex.etapas || ex.etapas.length === 0) {
      bEtapas.innerHTML += `<p class="gaveta-texto-mutado">Nenhuma etapa concluída registrada.</p>`;
    } else {
      const lista = document.createElement("div");
      lista.className = "gaveta-etapas-lista";
      for (const et of ex.etapas) {
        const item = document.createElement("div");
        item.className = "gaveta-etapa-linha";
        const dot = et.status === 'concluido' ? 'passou' : (et.status === 'falhou' ? 'falhou' : 'neutro');
        item.innerHTML = `
          <span class="led-indicador ${dot}"></span>
          <span class="etapa-linha-id">Etapa ${et.id}</span>
          <span class="badge-corp ${dot === 'passou' ? 'sucesso' : 'falha'}">${et.status}</span>
        `;
        lista.appendChild(item);
      }
      bEtapas.appendChild(lista);
    }
    corpo.appendChild(bEtapas);

    // 5. TELEMETRIA FACTUAL (MINI CARDS)
    const bTelemetria = document.createElement("div");
    bTelemetria.className = "bloco-gaveta";
    bTelemetria.innerHTML = `<h4 class="bloco-gaveta-titulo">Telemetria de Tokens & Recursos</h4>`;
    const custos = ex.custos;
    if (custos && typeof custos === "object" && custos.tokens_in !== undefined) {
      const totTokens = (custos.tokens_in || 0) + (custos.tokens_out || 0);
      bTelemetria.innerHTML += `
        <div class="bloco-custos-grid">
          <div class="custo-card"><span class="custo-card-label">Input</span><span class="custo-card-valor destaque-vivo">${custos.tokens_in.toLocaleString()}</span></div>
          <div class="custo-card"><span class="custo-card-label">Output</span><span class="custo-card-valor destaque-sucesso">${custos.tokens_out.toLocaleString()}</span></div>
          <div class="custo-card"><span class="custo-card-label">Total</span><span class="custo-card-valor">${totTokens.toLocaleString()}</span></div>
          <div class="custo-card"><span class="custo-card-label">Tools</span><span class="custo-card-valor">${(custos.skills?.length || 0) + (custos.mcps?.length || 0)}</span></div>
        </div>
      `;
    } else {
      bTelemetria.innerHTML += `<div class="custo-nao-medido-badge">ℹ Telemetria não-medida (sem logs JSONL anexados)</div>`;
    }
    corpo.appendChild(bTelemetria);

    // 6. DADOS BRUTOS EM ACCORDION / DETAILS (ZERO POLUIÇÃO)
    const bRaw = document.createElement("details");
    bRaw.className = "gaveta-accordion-raw";
    bRaw.innerHTML = `
      <summary class="gaveta-accordion-sumario">Auditoria Técnica Factual (JSON Bruto)</summary>
      <pre class="pre-dados-brutos">${JSON.stringify(ex, null, 2)}</pre>
    `;
    corpo.appendChild(bRaw);

    // 7. PREENCHER ABA TIMELINE (DEDICADA)
    corpoTimeline.innerHTML = `<h4 class="bloco-gaveta-titulo" style="margin-bottom:0.75rem;">Histórico Cronológico de Eventos</h4>`;
    if (!ex.historico || ex.historico.length === 0) {
      corpoTimeline.innerHTML += `<p class="gaveta-texto-mutado">Sem histórico cronológico registrado.</p>`;
    } else {
      const listaT = document.createElement("ul");
      listaT.className = "linha-tempo-lista";
      for (const h of ex.historico) {
        const li = document.createElement("li");
        li.className = "linha-tempo-item";
        li.innerHTML = `
          <span class="linha-tempo-hora">${(h.em || "").substring(11, 19)}</span>
          <span class="linha-tempo-evento">${h.evento}:</span>
          <span>${h.mensagem || ""}</span>
        `;
        listaT.appendChild(li);
      }
      corpoTimeline.appendChild(listaT);
    }

    // Default para aba 'detalhes'
    alternarAbaGaveta('detalhes');

    // Abrir drawer e backdrop
    const gavetaEl = document.getElementById("gaveta-detalhes");
    const backdropEl = document.getElementById("gaveta-backdrop");
    if (gavetaEl) {
      gavetaEl.classList.remove("escondido");
      gavetaEl.setAttribute("aria-hidden", "false");
    }
    if (backdropEl) backdropEl.classList.remove("escondido");

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
    // 1. Fecha modal de QR Code se aberto
    const modalQr = document.getElementById("modal-qrcode");
    if (modalQr && !modalQr.classList.contains("escondido")) {
      modalQr.classList.add("escondido");
      return;
    }
    // 2. Fecha modal de Launchpad se aberto
    const modalLaunchpad = document.getElementById("modal-launchpad");
    if (modalLaunchpad && !modalLaunchpad.classList.contains("escondido")) {
      modalLaunchpad.classList.add("escondido");
      return;
    }
    // 3. Fecha modal de Limpar se aberto
    const modalLimpar = document.getElementById("modal-limpar-execucoes");
    if (modalLimpar && !modalLimpar.classList.contains("escondido")) {
      modalLimpar.classList.add("escondido");
      return;
    }
    // 4. Fecha gaveta lateral se aberta
    const gaveta = document.getElementById("gaveta-detalhes");
    if (gaveta && !gaveta.classList.contains("escondido")) {
      fecharGaveta();
      return;
    }
    // 5. Volta do Kanban se ativo
    if (ESTADO_GLOBAL.pipelineSelecionado) {
      fecharKanban();
      return;
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

// ==========================================================================
// 13. RECURSO: ACESSO MOBILE VIA WI-FI COM QR CODE
// ==========================================================================
let _urlWifiCache = "";

async function abrirModalQRCode() {
  tocarSom("clique");
  const modal = document.getElementById("modal-qrcode");
  const container = document.getElementById("qrcode-container");
  const elUrl = document.getElementById("qrcode-url-texto");
  const elStatus = document.getElementById("qrcode-status-rede");

  if (!modal) return;
  modal.classList.remove("escondido");

  if (container) container.innerHTML = `<span style="font-size:0.75rem;color:#64748b;">Gerando QR Code...</span>`;
  if (elUrl) elUrl.textContent = "Obtendo endereço LAN...";

  try {
    const res = await fetch("/api/rede/wifi");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const dados = await res.json();
    _urlWifiCache = dados.url || "";

    if (elUrl) elUrl.textContent = _urlWifiCache;
    if (elStatus) {
      elStatus.textContent = dados.online 
        ? `IP na rede Wi-Fi: ${dados.ip} (Porta ${dados.porta})`
        : "Aviso: Sem IP de LAN detectado (operando em localhost)";
    }

    if (container && dados.qrcode_svg) {
      container.innerHTML = dados.qrcode_svg;
      const svg = container.querySelector("svg");
      if (svg) {
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
      }
    }
  } catch (err) {
    if (container) container.innerHTML = `<span style="font-size:0.75rem;color:var(--c-falha);">Erro ao obter dados de rede</span>`;
    if (elUrl) elUrl.textContent = "Erro de conexão";
  }
}

function fecharModalQRCode(evento) {
  if (evento && evento.target && evento.target.closest(".modal-janela") && !evento.target.classList.contains("btn-fechar")) {
    return;
  }
  const modal = document.getElementById("modal-qrcode");
  if (modal) modal.classList.add("escondido");
  tocarSom("clique");
}

function copiarUrlWifi() {
  const btn = document.getElementById("btn-copiar-url-wifi");
  if (!_urlWifiCache) return;
  navigator.clipboard.writeText(_urlWifiCache).then(() => {
    tocarSom("clique");
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = "✓ Copiado!";
      btn.style.background = "var(--c-sucesso)";
      btn.style.color = "#000";
      setTimeout(() => {
        btn.textContent = orig;
        btn.style.background = "";
        btn.style.color = "";
      }, 2000);
    }
  });
}

// ==========================================================================
// 14. RECURSO: LIMPAR / ARQUIVAR EXECUÇÕES CONCLUÍDAS E FALHAS
// ==========================================================================
async function confirmarArquivamento() {
  tocarSom("clique");
  const confirmar = confirm("Deseja mover todas as execuções CONCLUÍDAS e FALHAS para o Arquivo Histórico?\nIsso despoluirá a visão ativa sem perder dados.");
  if (!confirmar) return;

  const btn = document.getElementById("btn-arquivar-topo");
  if (btn) btn.style.opacity = "0.5";

  try {
    const res = await fetch("/api/acao/arquivar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: ["concluido", "falhou", "interrompido", "cancelado"] })
    });
    const dados = await res.json();
    if (res.ok) {
      tocarSom("sucesso");
      alert(`✓ ${dados.mensagem || 'Execuções arquivadas com sucesso!'}`);
      await atualizarDados();
    } else {
      tocarSom("falha");
      alert(`Erro ao arquivar: ${dados.erro || 'Falha na requisição'}`);
    }
  } catch (err) {
    tocarSom("falha");
    alert("Erro de conexão ao solicitar arquivamento.");
  } finally {
    if (btn) btn.style.opacity = "1";
  }
}


