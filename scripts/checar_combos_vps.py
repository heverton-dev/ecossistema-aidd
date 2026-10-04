import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-9router" / "scripts"))
from deploy_vps import conectar, rodar

c = conectar()
code, out = rodar(c, """
docker service update --force ninerouter_ninerouter
sleep 5
cid=$(docker ps -q --filter name=ninerouter_ninerouter)
echo "Novo container: $cid"
""")
print(out)
c.close()
