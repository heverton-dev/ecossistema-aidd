import os, pytest, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from services import LojaService

def test_catalogo_e_checkout_whatsapp(tmp_path):
    db_file = str(tmp_path / "test_loja.db")
    service = LojaService(db_file)
    service.seed_dados_iniciais()

    # 1. Configurações
    config = service.obter_configuracoes()
    assert "nome_loja" in config
    assert config["whatsapp"] == "5511999999999"

    # 2. Login Admin
    login_ok = service.autenticar_admin("admin@loja.com", "123456")
    assert login_ok["sucesso"] is True
    
    login_fail = service.autenticar_admin("admin@loja.com", "senha_errada")
    assert login_fail["sucesso"] is False

    # 3. Listagem de Produtos
    produtos = service.listar_produtos()
    assert len(produtos) == 5

    # 4. CRUD Produto (Admin)
    novo_prod = {
        "nome": "Webcam 4K Ultra HD",
        "descricao": "Microfone duplo com cancelamento de ruído.",
        "preco": 389.0,
        "preco_promo": 349.0,
        "categoria": "Periféricos",
        "thumbnail": "https://example.com/webcam.jpg",
        "destaque": 1
    }
    res_add = service.salvar_produto(novo_prod)
    assert res_add["sucesso"] is True
    pid = res_add["id"]

    prods_apos = service.listar_produtos(categoria="Periféricos")
    assert any(p["id"] == pid for p in prods_apos)

    # 5. Checkout WhatsApp
    carrinho = [
        {"id": pid, "nome": "Webcam 4K Ultra HD", "preco": 349.0, "qtd": 2}
    ]
    checkout = service.gerar_link_whatsapp(carrinho, "Heverton Peres")
    assert checkout["sucesso"] is True
    assert checkout["total"] == 698.0
    assert "https://api.whatsapp.com/send" in checkout["whatsapp_url"]
    assert "Webcam" in checkout["whatsapp_url"]

    # 6. Deletar Produto
    del_res = service.deletar_produto(pid)
    assert del_res["sucesso"] is True
