import os
import json
import logging
from bs4 import BeautifulSoup
import random
from flask import jsonify
from sqlalchemy import func
from newspaper import Article
import requests  # ✅ IMPORTANTE
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from config.settings import Config
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.message import EmailMessage
from openai import OpenAI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from flask_login import login_required
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from werkzeug.utils import secure_filename
from PIL import Image
from flask import jsonify
from models import LogAcesso
from models import Topico, Usuario
from models import db
from sqlalchemy import func, desc  # ⬅️ certifique-se de que o desc esteja aqui!
from models import db, Usuario, Topico, Resposta, CurtidaTopico, CurtidaResposta, MedalhaUsuario, Admin, LogAcesso
from sqlalchemy.ext.hybrid import hybrid_property
from flask import Blueprint, abort
from models import Ferramenta
from flask_login import current_user
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, flash

# ✅ Carrega variáveis do .env logo no início
load_dotenv()

# ✅ Diretório de upload de imagens
USUARIOS_FILE = "usuarios.json"
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'foto_de_perfil')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Inicialização do app Flask
app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Inicializa o SQLAlchemy com o app
db.init_app(app)
# ✅ Inicializa demais instâncias
serializer = URLSafeTimedSerializer(app.secret_key)
modelo_ia = SentenceTransformer('all-MiniLM-L6-v2')

# ✅ Cria as tabelas se não existirem
with app.app_context():
    db.create_all()

NOTICIAS_CURADAS_JSON = "noticias_curadas.json"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# ✅ Caminho fora da pasta 'static'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'imagens_ferramentas')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Configura o app Flask para usar essa pasta
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_usuario'  # ou o nome da sua rota de login

def registrar_atividade(usuario, pontos):
    if not usuario:
        return

    usuario.pontos = (usuario.pontos or 0) + pontos
    db.session.commit()
    verificar_e_conceder_medalhas(usuario)

def verificar_e_conceder_medalhas(usuario):
    medalhas_existentes = {m.nome for m in usuario.medalhas}
    medalhas_padrao = [
        {"nome": "🔥 Centelha do Saber", "pontos": 100, "icone": "medalha1.webp", "descricao": "Alcançou 100 pontos."},
        {"nome": "🚀 Explorador Ativo", "pontos": 500, "icone": "medalha2.webp", "descricao": "Alcançou 500 pontos."},
        {"nome": "🌟 Estrela do Fórum", "pontos": 1000, "icone": "medalha3.webp", "descricao": "Alcançou 1000 pontos."}
    ]

    for medalha in medalhas_padrao:
        if usuario.pontos >= medalha["pontos"] and medalha["nome"] not in medalhas_existentes:
            nova = MedalhaUsuario(
                usuario_id=usuario.id,
                nome=medalha["nome"],
                descricao=medalha["descricao"],
                icone=medalha["icone"]
            )
            db.session.add(nova)
            db.session.commit()
            flash(f"🏅 Medalha conquistada: {medalha['nome']}!", "success")

def adicionar_pontos(usuario_id, pontos, motivo=""):
    usuario = Usuario.query.get(usuario_id)
    usuario.pontos += pontos
    db.session.commit()
    print(f"✅ +{pontos} ponto(s) para o usuário {usuario.nome} — motivo: {motivo}")

def extrair_info_da_url(link):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resposta = requests.get(link, headers=headers, timeout=10)
        resposta.raise_for_status()

        soup = BeautifulSoup(resposta.text, 'html.parser')

        def meta(name):
            return (
                soup.find('meta', property=name) or
                soup.find('meta', attrs={'name': name})
            )

        title = (meta("og:title") or meta("title"))
        description = (meta("og:description") or meta("description"))
        image = (meta("og:image") or meta("image"))

        if title and description:
            return {
                "title": title.get("content", "Sem título"),
                "description": description.get("content", "Sem descrição"),
                "url": link,
                "source": link.split("//")[-1].split("/")[0],
                "image": image.get("content") if image else "/frontend/img/noticia_padrao.jpg"
            }

        article = Article(link)
        article.download()
        article.parse()

        return {
            "title": article.title,
            "description": article.meta_description or article.text[:160],
            "url": link,
            "source": link.split("//")[-1].split("/")[0],
            "image": article.top_image or "/frontend/img/noticia_padrao.jpg"
        }

    except Exception as e:
        print(f"⚠️ Erro ao extrair info da URL: {e}")
        return {"error": "Erro ao extrair dados. Verifique se o link é válido ou tente outro."}

def carregar_noticias():
    if os.path.exists(NOTICIAS_CURADAS_JSON):
        with open(NOTICIAS_CURADAS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Função utilitária para validar, redimensionar e converter imagem
def processar_imagem(imagem_arquivo):
    extensoes_validas = {"png", "jpg", "jpeg", "webp"}
    tamanho_maximo_mb = 2

    if not imagem_arquivo:
        raise ValueError("Nenhuma imagem enviada.")

    nome = secure_filename(imagem_arquivo.filename)
    ext = nome.rsplit('.', 1)[-1].lower()
    if ext not in extensoes_validas:
        raise ValueError("Formato inválido. Use PNG, JPG, JPEG ou WEBP.")

    imagem_arquivo.seek(0, os.SEEK_END)
    tamanho_mb = imagem_arquivo.tell() / (1024 * 1024)
    imagem_arquivo.seek(0)
    if tamanho_mb > tamanho_maximo_mb:
        raise ValueError("Imagem muito grande. O tamanho máximo é 2MB.")

    nome_seguro = secrets.token_hex(8) + ".webp"
    caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_seguro)

    imagem = Image.open(imagem_arquivo)
    imagem = imagem.convert("RGB")
    imagem = imagem.resize((150, 150))
    imagem.save(caminho_completo, "WEBP", quality=85)

    return nome_seguro

def salvar_noticias(lista):
    with open(NOTICIAS_CURADAS_JSON, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)

import requests

def obter_localizacao_por_ip(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        data = response.json()
        cidade = data.get("city", "")
        estado = data.get("region", "")
        return cidade, estado
    except Exception:
        return None, None

def gerar_graficos(perguntas_populares, categorias_populares):
    # Gráfico de barras
    img1_base64 = ""
    if perguntas_populares:
        fig1, ax1 = plt.subplots()
        perguntas, contagens = zip(*perguntas_populares)
        ax1.bar(perguntas, contagens, color="#007bff")
        ax1.set_title("Perguntas Mais Frequentes")
        ax1.set_ylabel("Quantidade")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png')
        plt.close(fig1)
        buf1.seek(0)
        img1_base64 = base64.b64encode(buf1.getvalue()).decode('utf-8')

    # Gráfico de pizza
    img2_base64 = ""
    if categorias_populares:
        fig2, ax2 = plt.subplots()
        categorias, valores = zip(*categorias_populares)
        ax2.pie(valores, labels=categorias, autopct='%1.1f%%', startangle=140)
        ax2.set_title("Categorias Mais Buscadas")
        plt.tight_layout()
        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png')
        plt.close(fig2)
        buf2.seek(0)
        img2_base64 = base64.b64encode(buf2.getvalue()).decode('utf-8')

    return img1_base64, img2_base64

# Carrega variáveis de ambiente
api_key = os.getenv("OPENROUTER_API_KEY")
print("🔑 OPENROUTER_API_KEY:", api_key)

# Inicializa cliente OpenAI após carregar a chave
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# App e Configs

serializer = URLSafeTimedSerializer(app.secret_key)
modelo_ia = SentenceTransformer('all-MiniLM-L6-v2')

# Logging
if not os.path.exists('logs'):
    os.makedirs('logs')

from logging.handlers import TimedRotatingFileHandler

log_handler = TimedRotatingFileHandler("logs/app_security.log", when="midnight", interval=1, backupCount=7, encoding='utf-8')
log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
log_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

ACCESS_LOG_FILE = 'logs/index_access.json'
BUSCA_LOG_FILE = 'logs/buscas.json'

def adicionar_pontos(usuario_id, pontos):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.pontos = (usuario.pontos or 0) + pontos
        db.session.commit()

def registrar_acesso_publico(ip):
    if not os.path.exists(ACCESS_LOG_FILE):
        with open(ACCESS_LOG_FILE, 'w') as f:
            json.dump({"total": 0, "ips": []}, f)
    with open(ACCESS_LOG_FILE, 'r+') as f:
        data = json.load(f)
        data["total"] += 1
        if ip not in data["ips"]:
            data["ips"].append(ip)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)

def salvar_busca(pergunta, categoria):
    busca = {"pergunta": pergunta.strip(), "categoria": categoria.strip()}
    if not os.path.exists(BUSCA_LOG_FILE):
        with open(BUSCA_LOG_FILE, 'w') as f:
            json.dump([], f)
    with open(BUSCA_LOG_FILE, 'r+') as f:
        try:
            historico = json.load(f)
        except json.JSONDecodeError:
            historico = []
        historico.append(busca)
        f.seek(0)
        f.truncate()
        json.dump(historico, f, indent=2)

def buscar_noticia_curada():
    try:
        if os.path.exists(NOTICIAS_CURADAS_JSON):
            with open(NOTICIAS_CURADAS_JSON, encoding="utf-8") as f:
                lista = json.load(f)
                if lista:
                    return random.choice(lista)
    except Exception as e:
        print(f"Erro ao carregar notícia curada: {e}")

    # Fallback padrão
    return {
        "title": "IA transforma escolas públicas com tutores personalizados",
        "description": "Uma nova ferramenta de IA está auxiliando professores no acompanhamento individualizado dos alunos em escolas públicas do Brasil.",
        "url": "https://example.com/noticia-sobre-ia-na-educacao",
        "source": "Educação Brasil",
        "image": "/frontend/img/noticia_padrao.jpg"
    }

def registrar_acesso_ia(nome_ia):
    caminho = 'logs/acessos_semana.json'
    if not os.path.exists(caminho):
        with open(caminho, 'w') as f:
            json.dump({}, f)
    with open(caminho, 'r+') as f:
        acessos = json.load(f)
        acessos[nome_ia] = acessos.get(nome_ia, 0) + 1
        f.seek(0)
        f.truncate()
        json.dump(acessos, f, indent=2)


SUPER_ADMINS = ['admin', 'luiz']




@app.route('/')
def pagina_publica():
    registrar_acesso_publico(request.remote_addr)
    return redirect('/ferramentas')

@app.route('/ferramentas')
def ferramentas():
    registrar_acesso_publico(request.remote_addr)
    return render_template("ferramentas.html")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        if not nome or not email or not senha:
            return render_template("registrar.html", erro="Preencha todos os campos.")

        if senha != confirmar_senha:
            return render_template("registrar.html", erro="As senhas não coincidem.")

        if Usuario.query.filter_by(email=email).first():
            return render_template("registrar.html", erro="Este e-mail já está registrado.")

        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash)
        db.session.add(novo_usuario)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("login_usuario"))

    return render_template("registrar.html")

@app.route('/login-user', methods=['GET', 'POST'])
def login_usuario():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)  # <- ISSO AQUI FAZ A AUTENTICAÇÃO FUNCIONAR
            # (mantém as outras atualizações de sessão que você usa)

            session['usuario_nome'] = usuario.nome
            session['usuario_id'] = usuario.id
            session['usuario_email'] = usuario.email
            session['tipo_usuario'] = usuario.tipo
            session['premium'] = usuario.premium

            # Atualização de métricas
            usuario.ultimo_login = datetime.utcnow()
            usuario.acessos_total += 1
            usuario.navegador = request.user_agent.browser
            usuario.dispositivo = request.user_agent.platform

            try:
                ip = request.remote_addr
                cidade, estado = obter_localizacao_por_ip(ip)
                usuario.cidade = cidade
                usuario.estado = estado
            except:
                pass

            db.session.commit()
            return redirect(url_for('painel_usuario'))
        else:
            flash("E-mail ou senha inválidos.", "danger")
    return render_template("login_user.html")

@app.route("/painel")
def painel_usuario():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        flash("Você precisa estar logado para acessar o painel.", "warning")
        return redirect(url_for("login_usuario"))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash("Sessão inválida. Faça login novamente.", "danger")
        session.clear()
        return redirect(url_for("login_usuario"))

    return render_template("painel.html", usuario=usuario)
@app.route('/logout-user')
def logout_usuario():
    session.pop('usuario_id', None)
    session.pop('usuario_nome', None)
    flash("Você saiu da conta com sucesso.", "info")
    return redirect(url_for('home_inteligente'))

@app.route('/frontend/<path:filename>')
def frontend_static(filename):
    return send_from_directory('../frontend', filename)

@app.route('/buscar_ia_local', methods=['POST'])
def buscar_ia_local():
    pergunta = request.json.get('pergunta', '')
    categoria = request.json.get('categoria', '').lower()

    salvar_busca(pergunta, categoria)

    with open(app.config['DATABASE_FILE'], 'r') as f:
        ferramentas = json.load(f)

    if categoria:
        ferramentas = [f for f in ferramentas if categoria in f.get('descricao', '').lower()]
    if not ferramentas:
        return jsonify([])

    descricoes = [f"{ia['nome']}: {ia['descricao']}" for ia in ferramentas]
    vetores_descricoes = modelo_ia.encode(descricoes)
    vetor_pergunta = modelo_ia.encode([pergunta])
    similaridades = cosine_similarity(vetor_pergunta, vetores_descricoes)[0]
    top_indices = similaridades.argsort()[-3:][::-1]

    top_3 = []
    for i, index in enumerate(top_indices):
        ferramenta = ferramentas[index]
        score = float(similaridades[index])

        prompt = f"""
Resuma de forma clara e objetiva por que a ferramenta {ferramenta['nome']} é últil para: \"{pergunta}\".

Escreva no máximo 3 linhas com:
- 2 pontos fortes específicos;
- 1 limitação curta (se houver);
- Linguagem simples, sem repetições nem floreios.
"""

        try:
            resposta = client.chat.completions.create(
                model="mistralai/mistral-7b-instruct",
                messages=[
                    {"role": "system", "content": "Você é um especialista em IA e deve fornecer respostas curtas, úteis e diretas."},
                    {"role": "user", "content": prompt}
                ]
            )
            explicacao = resposta.choices[0].message.content.strip()
            logging.info(f"[IA] Explicação: {explicacao}")
        except Exception as e:
            logging.error(f"Erro IA: {e}")
            explicacao = f"A ferramenta '{ferramenta['nome']}' foi selecionada por sua relevância."

        top_3.append({
            "nome": ferramenta["nome"],
            "descricao": ferramenta["descricao"],
            "link": ferramenta["link"],
            "imagem": ferramenta["imagem"],
            "score": round(score, 4),
            "explicacao": explicacao
        })

    return jsonify(top_3)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        if user == 'admin' and password == '1234':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
        admin = Admin.query.filter_by(username=user).first()
        if admin and check_password_hash(admin.password, password):
            session['user'] = admin.username
            return redirect(url_for('dashboard'))
        return render_template('login.html', erro=True)
    return render_template('login.html')

@app.route('/excluir_usuario_comum/<int:user_id>')
def excluir_usuario_comum(user_id):
    if 'user' not in session or session['user'] not in SUPER_ADMINS:
        return "Acesso negado", 403

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return "Usuário não encontrado", 404

    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído com sucesso.", "success")
    return redirect(url_for('gerenciar_usuarios'))

\

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    ferramentas = Ferramenta.query.order_by(Ferramenta.data_criacao.desc()).all()

    return render_template('dashboard.html', ferramentas=ferramentas)

@app.route('/usuarios')
def gerenciar_usuarios():
    if 'user' not in session or session['user'] not in SUPER_ADMINS:
        return "Acesso negado", 403

    admins = Admin.query.all()
    usuarios_comuns = Usuario.query.order_by(Usuario.data_cadastro.desc()).all()

    # MÉTRICAS
    try:
        with open('logs/app_security.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()
    except Exception as e:
        logs = [f"Erro ao carregar log: {e}"]

    total_index = 0
    unique_index_ips = 0
    try:
        with open(ACCESS_LOG_FILE, 'r') as f:
            index_data = json.load(f)
            total_index = index_data.get("total", 0)
            unique_index_ips = len(index_data.get("ips", []))
    except Exception:
        pass

    busca_contagem = {}
    categoria_contagem = {}
    try:
        with open("logs/buscas.json", "r") as f:
            buscas = json.load(f)
            for item in buscas:
                pergunta = item.get("pergunta", "").strip().lower()
                categoria = item.get("categoria", "").strip().lower()
                if pergunta:
                    busca_contagem[pergunta] = busca_contagem.get(pergunta, 0) + 1
                if categoria:
                    categoria_contagem[categoria] = categoria_contagem.get(categoria, 0) + 1
    except FileNotFoundError:
        pass

    perguntas_populares = sorted(busca_contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    categorias_populares = sorted(categoria_contagem.items(), key=lambda x: x[1], reverse=True)[:10]

    img1_base64, img2_base64 = gerar_graficos(perguntas_populares[:5], categorias_populares[:5])

    return render_template(
        "usuarios.html",
        admins=admins,
        usuarios=admins,
        usuarios_comuns=usuarios_comuns,
        total_index=total_index,
        unique_index_ips=unique_index_ips,
        perguntas_populares=perguntas_populares,
        categorias_populares=categorias_populares,
        grafico_barras=img1_base64,
        grafico_pizza=img2_base64,
        logs=logs[::-1]
    )



@app.route('/excluir_usuario/<int:user_id>')
def excluir_usuario(user_id):
    if 'user' not in session or session['user'] not in SUPER_ADMINS:
        return "Acesso negado", 403
    admin = Admin.query.get(user_id)
    if not admin or admin.username in SUPER_ADMINS:
        return "Não é permitido excluir este usuário.", 403
    db.session.delete(admin)
    db.session.commit()
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    if 'user' not in session or session['user'] not in SUPER_ADMINS:
        return "Acesso negado", 403
    admin = Admin.query.get(user_id)
    if not admin:
        return "Usuário não encontrado", 404

    if request.method == 'POST':
        admin.username = request.form['username']
        admin.email = request.form['email']
        senha = request.form.get('password')
        if senha:
            admin.password = generate_password_hash(senha)
        db.session.commit()
        return redirect(url_for('gerenciar_usuarios'))

    return render_template('editar_usuario.html', admin=admin)
@app.route('/adicionar', methods=['POST'])
def adicionar():
    if 'user' not in session:
        return redirect(url_for('login'))
    nome = request.form['nome']
    descricao = request.form['descricao']
    link = request.form['link']
    imagem = request.files['imagem']
    filename = secure_filename(imagem.filename)
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    imagem.save(caminho)
    nova_ferramenta = {
        "nome": nome,
        "descricao": descricao,
        "link": link,
        "imagem": "/frontend/img/" + filename
    }
    with open(app.config['DATABASE_FILE'], 'r+') as f:
        dados = json.load(f)
        dados.append(nova_ferramenta)
        f.seek(0)
        json.dump(dados, f, indent=4)
    return redirect(url_for('dashboard'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    with open(app.config['DATABASE_FILE'], 'r+') as f:
        dados = json.load(f)
        if request.method == 'POST':
            dados[id]['nome'] = request.form['nome']
            dados[id]['descricao'] = request.form['descricao']
            dados[id]['link'] = request.form['link']
            if 'imagem' in request.files and request.files['imagem'].filename:
                imagem = request.files['imagem']
                filename = secure_filename(imagem.filename)
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagem.save(caminho)
                dados[id]['imagem'] = "/frontend/img/" + filename
            f.seek(0)
            f.truncate()
            json.dump(dados, f, indent=4)
            return redirect(url_for('dashboard'))
        ferramenta = dados[id]
        return render_template('dashboard.html', ferramenta=ferramenta, id=id, ferramentas=dados)

@app.route('/remover/<int:id>')
def remover(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    with open(app.config['DATABASE_FILE'], 'r+') as f:
        dados = json.load(f)
        if 0 <= id < len(dados):
            dados.pop(id)
            f.seek(0)
            f.truncate()
            json.dump(dados, f, indent=4)
    return redirect(url_for('dashboard'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        instituicao = request.form['instituicao']
        motivo = request.form['motivo']
        token = serializer.dumps(email, salt='cadastro-salt')
        link = url_for('cadastrar_usuario', token=token, _external=True)
        corpo = f"""
Nova solicitação de acesso:
Nome: {nome}
Email: {email}
Instituição: {instituicao}
Motivo: {motivo}

Acesse para aprovar: {link} (expira em 1h)
"""
        msg = EmailMessage()
        msg['Subject'] = 'Solicitação de Acesso - Meu Site IA'
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = 'kallebyevangelho03@gmail.com'
        msg.set_content(corpo)
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
                smtp.send_message(msg)
            return render_template('cadastro_enviado.html')
        except Exception as e:
            return 'Erro ao enviar email.'
    return render_template('cadastro.html')

@app.route('/cadastrar_usuario/<token>', methods=['GET', 'POST'])
def cadastrar_usuario(token):
    try:
        email = serializer.loads(token, salt='cadastro-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        return 'Link expirado ou inválido.'

    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['password']
        if Admin.query.filter_by(username=username).first():
            return render_template('cadastro_token.html', erro='Usuário já existe.')
        if Admin.query.filter_by(email=email).first():
            return render_template('cadastro_token.html', erro='Email já cadastrado.')
        hash_pw = generate_password_hash(senha)
        novo = Admin(username=username, email=email, password=hash_pw)
        db.session.add(novo)
        db.session.commit()
        return render_template('cadastro_token.html', sucesso='Usuário cadastrado com sucesso!')

    return render_template('cadastro_token.html', email=email)

@app.route('/api/ferramentas')
def api_ferramentas():
    ferramentas = Ferramenta.query.all()
    return jsonify([
        {
            "id": f.id,
            "nome": f.nome,
            "descricao": f.descricao,
            "link": f.link,
            "imagem": f.imagem,
            "acessos_totais": f.acessos_totais
        } for f in ferramentas
    ])


@app.route("/noticias", methods=["GET", "POST"])
def gerenciar_noticias():
    if "user" not in session or session["user"] not in SUPER_ADMINS:
        return redirect(url_for("login"))

    noticias = carregar_noticias()

    if request.method == "POST":
        nova = {
            "title": request.form["title"],
            "description": request.form["description"],
            "url": request.form["url"],
            "source": request.form["source"],
            "image": request.form.get("image") or "/frontend/img/noticia_padrao.jpg"
        }
        noticias.insert(0, nova)
        salvar_noticias(noticias)
        return redirect(url_for("gerenciar_noticias"))

    return render_template("noticias.html", noticias=noticias)


@app.route('/editar_ferramenta/<int:id>', methods=['GET', 'POST'])
def editar_ferramenta(id):
    if 'user' not in session or session['user'] not in SUPER_ADMINS:
        return redirect(url_for('login'))

    ferramenta = Ferramenta.query.get_or_404(id)

    if request.method == 'POST':
        ferramenta.nome = request.form['nome']
        ferramenta.descricao = request.form['descricao']
        ferramenta.link = request.form['link']

        imagem = request.files.get('imagem')
        if imagem and imagem.filename:
            ext = imagem.filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                nome_arquivo = secrets.token_hex(8) + "." + ext
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                imagem.save(caminho)
                ferramenta.imagem = f"/imagens_ferramentas/{nome_arquivo}"
            else:
                flash("Formato de imagem inválido.", "danger")
                return redirect(url_for("dashboard"))

        db.session.commit()
        flash("Ferramenta atualizada com sucesso!", "success")
        return redirect(url_for("dashboard"))

    ferramentas = Ferramenta.query.order_by(Ferramenta.nome).all()
    return render_template("dashboard.html", ferramenta=ferramenta, ferramentas=ferramentas)

@app.route("/remover_ferramenta/<int:id>")
def remover_ferramenta(id):
    ferramenta = Ferramenta.query.get_or_404(id)
    db.session.delete(ferramenta)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/adicionar_ferramenta', methods=['POST'])
def adicionar_ferramenta():
    nome = request.form['nome']
    descricao = request.form['descricao']
    link = request.form['link']
    imagem = request.files['imagem']

    if imagem and imagem.filename:
        extensao = imagem.filename.rsplit('.', 1)[-1].lower()
        nome_unico = secrets.token_hex(8) + '.' + extensao
        caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
        imagem.save(caminho_imagem)
        imagem_url = f"/imagens_ferramentas/{nome_unico}"
    else:
        imagem_url = "/frontend/img/imagem_padrao.webp"  # caso queira uma imagem padrão

    nova = Ferramenta(
        nome=nome,
        descricao=descricao,
        link=link,
        imagem=imagem_url
    )
    db.session.add(nova)
    db.session.commit()
    flash("Ferramenta adicionada com sucesso!", "success")
    return redirect(url_for("dashboard"))

@app.route("/noticias/remover/<int:index>")
def remover_noticia(index):
    if "user" not in session or session["user"] not in SUPER_ADMINS:
        return redirect(url_for("login"))

    noticias = carregar_noticias()
    if 0 <= index < len(noticias):
        noticias.pop(index)
        salvar_noticias(noticias)
    return redirect(url_for("gerenciar_noticias"))


@app.route("/extrair_info_noticia", methods=["POST"])
def extrair_info_noticia():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "URL não fornecida"}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        resposta = requests.get(url, headers=headers, timeout=10)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")

        def meta(name):
            return (
                soup.find("meta", property=name) or
                soup.find("meta", attrs={"name": name})
            )

        title = (meta("og:title") or meta("title"))
        description = (meta("og:description") or meta("description"))
        image = (meta("og:image") or meta("image"))

        if title and description:
            return jsonify({
                "title": title.get("content", ""),
                "description": description.get("content", ""),
                "image": image.get("content", "") if image else ""
            })

        # Fallback com newspaper3k
        artigo = Article(url)
        artigo.download()
        artigo.parse()

        return jsonify({
            "title": artigo.title,
            "description": artigo.meta_description or artigo.text[:180],
            "image": artigo.top_image
        })

    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return jsonify({"error": "Erro ao extrair dados. Verifique se o link é válido."}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/foto_de_perfil/<filename>')
def foto_de_perfil(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/como-usar')
def como_usar():
    return render_template('como_usar.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/perfil', methods=['GET', 'POST'])
def editar_perfil():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login_usuario_comum"))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("login_usuario_comum"))

    if request.method == 'POST':
        # Verifica se foi enviado apenas a imagem
        if 'foto' in request.files and request.form.get('nome') is None:
            foto = request.files.get("foto")
            if foto and foto.filename:
                try:
                    nome_arquivo = processar_imagem(foto)
                    usuario.foto = nome_arquivo
                    db.session.commit()
                    flash("Imagem de perfil atualizada com sucesso!", "imagem_ok")
                except ValueError as e:
                    flash(str(e), "imagem_erro")
            return redirect(url_for('editar_perfil'))

        # Caso contrário, processa os dados do formulário
        usuario.nome = request.form.get("nome", usuario.nome)
        usuario.biografia = request.form.get("biografia")
        usuario.linkedin = request.form.get("linkedin")
        usuario.instagram = request.form.get("instagram")
        usuario.github = request.form.get("github")
        usuario.tipo = request.form.get("tipo")

        nova_senha = request.form.get("nova_senha")
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)

        db.session.commit()
        flash("Dados do perfil atualizados com sucesso!", "imagem_ok")
        return redirect(url_for('editar_perfil'))

    return render_template("editar_perfil.html", usuario=usuario)

@app.route('/excluir_conta', methods=['POST'])
def excluir_conta():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login_usuario_comum"))

    usuario = Usuario.query.get(usuario_id)
    if usuario:
        # Remove a foto do servidor se existir
        if usuario.foto:
            caminho_foto = os.path.join(app.config['UPLOAD_FOLDER'], usuario.foto)
            if os.path.exists(caminho_foto):
                os.remove(caminho_foto)

        db.session.delete(usuario)
        db.session.commit()
        session.clear()
        flash("Sua conta foi excluída.", "info")

    return redirect(url_for("pagina_publica"))


@app.route("/acessar/<int:ferramenta_id>")
def acessar_ferramenta(ferramenta_id):
    ferramenta = Ferramenta.query.get_or_404(ferramenta_id)
    ferramenta.acessos_totais = (ferramenta.acessos_totais or 0) + 1
    db.session.commit()
    return redirect(ferramenta.link)

@app.route("/api/uso_usuario")
def uso_usuario():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Não autenticado"}), 401

    resultados = (
        db.session.query(
            func.date(LogAcesso.data_acesso),
            func.count()
        )
        .filter_by(usuario_id=usuario_id)
        .group_by(func.date(LogAcesso.data_acesso))
        .order_by(func.date(LogAcesso.data_acesso))
        .all()
    )

    datas = [r[0].strftime("%d/%m") for r in resultados]
    acessos = [r[1] for r in resultados]

    return jsonify({"datas": datas, "acessos": acessos})

from datetime import datetime, timedelta

@app.route("/forum")
def forum():
    if "usuario_id" not in session:
        flash("Você precisa estar logado para acessar o fórum.", "warning")
        return redirect(url_for("login_usuario"))

    usuario_id = session["usuario_id"]
    usuario_nome = session["usuario_nome"]

    categoria = request.args.get("categoria", "")
    ordem = request.args.get("ordem", "recentes")

    # Filtros e ordenações
    query = Topico.query
    if categoria:
        query = query.filter_by(categoria=categoria)

    if ordem == "populares":
        query = query.outerjoin(CurtidaTopico).group_by(Topico.id).order_by(func.count(CurtidaTopico.id).desc())
    elif ordem == "sem-resposta":
        query = query.outerjoin(Resposta).group_by(Topico.id).having(func.count(Resposta.id) == 0)
    else:
        query = query.order_by(Topico.data_criacao.desc())

    topicos = query.all()

    # Ranking top 10
    ranking = Usuario.query.order_by(Usuario.pontos.desc()).limit(10).all()

    # Usuário logado com medalhas
    usuario_logado = Usuario.query.get(usuario_id)

    return render_template(
        "forum.html",
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        topicos=topicos,
        categoria=categoria,
        ordem=ordem,
        ranking=ranking,
        usuario_logado=usuario_logado,
        datetime=datetime,
        timedelta=timedelta
    )

@app.route("/forum/nova", methods=["GET", "POST"])
def criar_topico():
    if "usuario_id" not in session:
        flash("Você precisa estar logado para criar um tópico.", "warning")
        return redirect(url_for("login_usuario"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        conteudo = request.form.get("conteudo", "").strip()
        categoria = request.form.get("categoria", "Geral")

        if not titulo or not conteudo:
            flash("Preencha todos os campos!", "danger")
            return redirect(url_for("forum"))

        resumo_ia = None
        try:
            resposta = client.chat.completions.create(
                model="mistralai/mistral-7b-instruct",
                messages=[
                    {"role": "system", "content": "Você é uma IA especialista que gera resumos claros e concisos."},
                    {"role": "user", "content": f"Resuma brevemente o tópico: {conteudo}"}
                ]
            )
            resumo_ia = resposta.choices[0].message.content.strip()
        except Exception as e:
            print("Erro no resumo IA:", e)

        novo_topico = Topico(titulo=titulo, conteudo=conteudo, categoria=categoria, usuario_id=session["usuario_id"], resumo_ia=resumo_ia)
        db.session.add(novo_topico)
        db.session.commit()

        adicionar_pontos(session["usuario_id"], 5)
        flash("Tópico criado com sucesso!", "success")
        return redirect(url_for("forum"))

    return render_template("forum_novo.html")


@app.route("/forum/topico/<int:id>")
def ver_topico(id):
    topico = Topico.query.get_or_404(id)
    ordenar = request.args.get('ordenar', 'recentes')
    respostas = Resposta.query.filter_by(topico_id=id).order_by(
        Resposta.criado_em.desc() if ordenar == 'recentes' else func.length(Resposta.curtidas).desc()
    ).all()
    usuario_id = session.get("usuario_id")
    return render_template("topico_detalhado.html", topico=topico, respostas=respostas, usuario_id=usuario_id)

@app.route("/forum/responder/<int:id>", methods=["POST"])
def responder_topico(id):
    if "usuario_id" not in session:
        flash("Você precisa estar logado para responder.", "warning")
        return redirect(url_for("login_usuario"))

    conteudo = request.form.get("conteudo", "").strip()
    citado_id = request.form.get("citado_id") or None
    usuario_id = session["usuario_id"]

    if conteudo:
        # Verifica se já respondeu recentemente ao mesmo tópico
        ultima_resposta = (
            Resposta.query
            .filter_by(topico_id=id, usuario_id=usuario_id)
            .order_by(Resposta.criado_em.desc())
            .first()
        )
        if ultima_resposta and (datetime.utcnow() - ultima_resposta.criado_em).total_seconds() < 60:
            flash("Aguarde um momento antes de responder novamente ao mesmo tópico.", "warning")
            return redirect(url_for("ver_topico", id=id))

        resposta = Resposta(
            conteudo=conteudo,
            topico_id=id,
            usuario_id=usuario_id,
            citado_id=citado_id
        )
        db.session.add(resposta)
        db.session.commit()

        usuario_que_respondeu = Usuario.query.get(usuario_id)
        topico = Topico.query.get(id)

        # Só ganha pontos se não estiver respondendo ao próprio tópico
        if topico.usuario_id != usuario_que_respondeu.id:
            adicionar_pontos(usuario_id, 2, "Resposta em tópico alheio")

    return redirect(url_for("ver_topico", id=id))

@app.route('/imagens_ferramentas/<path:filename>')
def imagens_ferramentas_static(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota de curtida com verificação de pontos
@app.route("/forum/curtir/<int:id>", methods=["POST"])
def curtir_topico(id):
    if "usuario_id" not in session:
        return jsonify({"status": "erro", "mensagem": "Login necessário"}), 401

    usuario_id = session["usuario_id"]
    curtida_existente = CurtidaTopico.query.filter_by(topico_id=id, usuario_id=usuario_id).first()

    if curtida_existente:
        db.session.delete(curtida_existente)
        db.session.commit()
        return jsonify({"status": "removido", "curtidas": Topico.query.get(id).curtidas})

    nova_curtida = CurtidaTopico(topico_id=id, usuario_id=usuario_id)
    db.session.add(nova_curtida)

    topico = Topico.query.get(id)

    if topico.usuario_id != usuario_id:
        adicionar_pontos(topico.usuario_id, 1, "Curtida recebida de outro usuário")

    db.session.commit()
    return jsonify({"status": "curtido", "curtidas": Topico.query.get(id).curtidas})


@app.route("/conquistas")
def conquistas():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        flash("Você precisa estar logado para ver suas conquistas.", "warning")
        return redirect(url_for("login_usuario"))

    usuario = Usuario.query.get(usuario_id)
    conquistas = []

    if usuario.pontos >= 100:
        conquistas.append("🥇 Mestre do Fórum — 100+ pontos acumulados")
    if len(usuario.topicos) >= 10:
        conquistas.append("📢 Debatedor Ativo — 10+ tópicos criados")
    if len(usuario.respostas) >= 20:
        conquistas.append("💬 Responder é viver — 20+ respostas dadas")
    if any(len(t.curtidas_topico) >= 10 for t in usuario.topicos):
        conquistas.append("🔥 Tópico em Alta — 10+ curtidas em um tópico")

    return render_template("conquistas.html", usuario=usuario, conquistas=conquistas)


@app.route("/forum/editar/<int:id>", methods=["POST"])
def editar_topico(id):
    topico = Topico.query.get_or_404(id)
    if session.get("usuario_id") != topico.usuario_id:
        return redirect(url_for("ver_topico", id=id))

    topico.titulo = request.form["titulo"]
    topico.conteudo = request.form["conteudo"]
    topico.categoria = request.form["categoria"]
    topico.data_atualizacao = datetime.utcnow()
    db.session.commit()
    flash("Tópico atualizado com sucesso!", "success")
    return redirect(url_for("ver_topico", id=id))

@app.route("/forum/excluir/<int:id>", methods=["POST"])
def excluir_topico(id):
    topico = Topico.query.get_or_404(id)
    if session.get("usuario_id") != topico.usuario_id:
        return redirect(url_for("ver_topico", id=id))

    db.session.delete(topico)
    db.session.commit()
    flash("Tópico excluído com sucesso!", "info")
    return redirect(url_for("forum"))

@app.route("/forum/resumir/<int:id>", methods=["POST"])
def resumir_topico(id):
    topico = Topico.query.get_or_404(id)
    if session.get("usuario_id") != topico.usuario_id:
        return jsonify({"erro": "Sem permissão."}), 403

    try:
        resposta = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": "Você é uma IA especialista em fóruns e resumos."},
                {"role": "user", "content": f"Resuma o seguinte tópico: {topico.conteudo}"}
            ]
        )
        topico.resumo_ia = resposta.choices[0].message.content.strip()
        db.session.commit()
        return jsonify({"status": "ok", "resumo": topico.resumo_ia})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/historico/<int:id>")
def api_historico_pontos(id):
    usuario = Usuario.query.get_or_404(id)

    atividades = []

    topicos = Topico.query.filter_by(usuario_id=id).all()
    for t in topicos:
        atividades.append({
            "descricao": f"Criou tópico: {t.titulo}",
            "pontos": 10,
            "data": t.data_criacao.strftime("%d/%m/%Y")
        })

    respostas = Resposta.query.filter_by(usuario_id=id).all()
    for r in respostas:
        atividades.append({
            "descricao": "Respondeu a um tópico",
            "pontos": 5,
            "data": r.criado_em.strftime("%d/%m/%Y")
        })

    medalhas = MedalhaUsuario.query.filter_by(usuario_id=id).all()
    for m in medalhas:
        atividades.append({
            "descricao": f"Conquistou medalha: {m.nome}",
            "pontos": 0,
            "data": m.data_conquista.strftime("%d/%m/%Y")
        })

    atividades.sort(key=lambda x: x["data"], reverse=True)

    return jsonify({"atividades": atividades})

@app.route("/forum/reportar/<int:id>", methods=["POST"])
def reportar_topico(id):
    flash("Tópico reportado. Nossa equipe irá avaliar.", "warning")
    return redirect(url_for("ver_topico", id=id))

@app.route("/forum/resposta/curtir/<int:id>", methods=["POST"])
def curtir_resposta(id):
    if "usuario_id" not in session:
        return jsonify({"status": "erro", "mensagem": "Login necessário"}), 401

    resposta = Resposta.query.get_or_404(id)
    usuario_id = session["usuario_id"]

    curtida_existente = CurtidaResposta.query.filter_by(resposta_id=id, usuario_id=usuario_id).first()

    if curtida_existente:
        db.session.delete(curtida_existente)
        db.session.commit()
        return jsonify({"status": "removido"})
    else:
        nova_curtida = CurtidaResposta(resposta_id=id, usuario_id=usuario_id)
        db.session.add(nova_curtida)
        db.session.commit()
        return jsonify({"status": "curtido"})

@app.route("/forum/resposta/editar/<int:id>", methods=["POST"])
def editar_resposta(id):
    resposta = Resposta.query.get_or_404(id)

    if session.get("usuario_id") != resposta.usuario_id:
        flash("Você não tem permissão para editar essa resposta.", "danger")
        return redirect(url_for("ver_topico", id=resposta.topico_id))

    novo_conteudo = request.form.get("conteudo", "").strip()
    if novo_conteudo:
        resposta.conteudo = novo_conteudo
        db.session.commit()
        flash("Resposta atualizada com sucesso!", "success")

    return redirect(url_for("ver_topico", id=resposta.topico_id))

@app.route("/forum/resposta/excluir/<int:id>", methods=["POST"])
def excluir_resposta(id):
    resposta = Resposta.query.get_or_404(id)
    if session.get("usuario_id") != resposta.usuario_id:
        flash("Você não tem permissão para excluir essa resposta.", "danger")
        return redirect(url_for("ver_topico", id=resposta.topico_id))

    db.session.delete(resposta)
    db.session.commit()
    flash("Resposta excluída com sucesso!", "info")
    return redirect(url_for("ver_topico", id=resposta.topico_id))

@app.route("/forum/resumir_thread/<int:id>", methods=["POST"])
def resumir_thread_ia(id):
    topico = Topico.query.get_or_404(id)
    respostas = Resposta.query.filter_by(topico_id=id).order_by(Resposta.criado_em.asc()).all()

    conteudo_completo = f"Título: {topico.titulo}\n\nDescrição: {topico.conteudo}\n\n"
    conteudo_completo += "Respostas:\n" + "\n".join(
        [f"{r.usuario.nome} disse: {r.conteudo}" for r in respostas]
    )

    try:
        resposta = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": "Você é uma IA especialista em fóruns que gera resumos curtos e úteis."},
                {"role": "user", "content": f"Resuma o seguinte tópico com base no título, descrição e respostas:\n\n{conteudo_completo}"}
            ]
        )
        resumo_thread = resposta.choices[0].message.content.strip()
        return jsonify({"status": "ok", "resumo": resumo_thread})
    except Exception as e:
        print("Erro ao resumir thread:", e)
        return jsonify({"erro": str(e)}), 500

@app.route("/ranking")
def ranking():
    usuarios = Usuario.query.order_by(desc(Usuario.pontos)).all()
    return render_template("ranking.html", usuarios=usuarios)


@app.route("/notificacoes")
def ver_notificacoes():
    if "usuario_id" not in session:
        return redirect(url_for("login_usuario"))
    notificacoes = Notificacao.query.filter_by(usuario_id=session["usuario_id"]).order_by(desc(Notificacao.data)).all()
    return render_template("notificacoes.html", notificacoes=notificacoes)

# Marcar notificação como lida
@app.route("/notificacao/lida/<int:id>", methods=["POST"])
def marcar_notificacao_lida(id):
    notificacao = Notificacao.query.get(id)
    if notificacao and notificacao.usuario_id == session.get("usuario_id"):
        notificacao.lida = True
        db.session.commit()
    return redirect(url_for("ver_notificacoes"))

@app.route("/api/evolucao_pontos/<int:usuario_id>")
def api_evolucao_pontos(usuario_id):
    pontos_por_data = (
        db.session.query(
            func.date(MedalhaUsuario.data_conquista).label('data'),
            func.count().label('pontos')  # ou usa Usuario.pontos se houver histórico
        )
        .filter(MedalhaUsuario.usuario_id == usuario_id)
        .group_by(func.date(MedalhaUsuario.data_conquista))
        .order_by(func.date(MedalhaUsuario.data_conquista))
        .all()
    )

    datas = [str(data) for data, _ in pontos_por_data]
    pontos = [p for _, p in pontos_por_data]

    return jsonify({"labels": datas, "data": pontos})


# Denunciar conteúdo
@app.route("/denunciar", methods=["POST"])
def denunciar():
    tipo = request.form.get("tipo")  # topico ou resposta
    id_conteudo = request.form.get("id")
    motivo = request.form.get("motivo")
    nova_denuncia = Denuncia(
        tipo=tipo,
        id_conteudo=id_conteudo,
        motivo=motivo,
        usuario_id=session.get("usuario_id")
    )
    db.session.add(nova_denuncia)
    db.session.commit()
    flash("Denúncia enviada com sucesso!", "info")
    return redirect(request.referrer)

@app.route("/usuario/<int:id>")
def perfil_publico(id):
    usuario = Usuario.query.get_or_404(id)
    topicos = Topico.query.filter_by(usuario_id=id).order_by(desc(Topico.data_criacao)).all()
    respostas = Resposta.query.filter_by(usuario_id=id).order_by(desc(Resposta.criado_em)).all()
    medalhas = MedalhaUsuario.query.filter_by(usuario_id=id).order_by(desc(MedalhaUsuario.data_conquista)).all()
    atividades = LogAcesso.query.filter_by(usuario_id=id).order_by(desc(LogAcesso.data_acesso)).limit(10).all()

    # Preparar dados do gráfico
    pontos_por_data = (
        db.session.query(
            func.date(MedalhaUsuario.data_conquista).label('data'),
            func.sum(Usuario.pontos).label('pontos')
        )
        .join(Usuario)
        .filter(MedalhaUsuario.usuario_id == id)
        .group_by(func.date(MedalhaUsuario.data_conquista))
        .order_by(func.date(MedalhaUsuario.data_conquista))
        .all()
    )
    datas_grafico = [str(data) for data, _ in pontos_por_data]
    pontos_grafico = [p for _, p in pontos_por_data]

    return render_template(
        "perfil_publico.html",
        usuario=usuario,
        topicos=topicos,
        respostas=respostas,
        medalhas=medalhas,
        atividades=atividades,
        datas_grafico=datas_grafico,
        pontos_grafico=pontos_grafico
    )

@app.route("/favoritar/<int:id>", methods=["POST"])
def favoritar(id):
    if "usuario_id" not in session:
        return jsonify({"status": "erro", "mensagem": "Você precisa estar logado."}), 401

    usuario_id = session["usuario_id"]
    usuario = Usuario.query.get_or_404(usuario_id)
    ferramenta = Ferramenta.query.get_or_404(id)

    # Crie o relacionamento de favoritos se ainda não existir
    if not hasattr(usuario, "favoritos"):
        flash("Modelo 'favoritos' ainda não implementado.", "danger")
        return jsonify({"status": "erro", "mensagem": "Favoritos não ativado."}), 400

    if ferramenta not in usuario.favoritos:
        usuario.favoritos.append(ferramenta)
        db.session.commit()

    return jsonify({"status": "ok"})

@app.route("/remover_favorito/<int:ferramenta_id>", methods=["POST"])
def remover_favorito(ferramenta_id):
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        flash("Você precisa estar logado para remover favoritos.", "warning")
        return redirect(url_for("login_usuario"))

    usuario = Usuario.query.get(usuario_id)
    ferramenta = Ferramenta.query.get_or_404(ferramenta_id)

    if ferramenta in usuario.favoritos:
        usuario.favoritos.remove(ferramenta)
        db.session.commit()
        flash("Removido dos seus favoritos!", "info")
    
    return redirect(url_for("painel_usuario"))

from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/seguir/<int:id>', methods=['POST'])
@login_required
def seguir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario == current_user:
        return jsonify({"erro": "Você não pode seguir a si mesmo."}), 400

    if current_user.esta_seguindo(usuario):
        current_user.deixar_de_seguir(usuario)
        db.session.commit()
        return jsonify({"seguindo": False})
    else:
        current_user.seguir(usuario)
        db.session.commit()
        return jsonify({"seguindo": True})
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Nome da sua rota de login

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route("/painel-premium")
def painel_premium():
    if not current_user.premium:
        return redirect(url_for("painel_usuario"))

    if current_user.tipo == "aluno":
        return redirect(url_for("painel_aluno"))
    elif current_user.tipo == "professor":
        return redirect(url_for("painel_professor"))
    else:
        return redirect(url_for("painel_usuario"))

@app.route("/painel-premium/<int:user_id>")
def painel_premium_id(user_id):
    usuario = Usuario.query.get(user_id)

    if not usuario:
        return "Usuário não encontrado.", 404

    if not usuario.premium:
        return redirect(url_for("painel_usuario"))  # Ou outra rota pública

    if usuario.tipo == "aluno":
        return render_template("painel_aluno.html", usuario=usuario)

    if usuario.tipo == "professor":
        return render_template("painel_professor.html", usuario=usuario)

    return redirect(url_for("painel_usuario"))

@app.route("/painel_aluno")
@app.route("/painel_aluno/<int:user_id>")
def painel_aluno(user_id=None):
    if user_id:
        usuario = Usuario.query.get_or_404(user_id)
        if usuario.tipo != 'aluno' or not usuario.premium:
            return "Acesso negado.", 403
    else:
        usuario_id = session.get("usuario_id")
        if not usuario_id:
            return redirect(url_for("login_usuario"))
        usuario = Usuario.query.get(usuario_id)
        if not usuario or usuario.tipo != 'aluno' or not usuario.premium:
            return redirect(url_for("painel_usuario"))

    return render_template("painel_aluno.html", usuario=usuario)

@app.route("/painel_professor")
@app.route("/painel_professor/<int:user_id>")
def painel_professor(user_id=None):
    if user_id:
        usuario = Usuario.query.get_or_404(user_id)
        if usuario.tipo != 'professor' or not usuario.premium:
            return "Acesso negado.", 403
    else:
        usuario_id = session.get("usuario_id")
        if not usuario_id:
            return redirect(url_for("login_usuario"))
        usuario = Usuario.query.get(usuario_id)
        if not usuario or usuario.tipo != 'professor' or not usuario.premium:
            return redirect(url_for("painel_usuario"))

    return render_template("painel_professor.html", usuario=usuario)

@app.route('/usuario/<int:user_id>/toggle_premium')
def toggle_premium(user_id):
    if 'user' not in session or session['user'] not in SUPER_ADMINS:
        return "Acesso negado", 403

    usuario = Usuario.query.get_or_404(user_id)
    usuario.premium = not usuario.premium
    db.session.commit()

    flash(f"{'✅ Usuário agora é premium!' if usuario.premium else '❌ Premium removido com sucesso.'}", "info")
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/admin/trocar-tipo', methods=['POST'])
def trocar_tipo_usuario():
    data = request.get_json()
    user_id = data.get("user_id")

    usuario = Usuario.query.get(user_id)

    if not usuario:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário não encontrado'}), 404

    # Trocar tipo
    if usuario.tipo == "aluno":
        usuario.tipo = "professor"
    else:
        usuario.tipo = "aluno"

    db.session.commit()

    return jsonify({'status': 'sucesso', 
    'novo_tipo': usuario.tipo})

EBOOK_FOLDER = os.path.join(os.path.dirname(__file__), 'ebooks')

@app.route('/ebooks')
def pagina_ebooks():
    if not session.get('usuario_id') or not session.get('premium'):
        flash("Acesso restrito a usuários premium.", "danger")
        return redirect(url_for('painel_usuario'))

    try:
        arquivos = [f for f in os.listdir(EBOOK_FOLDER) if f.endswith('.pdf') or f.endswith('.epub')]
    except FileNotFoundError:
        arquivos = []

    return render_template("ebooks.html", arquivos=arquivos)

@app.route('/ebooks/<path:nome>')
def baixar_ebook(nome):
    return send_from_directory(EBOOK_FOLDER, nome, as_attachment=True)

# ✅ Rota principal da home
@app.route("/home-inteligente")
def home_inteligente():
    try:
        ferramentas = Ferramenta.query.all()
    except Exception as e:
        ferramentas = []
        print(f"Erro ao carregar ferramentas: {e}")

    # 🔥 IA Mais Usada da Semana (com base em acessos_semana.json)
    try:
        with open('logs/acessos_semana.json') as f:
            acessos_semana = json.load(f)
    except Exception:
        acessos_semana = {}

    nome_top = max(acessos_semana, key=acessos_semana.get) if acessos_semana else None
    ia_mais_usada = next((f for f in ferramentas if f.nome == nome_top), None) if nome_top else None

    # 🏆 Top 5 com base nos acessos
    top_5 = Ferramenta.query.order_by(desc(Ferramenta.acessos_totais)).limit(5).all()

    # 🎲 Aleatória e recomendada
    ia_aleatoria = random.choice(ferramentas) if ferramentas else None
    ia_recomendada = random.choice(ferramentas) if ferramentas else None

    # 💡 Dicas
    dicas = [
        "Você sabia que pode automatizar posts no Instagram com IA?",
        "Use IAs para gerar resumos de textos em segundos!",
        "A IA pode criar apresentações de slides inteiras com base num texto.",
        "Você pode criar imagens a partir de descrições usando IA de texto para imagem!",
        "Use IA para gerar contratos, currículos e propostas em segundos!"
    ]
    dica = random.choice(dicas)

    # 📰 Notícia curada
    noticia = buscar_noticia_curada()

    # 📢 Casos reais (estáticos por enquanto)
    casos_reais = [
        {
            "titulo": "Estudantes do IFPR usam IA para monitorar aprendizado",
            "descricao": "O projeto utiliza análise de dados de desempenho e recomendações automatizadas para auxiliar alunos com dificuldades.",
            "link": "https://example.com/ia-ifpr"
        },
        {
            "titulo": "Professora do ensino básico cria plano de aula com ChatGPT",
            "descricao": "A ferramenta ajudou na criação de um cronograma adaptativo para alunos com deficiência auditiva.",
            "link": "https://example.com/chatgpt-escola"
        }
    ]

    # 🔗 Fórum e ranking
    topicos_recentes = Topico.query.order_by(Topico.data_criacao.desc()).limit(5).all()
    ranking = Usuario.query.order_by(Usuario.pontos.desc()).limit(10).all()

    return render_template(
        "home_inteligente.html",
        ia_mais_usada=ia_mais_usada,
        top_5=top_5,
        ia_aleatoria=ia_aleatoria,
        ia_recomendada=ia_recomendada,
        dica=dica,
        noticia=noticia,
        casos_reais=casos_reais,
        topicos_recentes=topicos_recentes,
        ranking=ranking
    )

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.path.exists(app.config['DATABASE_FILE']):
        with open(app.config['DATABASE_FILE'], 'w') as f:
            json.dump([], f)
    with app.app_context():
        db.create_all()
    app.run(debug=app.config['DEBUG'])