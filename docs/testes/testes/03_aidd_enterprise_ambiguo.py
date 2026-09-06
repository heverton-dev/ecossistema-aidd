import sys
import os

def test_ambiguo():
    sys.path.insert(0, os.path.abspath('tools/aidd-enterprise/src/core'))
    from detector_camada import detectar_de_texto

    result = detectar_de_texto('crie uma regra de hook para governança')
    print(f"Sucesso: {result.sucesso}")
    print(f"Codigo: {result.codigo}")
    print(f"Detalhes: {result.detalhes}")

    if not result.sucesso and result.codigo == 'TIPO_AMBIGUO':
        cands = result.detalhes.get('candidatos', [])
        if 'rule' in cands and 'hook' in cands:
            print("SUCESSO: TIPO_AMBIGUO comprovado com 'rule' e 'hook'.")
            sys.exit(0)
    
    print("FALHA: TIPO_AMBIGUO não comprovado adequadamente.")
    sys.exit(1)

if __name__ == '__main__':
    test_ambiguo()
