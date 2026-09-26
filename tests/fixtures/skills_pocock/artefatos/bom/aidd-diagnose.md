# RELATORIO-CAUSA-RAIZ

- **Comando**: `python -c "from calc import media; assert media([2, 4, 6]) == 4.0"`
- 3 execuções com o mesmo resultado (AssertionError)

## Hipóteses candidatas

1. `media()` divide por `len - 1` em vez de `len`. Refutada se `media([2, 4, 6])` dividir 12 por 3.
2. `sum()` recebe strings em vez de números. Refutada se os valores forem `int`.
3. Erro de arredondamento de float. Refutada se `12 / 3` der exato.

HIPOTESES ATIVAS:
  - `media()` divide por `len - 1` em vez de `len`
