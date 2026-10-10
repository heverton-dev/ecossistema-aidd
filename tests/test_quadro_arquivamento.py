import json
import os
import tempfile
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path("scripts").resolve()))
import estado_execucao
import quadro_leitor

def test_arquivamento_simulacao_nao_apaga_nada():
    import quadro_arquivador
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="pure", chave="antigo", titulo="Projeto Antigo") as ex:
                ex.etapa("fundacao", "concluida")
                run_id = ex.run_id
                
            # Forcar data de atualizacao para 40 dias atras no estado.json
            estado_path = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            dados = json.loads(estado_path.read_text(encoding="utf-8"))
            data_antiga = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
            dados["atualizado_em"] = data_antiga
            estado_path.write_text(json.dumps(dados), encoding="utf-8")
            
            # Executar dry-run (sem confirmar)
            candidatos = quadro_arquivador.executar_arquivamento(raiz_aidd=Path(tmpdir), dias=30, confirmar=False)
            assert len(candidatos) == 1
            assert candidatos[0]["run_id"] == run_id
            
            # Garantir que NADA foi apagado e nenhum .zip foi criado
            assert estado_path.exists(), "Estado original nao deveria ter sido apagado"
            pasta_arquivo = Path(tmpdir) / "arquivo"
            assert not pasta_arquivo.exists() or len(list(pasta_arquivo.glob("*.zip"))) == 0
        finally:
            os.environ.pop("AIDD_HOME", None)

def test_arquivamento_com_confirmar_compacta_e_leitor_acessa():
    import quadro_arquivador
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="pure", chave="antigo-2", titulo="Projeto Antigo 2") as ex:
                ex.etapa("fundacao", "concluida")
                run_id = ex.run_id
                
            estado_path = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            dados = json.loads(estado_path.read_text(encoding="utf-8"))
            data_antiga = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
            dados["atualizado_em"] = data_antiga
            estado_path.write_text(json.dumps(dados), encoding="utf-8")
            
            # Executar com confirmar=True
            arquivados = quadro_arquivador.executar_arquivamento(raiz_aidd=Path(tmpdir), dias=30, confirmar=True)
            assert len(arquivados) == 1
            
            # Pasta original removida
            assert not estado_path.exists(), "Pasta original deveria ter sido limpa apos compactacao"
            
            # .zip gerado
            pasta_arquivo = Path(tmpdir) / "arquivo"
            zips = list(pasta_arquivo.glob("*.zip"))
            assert len(zips) >= 1
            
            # Leitor do quadro acessa transparentemente a execucao arquivada
            leitor = quadro_leitor.QuadroLeitor(raiz_aidd=Path(tmpdir))
            ex_recuperada = leitor.obter_execucao(run_id)
            assert ex_recuperada is not None
            assert ex_recuperada["run_id"] == run_id
            assert ex_recuperada["titulo"] == "Projeto Antigo 2"
        finally:
            os.environ.pop("AIDD_HOME", None)
