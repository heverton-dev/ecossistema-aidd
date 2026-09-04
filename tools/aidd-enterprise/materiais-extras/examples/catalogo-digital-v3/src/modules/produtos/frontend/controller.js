const ProdutosModule = {
    cache: [],
    filtro: 'todos',
    async carregar() {
        const res = await fetch('/api/produtos');
        this.cache = await res.json();
        this.render();
    },
    filtrar(cat) {
        this.filtro = cat;
        document.querySelectorAll('.filter-pill').forEach(el => {
            el.className = el.innerText.includes(cat) || (cat === 'todos' && el.innerText.includes('Todos')) ? 'filter-pill active' : 'filter-pill';
        });
        this.render();
    },
    render(busca = '') {
        const grid = document.getElementById('products-grid');
        let lista = this.filtro === 'todos' ? this.cache : this.cache.filter(p => p.categoria.toLowerCase() === this.filtro.toLowerCase());
        if (busca) {
            lista = lista.filter(p => p.nome.toLowerCase().includes(busca.toLowerCase()));
        }
        grid.innerHTML = lista.map(p => `
            <div class="card">
                <div class="card-img-wrap">
                    <img src="${p.thumbnail}" class="card-img" alt="${p.nome}">
                    <span class="card-tag">${p.categoria}</span>
                    ${p.destaque ? '<span class="card-destaque">Destaque</span>' : ''}
                </div>
                <div class="card-body">
                    <div class="card-title">${p.nome}</div>
                    <div class="card-desc">${p.descricao}</div>
                    <div class="card-footer">
                        <div class="price-box">
                            ${p.preco_promo ? `<span class="price-old">R$ ${p.preco.toFixed(2)}</span><span class="price-current">R$ ${p.preco_promo.toFixed(2)}</span>` : `<span class="price-current">R$ ${p.preco.toFixed(2)}</span>`}
                        </div>
                        <button class="btn btn-gold" onclick="CarrinhoModule.adicionar(${p.id})">Adicionar</button>
                    </div>
                </div>
            </div>
        `).join('');
    }
};
