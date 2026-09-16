# Item 1 — Corrigir test live

> **Escopo:** Encapsular e proteger `scripts/test_live.py` em `tools/aidd-master` e `tools/aidd-enterprise` para evitar execução indevida e falha de conexão HTTP durante a fase de coleta (`collection`) do pytest.
> **Status:** [CONCLUÍDO]
> **Nota Atual (0-10):** 0.0 — evidencia: pytest tools/aidd-master falhava com ConnectionRefusedError em scripts/test_live.py.
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** 10.0 — evidencia: scripts/test_live.py protegido com __test__ = False e main(); 2213 testes em 7 ferramentas executados com 100% de sucesso.

---

## Contexto ja investigado

- O arquivo `scripts/test_live.py` em `tools/aidd-master` e `tools/aidd-enterprise` contém chamadas HTTP de nível superior (`urllib.request.urlopen("http://localhost:3000")`) sem proteção de `if __name__ == "__main__":`.
- Por começar com o prefixo `test_`, o `pytest` tenta importá-lo automaticamente durante a fase de coleta, causando `urllib.error.URLError: [WinError 10061]` e quebrando o gate `G_TESTES_REAIS`.

## Definicao de Pronto

1. Encapsular a lógica de verificação em uma função (ex: `main()`) protegida por `if __name__ == "__main__":` em ambos os arquivos (`tools/aidd-master/scripts/test_live.py` e `tools/aidd-enterprise/scripts/test_live.py`).
2. Configurar o pytest ou renomear/marcar o script para que a suíte de testes unitários offline não tente conectar em portas de rede externas na fase de coleta.
3. Executar `pytest tools/aidd-master` e `pytest tools/aidd-enterprise` com 100% de sucesso.

## Criterio de saida

- Zero collection errors no pytest.
- Gate `G_TESTES_REAIS` aprovado em `aidd-master` e `aidd-enterprise`.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Corrigir test live.
1. Edite tools/aidd-master/scripts/test_live.py e tools/aidd-enterprise/scripts/test_live.py.
2. Encapsule o codigo de execucao em def main(): e proteja sob if __name__ == '__main__':.
3. Adicione no topo do arquivo skip caso seja importado por pytest ou renomeie/configure conforme a convencao do monorepo.
4. Execute pytest tools/aidd-master e pytest tools/aidd-enterprise e valide exit code 0.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Corrigir test live.
1. Edit tools/aidd-master/scripts/test_live.py and tools/aidd-enterprise/scripts/test_live.py.
2. Wrap top-level execution code inside def main(): and guard with if __name__ == '__main__':.
3. Prevent pytest from running HTTP calls during collection phase.
4. Run pytest tools/aidd-master and pytest tools/aidd-enterprise and ensure exit code 0.
```
