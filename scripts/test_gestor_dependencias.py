# -*- coding: utf-8 -*-
"""Testes de unidade e integridade para gestor_dependencias.py.

Foco:
- Tratamento de ausência de npx (pre-check com shutil.which / npx.cmd)
- Tratamento de FileNotFoundError em POSIX
- Tradução de erro do cmd.exe no Windows
- Preservação do relatório estruturado (ja_instaladas, instaladas, falhas)
"""

import os
import subprocess
import pytest

import gestor_dependencias


class TestNpxDeteccao:
    def test_comando_requer_npx_positivo(self):
        assert gestor_dependencias._comando_requer_npx("npx impeccable install -y") is True
        assert gestor_dependencias._comando_requer_npx("cd /app && npx run build") is True
        assert gestor_dependencias._comando_requer_npx("npx.cmd install") is True

    def test_comando_requer_npx_negativo(self):
        assert gestor_dependencias._comando_requer_npx("pip install code-review-graph") is False
        assert gestor_dependencias._comando_requer_npx("git status") is False
        assert gestor_dependencias._comando_requer_npx("python ecossistema.py") is False

    def test_npx_disponivel_retorna_bool(self):
        res = gestor_dependencias._npx_disponivel()
        assert isinstance(res, bool)

    def test_npx_ausente_quando_which_retorna_none(self, monkeypatch):
        monkeypatch.setattr(gestor_dependencias.shutil, "which", lambda cmd: None)
        assert gestor_dependencias._npx_disponivel() is False

    def test_npx_presente_via_shutil(self, monkeypatch):
        monkeypatch.setattr(gestor_dependencias.shutil, "which", lambda cmd: "/usr/bin/npx" if cmd == "npx" else None)
        assert gestor_dependencias._npx_disponivel() is True

    def test_npx_presente_via_npx_cmd_no_windows(self, monkeypatch):
        monkeypatch.setattr(gestor_dependencias.os, "name", "nt")
        monkeypatch.setattr(
            gestor_dependencias.shutil,
            "which",
            lambda cmd: "C:\\Program Files\\nodejs\\npx.cmd" if cmd == "npx.cmd" else None,
        )
        assert gestor_dependencias._npx_disponivel() is True


class TestBootstrapSkillsTratamentoNpx:
    @pytest.fixture
    def manifesto_fake(self):
        return {
            "skills": {
                "skill_instalada_anteriormente": {
                    "pacote": "skill-ok",
                    "instalar": "npx skill-ok install",
                    "verificar": "nao_existe_mas_vamos_mockar",
                },
                "impeccable": {
                    "pacote": "impeccable",
                    "instalar": "npx impeccable install --scope=project -y",
                    "verificar": ".claude/skills/impeccable/SKILL.md",
                },
            }
        }

    def test_npx_ausente_aborta_graciosamente_com_diagnostico_claro(self, monkeypatch, manifesto_fake):
        """DoD 1, 2 e 3: sem npx, emite msg orientando preflight-host --fix e preserva relatorio."""
        monkeypatch.setattr(gestor_dependencias, "carregar_manifesto", lambda: manifesto_fake)
        monkeypatch.setattr(gestor_dependencias, "_npx_disponivel", lambda: False)

        # A primeira skill finge que já estava instalada
        def fake_instalada(cfg):
            return cfg["pacote"] == "skill-ok"

        monkeypatch.setattr(gestor_dependencias, "_skill_instalada", fake_instalada)

        relatorio = gestor_dependencias.bootstrap_skills()

        # ja_instaladas preservadas sem perda
        assert "skill_instalada_anteriormente" in relatorio["ja_instaladas"]
        assert len(relatorio["instaladas"]) == 0

        # falha registrada com a mensagem amigavel exata
        assert len(relatorio["falhas"]) == 1
        falha = relatorio["falhas"][0]
        assert "impeccable" in falha
        assert "Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix" in falha

    def test_posix_filenotfounderror_tratado_sem_traceback(self, monkeypatch, manifesto_fake):
        """POSIX: Se subprocess.run lançar FileNotFoundError, trata graciosamente."""
        monkeypatch.setattr(gestor_dependencias.os, "name", "posix")
        monkeypatch.setattr(gestor_dependencias, "carregar_manifesto", lambda: manifesto_fake)
        # Permite passar pelo pre-check inicial para simular a falha no spawn do subprocess
        monkeypatch.setattr(gestor_dependencias, "_npx_disponivel", lambda: True)
        monkeypatch.setattr(gestor_dependencias, "_skill_instalada", lambda cfg: False)

        def fake_run(*args, **kwargs):
            raise FileNotFoundError(2, "No such file or directory: 'npx'")

        monkeypatch.setattr(gestor_dependencias.subprocess, "run", fake_run)

        relatorio = gestor_dependencias.bootstrap_skills(apenas="impeccable")

        assert len(relatorio["falhas"]) == 1
        assert "Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix" in relatorio["falhas"][0]

    def test_windows_cmd_erro_traduzido(self, monkeypatch, manifesto_fake):
        """Windows: cmd.exe emitindo 'not recognized' é traduzido para mensagem amigável."""
        monkeypatch.setattr(gestor_dependencias.os, "name", "nt")
        monkeypatch.setattr(gestor_dependencias, "carregar_manifesto", lambda: manifesto_fake)
        # Permite passar pelo pre-check para exercitar o bloco do cmd.exe
        monkeypatch.setattr(gestor_dependencias, "_npx_disponivel", lambda: True)
        monkeypatch.setattr(gestor_dependencias, "_skill_instalada", lambda cfg: False)

        class FakeCompletedProcess:
            returncode = 1
            stdout = "'npx' is not recognized as an internal or external command"
            stderr = ""

        monkeypatch.setattr(gestor_dependencias.subprocess, "run", lambda *args, **kwargs: FakeCompletedProcess())

        relatorio = gestor_dependencias.bootstrap_skills(apenas="impeccable")

        assert len(relatorio["falhas"]) == 1
        assert "Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix" in relatorio["falhas"][0]

    def test_dry_run_nao_dispara_subprocess(self, monkeypatch, manifesto_fake):
        monkeypatch.setattr(gestor_dependencias, "carregar_manifesto", lambda: manifesto_fake)
        monkeypatch.setattr(gestor_dependencias, "_skill_instalada", lambda cfg: False)

        def explodir(*args, **kwargs):
            raise AssertionError("Subprocess nao deveria ser chamado em dry-run")

        monkeypatch.setattr(gestor_dependencias.subprocess, "run", explodir)

        relatorio = gestor_dependencias.bootstrap_skills(dry_run=True)
        assert len(relatorio["falhas"]) == 0
        assert any("[DRY-RUN]" in s for s in relatorio["instaladas"])
