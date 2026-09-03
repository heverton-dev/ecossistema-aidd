#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_CYBERSECURITY_OWASP — Varredura de vulnerabilidades OWASP Top 10.

Escaneia código Python gerado pelo pipeline AIDD em busca de:
  - Injeção SQL (OWASP A03:2021)
  - Vulnerabilidades de autenticação (OWASP A07:2021)
  - IDOR — Insecure Direct Object Reference (OWASP A01:2021)
  - Credenciais hardcoded (OWASP A07:2021)
  - XSS via template rendering (OWASP A03:2021)
  - Uso inseguro de eval/exec (OWASP A03:2021)
  - Deserialização insegura (OWASP A08:2021)

Falha com exit 1 se encontrar vulnerabilidades de severidade Alta ou Crítica.

Uso:
    python scripts/gates/G_CYBERSECURITY_OWASP.py <pasta_projeto>
    python scripts/gates/G_CYBERSECURITY_OWASP.py --cache-dir .aidd/cache

Princípio AIDD: Gate mecânico — zero LLM, 100% determinístico (regex + AST).
"""

import sys
import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# MODELO DE VULNERABILIDADE
# =============================================================================

@dataclass
class Vulnerabilidade:
    """Representa uma vulnerabilidade encontrada."""
    vuln_id: str
    owasp_categoria: str
    severidade: str  # Critica, Alta, Media, Baixa
    descricao: str
    arquivo: str
    linha: int
    trecho: str
    recomendacao: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'vuln_id': self.vuln_id,
            'owasp_categoria': self.owasp_categoria,
            'severidade': self.severidade,
            'descricao': self.descricao,
            'arquivo': self.arquivo,
            'linha': self.linha,
            'trecho': self.trecho,
            'recomendacao': self.recomendacao,
        }


# =============================================================================
# PADRÕES DE VULNERABILIDADE (regex-based scanning)
# =============================================================================

# A03:2021 — Injection (SQL Injection)
PADROES_SQL_INJECTION = [
    (
        r'''(?:execute|cursor\.execute|raw|query)\s*\(\s*(?:f["\']|["\'].*%s|["\'].*\%s|["\'].*\.format)''',
        'Alta',
        'SQL query com interpolação de string (possível SQL injection)',
        'Use parameterized queries: cursor.execute("SELECT * FROM t WHERE id = %s", (id,))',
    ),
    (
        r'''(?:execute|raw|query)\s*\(\s*["\'].*(?:\+\s*\w+|\%\s*\w+|\{.*\})''',
        'Alta',
        'SQL query com concatenação/interpolação (possível SQL injection)',
        'Use parameterized queries ou ORM (SQLAlchemy, Django ORM)',
    ),
    (
        r'''\.format\s*\(.*(?:execute|raw|query)''',
        'Alta',
        'String .format() usada em query SQL (SQL injection)',
        'Use parameterized queries em vez de .format()',
    ),
    (
        r'''(?:f["\']SELECT|f["\']INSERT|f["\']UPDATE|f["\']DELETE|f["\']DROP)''',
        'Critica',
        'F-string diretamente em statement SQL (SQL injection crítica)',
        'Use parameterized queries: cursor.execute("... WHERE id = %s", (var,))',
    ),
]

# A07:2021 — Identification and Authentication Failures
PADROES_AUTH = [
    (
        r'''(?:password|senha|passwd)\s*==\s*["\']''',
        'Critica',
        'Comparação de senha hardcoded (bypass de autenticação)',
        'Use hash + salt: bcrypt.checkpw(password, hashed)',
    ),
    (
        r'''(?:md5|sha1)\s*\(\s*(?:password|senha|passwd)''',
        'Alta',
        'Hash fraco (MD5/SHA1) para senha',
        'Use bcrypt, scrypt ou argon2 para hash de senhas',
    ),
    (
        r'''(?:verify\s*=\s*False|CERT_NONE|verify_ssl\s*=\s*False)''',
        'Alta',
        'Verificação SSL/TLS desabilitada',
        'Nunca desabilite verify=False em produção',
    ),
    (
        r'''(?:session|cookie)\[.*\]\s*=.*(?:admin|root|superuser)''',
        'Alta',
        'Sessão/cookie com valor de admin hardcoded',
        'Use autenticação baseada em token (JWT) com assinatura',
    ),
]

# A01:2021 — Broken Access Control (IDOR)
PADROES_IDOR = [
    (
        r'''(?:request\.(?:args|form|json|get)\s*\[?\s*["\']?(?:id|user_id|account_id|order_id))''',
        'Media',
        'Possível IDOR: ID de recurso vindo direto do request sem validação de ownership',
        'Valide que o recurso pertence ao usuário autenticado antes de acessá-lo',
    ),
    (
        r'''(?:GET|POST|PUT|DELETE)\s*.*(?:/(\{.*id\}|:(?:id|user_id)))''',
        'Media',
        'Rota com parâmetro ID dinâmico (verificar autorização)',
        'Implemente verificação de ownership: if resource.user_id != current_user.id: abort(403)',
    ),
]

# A07:2021 — Hardcoded Credentials
PADROES_CREDENCIAIS = [
    (
        r'''(?i)(?:api[_-]?key|secret[_-]?key|password|token|auth)\s*[:=]\s*["\'][A-Za-z0-9_\-./+=]{8,}["\']''',
        'Critica',
        'Credencial/segredo hardcoded no código-fonte',
        'Use variáveis de ambiente: os.environ.get("API_KEY")',
    ),
    (
        r'''(?:sk-[A-Za-z0-9]{20,}|AIzaSy[A-Za-z0-9_\-]{33}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36})''',
        'Critica',
        'Chave de API real detectada no código-fonte',
        'Remova a chave e use variável de ambiente',
    ),
    (
        r'''(?:AWS_SECRET_ACCESS_KEY|DATABASE_URL|MONGODB_URI)\s*=\s*["\'][^"\']+["\']''',
        'Critica',
        'Variável de ambiente de infraestrutura hardcoded',
        'Use os.environ.get() ou dotenv para carregar de .env',
    ),
]

# A03:2021 — Cross-Site Scripting (XSS)
PADROES_XSS = [
    (
        r'''(?:render_template_string|Markup)\s*\(\s*(?:request\.|f["\']|\+)''',
        'Alta',
        'Template rendering com input do usuário (possível XSS)',
        'Use render_template() com arquivos .html e escape automático (Jinja2)',
    ),
    (
        r'''(?:innerHTML|outerHTML|document\.write)\s*=.*(?:\+|f["\'])''',
        'Alta',
        'DOM manipulation com interpolação (possível XSS)',
        'Use textContent ou framework com auto-escape (React, Vue)',
    ),
    (
        r'''(?:\|\s*safe|autoescape\s+off|{% autoescape false %})''',
        'Media',
        'Auto-escape desabilitado em template (possível XSS)',
        'Nunca desabilite auto-escape; use |forceescape se necessário',
    ),
]

# A03:2021 — Command Injection / Code Injection
PADROES_INJECTION = [
    (
        r'''(?:eval|exec)\s*\(\s*(?:request\.|input\(|f["\']|\+)''',
        'Critica',
        'eval/exec com input do usuário (code injection crítica)',
        'Nunca use eval/exec com input externo; use ast.literal_eval() se precisar',
    ),
    (
        r'''(?:os\.system|subprocess\.call|subprocess\.run|subprocess\.Popen)\s*\(.*(?:request\.|input\(|f["\']|\+)''',
        'Alta',
        'Comando do sistema com input do usuário (command injection)',
        'Use subprocess.run([...], shell=False) com lista de argumentos',
    ),
    (
        r'''(?:os\.system|subprocess\.call|subprocess\.run|subprocess\.Popen)\s*\(.*shell\s*=\s*True''',
        'Alta',
        'Execução com shell=True (command injection)',
        'Use shell=False com lista de argumentos',
    ),
]

# A08:2021 — Software and Data Integrity Failures
PADROES_DESERIALIZACAO = [
    (
        r'''(?:pickle\.loads?|yaml\.load\s*\((?!.*Loader)|shelve\.open|marshal\.loads?)''',
        'Alta',
        'Deserialização insegura (pickle/yaml sem Loader)',
        'Use json para serialização; yaml.safe_load() para YAML',
    ),
    (
        r'''(?:pickle\.loads?\s*\(\s*(?:request\.|input\())''',
        'Critica',
        'Deserialização pickle com input externo (remote code execution)',
        'NUNCA deserialize pickle de fontes não confiáveis; use JSON',
    ),
]


# =============================================================================
# SCANNER
# =============================================================================

class ScannerOWASP:
    """Scanner de vulnerabilidades OWASP para código Python."""

    def __init__(self):
        self.categorias = [
            ('A03_SQL_INJECTION', 'A03:2021 — Injection', PADROES_SQL_INJECTION),
            ('A07_AUTH', 'A07:2021 — Auth Failures', PADROES_AUTH),
            ('A01_IDOR', 'A01:2021 — Broken Access Control', PADROES_IDOR),
            ('A07_CREDENCIAIS', 'A07:2021 — Hardcoded Credentials', PADROES_CREDENCIAIS),
            ('A03_XSS', 'A03:2021 — XSS', PADROES_XSS),
            ('A03_INJECTION', 'A03:2021 — Code/Command Injection', PADROES_INJECTION),
            ('A08_DESERIALIZACAO', 'A08:2021 — Data Integrity', PADROES_DESERIALIZACAO),
        ]

    def escanear_arquivo(self, caminho: Path, conteudo: str) -> List[Vulnerabilidade]:
        """Escaneia um arquivo em busca de todas as categorias de vulnerabilidade."""
        vulnerabilidades = []
        linhas = conteudo.split('\n')

        for cat_id, cat_nome, padroes in self.categorias:
            for idx, (padrao, severidade, descricao, recomendacao) in enumerate(padroes):
                for linha_num, linha in enumerate(linhas, 1):
                    # Pular comentários e linhas de teste
                    stripped = linha.strip()
                    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    if 'test' in str(caminho).lower() and 'assert' in stripped.lower():
                        continue

                    matches = re.finditer(padrao, linha)
                    for match in matches:
                        trecho = match.group(0)
                        # Limitar trecho a 100 chars
                        if len(trecho) > 100:
                            trecho = trecho[:100] + '...'

                        vuln_id = f'{cat_id}_{idx + 1}'
                        vulnerabilidades.append(Vulnerabilidade(
                            vuln_id=vuln_id,
                            owasp_categoria=cat_nome,
                            severidade=severidade,
                            descricao=descricao,
                            arquivo=str(caminho),
                            linha=linha_num,
                            trecho=trecho,
                            recomendacao=recomendacao,
                        ))

        return vulnerabilidades

    def escanear_diretorio(self, pasta: Path) -> List[Vulnerabilidade]:
        """Escaneia todos os arquivos Python de um diretório recursivamente."""
        excluidos = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', '.aidd', 'tests', 'gates'}
        vulnerabilidades = []

        for py_file in sorted(pasta.rglob('*.py')):
            partes = py_file.relative_to(pasta).parts
            if any(p in excluidos for p in partes):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()
            except OSError:
                continue

            caminho_relativo = py_file.relative_to(pasta)
            vulns = self.escanear_arquivo(caminho_relativo, conteudo)
            vulnerabilidades.extend(vulns)

        return vulnerabilidades


# =============================================================================
# MAIN
# =============================================================================

def executar_gate(pasta_projeto: Path) -> int:
    """Executa o gate de cibersegurança OWASP. Retorna 0 (passou) ou 1 (falhou)."""

    print("\n" + "=" * 70)
    print("GATE: G_CYBERSECURITY_OWASP — Varredura OWASP Top 10")
    print("=" * 70 + "\n")

    if not pasta_projeto.exists():
        print(f"❌ Pasta do projeto não encontrada: {pasta_projeto}")
        print("=" * 70)
        print("❌ GATE FALHOU")
        print("=" * 70)
        return 1

    scanner = ScannerOWASP()
    vulnerabilidades = scanner.escanear_diretorio(pasta_projeto)

    # Filtrar duplicatas (mesmo vuln_id + mesmo arquivo + mesma linha)
    vistos = set()
    vulns_unicas = []
    for v in vulnerabilidades:
        chave = (v.vuln_id, v.arquivo, v.linha)
        if chave not in vistos:
            vistos.add(chave)
            vulns_unicas.append(v)

    vulnerabilidades = vulns_unicas

    # Classificar por severidade
    criticas = [v for v in vulnerabilidades if v.severidade == 'Critica']
    altas = [v for v in vulnerabilidades if v.severidade == 'Alta']
    medias = [v for v in vulnerabilidades if v.severidade == 'Media']
    baixas = [v for v in vulnerabilidades if v.severidade == 'Baixa']

    # Relatório
    print(f"🔍 Varredura concluída\n")
    print(f"📊 Resumo de vulnerabilidades:")
    print(f"   🔴 Críticas:  {len(criticas)}")
    print(f"   🟠 Altas:     {len(altas)}")
    print(f"   🟡 Médias:    {len(medias)}")
    print(f"   🟢 Baixas:    {len(baixas)}")
    print(f"   📋 Total:     {len(vulnerabilidades)}")
    print()

    if vulnerabilidades:
        print("-" * 70)
        print("DETALHAMENTO:")
        print("-" * 70)

        for v in sorted(vulnerabilidades, key=lambda x: ['Critica', 'Alta', 'Media', 'Baixa'].index(x.severidade)):
            icon = {'Critica': '🔴', 'Alta': '🟠', 'Media': '🟡', 'Baixa': '🟢'}[v.severidade]
            print(f"\n  {icon} [{v.severidade}] {v.owasp_categoria}")
            print(f"     Arquivo: {v.arquivo}:{v.linha}")
            print(f"     Problema: {v.descricao}")
            print(f"     Trecho: {v.trecho}")
            print(f"     Fix: {v.recomendacao}")

    # Gate falha se houver vulnerabilidades Alta ou Crítica
    vulns_bloqueantes = criticas + altas

    print("\n" + "=" * 70)
    if vulns_bloqueantes:
        print(f"❌ GATE FALHOU — {len(vulns_bloqueante := vulns_bloqueantes)} vulnerabilidade(s) de severidade Alta/Crítica")
        for v in vulns_bloqueantes:
            print(f"   • [{v.severidade}] {v.descricao} ({v.arquivo}:{v.linha})")
        print("=" * 70 + "\n")
        return 1
    else:
        if vulnerabilidades:
            print(f"✅ GATE PASSOU — {len(vulnerabilidades)} vulnerabilidade(s) de severidade Média/Baixa (não bloqueante)")
        else:
            print("✅ GATE PASSOU — nenhuma vulnerabilidade encontrada")
        print("=" * 70 + "\n")
        return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Gate OWASP: Varredura de vulnerabilidades em código gerado'
    )
    parser.add_argument(
        'pasta_projeto',
        nargs='?',
        default='.',
        help='Pasta raiz do projeto a ser analisado (default: diretório atual)',
    )
    parser.add_argument(
        '--cache-dir',
        help='Pasta de cache do projeto (alternativa a pasta_projeto)',
    )
    args = parser.parse_args()

    if args.cache_dir:
        pasta = Path(args.cache_dir)
    else:
        pasta = Path(args.pasta_projeto)

    return executar_gate(pasta)


if __name__ == '__main__':
    sys.exit(main())
