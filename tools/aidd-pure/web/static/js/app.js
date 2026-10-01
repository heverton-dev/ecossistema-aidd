/**
 * AIDD Project Generator — Frontend Controller
 * web/static/js/app.js
 */

document.addEventListener('DOMContentLoaded', () => {
    // Estado da aplicação
    const estado = {
        config: null,
        pollingInterval: null,
        ultimoStatus: null,
        pastaSugeridaModificadaManual: false,
        pastaMonitorada: null
    };

    // Elementos DOM principais
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const headerStatusDot = document.getElementById('header-status-dot');
    const progressoPulse = document.getElementById('progresso-pulse');

    // Elementos Formulário Novo Projeto
    const alertaSemChave = document.getElementById('alerta-sem-chave');
    const btnIrConfigAlerta = document.getElementById('btn-ir-config-alerta');
    const inputIdeia = document.getElementById('input-ideia');
    const inputPasta = document.getElementById('input-pasta');
    const btnSugerirPasta = document.getElementById('btn-sugerir-pasta');
    const hintPastaAbsoluta = document.getElementById('hint-pasta-absoluta');
    const checkImplementar = document.getElementById('check-implementar-codigo');
    const formNovoProjeto = document.getElementById('form-novo-projeto');
    const btnGerarProjeto = document.getElementById('btn-gerar-projeto');

    // Elementos Progresso
    const progressoTituloIdeia = document.getElementById('progresso-titulo-ideia');
    const progressoCaminhoPasta = document.getElementById('progresso-caminho-pasta');
    const progressoTempo = document.getElementById('progresso-tempo');
    const progressoTagStatus = document.getElementById('progresso-tag-status');
    const progressoBarraFill = document.getElementById('progresso-barra-fill');
    const progressoTextoFases = document.getElementById('progresso-texto-fases');
    const progressoTextoPorcentagem = document.getElementById('progresso-texto-porcentagem');
    const btnCancelarPipeline = document.getElementById('btn-cancelar-pipeline');
    const cardErroAmigavel = document.getElementById('card-erro-amigavel');
    const erroAmigavelTexto = document.getElementById('erro-amigavel-texto');
    const erroAcaoContainer = document.getElementById('erro-acao-container');
    const btnErroIrConfig = document.getElementById('btn-erro-ir-config');
    const erroTecnicoLog = document.getElementById('erro-tecnico-log');
    const containerFasesGrid = document.getElementById('container-fases-grid');
    const terminalLogsBody = document.getElementById('terminal-logs-body');
    const btnToggleLogs = document.getElementById('btn-toggle-logs');

    // Elementos Monitorar Pasta
    const inputMonitorPasta = document.getElementById('input-monitor-pasta');
    const btnMonitorarPasta = document.getElementById('btn-monitorar-pasta');

    // Elementos Workspace
    const workspaceConteudo = document.getElementById('workspace-conteudo');
    const workspaceVazio = document.getElementById('workspace-vazio');
    const workspaceObjetivo = document.getElementById('workspace-objetivo');
    const workspaceData = document.getElementById('workspace-data');
    const workspaceCompletas = document.getElementById('workspace-completas');
    const workspaceProgressoSub = document.getElementById('workspace-progresso-sub');
    const workspaceBarraFill = document.getElementById('workspace-barra-fill');
    const workspaceTextoEtapas = document.getElementById('workspace-texto-etapas');
    const workspaceTextoPorcentagem = document.getElementById('workspace-texto-porcentagem');
    const workspaceEtapasGrid = document.getElementById('workspace-etapas-grid');

    // Elementos Resultado
    const resultadoVazio = document.getElementById('resultado-vazio');
    const resultadoConteudo = document.getElementById('resultado-conteudo');
    const btnIrNovoVazio = document.getElementById('btn-ir-novo-vazio');
    const btnNovoAposConclusao = document.getElementById('btn-novo-apos-conclusao');
    const resultadoBadgeStatus = document.getElementById('resultado-badge-status');
    const resultadoTituloProjeto = document.getElementById('resultado-titulo-projeto');
    const resultadoPastaCaminho = document.getElementById('resultado-pasta-caminho');
    const btnAbrirExplorer = document.getElementById('btn-abrir-explorer');
    const resultadoScoreValor = document.getElementById('resultado-score-valor');
    const resultadoGatesValor = document.getElementById('resultado-gates-valor');
    const resultadoGatesSub = document.getElementById('resultado-gates-sub');
    const resultadoTokensValor = document.getElementById('resultado-tokens-valor');
    const cardResultadoTestes = document.getElementById('card-resultado-testes');
    const resultadoTestesValor = document.getElementById('resultado-testes-valor');
    const resultadoTestesSub = document.getElementById('resultado-testes-sub');
    const listaPontosFortes = document.getElementById('lista-pontos-fortes');
    const listaPontosFracos = document.getElementById('lista-pontos-fracos');

    // Elementos Configuração
    const selectProvedor = document.getElementById('select-provedor');
    const hintProvedorDesc = document.getElementById('hint-provedor-desc');
    const inputModelo = document.getElementById('input-modelo');
    const grupoBaseUrl = document.getElementById('grupo-base-url');
    const inputBaseUrl = document.getElementById('input-base-url');
    const inputChaveApi = document.getElementById('input-chave-api');
    const badgeChaveStatus = document.getElementById('badge-chave-status');
    const btnToggleSenha = document.getElementById('btn-toggle-senha');
    const inputTimeout = document.getElementById('input-timeout');
    const feedbackTesteChave = document.getElementById('feedback-teste-chave');
    const feedbackTesteIcon = document.getElementById('feedback-teste-icon');
    const feedbackTesteMsg = document.getElementById('feedback-teste-msg');
    const btnTestarChave = document.getElementById('btn-testar-chave');
    const btnSalvarConfig = document.getElementById('btn-salvar-config');


    // =========================================================================
    // NAVEGAÇÃO DE ABAS
    // =========================================================================
    function alternarAba(tabId) {
        navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        tabContents.forEach(tab => {
            tab.classList.toggle('active', tab.id === tabId);
        });
    }

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            alternarAba(btn.dataset.tab);
            if (btn.dataset.tab === 'tab-workspace') {
                carregarWorkspace();
            }
        });
    });

    if (btnIrConfigAlerta) {
        btnIrConfigAlerta.addEventListener('click', () => alternarAba('tab-config'));
    }
    if (btnErroIrConfig) {
        btnErroIrConfig.addEventListener('click', () => alternarAba('tab-config'));
    }
    if (btnIrNovoVazio) {
        btnIrNovoVazio.addEventListener('click', () => alternarAba('tab-novo'));
    }
    if (btnNovoAposConclusao) {
        btnNovoAposConclusao.addEventListener('click', () => alternarAba('tab-novo'));
    }


    // =========================================================================
    // CARREGAR CONFIGURAÇÃO INICIAL
    // =========================================================================
    async function carregarConfiguracao() {
        try {
            const resp = await fetch('/api/config');
            const data = await resp.json();
            if (data.sucesso && data.config) {
                estado.config = data.config;
                atualizarInterfaceConfiguracao(data.config);
            }
        } catch (err) {
            console.error('Erro ao carregar configuração:', err);
        }
    }

    function atualizarInterfaceConfiguracao(cfg) {
        // Atualiza status dot do header
        if (cfg.esta_configurado) {
            headerStatusDot.className = 'status-dot active';
            headerStatusDot.title = `IA Pronta: ${cfg.modelo_ativo}`;
            alertaSemChave.classList.add('hidden');
        } else {
            headerStatusDot.className = 'status-dot warning';
            headerStatusDot.title = 'Atenção: Nenhuma chave de IA configurada';
            alertaSemChave.classList.remove('hidden');
        }

        // Popula Select de Provedores
        selectProvedor.innerHTML = '';
        cfg.provedores_disponiveis.forEach(prov => {
            const opt = document.createElement('option');
            opt.value = prov.id;
            opt.textContent = prov.nome;
            if (prov.id === cfg.provedor_ativo) {
                opt.selected = true;
            }
            selectProvedor.appendChild(opt);
        });

        // Atualiza campos
        inputModelo.value = cfg.modelo_ativo || '';
        inputBaseUrl.value = cfg.base_url || '';
        inputTimeout.value = cfg.timeout_segundos || 120;

        if (cfg.tem_chave) {
            badgeChaveStatus.className = 'key-status-badge configurado';
            badgeChaveStatus.textContent = `Configurada (${cfg.chave_mascarada})`;
            inputChaveApi.placeholder = 'Chave já configurada (digite para alterar)';
        } else {
            badgeChaveStatus.className = 'key-status-badge';
            badgeChaveStatus.textContent = 'Não configurada';
            inputChaveApi.placeholder = 'Cole sua chave de API';
        }

        atualizarDescricaoProvedor();
    }

    function atualizarDescricaoProvedor() {
        if (!estado.config) return;
        const provedorId = selectProvedor.value;
        const prov = estado.config.provedores_disponiveis.find(p => p.id === provedorId);
        if (prov) {
            hintProvedorDesc.textContent = prov.descricao;
            grupoBaseUrl.classList.toggle('hidden', !prov.requer_base_url);
            if (!inputModelo.value || inputModelo.value.includes('/')) {
                inputModelo.value = prov.modelo_padrao;
            }
        }
    }

    selectProvedor.addEventListener('change', () => {
        atualizarDescricaoProvedor();
        feedbackTesteChave.classList.add('hidden');
    });

    // Toggle de visibilidade da senha
    btnToggleSenha.addEventListener('click', () => {
        if (inputChaveApi.type === 'password') {
            inputChaveApi.type = 'text';
            btnToggleSenha.textContent = '🔒';
        } else {
            inputChaveApi.type = 'password';
            btnToggleSenha.textContent = '👁️';
        }
    });


    // =========================================================================
    // TESTAR CHAVE DE IA
    // =========================================================================
    btnTestarChave.addEventListener('click', async () => {
        const provedorId = selectProvedor.value;
        const chave = inputChaveApi.value.trim();
        const modelo = inputModelo.value.trim();
        const baseUrl = inputBaseUrl.value.trim();

        feedbackTesteChave.className = 'alert alert-warning';
        feedbackTesteIcon.textContent = '⏳';
        feedbackTesteMsg.textContent = 'Realizando chamada mínima de teste via LiteLLM...';
        feedbackTesteChave.classList.remove('hidden');
        btnTestarChave.disabled = true;

        try {
            const resp = await fetch('/api/test-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provedor_id: provedorId,
                    chave: chave,
                    modelo: modelo,
                    base_url: baseUrl
                })
            });

            const data = await resp.json();
            btnTestarChave.disabled = false;

            if (data.sucesso) {
                feedbackTesteChave.className = 'alert alert-success';
                feedbackTesteIcon.textContent = '✅';
                feedbackTesteMsg.textContent = data.mensagem;
            } else {
                feedbackTesteChave.className = 'alert alert-danger';
                feedbackTesteIcon.textContent = '❌';
                feedbackTesteMsg.textContent = data.mensagem;
            }
        } catch (err) {
            btnTestarChave.disabled = false;
            feedbackTesteChave.className = 'alert alert-danger';
            feedbackTesteIcon.textContent = '❌';
            feedbackTesteMsg.textContent = `Erro ao comunicar com o servidor: ${err.message}`;
        }
    });


    // =========================================================================
    // SALVAR CONFIGURAÇÃO
    // =========================================================================
    btnSalvarConfig.addEventListener('click', async () => {
        const provedorId = selectProvedor.value;
        const chave = inputChaveApi.value.trim();
        const modelo = inputModelo.value.trim();
        const baseUrl = inputBaseUrl.value.trim();
        const timeout = parseInt(inputTimeout.value) || 120;

        btnSalvarConfig.disabled = true;
        btnSalvarConfig.innerHTML = '<span class="btn-icon">⏳</span> Salvando...';

        try {
            const resp = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provedor_id: provedorId,
                    chave: chave,
                    modelo: modelo,
                    base_url: baseUrl,
                    timeout: timeout
                })
            });

            const data = await resp.json();
            btnSalvarConfig.disabled = false;
            btnSalvarConfig.innerHTML = '<span class="btn-icon">💾</span> Salvar Configurações';

            if (data.sucesso) {
                estado.config = data.config;
                atualizarInterfaceConfiguracao(data.config);
                inputChaveApi.value = ''; // Limpa campo de texto puro

                feedbackTesteChave.className = 'alert alert-success';
                feedbackTesteIcon.textContent = '💾';
                feedbackTesteMsg.textContent = 'Configurações gravadas com sucesso no arquivo .env!';
                feedbackTesteChave.classList.remove('hidden');
            } else {
                feedbackTesteChave.className = 'alert alert-danger';
                feedbackTesteIcon.textContent = '❌';
                feedbackTesteMsg.textContent = data.mensagem || 'Falha ao salvar configuração.';
                feedbackTesteChave.classList.remove('hidden');
            }
        } catch (err) {
            btnSalvarConfig.disabled = false;
            btnSalvarConfig.innerHTML = '<span class="btn-icon">💾</span> Salvar Configurações';
            alert(`Erro ao salvar: ${err.message}`);
        }
    });


    // =========================================================================
    // SUGESTÃO DINÂMICA DE PASTA
    // =========================================================================
    let timeoutDebounce = null;
    inputIdeia.addEventListener('input', () => {
        if (estado.pastaSugeridaModificadaManual) return;
        clearTimeout(timeoutDebounce);
        timeoutDebounce = setTimeout(async () => {
            const ideia = inputIdeia.value.trim();
            if (ideia.length > 3) {
                try {
                    const resp = await fetch(`/api/suggest-folder?ideia=${encodeURIComponent(ideia)}`);
                    const data = await resp.json();
                    if (data.sucesso && !estado.pastaSugeridaModificadaManual) {
                        inputPasta.value = data.sugestao_relativa;
                        hintPastaAbsoluta.textContent = `Destino: ${data.sugestao_absoluta}`;
                    }
                } catch (e) {}
            }
        }, 400);
    });

    inputPasta.addEventListener('input', () => {
        estado.pastaSugeridaModificadaManual = true;
    });

    btnSugerirPasta.addEventListener('click', async () => {
        estado.pastaSugeridaModificadaManual = false;
        const ideia = inputIdeia.value.trim() || 'novo-projeto';
        const resp = await fetch(`/api/suggest-folder?ideia=${encodeURIComponent(ideia)}`);
        const data = await resp.json();
        if (data.sucesso) {
            inputPasta.value = data.sugestao_relativa;
            hintPastaAbsoluta.textContent = `Destino: ${data.sugestao_absoluta}`;
        }
    });


    // =========================================================================
    // INICIAR GERAÇÃO DO PROJETO
    // =========================================================================
    formNovoProjeto.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Verificação preventiva obrigatória de chave
        if (!estado.config || !estado.config.esta_configurado) {
            alert('Atenção: Você precisa configurar uma chave de IA antes de gerar o projeto.');
            alternarAba('tab-config');
            return;
        }

        const ideia = inputIdeia.value.trim();
        const pasta = inputPasta.value.trim();
        const implementarCodigo = checkImplementar.checked;

        if (!ideia) {
            alert('Por favor, descreva o que você quer construir.');
            inputIdeia.focus();
            return;
        }

        btnGerarProjeto.disabled = true;
        btnGerarProjeto.innerHTML = '<span class="btn-icon">⏳</span> Iniciando...';

        try {
            const resp = await fetch('/api/pipeline/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ideia: ideia,
                    pasta_projeto: pasta,
                    implementar_codigo: implementarCodigo
                })
            });

            const data = await resp.json();
            btnGerarProjeto.disabled = false;
            btnGerarProjeto.innerHTML = '<span class="btn-icon">🚀</span> Gerar Projeto';

            if (data.sucesso) {
                // Prepara UI de progresso
                progressoTituloIdeia.textContent = ideia;
                progressoCaminhoPasta.textContent = data.pasta_projeto;
                cardErroAmigavel.classList.add('hidden');
                progressoPulse.classList.remove('hidden');

                // Alterna para aba de progresso
                alternarAba('tab-progresso');

                // Inicia polling a cada 2s
                iniciarPollingProgresso();
            } else {
                if (data.bloqueado_por_configuracao) {
                    alert(data.mensagem);
                    alternarAba('tab-config');
                } else {
                    alert(`Falha ao iniciar: ${data.mensagem}`);
                }
            }
        } catch (err) {
            btnGerarProjeto.disabled = false;
            btnGerarProjeto.innerHTML = '<span class="btn-icon">🚀</span> Gerar Projeto';
            alert(`Erro na requisição: ${err.message}`);
        }
    });


    // =========================================================================
    // POLLING DE PROGRESSO (2 SEGUNDOS)
    // =========================================================================
    function iniciarPollingProgresso() {
        pararPollingProgresso();
        consultarStatusPipeline();
        estado.pollingInterval = setInterval(consultarStatusPipeline, 2000);
    }

    function pararPollingProgresso() {
        if (estado.pollingInterval) {
            clearInterval(estado.pollingInterval);
            estado.pollingInterval = null;
        }
    }

    async function consultarStatusPipeline() {
        try {
            let resp;
            if (estado.pastaMonitorada) {
                resp = await fetch(`/api/projeto/status?pasta=${encodeURIComponent(estado.pastaMonitorada)}`);
            } else {
                resp = await fetch('/api/pipeline/status');
            }
            const data = await resp.json();

            if (!data.sucesso || !data.status) return;

            const st = data.status;
            estado.ultimoStatus = st;

            atualizarTelaProgresso(st);

            // Se terminou a execução
            if (!st.em_execucao) {
                pararPollingProgresso();
                progressoPulse.classList.add('hidden');
                btnCancelarPipeline.disabled = true;

                if (st.sucesso === true) {
                    progressoTagStatus.className = 'metric-value status-tag status-concluido';
                    progressoTagStatus.textContent = 'Concluído';
                    renderizarResultado(st);
                } else if (st.sucesso === false) {
                    progressoTagStatus.className = 'metric-value status-tag status-falhou';
                    progressoTagStatus.textContent = 'Falhou';
                }
            } else {
                btnCancelarPipeline.disabled = false;
                progressoTagStatus.className = 'metric-value status-tag status-executando';
                progressoTagStatus.textContent = 'Em Execução';
            }
        } catch (err) {
            console.error('Erro ao consultar status:', err);
        }
    }

    function atualizarTelaProgresso(st) {
        progressoTempo.textContent = `${st.duracao_segundos}s`;

        const fasesDados = st.fases_dados || {};
        const fasesLista = fasesDados.fases || [];
        const percentual = fasesDados.progresso_percentual || 0;
        const concluidas = fasesDados.fases_concluidas || 0;
        const total = fasesDados.total_fases || (st.implementar_codigo ? 8 : 7);

        progressoBarraFill.style.width = `${percentual}%`;
        progressoTextoFases.textContent = `${concluidas} de ${total} fases concluídas`;
        progressoTextoPorcentagem.textContent = `${percentual}%`;

        // Renderizar Cards de Fases
        containerFasesGrid.innerHTML = '';
        fasesLista.forEach(f => {
            const card = document.createElement('div');
            card.className = `phase-card phase-${f.status}`;

            let icon = '⏳';
            let badgeClass = 'pendente';
            let badgeTexto = 'Pendente';

            if (f.status === 'concluida') {
                icon = '✅';
                badgeClass = 'concluida';
                badgeTexto = 'Concluída';
            } else if (f.status === 'rodando') {
                icon = '🔄';
                badgeClass = 'rodando';
                badgeTexto = 'Em Execução';
            } else if (f.status === 'falhou') {
                icon = '❌';
                badgeClass = 'falhou';
                badgeTexto = 'Falhou';
            }

            const tokensStr = f.tokens_consumidos > 0 ? `• ${f.tokens_consumidos} tokens` : '';
            const tempoStr = f.duracao_segundos > 0 ? `${f.duracao_segundos.toFixed(1)}s` : '';

            card.innerHTML = `
                <div class="phase-left">
                    <div class="phase-icon">${icon}</div>
                    <div class="phase-info">
                        <h4>${f.nome}</h4>
                        <p>${f.subtitulo}</p>
                    </div>
                </div>
                <div class="phase-meta">
                    <span>${tempoStr} ${tokensStr}</span>
                    <span class="phase-badge ${badgeClass}">${badgeTexto}</span>
                </div>
            `;
            containerFasesGrid.appendChild(card);
        });

        // Tratamento de Erro Amigável
        if (st.sucesso === false || st.erro_amigavel) {
            cardErroAmigavel.classList.remove('hidden');
            erroAmigavelTexto.textContent = st.erro_amigavel || 'Ocorreu um erro inesperado durante a execução do pipeline.';

            if (st.precisa_configuracao) {
                erroAcaoContainer.classList.remove('hidden');
            } else {
                erroAcaoContainer.classList.add('hidden');
            }

            erroTecnicoLog.textContent = st.erro_tecnico || (st.logs || []).join('\n') || 'Nenhum log técnico capturado.';
        } else {
            cardErroAmigavel.classList.add('hidden');
        }

        // Terminal de logs
        if (st.logs && st.logs.length > 0) {
            terminalLogsBody.innerHTML = st.logs.map(l => `<div class="log-line">${escapeHtml(l)}</div>`).join('');
            terminalLogsBody.scrollTop = terminalLogsBody.scrollHeight;
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }


    // =========================================================================
    // CANCELAR PIPELINE
    // =========================================================================
    btnCancelarPipeline.addEventListener('click', async () => {
        if (!confirm('Deseja realmente cancelar a execução do pipeline em andamento?')) return;

        btnCancelarPipeline.disabled = true;
        try {
            await fetch('/api/pipeline/cancel', { method: 'POST' });
        } catch (e) {
            console.error('Erro ao cancelar:', e);
        }
    });


    // =========================================================================
    // RENDERIZAR RESULTADO FINAL
    // =========================================================================
    function renderizarResultado(st) {
        resultadoVazio.classList.add('hidden');
        resultadoConteudo.classList.remove('hidden');

        resultadoTituloProjeto.textContent = st.ideia || 'Projeto Concluído';
        resultadoPastaCaminho.textContent = st.pasta_projeto || '-';

        const fd = st.fases_dados || {};

        // Score Auto-crítica
        if (fd.score_final !== null && fd.score_final !== undefined) {
            resultadoScoreValor.textContent = `${fd.score_final}/100`;
        } else {
            resultadoScoreValor.textContent = '100/100';
        }

        // Gates
        resultadoGatesValor.textContent = `${fd.gates_passaram || 0} / ${(fd.gates_passaram || 0) + (fd.gates_falharam || 0)}`;
        resultadoGatesSub.textContent = (fd.gates_falharam === 0) ? 'Todos os gates aprovados' : `${fd.gates_falharam} gate(s) com atenção`;

        // Tokens
        resultadoTokensValor.textContent = (fd.tokens_totais_consumidos || 0).toLocaleString();

        // Testes Fase 8
        if (fd.resultado_testes) {
            cardResultadoTestes.classList.remove('hidden');
            const rt = fd.resultado_testes;
            resultadoTestesValor.textContent = `${rt.passaram} / ${rt.coletados}`;
            resultadoTestesSub.textContent = rt.todos_passaram ? '100% dos testes passando' : `${rt.falharam} falha(s)`;
            resultadoTestesValor.className = rt.todos_passaram ? 'stat-value text-success' : 'stat-value text-accent';
        } else {
            cardResultadoTestes.classList.add('hidden');
        }

        // Diagnóstico Auto-crítica
        if (fd.autocritica) {
            const ac = fd.autocritica;
            if (ac.pontos_fortes && ac.pontos_fortes.length > 0) {
                listaPontosFortes.innerHTML = ac.pontos_fortes.map(p => `<li>✓ ${escapeHtml(p)}</li>`).join('');
            } else {
                listaPontosFortes.innerHTML = '<li>✓ Estrutura arquitetural e templates gerados com integridade.</li>';
            }

            if (ac.pontos_fracos && ac.pontos_fracos.length > 0) {
                listaPontosFracos.innerHTML = ac.pontos_fracos.map(p => `<li>⚠️ ${escapeHtml(p)}</li>`).join('');
            } else {
                listaPontosFracos.innerHTML = '<li>Nenhuma inconformidade crítica identificada.</li>';
            }
        }
    }


    // =========================================================================
    // ABRIR PASTA NO WINDOWS EXPLORER
    // =========================================================================
    btnAbrirExplorer.addEventListener('click', async () => {
        const caminho = resultadoPastaCaminho.textContent;
        if (!caminho || caminho === '-') return;

        btnAbrirExplorer.disabled = true;
        btnAbrirExplorer.innerHTML = '<span class="icon">⏳</span> Abrindo...';

        try {
            const resp = await fetch('/api/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ caminho: caminho })
            });
            const data = await resp.json();
            btnAbrirExplorer.disabled = false;
            btnAbrirExplorer.innerHTML = '<span class="icon">📂</span> Abrir no Explorador de Arquivos';

            if (!data.sucesso) {
                alert(`Erro ao abrir pasta: ${data.mensagem}`);
            }
        } catch (err) {
            btnAbrirExplorer.disabled = false;
            btnAbrirExplorer.innerHTML = '<span class="icon">📂</span> Abrir no Explorador de Arquivos';
            alert(`Erro na chamada: ${err.message}`);
        }
    });

    // =========================================================================
    // MONITORAR PASTA ARBITRÁRIA
    // =========================================================================
    btnMonitorarPasta.addEventListener('click', async () => {
        const pasta = inputMonitorPasta.value.trim();
        if (!pasta) {
            alert('Informe o caminho de uma pasta de projeto para monitorar.');
            inputMonitorPasta.focus();
            return;
        }

        // Define a pasta monitorada e inicia o polling
        estado.pastaMonitorada = pasta;
        progressoTituloIdeia.textContent = 'Monitorando Projeto';
        progressoCaminhoPasta.textContent = pasta;
        cardErroAmigavel.classList.add('hidden');
        progressoPulse.classList.remove('hidden');

        // Alterna para aba de progresso e inicia polling
        alternarAba('tab-progresso');
        iniciarPollingProgresso();
    });

    // Permitir monitorar ao pressionar Enter no campo
    inputMonitorPasta.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            btnMonitorarPasta.click();
        }
    });


    // =========================================================================
    // WORKSPACE (PLANO-EXECUCAO-ESTRUTURADO.json)
    // =========================================================================
    async function carregarWorkspace() {
        try {
            const resp = await fetch('/api/workspace/status');
            const data = await resp.json();

            if (!data.sucesso || !data.workspace) {
                workspaceConteudo.classList.add('hidden');
                workspaceVazio.classList.remove('hidden');
                return;
            }

            const ws = data.workspace;
            workspaceConteudo.classList.remove('hidden');
            workspaceVazio.classList.add('hidden');

            workspaceObjetivo.textContent = ws.objetivo_geral || '-';
            workspaceData.textContent = ws.ultima_atualizacao || '-';
            workspaceCompletas.textContent = `${ws.etapas_completas} / ${ws.total_etapas}`;
            workspaceProgressoSub.textContent = `${ws.etapas_pendentes} pendente(s) • ${ws.etapas_parciais} parcial(is)`;

            const percentual = ws.progresso_percentual || 0;
            workspaceBarraFill.style.width = `${percentual}%`;
            workspaceTextoEtapas.textContent = `${ws.etapas_completas} de ${ws.total_etapas} etapas concluídas`;
            workspaceTextoPorcentagem.textContent = `${percentual}%`;

            // Renderizar lista de etapas
            workspaceEtapasGrid.innerHTML = '';
            (ws.etapas || []).forEach(etapa => {
                const statusUpper = (etapa.status || '').toUpperCase();
                let icon = '⏳';
                let badgeClass = 'pendente';
                let badgeTexto = 'Pendente';

                if (statusUpper.includes('COMPLETO')) {
                    icon = '✅';
                    badgeClass = 'concluida';
                    badgeTexto = 'Completo';
                } else if (statusUpper.includes('PARCIALMENTE')) {
                    icon = '🔄';
                    badgeClass = 'rodando';
                    badgeTexto = 'Parcialmente';
                }

                const card = document.createElement('div');
                card.className = `phase-card phase-${badgeClass}`;

                const metaParts = [];
                if (etapa.data_conclusao) metaParts.push(etapa.data_conclusao);
                if (etapa.commit) metaParts.push(`<code>${escapeHtml(etapa.commit)}</code>`);

                card.innerHTML = `
                    <div class="phase-left">
                        <div class="phase-icon">${icon}</div>
                        <div class="phase-info">
                            <h4>${escapeHtml(etapa.nome || etapa.id || 'Etapa')}</h4>
                            <p>${escapeHtml(etapa.id || '')}</p>
                        </div>
                    </div>
                    <div class="phase-meta">
                        <span>${metaParts.join(' • ')}</span>
                        <span class="phase-badge ${badgeClass}">${badgeTexto}</span>
                    </div>
                `;
                workspaceEtapasGrid.appendChild(card);
            });
        } catch (err) {
            console.error('Erro ao carregar workspace:', err);
            workspaceConteudo.classList.add('hidden');
            workspaceVazio.classList.remove('hidden');
        }
    }


    // Inicialização
    carregarConfiguracao();
});
