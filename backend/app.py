import os
import json
import logging
from bs4 import BeautifulSoup
import random
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
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash

USUARIOS_FILE = "usuarios.json"

# ✅ Carregar variáveis do .env
load_dotenv()

NOTICIAS_CURADAS_JSON = "noticias_curadas.json"
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
app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
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

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

SUPER_ADMINS = ['admin', 'luiz']

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    acessos_total = db.Column(db.Integer, default=0)
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    navegador = db.Column(db.String(200))
    dispositivo = db.Column(db.String(100))



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
def login_usuario_comum():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            flash(f"Bem-vindo(a), {usuario.nome.split()[0]}!", "info")
            return redirect(url_for("painel_usuario"))

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

@app.route('/login-user', methods=['GET', 'POST'])
def login_usuario():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_nome'] = usuario.nome
            session['usuario_id'] = usuario.id
            session['usuario_email'] = usuario.email

            # Atualiza métricas de uso
            usuario.ultimo_login = datetime.utcnow()
            usuario.acessos_total += 1
            usuario.navegador = request.user_agent.browser
            usuario.dispositivo = request.user_agent.platform

            # Geolocalização baseada no IP (usando IPInfo ou outro serviço externo se necessário)
            try:
                ip = request.remote_addr
                cidade, estado = obter_localizacao_por_ip(ip)  # função fictícia, deve implementar API externa
                usuario.cidade = cidade
                usuario.estado = estado
            except:
                pass

            db.session.commit()
            return redirect(url_for('painel_usuario'))
        else:
            flash("E-mail ou senha inválidos.", "danger")
    return render_template("login_user.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        with open(app.config['DATABASE_FILE']) as f:
            ferramentas = json.load(f)
    except Exception:
        ferramentas = []
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
def api():
    with open(app.config['DATABASE_FILE']) as f:
        return jsonify(json.load(f))


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

@app.route('/como-usar')
def como_usar():
    return render_template('como_usar.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


# ✅ Rota principal da home
@app.route("/home-inteligente")
def home_inteligente():
    try:
        with open(app.config['DATABASE_FILE']) as f:
            ferramentas = json.load(f)
    except Exception as e:
        ferramentas = []
        print(f"Erro ao carregar ferramentas: {e}")

    try:
        with open('logs/acessos_semana.json') as f:
            acessos_semana = json.load(f)
    except Exception:
        acessos_semana = {}

    nome_top = max(acessos_semana, key=acessos_semana.get) if acessos_semana else None
    ia_mais_usada = next((f for f in ferramentas if f['nome'] == nome_top), {}) if nome_top else {}

    top_5 = sorted(ferramentas, key=lambda x: x.get("acessos_totais", 0), reverse=True)[:5]
    ia_aleatoria = random.choice(ferramentas) if ferramentas else {}
    ia_recomendada = random.choice(ferramentas) if ferramentas else {}

    dicas = [
        "Você sabia que pode automatizar posts no Instagram com IA?",
        "Use IAs para gerar resumos de textos em segundos!",
        "A IA pode criar apresentações de slides inteiras com base num texto.",
        "Você pode criar imagens a partir de descrições usando IA de texto para imagem!",
        "Use IA para gerar contratos, currículos e propostas em segundos!"
    ]
    dica = random.choice(dicas)

    noticia = buscar_noticia_curada()  # ✅ aqui você chama a função nova

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

    return render_template("home_inteligente.html",
                           ia_mais_usada=ia_mais_usada,
                           top_5=top_5,
                           ia_aleatoria=ia_aleatoria,
                           ia_recomendada=ia_recomendada,
                           dica=dica,
                           noticia=noticia,
                           casos_reais=casos_reais)


if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.path.exists(app.config['DATABASE_FILE']):
        with open(app.config['DATABASE_FILE'], 'w') as f:
            json.dump([], f)
    with app.app_context():
        db.create_all()
    app.run(debug=app.config['DEBUG'])