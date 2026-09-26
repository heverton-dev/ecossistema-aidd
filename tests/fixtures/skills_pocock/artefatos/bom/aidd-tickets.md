### [TICKET-01] Cadastrar usuário com senha protegida
- **Target Files:** usuarios.py, tests/test_cadastrar.py
- **Validation Command:** `pytest tests/test_cadastrar.py`
- **Blocked by:** none

### [TICKET-02] Rejeitar e-mail repetido
- **Target Files:** usuarios.py, tests/test_email_duplicado.py
- **Validation Command:** `pytest tests/test_email_duplicado.py`
- **Blocked by:** TICKET-01
