document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("#pesquisar").addEventListener("click", pesquisar)

    document.querySelector("#limpar").addEventListener("click", () => {
        document.querySelector('#busca_data_encontrado').value = '';
        document.querySelector('#busca_categoria').value = 0;
        document.querySelector('#busca_identificacao').value = '';
        document.querySelector('#busca_local_encontrado').value = '';
        pesquisar()
    })

    initTableSortingWithDelegation('objetos');
});

function pesquisar() {
    const data = document.querySelector('#busca_data_encontrado').value;
    const categoria = document.querySelector('#busca_categoria').value;
    const identificacao = document.querySelector('#busca_identificacao').value;
    const local = document.querySelector('#busca_local_encontrado').value;

    const queryParams = new URLSearchParams();
    if (data) queryParams.append('data_encontrado', data);
    if (categoria) queryParams.append('categoria_id', categoria);
    if (identificacao) queryParams.append('identificacao', identificacao);
    if (local) queryParams.append('local_encontrado', local);

    fetch(`busca?${queryParams.toString()}`, {mode: 'cors'})
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(objetos => {
            atualizarTabela(objetos);
        })
        .catch(error => {
            console.error('Erro ao buscar objetos:', error);
            alert('Ocorreu um erro ao realizar a busca. Tente novamente mais tarde.');
        });
}

function atualizarTabela(objetos) {
    const tbody = document.querySelector("#objetos tbody");
    tbody.innerHTML = "";

    if (objetos.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td class="text-center" colspan="4">Nenhum objeto encontrado com os filtros aplicados.</td>';
        tbody.appendChild(row);
        return;
    }

    objetos.forEach(objeto => {
        const row = document.createElement('tr');

        let col = document.createElement('td');
        col.textContent = formata_data(objeto.data_encontrado);
        row.appendChild(col)

        col = document.createElement('td');
        col.textContent = objeto.categoria_nome || '';
        row.appendChild(col)

        col = document.createElement('td');
        col.textContent = objeto.identificacao || '';
        row.appendChild(col)

        col = document.createElement('td');
        col.textContent = objeto.local_encontrado || '';
        row.appendChild(col)

        tbody.appendChild(row);
    });
}

function formata_data(value) {
    return value ? value.split('-').reverse().join('/') : ''
}

function initTableSortingWithDelegation(tableId) {
    const tabela = document.querySelector(`#${tableId}`);
    if (!tabela) {
        console.warn(`Table with ID '${tableId}' not found. Sorting will not be enabled.`);
        return;
    }

    const thead = tabela.querySelector("thead"); // Seleciona o thead
    const headers = thead.querySelectorAll("th"); // Ainda precisamos deles para o texto e índice
    const tbody = tabela.querySelector("tbody");

    let currentColumn = null;
    let isAscending = true;

    // Adiciona o listener APENAS ao thead (elemento pai)
    thead.addEventListener('click', (event) => {
        const clickedHeader = event.target.closest('th'); // Encontra o TH mais próximo do elemento clicado
        if (!clickedHeader) return; // Se o clique não foi em um TH, ignora

        const columnIndex = Array.from(headers).indexOf(clickedHeader); // Encontra o índice do TH clicado
        if (columnIndex === -1) return; // Se não encontrou o índice, ignora

        if (currentColumn === columnIndex) {
            isAscending = !isAscending;
        } else {
            currentColumn = columnIndex;
            isAscending = true;
        }

        sortTable(columnIndex, isAscending);
        updateHeaderIndicators(columnIndex, isAscending);
    });


    headers.forEach((header) => {
        header.classList.add('sortable');
        header.style.cursor = 'pointer';
    });


    function sortTable(columnIndex, ascending) {
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isDateColumn = headers[columnIndex].textContent.trim() === 'Data Encontrado';

        rows.sort((a, b) => {
            const aVal = a.children[columnIndex].textContent.trim();
            const bVal = b.children[columnIndex].textContent.trim();

            if (isDateColumn) {
                return compareDates(aVal, bVal, ascending);
            }
            return compareStrings(aVal, bVal, ascending);
        });

        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
    }

    function compareDates(a, b, ascending) {
        const dateA = parseDate(a);
        const dateB = parseDate(b);
        if (isNaN(dateA.getTime()) || isNaN(dateB.getTime())) {
            return 0;
        }
        return ascending ? dateA - dateB : dateB - dateA;
    }

    function parseDate(dateString) {
        if (!dateString) return new Date(0);
        const [day, month, year] = dateString.split('/');
        if (isNaN(day) || isNaN(month) || isNaN(year)) {
             return new Date(NaN);
        }
        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }

    function compareStrings(a, b, ascending) {
        const comparison = a.localeCompare(b, 'pt-BR', { sensitivity: 'base' });
        return ascending ? comparison : -comparison;
    }

    function updateHeaderIndicators(activeColumn, ascending) {
        headers.forEach((header, index) => {
            header.classList.remove('asc', 'desc');

            if (index === activeColumn) {
                header.classList.add(ascending ? 'asc' : 'desc');
            }
        });
    }
}
