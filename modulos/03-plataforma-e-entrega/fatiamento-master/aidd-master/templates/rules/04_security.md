# 🛡️ Segurança & Zero Vazamentos
- Senhas com PBKDF2-HMAC-SHA256 e comparação de tempo constante hmac.compare_digest.
- Parâmetros preparados em todas as consultas de banco de dados (Zero SQL Injection).
- Scanner de Entropia de Shannon (> 4.6 bits) ativo em G_SEGREDOS.py.
