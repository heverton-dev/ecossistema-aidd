# =========================================================================
# AIDD v4 Enterprise — Production Dockerfile
# Optimized for High Concurrency, Clean Architecture & Extreme Performance
# =========================================================================

FROM python:3.12-slim AS runtime

# Criação de usuário sem privilégios de root (Princípio de Menor Privilégio OWASP)
RUN groupadd -g 10001 aiddgroup && \
    useradd -u 10001 -g aiddgroup -s /bin/bash -m aidduser

WORKDIR /app

# Variáveis de ambiente de produção
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3000 \
    ALLOW_ANONYMOUS=0 \
    DB_PATH=/app/data/suite.db

# Copia o código da aplicação
COPY --chown=aidduser:aiddgroup src/ /app/src/

# Cria o diretório de dados persistentes para SQLite WAL
RUN mkdir -p /app/data && chown -R aidduser:aiddgroup /app/data

USER aidduser

EXPOSE 3000

# Healthcheck nativo
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/openapi.json', timeout=2)" || exit 1

ENTRYPOINT ["python", "src/server.py"]
