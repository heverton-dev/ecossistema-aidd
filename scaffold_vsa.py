import os
from pathlib import Path

def create_vsa_scaffold():
    root = Path("modulos")
    
    directories = [
        "01-governanca-e-qualidade/core",
        "01-governanca-e-qualidade/skills",
        "01-governanca-e-qualidade/gates",
        "01-governanca-e-qualidade/tests",
        "01-governanca-e-qualidade/prompts",
        "01-governanca-e-qualidade/docs",
        
        "02-triade-motores/fluxo-01-pure/core",
        "02-triade-motores/fluxo-01-pure/templates",
        "02-triade-motores/fluxo-01-pure/skills",
        "02-triade-motores/fluxo-01-pure/gates",
        "02-triade-motores/fluxo-01-pure/tests",
        
        "02-triade-motores/fluxo-02-open/core",
        "02-triade-motores/fluxo-02-open/templates",
        "02-triade-motores/fluxo-02-open/skills",
        "02-triade-motores/fluxo-02-open/gates",
        "02-triade-motores/fluxo-02-open/tests",
        
        "02-triade-motores/fluxo-03-freedom/core",
        "02-triade-motores/fluxo-03-freedom/scripts",
        "02-triade-motores/fluxo-03-freedom/skills",
        "02-triade-motores/fluxo-03-freedom/gates",
        "02-triade-motores/fluxo-03-freedom/tests",
        
        "03-plataforma-e-entrega/fatiamento-master",
        "03-plataforma-e-entrega/blindagem-enterprise",
        "03-plataforma-e-entrega/operacoes-ops",
        "03-plataforma-e-entrega/quarteto-studios",
        "03-plataforma-e-entrega/skills",
        "03-plataforma-e-entrega/gates",
        "03-plataforma-e-entrega/contracts",
        "03-plataforma-e-entrega/tests",
        
        "04-nucleo-compartilhado/cli",
        "04-nucleo-compartilhado/sync",
        "04-nucleo-compartilhado/contracts",
        "04-nucleo-compartilhado/scripts",
        "04-nucleo-compartilhado/gates",
        "04-nucleo-compartilhado/tests",
    ]
    
    for d in directories:
        dir_path = root / d
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create empty __init__.py for Python packages where applicable
        if dir_path.name in ("core", "skills", "gates", "tests", "scripts", "fatiamento-master", "blindagem-enterprise", "operacoes-ops", "quarteto-studios", "cli", "sync", "contracts"):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    print("Estrutura VSA base criada com sucesso em modulos/")

if __name__ == "__main__":
    create_vsa_scaffold()
