#!/bin/bash
set -e

echo "🚀 [DEPLOY] Iniciando deploy na VPS..."
git pull origin main
python3 nginx/ssl/generate_ssl.py
docker compose down
docker compose build --no-cache
docker compose up -d
echo "✅ [DEPLOY] Aplicação atualizada e rodando em produção!"
