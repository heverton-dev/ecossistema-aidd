# 9Router on the VPS (24/7)

`scripts/deploy_vps.py` turns the local install into the Swarm stack `ninerouter` behind Traefik.

## What is carried over

- `db/data.sqlite` (providers, OAuth tokens, API keys, combos, settings) copied with SQLite's backup API, so it is consistent even while 9Router runs.
- `jwt-secret`, `machine-id`, `auth/cli-secret`: keep dashboard password and keys valid. Same image tag as local (`--versao`), so the database schema matches.
- OAuth providers (Kiro, Antigravity) kept working from the VPS IP. Provider `ollama-local` does not: it points to the PC.

## Security

- API key required and secure auth cookie are both on in the stack; the dashboard login is the same as the local one.
- Volume files are `600`, folders `700`; the upload package is deleted after extraction.
- DNS A record without Cloudflare proxy, same as the other Traefik services (Let's Encrypt via Traefik).

## Operating

- Re-run is safe: an existing volume is kept unless `--sobrescrever-dados`; identical stack spec does not restart the service.
- After the first deploy: set `NINEROUTER_URL=https://<sub>.<domain>` in `.env`, run `scripts/orca_9router.py --aplicar`, then `scripts/doctor.py`.
- Turn the local 9Router off afterwards, or keep it as a fallback knowing its database diverges.
- Logs: `docker service logs --tail 50 ninerouter_ninerouter`. Rollback: `docker stack rm ninerouter` (the volume stays).
- Password reset on the VPS (from the 9Router README, not exercised yet): remove the `password` field from the `settings` row in the volume database, set `INITIAL_PASSWORD` on the service, `docker service update --force ninerouter_ninerouter`, log in and change it.
