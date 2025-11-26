document.addEventListener('DOMContentLoaded', () => {
    const categoria = document.querySelector('#categoria');

    categoria.addEventListener('change', function () {
        const categoriaId = this.value

        if (categoria.length) {
            fetch(`_get_campos/${categoriaId}`, {mode: 'cors'})
            .then(response => response.json())
            .then(data => {
                const campos = document.querySelector('#campos');
                campos.innerHTML = '';
                let row = null;

                for (i = 0; i < data.campos.length; i++) {
                    item = data.campos[i]

                    if (i === 0) {
                        row = document.createElement('div')
                        row.classList.add('row');
                    } else if (i % 3 === 0) {
                        campos.appendChild(row);
                        row = document.createElement('div');
                        row.classList.add('row');
                    }

                    const col = document.createElement('div');
                    col.classList.add('col-md-4', 'mb-3');

                    const label = document.createElement('label');
                    label.setAttribute('for', item);
                    label.classList.add('form-label');
                    label.textContent = item;
                    col.appendChild(label)

                    const input = document.createElement('input');
                    input.setAttribute('type', 'text');
                    input.classList.add('form-control');
                    input.setAttribute('id', item);
                    input.setAttribute('name', `campos_valores[${item}]item`);
                    col.appendChild(input)

                    row.appendChild(col);
                }

                campos.appendChild(row);
            });
        }
    })
});

