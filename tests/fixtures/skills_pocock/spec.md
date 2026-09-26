# Spec: cadastro de usuários (3 comportamentos)

Módulo Python `usuarios.py`, guardando os usuários em memória. Os testes ficam em `tests/`.

1. **Cadastrar:** `cadastrar(email, senha)` guarda o usuário e devolve o id novo. A senha nunca é guardada em texto puro.
2. **Rejeitar e-mail repetido:** cadastrar um e-mail que já existe levanta `EmailDuplicado`.
3. **Entrar:** `entrar(email, senha)` devolve o id quando a senha confere e levanta `CredencialInvalida` quando não confere.

Em aberto (ninguém decidiu): tamanho mínimo da senha; se o e-mail diferencia maiúsculas; o que `entrar` faz com usuário inexistente.
