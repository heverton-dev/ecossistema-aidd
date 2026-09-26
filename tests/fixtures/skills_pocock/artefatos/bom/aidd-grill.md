### Consolidated Assumptions

1. Tamanho mínimo da senha? Recommended: 8 caracteres, because it is the common default.
2. O e-mail diferencia maiúsculas? Recommended: não, normalizar para minúsculas, because users type both.
3. `entrar` com usuário inexistente? Recommended: levantar `CredencialInvalida`, because it avoids revealing which e-mails exist.
