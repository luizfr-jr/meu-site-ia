# 🤖 Hub Científico de IA

Uma plataforma moderna e intuitiva para descobrir, explorar e gerenciar ferramentas de Inteligência Artificial científica e acadêmica.

## 🌟 Sobre o Projeto

O Hub Científico de IA é uma aplicação web desenvolvida para centralizar e organizar ferramentas de IA voltadas para pesquisa científica, oferecendo uma interface limpa e funcional para pesquisadores, estudantes e profissionais da área.

## ✨ Funcionalidades

### 🔍 Exploração de IAs
- **Catálogo Completo**: Mais de 50 ferramentas de IA categorizadas
- **Filtros Avançados**: Busca por categoria, popularidade e funcionalidade
- **Interface Responsiva**: Design adaptável para desktop e mobile
- **Tema Claro/Escuro**: Suporte completo a temas personalizáveis

### 🔐 Sistema de Autenticação
- **Login Seguro**: Autenticação protegida para administradores
- **Gestão de Sessões**: Tokens JWT com cookies seguros
- **Rotas Protegidas**: Área administrativa restrita
- **Credenciais Seguras**: Variáveis de ambiente para proteção

### 🛠️ Área Administrativa
- **Gerenciamento de Conteúdo**: Adicionar/editar ferramentas de IA
- **Dashboard Completo**: Estatísticas e métricas do sistema
- **Interface Intuitiva**: Formulários e controles avançados

## 🚀 Tecnologias Utilizadas

### Frontend
- **React 18.3.1** - Biblioteca JavaScript moderna
- **TypeScript** - Tipagem estática para JavaScript
- **Vite** - Build tool rápido e moderno
- **React Router DOM** - Roteamento SPA

### UI/UX
- **Tailwind CSS 3.4.17** - Framework CSS utilitário
- **HeroUI React** - Componentes UI modernos
- **Framer Motion** - Animações suaves
- **Lucide React** - Ícones vetoriais

### Autenticação & Formulários
- **React Hook Form** - Gerenciamento de formulários
- **Zod** - Validação de esquemas
- **js-cookie** - Gerenciamento de cookies
- **JWT** - JSON Web Tokens

### Deploy & CI/CD
- **Vercel** - Hospedagem e deploy automático
- **GitHub Actions** - Integração contínua
- **GitHub Pages** - Redirecionamento automático

## 📱 Demonstração

🌐 **Site Principal**: [https://hubcientifico.vercel.app/](https://hubcientifico.vercel.app/)

## 🔧 Instalação e Uso

### Pré-requisitos
- Node.js 18+ 
- npm ou yarn

### 1. Clone o repositório
```bash
git clone https://github.com/KallebyX/hubcientifico.git
cd hubcientifico
```

### 2. Instale as dependências
```bash
npm install
```

### 3. Configure as variáveis de ambiente
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:
```env
VITE_ADMIN_USER_1=seu_usuario_1
VITE_ADMIN_PASS_1=sua_senha_1
VITE_ADMIN_USER_2=seu_usuario_2
VITE_ADMIN_PASS_2=sua_senha_2
```

### 4. Execute o projeto
```bash
npm run dev
```

O projeto estará disponível em `http://localhost:5173`

## 🚀 Deploy

### Deploy Automático (Vercel)
O projeto está configurado para deploy automático no Vercel:
- Commits na branch `main` disparam deploy automaticamente
- Variáveis de ambiente configuradas no painel do Vercel
- URL personalizada: `hubcientifico.vercel.app`

### Deploy Manual
```bash
npm run build
npm run preview
```

## 🔐 Autenticação

O sistema possui duas contas administrativas pré-configuradas:
- **Usuário 1**: Kalleby (configurado via variáveis de ambiente)
- **Usuário 2**: Luiz (configurado via variáveis de ambiente)

### Recursos de Segurança
- Senhas hasheadas com salt
- Tokens JWT com expiração
- Cookies seguros com httpOnly
- Proteção contra ataques CSRF

## 📁 Estrutura do Projeto

```
hubcientifico/
├── public/                 # Arquivos estáticos
├── src/
│   ├── components/        # Componentes React
│   ├── contexts/         # Contextos React
│   ├── data/            # Dados estáticos
│   ├── hooks/           # Hooks customizados
│   ├── pages/           # Páginas da aplicação
│   ├── types/           # Tipos TypeScript
│   └── utils/           # Utilitários
├── .github/
│   └── workflows/       # GitHub Actions
├── .env.example         # Exemplo de variáveis
├── vite.config.ts       # Configuração Vite
└── tailwind.config.js   # Configuração Tailwind
```

## 🎨 Personalização

### Temas
O projeto suporta temas claro e escuro através do `useTheme` hook:
```typescript
const { theme, toggleTheme } = useTheme();
```

### Adicionando Novas IAs
Para adicionar novas ferramentas de IA, edite o arquivo `src/data/ias.ts`:
```typescript
{
  id: 'nova-ia',
  name: 'Nome da IA',
  description: 'Descrição completa',
  category: 'categoria',
  url: 'https://exemplo.com',
  isPopular: false
}
```

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autores

- **Kalleby** - [@KallebyX](https://github.com/KallebyX)
- **Luiz** - [@luizfr-jr](https://github.com/luizfr-jr)

## 🙏 Agradecimentos

- Comunidade React e TypeScript
- Equipe do Tailwind CSS
- Contribuidores do HeroUI
- Plataforma Vercel

---

**Desenvolvido com ❤️ para a comunidade científica brasileira**
