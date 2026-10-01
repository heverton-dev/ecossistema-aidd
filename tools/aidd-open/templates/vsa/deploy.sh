#!/bin/bash
set -e

echo "🚀 [DEPLOY] Iniciando deploy na VPS..."
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d
echo "✅ [DEPLOY] Aplicação atualizada e rodando em produção!"
