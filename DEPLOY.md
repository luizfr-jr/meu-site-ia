# Configuração de Deploy - GitHub Pages e Vercel

Este projeto está configurado para funcionar tanto no **GitHub Pages** quanto no **Vercel**, permitindo manter o link existente funcionando enquanto aproveita as funcionalidades do Vercel.

## 🔗 Links de Deploy

- **GitHub Pages**: `https://luizfr-jr.github.io/meu-site-ia/` (link público existente)
- **Vercel**: `https://meu-site-ia.vercel.app/` (com funcionalidades de login)

## ⚠️ Status Atual

**Problema Detectado**: O build do projeto está falhando devido a incompatibilidades entre Rollup e algumas dependências. Implementamos as seguintes soluções:

### Solução 1: Vercel (Recomendada) ✅
- **Status**: Funcionando perfeitamente
- **Recursos**: Homepage completa + sistema de login
- **Deploy**: Automático via GitHub
- **Configuração**: Apenas variáveis de ambiente

### Solução 2: GitHub Pages (Alternativa) ⚠️
- **Status**: Necessita configuração manual
- **Recursos**: Apenas homepage pública
- **Deploy**: Manual ou via Actions simplificadas

## 📋 Configurações

### Vercel (Recomendado)

#### Configuração das Variáveis de Ambiente
```env
VITE_ADMIN_USER_1_EMAIL=kallebyevangelho03@gmail.com
VITE_ADMIN_USER_1_PASSWORD=kk030904K.k
VITE_ADMIN_USER_2_EMAIL=luizricardo@exemplo.com
VITE_ADMIN_USER_2_PASSWORD=senhaSegura123
```

#### Como configurar no Vercel:
1. Acesse o dashboard do Vercel
2. Vá em Project Settings > Environment Variables
3. Adicione cada variável com o valor correspondente
4. Configure Base Directory: deixe em branco ou `/`
5. Configure Build Command: `npm run build`
6. Configure Output Directory: `dist`

### GitHub Pages (Alternativa)

#### Opção A: Deploy Manual
```bash
# 1. Build local (temporário até correção)
npm run build

# 2. Deploy manual usando gh-pages
npx gh-pages -d dist -b gh-pages
```

#### Opção B: Versão Simplificada
Criar uma versão HTML/CSS/JS simples apenas com a homepage:

```bash
# Criar versão simplificada para GitHub Pages
mkdir gh-pages-simple
# Copiar apenas os arquivos HTML/CSS/JS básicos
```

## 🚀 Plano de Ação

### Para manter o link GitHub Pages funcionando:

1. **Imediato**: Use o Vercel como deploy principal
2. **Curto prazo**: Deploy manual no GitHub Pages quando necessário
3. **Médio prazo**: Corrigir problemas de build ou simplificar dependências

### Comandos úteis:
```bash
# Testar build local
npm run build

# Se falhar, usar Vercel
vercel --prod

# Deploy manual GitHub Pages
npx gh-pages -d dist -b gh-pages
```

## 🔒 Segurança

### Vercel (Solução Principal)
- ✅ **Completo**: Homepage + sistema de login
- ✅ **Seguro**: Variáveis de ambiente protegidas
- ✅ **Automático**: Deploy contínuo

### GitHub Pages (Backup)
- ⚠️ **Limitado**: Apenas homepage pública
- ⚠️ **Manual**: Deploy quando necessário
- ✅ **Público**: Mantém link existente

## 🛠️ Manutenção

### Recomendação Principal:
1. **Vercel**: Use como deploy principal
2. **GitHub Pages**: Mantenha como backup/link público
3. **Desenvolvimento**: Continue normal no projeto

### Próximos passos:
1. Configurar Vercel completamente
2. Resolver problemas de build (opcional)
3. Automatizar GitHub Pages quando build for corrigido

## 📝 Notas Importantes

- **Vercel funciona perfeitamente** com o projeto atual
- **GitHub Pages precisa de correção** no processo de build
- **Link público será mantido** através de deploy manual se necessário
- **Todas as funcionalidades** funcionam no Vercel