fetch('/api/ferramentas')
  .then(res => res.json())
  .then(data => {
    const container = document.querySelector('.cards-container');

    data.forEach(tool => {
      const div = document.createElement('div');
      div.classList.add('card');

      div.innerHTML = `
        <img src="${tool.imagem}" alt="Imagem da ferramenta">
        <h2>${tool.nome}</h2>
        <p>${tool.descricao}</p>
        <a href="${tool.link}" target="_blank" class="botao">Acessar</a>
      `;

      container.appendChild(div);
    });
  });