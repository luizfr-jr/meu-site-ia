from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

# Inicializa o SQLAlchemy
db = SQLAlchemy()

# Tabela de relacionamento de seguidores
seguidores = db.Table('seguidores',
    db.Column('seguidor_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('seguido_id', db.Integer, db.ForeignKey('usuario.id'))
)

class Usuario(db.Model):
    __tablename__ = 'usuario'

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
    biografia = db.Column(db.Text)
    linkedin = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    github = db.Column(db.String(255))
    tipo = db.Column(db.String(50))  # aluno ou professor
    foto = db.Column(db.String(255))
    pontos = db.Column(db.Integer, default=0)

    topicos = db.relationship("Topico", backref="usuario", lazy=True)
    respostas = db.relationship("Resposta", backref="usuario", lazy=True)
    medalhas = db.relationship("MedalhaUsuario", backref="usuario", lazy=True)
    curtidas_topico = db.relationship("CurtidaTopico", backref="usuario", lazy=True)
    curtidas_resposta = db.relationship("CurtidaResposta", backref="usuario", lazy=True)
    notificacoes = db.relationship("Notificacao", backref="usuario", lazy=True)

    seguindo = db.relationship(
        'Usuario',
        secondary=seguidores,
        primaryjoin=(seguidores.c.seguidor_id == id),
        secondaryjoin=(seguidores.c.seguido_id == id),
        backref=db.backref('seguidores', lazy='dynamic'),
        lazy='dynamic'
    )

    def atualizar_pontuacao(self, valor):
        self.pontos += valor
        db.session.commit()
        self.verificar_conquistas()

    def verificar_conquistas(self):
        conquistas = [
            (100, "🔥 Centelha do Saber", "Alcançou 100 pontos.", "medalha1.webp"),
            (500, "🚀 Explorador Ativo", "Contribuiu com 10 respostas.", "medalha2.webp"),
            (1000, "🌟 Estrela do Fórum", "Acumulou 1000 pontos.", "medalha3.webp")
        ]
        for pontos, nome, desc, icone in conquistas:
            existente = MedalhaUsuario.query.filter_by(usuario_id=self.id, nome=nome).first()
            if self.pontos >= pontos and not existente:
                nova = MedalhaUsuario(usuario_id=self.id, nome=nome, descricao=desc, icone=icone, tipo="pontuacao")
                db.session.add(nova)
                db.session.commit()

    def seguir(self, usuario):
        if not self.esta_seguindo(usuario):
            self.seguindo.append(usuario)

    def deixar_de_seguir(self, usuario):
        if self.esta_seguindo(usuario):
            self.seguindo.remove(usuario)

    def esta_seguindo(self, usuario):
        return self.seguindo.filter(seguidores.c.seguido_id == usuario.id).count() > 0

class LogAcesso(db.Model):
    __tablename__ = 'log_acesso'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_acesso = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Topico(db.Model):
    __tablename__ = 'topico'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    resumo_ia = db.Column(db.Text)

    respostas = db.relationship("Resposta", backref="topico", lazy=True, cascade="all, delete-orphan")
    curtidas_topico = db.relationship("CurtidaTopico", backref="topico", lazy=True, cascade="all, delete-orphan")
    denuncias = db.relationship("Denuncia", backref="topico", lazy=True, cascade="all, delete-orphan")

    @hybrid_property
    def curtidas(self):
        return len(self.curtidas_topico)

    @hybrid_property
    def respostas_count(self):
        return len(self.respostas)

class Resposta(db.Model):
    __tablename__ = 'resposta'

    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    topico_id = db.Column(db.Integer, db.ForeignKey('topico.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    citado_id = db.Column(db.Integer, db.ForeignKey('resposta.id'), nullable=True)

    citado = db.relationship('Resposta', remote_side=[id], backref='citacoes')
    curtidas_resposta = db.relationship("CurtidaResposta", backref="resposta", lazy=True, cascade="all, delete-orphan")
    denuncias = db.relationship("Denuncia", backref="resposta", lazy=True, cascade="all, delete-orphan")

    @hybrid_property
    def curtidas(self):
        return len(self.curtidas_resposta)

class CurtidaTopico(db.Model):
    __tablename__ = 'curtida_topico'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    topico_id = db.Column(db.Integer, db.ForeignKey('topico.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class CurtidaResposta(db.Model):
    __tablename__ = 'curtida_resposta'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class MedalhaUsuario(db.Model):
    __tablename__ = 'medalha_usuario'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    nome = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    icone = db.Column(db.String(100))
    tipo = db.Column(db.String(50))  # ex: "pontuacao", "atividade"
    data_conquista = db.Column(db.DateTime, default=datetime.utcnow)

class Notificacao(db.Model):
    __tablename__ = 'notificacao'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    mensagem = db.Column(db.String(255))
    lida = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

class Denuncia(db.Model):
    __tablename__ = 'denuncia'

    id = db.Column(db.Integer, primary_key=True)
    topico_id = db.Column(db.Integer, db.ForeignKey('topico.id'), nullable=True)
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta.id'), nullable=True)
    motivo = db.Column(db.String(255))
    comentario = db.Column(db.Text)
    data_denuncia = db.Column(db.DateTime, default=datetime.utcnow)
    moderada = db.Column(db.Boolean, default=False)

class Ferramenta(db.Model):
    __tablename__ = 'ferramenta'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=False)
    imagem = db.Column(db.String(255), nullable=True)
    categoria = db.Column(db.String(100), nullable=True)
    acessos_totais = db.Column(db.Integer, default=0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)