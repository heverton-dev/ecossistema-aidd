# RELATORIO-CAUSA-RAIZ

- **Comando**: `python -c "from calc import media; assert media([2, 4, 6]) == 4.0"`

HIPOTESES ATIVAS:
  - `media()` divide por `len - 1` em vez de `len`
