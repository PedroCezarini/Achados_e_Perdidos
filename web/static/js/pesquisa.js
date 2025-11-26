document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("#pesquisa").addEventListener("click", (e) => {
        const data = document.querySelector('#busca_data_encontrado').value;
        const categoria = document.querySelector('#busca_categoria').value;
        const identificacao = document.querySelector('#busca_identificacao').value;
        const local = document.querySelector('#busca_local_encontrado').value;

        const queryParams = new URLSearchParams();
        if (data) queryParams.append('data_encontrado', dataField);
        if (categoria) queryParams.append('categoria_id', categoriaIdField);
        if (identificacao) queryParams.append('identificacao', identificacaoField);
        if (local) queryParams.append('local_encontrado', localField);

        fetch(`busca?${queryParams.toString()}`, {mode: 'cors'})
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
                }
                return response.json();
            })
            .then(objetos => {
                console.log('Resultados da busca:', objetos);
                atualizarTabela(objetos);
            })
            .catch(error => {
                console.error('Erro ao buscar objetos:', error);
                alert('Ocorreu um erro ao realizar a busca. Tente novamente mais tarde.');
            });
    });
})

function atualizarTabela(objetos) {
    const tbody = document.querySelector("#objetos tbody");
    tbody.innerHTML = "";

    if (objetos.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4">Nenhum objeto encontrado com os filtros aplicados.</td>'; // Ajuste o colspan
        tbody.appendChild(row);
        return;
    }

    objetos.forEach(objeto => {
        const row = document.createElement('tr');
        const dataFormatada = objeto.data_encontrado ?
            objeto.data_encontrado.split('-').reverse().join('/') : '';

            let col = document.createElement('td');
            col.textContent = dataFormatada;

            row.appendChild(col)

            col = document.createElement('td');
            col.textContent = objeto.categoria_nome || 'N/A';

            row.appendChild(col)


            col = document.createElement('td');
            col.textContent = objeto.local_encontrado || '';

            row.appendChild(col)

        tbody.appendChild(row);
    });
}
