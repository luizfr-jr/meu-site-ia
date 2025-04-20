import json
from flask import Flask
from config.settings import Config
from models import db, Ferramenta  # ✅ Corrigido: importa Ferramenta corretamente

# Inicializa app Flask
app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Dados das ferramentas
ferramentas_data = [
    {
        "nome": "ChatGPT",
        "descricao": "IA de conversação para dúvidas, redação e ideias.",
        "link": "https://chat.openai.com",
        "imagem": "/frontend/img/chatgpt.jpg"
    },
    {
        "nome": "Leonardo",
        "descricao": "Gere imagens criativas a partir de descrições textuais.",
        "link": "https://leonardo.ai/",
        "imagem": "/frontend/img/leonardo.png"
    },
    {
        "nome": "SciSpace",
        "descricao": "IA para busca de artigos e interação de leituras e partes de cada artigo.",
        "link": "https://scispace.com/",
        "imagem": "/frontend/img/scispace.jpg"
    },
    {
        "nome": "DeepSeek",
        "descricao": "IA de conversação para dúvidas, redação e ideias.",
        "link": "https://chat.deepseek.com/",
        "imagem": "/frontend/img/deepseek.png"
    },
    {
        "nome": "NoteBookLM",
        "descricao": "Assistente de pesquisa e anotações inteligente.",
        "link": "https://notebooklm.google.com/",
        "imagem": "/frontend/img/NoteBookLM.jpg"
    },
    {
        "nome": "Elcit",
        "descricao": "Assistente de pesquisa que automatiza revisões sistemáticas e extração de dados.",
        "link": "https://elicit.com/",
        "imagem": "/frontend/img/elicit.jpg"
    },
    {
        "nome": "Consensus",
        "descricao": "IA para busca de artigos e interação de leituras e partes de cada artigo.",
        "link": "https://consensus.app/search/",
        "imagem": "/frontend/img/consensus.png"
    },
    {
        "nome": "DeepL",
        "descricao": "IA para tradução e escrita em diversas línguas.",
        "link": "https://www.deepl.com/pt-BR/translator",
        "imagem": "/frontend/img/deepl.jpg"
    },
    {
        "nome": "Napkin",
        "descricao": "Ferramenta que transforma texto em diagramas automaticamente.",
        "link": "https://app.napkin.ai/page/create",
        "imagem": "/frontend/img/napkin.jpg"
    },
    {
        "nome": "Heurística",
        "descricao": "Facilita a aprendizagem visual e investigação por meio de mapas conceptuais e mentais.",
        "link": "https://www.heuristi.ca/",
        "imagem": "/frontend/img/heuristica.png"
    },
    {
        "nome": "CopiLot",
        "descricao": "IA de conversação para dúvidas, redação e ideias.",
        "link": "https://copilot.microsoft.com",
        "imagem": "/frontend/img/copilot.jpg"
    },
    {
        "nome": "Qwen",
        "descricao": "IA de conversação para dúvidas, redação e ideias.",
        "link": "https://chat.qwen.ai/",
        "imagem": "/frontend/img/qwen.jpg"
    },
    {
        "nome": "Bohrium",
        "descricao": "Plataforma que utiliza inteligência artificial para acelerar descobertas científicas.",
        "link": "https://www.bohrium.com/home",
        "imagem": "/frontend/img/bohrium.png"
    },
    {
        "nome": "GitMind",
        "descricao": "Crie mapas mentais, fluxogramas e organogramas com colaboração em tempo real.",
        "link": "https://gitmind.com/app/recents",
        "imagem": "/frontend/img/gitmind.png"
    },
    {
        "nome": "Perplexity",
        "descricao": "Ferramenta de busca com respostas baseadas em IA, com fontes confiáveis e contextualização.",
        "link": "https://www.perplexity.ai/",
        "imagem": "/frontend/img/perplexity.png"
    },
    {
        "nome": "Gemini",
        "descricao": "IA generativa do Google que responde perguntas, cria conteúdos e auxilia nos estudos.",
        "link": "https://gemini.google.com/",
        "imagem": "/frontend/img/gemini.png"
    }
]

# Execução
with app.app_context():
    db.create_all()

    for f in ferramentas_data:
        existente = Ferramenta.query.filter_by(nome=f["nome"]).first()
        if not existente:
            nova = Ferramenta(
                nome=f["nome"],
                descricao=f["descricao"],
                link=f["link"],
                imagem=f["imagem"],
                acessos_totais=0
            )
            db.session.add(nova)
    db.session.commit()
    print("✅ Ferramentas importadas com sucesso!")