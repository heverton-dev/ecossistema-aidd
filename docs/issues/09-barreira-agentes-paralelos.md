---
id: ISSUE-0009
title: Barreira real contra agentes disparados em paralelo (G_ZERO_HEADLESS)
status: ready-for-agent
blocked_by: []
created: 2026-09-19
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

- [ ] Hook exists and is configured in the assistant.
- [ ] Real reproduction: an attempt to launch two parallel agents without confirmation is **actually blocked**, with the block visible in output. Hook code merely existing does not count.
- [ ] Real reproduction of the legitimate path: a launch the user explicitly asked for passes through.
- [ ] The recorded incident scenario (agent surviving app closure) is either covered, or its exclusion is written into the ticket — claim no coverage that was not tested.
- [ ] PLAN-0025 item 2 updated with outcome and evidence.
