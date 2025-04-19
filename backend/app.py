import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from config.settings import Config
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.message import EmailMessage
from openai import OpenAI

# Carrega variáveis de ambiente
load_dotenv()
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
logging.basicConfig(filename='logs/app_security.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

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

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

SUPER_ADMINS = ['admin', 'luiz']

@app.route('/')
def pagina_publica():
    registrar_acesso_publico(request.remote_addr)
    return redirect('/ferramentas')

@app.route('/ferramentas')
def ferramentas():
    return send_from_directory('../frontend', 'index.html')

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

    # Carregar admins do banco
    admins = Admin.query.all()

    # Carregar logs
    try:
        with open('logs/app_security.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()
    except Exception as e:
        logs = [f"Erro ao carregar log: {e}"]

    # Carregar métricas de acesso
    total_index = 0
    unique_index_ips = 0
    try:
        with open(ACCESS_LOG_FILE, 'r') as f:
            index_data = json.load(f)
            total_index = index_data.get("total", 0)
            unique_index_ips = len(index_data.get("ips", []))
    except Exception:
        pass

    # Carregar histórico de buscas
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

    # Ordenar por frequência
    perguntas_populares = sorted(busca_contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    categorias_populares = sorted(categoria_contagem.items(), key=lambda x: x[1], reverse=True)[:10]

    return render_template(
    'usuarios.html',
    admins=admins,
    logs=logs[::-1],
    total_index=total_index,
    unique_index_ips=unique_index_ips,
    perguntas_populares=perguntas_populares,
    categorias_populares=categorias_populares
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.path.exists(app.config['DATABASE_FILE']):
        with open(app.config['DATABASE_FILE'], 'w') as f:
            json.dump([], f)
    with app.app_context():
        db.create_all()
    app.run(debug=app.config['DEBUG'])