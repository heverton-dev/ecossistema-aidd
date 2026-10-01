# 🌉 AIDD Bridge

> **Extrator, Unificador e Empacotador de Projetos Low-Code (Lovable, v0, Bolt) para VPS Própria.**

O **AIDD Bridge** liberta aplicações geradas em plataformas No-Code/Low-Code do aprisionamento de fornecedor (vendor lock-in), convertendo-as em código limpo, autônomo e pronto para produção em VPS particular.

---

## 🚀 Capacidades

1. **Scanner & Ingestor (`scan`):**
   - Inspeciona projetos React + Vite + Tailwind + Supabase.
   - Extrai páginas, componentes UI shadcn, rotas e migrações SQL.
   - Produz o `bridge-manifest.json`.

2. **Data Bridge: Supabase -> PostgreSQL Puro (`convert-db`):**
   - Sanitiza scripts SQL do Supabase.
   - Remove hooks proprietários da nuvem.
   - Prepara o `init-db.sql` e a emulação REST via PostgREST oficial (mantendo o cliente `@supabase/supabase-js` funcionando com zero refatoração).

3. **Multi-App Unifier (`merge`):**
   - Funde de 2 a N aplicações distintas em um único monorepo.
   - Organiza em Fatias Verticais (`src/modules/<app>/`).
   - Harmoniza dependências e gera um Roteador Central Unificado.

4. **DevOps & VPS Packager (`pack`):**
   - Gera `Dockerfile` multi-stage com Nginx Alpine (~25MB).
   - Gera `docker-compose.yml` com Web, PostgreSQL, PostgREST e Caddy/Traefik.
   - Emite certificados SSL HTTPS automáticos com Let's Encrypt para o seu domínio.

5. **Migração Real de Contas (`migrate-auth`):**
   - Migra contas de verdade (`auth.users`/`auth.identities`) de um Postgres de origem (ex.: Supabase Cloud) para o destino self-hosted, preservando o hash de senha — ninguém precisa trocar senha depois da migração.
   - Roda em modo preview por padrão (não grava nada); só aplica de verdade com `--apply`.

6. **Desinstalação Atômica (`destroy`):**
   - Remove a aplicação da VPS de ponta a ponta: stack Docker Swarm, volumes e registro DNS no Cloudflare.
   - Pede confirmação antes de agir, a menos que `--yes` seja passado.

---

## 💻 Uso via CLI do Ecossistema

```bash
# 1. Escanear projeto Lovable
python ecossistema.py bridge scan ./meu-app-lovable

# 2. Converter banco Supabase em PostgreSQL puro
python ecossistema.py bridge convert-db ./meu-app-lovable

# 3. Unificar múltiplos apps em um só
python ecossistema.py bridge merge ./app1 ./app2 ./app3 --output ./app-unificado

# 4. Gerar pacote de deploy para VPS com SSL
python ecossistema.py bridge pack ./app-unificado --domain app.meudominio.com

# 5. Migrar contas reais (senhas preservadas) do Supabase Cloud para o Postgres self-hosted
python ecossistema.py bridge migrate-auth --source postgres://... --target postgres://... --apply

# 6. Remover a aplicação da VPS (stack, volumes e DNS)
python ecossistema.py bridge destroy hub-teste --domain hub-teste.meudominio.com
```