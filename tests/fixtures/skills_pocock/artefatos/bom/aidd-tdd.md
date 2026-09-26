## 0. Agree Test Seams

- `cadastrar(email, senha)`: devolve id novo; senha não fica em texto puro.
- `entrar(email, senha)`: devolve o id com a senha certa.

## Red

```python
def test_cadastrar_devolve_id():
    assert cadastrar("a@b.com", "segredo1") == 1
```
