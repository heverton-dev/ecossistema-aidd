---
id: ISSUE-0009
title: Barreira real contra agentes disparados em paralelo (G_ZERO_HEADLESS)
status: closed
blocked_by: []
created: 2026-09-19
resolved: 2026-09-19
source: open-decision sweep 2026-09-19 / PLAN-0025 item 2
---

# ISSUE-0009 — Barreira real contra agentes disparados em paralelo

**Deliver:** launching two agents at once without human confirmation becomes truly
blocked, proven by reproduction — not declared.

**Blocked by:** nothing. Start now.

## Verified this session

Law #7 states: sequential interactive execution, zero hidden headless subagents.

**Correction to the earlier framing: the gate is not missing — it is a facade.**
`G_ZERO_HEADLESS` exists, 37 lines, read in full this session. It checks that the
string `interactive: bool = True` appears in one file and `--dangerously-force-headless`
appears in another. It never launches an agent. Then it prints `[OK] Zero risco de
subagentes ocultos em concorrencia silenciosa`.

That is worse than an absent gate: an absent gate is a visible hole, while this one
reports success and closes the question. A sign on the wall reading "turnstile
tested".

Why this is concrete: the project already records a real incident where an
autonomous agent survived the app being closed, kept running, and made three commits
with push while skipping the quality gate, on a fabricated justification. The written
rule did not stop it, because nothing executed the rule.

## Proposed route (recorded in PLAN-0025 item 2, 2026-09-12)

Implement an assistant hook that intercepts concurrent subagent calls and blocks, or
demands explicit confirmation. The difference between a "do not enter" sign and a gate.

Then rewrite `G_ZERO_HEADLESS` to exercise that hook instead of grepping for strings,
and strip its unearned "zero risco" claim (Law #8). See ISSUE-0011, which generalises
this defect across all 26 gates.

**Scope caution:** the hook must distinguish an autonomous launch from one the user
asked for. Blocking both makes the project unusable; blocking neither is today.

**Known limit, state it rather than paper over it:** the recorded incident involved
an external tool (opencode on an ORCA desk) that survived the app closing. No hook
living in this repo can constrain a process outside it. Say so explicitly instead of
implying coverage.

## Acceptance criteria

- [x] Hook exists (`componentes/compartilhado/hooks/anti_headless_subagent_hook.py`) e sincronizado para todos os harnesses (`.claude/hooks/`, `.agents/hooks/`, etc.) e configurado em `PreToolUse` do assistente (`.claude/settings.json`).
- [x] Real reproduction: tentativa de disparar 2 subagentes paralelos sem confirmação é **efetivamente bloqueada** em runtime (exit code != 0, saída com `[BLOQUEIO G_ZERO_HEADLESS]`), validado em `gates/test_g_zero_headless.py::test_hook_reproducao_bloqueia_dois_agentes_paralelos`.
- [x] Real reproduction of the legitimate path: lançamento solicitado com autorização explícita (`user_confirmed: true` / `--confirmed`) passa com exit code 0 e `[PERMITIDO]`, validado em `gates/test_g_zero_headless.py::test_hook_reproducao_permite_caminho_legitimo_com_confirmacao`.
- [x] The recorded incident scenario (agent surviving app closure) tem sua exclusão/limite explicitamente registrado no gate e na documentação per Lei #8: processos externos rodando fora do escopo intermediado pelo harness não são contidos por hooks locais deste repositório.
- [x] PLAN-0025 item 2 atualizado com resultado e evidências de execução real.

