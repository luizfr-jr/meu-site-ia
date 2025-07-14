# Configuração do Banco de Dados - Firebase Firestore

Este documento explica como configurar o Firebase Firestore para habilitar o gerenciamento dinâmico das ferramentas de IA.

## Estado Atual

O sistema possui duas funcionalidades:

1. **Modo Local** (padrão): Usa dados estáticos do arquivo `src/data/ias.ts`
2. **Modo Database** (quando configurado): Usa Firebase Firestore para CRUD completo

## Como Configurar o Firebase

### 1. Criar Projeto no Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Clique em "Adicionar projeto"
3. Nomeie seu projeto (ex: "meu-site-ia")
4. Siga as etapas de criação

### 2. Configurar Firestore

1. No painel do Firebase, vá em "Firestore Database"
2. Clique em "Criar banco de dados"
3. Escolha o modo de produção
4. Selecione uma localização (ex: southamerica-east1)

### 3. Obter Configurações

1. Vá em "Configurações do projeto" (ícone de engrenagem)
2. Na aba "Geral", role até "Seus aplicativos"
3. Clique em "Adicionar app" e selecione "Web"
4. Registre o app com um nome
5. Copie o objeto de configuração

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as configurações do Firebase:

```env
# Configuração do Firebase
VITE_FIREBASE_API_KEY=sua-api-key-aqui
VITE_FIREBASE_AUTH_DOMAIN=seu-projeto.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=seu-projeto-id
VITE_FIREBASE_STORAGE_BUCKET=seu-projeto.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef123456

# Credenciais de administrador
VITE_ADMIN_USER_1_EMAIL=admin@exemplo.com
VITE_ADMIN_USER_1_PASSWORD=sua-senha-segura
VITE_ADMIN_USER_2_EMAIL=admin2@exemplo.com
VITE_ADMIN_USER_2_PASSWORD=outra-senha-segura
```

### 5. Configurar Regras de Segurança

No Firestore, configure as regras de segurança:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Permitir leitura pública da coleção ai-tools
    match /ai-tools/{document} {
      allow read: if true;
      allow write: if false; // Desabilitar escrita pública por segurança
    }
  }
}
```

**Nota**: Para um sistema de produção completo, você precisaria implementar autenticação Firebase no frontend.

### 6. Deploy das Variáveis

#### Vercel
1. Vá no painel do Vercel
2. Selecione seu projeto
3. Vá em "Settings" > "Environment Variables"
4. Adicione cada variável `VITE_*` com seus valores

#### Netlify
1. Vá no painel do Netlify
2. Selecione seu site
3. Vá em "Site settings" > "Environment variables"
4. Adicione as variáveis

## Funcionalidades Ativadas

Quando o Firebase estiver configurado corretamente, o sistema automaticamente:

1. ✅ **Detecta a configuração** e ativa o modo database
2. ✅ **Inicializa o banco** com os dados padrão na primeira execução
3. ✅ **Habilita CRUD completo** no painel administrativo
4. ✅ **Sincroniza em tempo real** entre múltiplas sessões
5. ✅ **Persiste alterações** permanentemente

## Interface Administrativa

### Modo Local (sem configuração)
- ⚠️ Mostra aviso "Modo Local Ativo"
- 🔒 Botões de edição/exclusão desabilitados
- 🔒 Botão "Adicionar Nova" desabilitado
- 📊 Exibe dados estáticos apenas

### Modo Database (configurado)
- ✅ Interface completa habilitada
- ✏️ Adicionar, editar e excluir ferramentas
- 🔄 Atualizações em tempo real
- 💾 Persistência automática

## Estrutura de Dados

Cada ferramenta no Firestore terá esta estrutura:

```typescript
{
  id: string;           // ID do documento
  name: string;         // Nome da ferramenta
  description: string;  // Descrição
  image: string;        // URL da imagem
  url: string;          // URL da ferramenta
  category: string;     // Categoria
  tags: string[];       // Array de tags
  createdAt: Date;      // Data de criação
  updatedAt: Date;      // Data da última atualização
}
```

## Troubleshooting

### Problema: "Modo Local" ainda ativo após configuração

**Possíveis causas:**
1. Variáveis de ambiente não definidas corretamente
2. Valores ainda com defaults ("demo-api-key", etc.)
3. Deploy não realizado após adicionar variáveis

**Solução:**
1. Verifique se todas as variáveis `VITE_FIREBASE_*` estão definidas
2. Confirme que os valores não são os defaults
3. Faça novo deploy após adicionar variáveis

### Problema: Erro de conexão com Firebase

**Possíveis causas:**
1. Configurações incorretas
2. Regras do Firestore muito restritivas
3. Projeto Firebase não configurado corretamente

**Solução:**
1. Verifique as configurações no Console Firebase
2. Confirme que o Firestore está ativado
3. Verifique as regras de segurança

## Migração de Dados

O sistema automaticamente inicializa o banco com os dados padrão do arquivo `src/data/ias.ts` na primeira execução. Não é necessária migração manual.

## Backup e Recuperação

Para fazer backup dos dados:

1. Use o Firebase CLI:
```bash
firebase firestore:export gs://seu-bucket/backup
```

2. Ou export via código JavaScript no console do navegador:
```javascript
// Este código pode ser executado no console do admin para exportar dados
const tools = await DatabaseService.getAllTools();
console.log(JSON.stringify(tools, null, 2));
```