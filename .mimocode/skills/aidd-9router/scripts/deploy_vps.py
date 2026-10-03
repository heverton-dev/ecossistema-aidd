#!/usr/bin/env python3
"""Sobe o 9Router 24/7 na VPS (Swarm + Traefik) preservando provedores, chaves e combos.

Uso:
  python scripts/deploy_vps.py [--subdominio 9router] [--versao 0.5.95] [--dry-run]
                               [--sobrescrever-dados] [--sem-dados] [--pular-dns]

Etapas (idempotentes):
  1. copia consistente do banco local (API de backup do SQLite) + jwt-secret, machine-id,
     auth/cli-secret e catálogos -> pacote .tar.gz no scratch;
  2. SSH (VPS_HOST/PORT/USER + VPS_PASSWORD ou SSH_KEY_PATH do .env): volume ninerouter_data.
     Volume já existente NÃO é sobrescrito sem --sobrescrever-dados;
  3. stack `ninerouter` a partir de assets/ninerouter-stack.yml (rede TRAEFIK_NETWORK);
  4. DNS A não-proxied <subdominio>.<DEFAULT_ROOT_DOMAIN> -> VPS_HOST na Cloudflare;
  5. espera https://<host>/api/health = {"ok":true}.
Nenhum segredo é impresso. Saída: 0 no ar, 1 falha (etapa indicada).
"""
import argparse
import io
import json
import os
import shutil
import sqlite3
import string
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

from _comum import ler_env

PASTA_SKILL = Path(__file__).resolve().parent.parent
VOLUME = "ninerouter_data"
PASTA_REMOTA = "/root/9router-deploy"
ARQUIVOS_DADOS = ["jwt-secret", "machine-id", "auth/cli-secret", "model-catalog.json", "model-catalog-raw.json"]


def pasta_dados_local():
    candidatas = [Path(os.path.expandvars(r"%APPDATA%")) / "9router", Path.home() / ".9router"]
    return next((p for p in candidatas if (p / "db" / "data.sqlite").is_file()), None)


def empacotar(origem: Path) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        st = Path(tmp)
        (st / "db").mkdir()
        a = sqlite3.connect(f"file:{origem / 'db' / 'data.sqlite'}?mode=ro", uri=True)
        b = sqlite3.connect(st / "db" / "data.sqlite")
        a.backup(b)
        ok = b.execute("pragma integrity_check").fetchone()[0]
        combos = [r[0] for r in b.execute("select name from combos")]
        b.close(); a.close()
        if ok != "ok":
            raise RuntimeError(f"banco local corrompido: {ok}")
        for rel in ARQUIVOS_DADOS:
            if (origem / rel).is_file():
                (st / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem / rel, st / rel)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            t.add(st, arcname=".")
        print(f"  pacote: {len(buf.getvalue()) // 1024} KB, combos: {combos}")
        return buf.getvalue()


def conectar():
    import paramiko
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    chave = ler_env("SSH_KEY_PATH")
    c.connect(ler_env("VPS_HOST"), port=int(ler_env("VPS_PORT", "22")), username=ler_env("VPS_USER", "root"),
              password=None if chave else ler_env("VPS_PASSWORD"),
              key_filename=os.path.expanduser(chave) if chave else None, timeout=20)
    return c


def rodar(c, cmd):
    _, out, err = c.exec_command(cmd, timeout=600)
    codigo = out.channel.recv_exit_status()
    return codigo, out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")


def renderizar_stack(host, versao):
    modelo = (PASTA_SKILL / "assets" / "ninerouter-stack.yml").read_text(encoding="utf-8")
    return string.Template(modelo).substitute(
        VERSAO=versao, HOST=host, VOLUME=VOLUME, REDE=ler_env("TRAEFIK_NETWORK", "network_conexao"),
        ENTRYPOINT=ler_env("TRAEFIK_ENTRYPOINT", "websecure"),
        CERTRESOLVER=ler_env("TRAEFIK_CERTRESOLVER", "letsencryptresolver"))


def cloudflare(metodo, caminho, corpo=None):
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4{caminho}", method=metodo,
                                 data=json.dumps(corpo).encode() if corpo else None,
                                 headers={"Authorization": f"Bearer {ler_env('CLOUDFLARE_API_TOKEN')}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def garantir_dns(host, ip, dry_run):
    zona = ler_env("CLOUDFLARE_ZONE_ID")
    existentes = cloudflare("GET", f"/zones/{zona}/dns_records?name={host}")["result"]
    if existentes:
        print(f"  DNS já existe: {host} -> {existentes[0]['content']} (proxied={existentes[0]['proxied']})")
        return
    print(f"  {'[DRY-RUN] ' if dry_run else ''}criando A {host} -> {ip} (sem proxy, como os outros serviços do Traefik)")
    if not dry_run:
        cloudflare("POST", f"/zones/{zona}/dns_records", {"type": "A", "name": host, "content": ip, "proxied": False, "ttl": 1})


def esperar_health(host, segundos=240):
    fim = time.time() + segundos
    while time.time() < fim:
        try:
            with urllib.request.urlopen(f"https://{host}/api/health", timeout=15) as r:
                if json.loads(r.read()).get("ok"):
                    return True
        except Exception:
            pass
        time.sleep(10)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subdominio", default="9router")
    ap.add_argument("--versao", default="0.5.95", help="tag da imagem decolua/9router (igual à local)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sobrescrever-dados", action="store_true")
    ap.add_argument("--sem-dados", action="store_true", help="instalação limpa, sem copiar o banco local")
    ap.add_argument("--pular-dns", action="store_true")
    a = ap.parse_args()
    host = f"{a.subdominio}.{ler_env('DEFAULT_ROOT_DOMAIN')}"
    ip = ler_env("VPS_HOST")
    faltam = [k for k in ("VPS_HOST", "DEFAULT_ROOT_DOMAIN") if not ler_env(k)]
    if not (ler_env("VPS_PASSWORD") or ler_env("SSH_KEY_PATH")):
        faltam.append("VPS_PASSWORD ou SSH_KEY_PATH")
    if not a.pular_dns:
        faltam += [k for k in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ZONE_ID") if not ler_env(k)]
    if faltam:
        print(f"ERRO: faltam no .env: {', '.join(faltam)}", file=sys.stderr)
        return 1
    print(f"Destino: https://{host} (VPS {ip}, imagem decolua/9router:{a.versao})")

    print("1. dados")
    pacote = None
    if not a.sem_dados:
        origem = pasta_dados_local()
        if not origem:
            print("ERRO etapa 1: banco local do 9Router não encontrado", file=sys.stderr)
            return 1
        pacote = empacotar(origem)

    print("2. volume na VPS")
    if a.dry_run:
        print(f"  [DRY-RUN] criaria/atualizaria o volume {VOLUME}")
        print(f"3. [DRY-RUN] stack renderizado: {len(renderizar_stack(host, a.versao).splitlines())} linhas")
    else:
        c = conectar()
        rodar(c, f"mkdir -p {PASTA_REMOTA} && chmod 700 {PASTA_REMOTA}")
        existe = rodar(c, f"docker volume inspect {VOLUME} >/dev/null 2>&1")[0] == 0
        if pacote and (not existe or a.sobrescrever_dados):
            sftp = c.open_sftp()
            with sftp.file(f"{PASTA_REMOTA}/dados.tar.gz", "wb") as f:
                f.write(pacote)
            sftp.close()
            codigo, saida = rodar(c, (
                f"docker volume create {VOLUME} >/dev/null && docker run --rm -v {VOLUME}:/data -v {PASTA_REMOTA}:/src alpine sh -c "
                f"'cd /data && tar xzf /src/dados.tar.gz && find /data -type d -exec chmod 700 {{}} + && find /data -type f -exec chmod 600 {{}} +'"
                f" && rm -f {PASTA_REMOTA}/dados.tar.gz"))
            if codigo:
                print(f"ERRO etapa 2: {saida[-400:]}", file=sys.stderr)
                return 1
            print(f"  dados copiados para {VOLUME}")
        else:
            rodar(c, f"docker volume create {VOLUME} >/dev/null")
            print(f"  volume {VOLUME} {'mantido (já existe; use --sobrescrever-dados para trocar)' if existe else 'criado vazio'}")

        print("3. stack")
        sftp = c.open_sftp()
        with sftp.file(f"{PASTA_REMOTA}/ninerouter-stack.yml", "w") as f:
            f.write(renderizar_stack(host, a.versao))
        sftp.close()
        codigo, saida = rodar(c, f"cd {PASTA_REMOTA} && docker stack deploy -c ninerouter-stack.yml ninerouter")
        if codigo:
            print(f"ERRO etapa 3: {saida[-400:]}", file=sys.stderr)
            return 1
        print("  stack ninerouter aplicado")
        c.close()

    print("4. DNS")
    if a.pular_dns:
        print("  pulado")
    else:
        garantir_dns(host, ip, a.dry_run)

    if a.dry_run:
        print("5. [DRY-RUN] health não verificado")
        return 0
    print("5. health")
    if not esperar_health(host):
        print(f"ERRO etapa 5: https://{host}/api/health não respondeu ok", file=sys.stderr)
        return 1
    print(f"  no ar: https://{host}  (troque NINEROUTER_URL no .env e rode orca_9router.py --aplicar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
