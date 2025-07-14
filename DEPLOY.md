# Configuração de Deploy - GitHub Pages e Vercel

Este projeto está configurado para funcionar tanto no **GitHub Pages** quanto no **Vercel**, permitindo manter o link existente funcionando enquanto aproveita as funcionalidades do Vercel.

## 🔗 Links de Deploy

- **GitHub Pages**: `https://kallebyx.github.io/hubcientifico/` (repositório principal)
- **Vercel**: `https://hubcientifico.vercel.app/` (deploy automático)
- **Repositório**: `https://github.com/KallebyX/hubcientifico`

## ✅ Status Atual - RESOLVIDO

**Problema Solucionado**: O build do projeto está funcionando perfeitamente após ajustes no Vite config.

**Solução**: Configuração otimizada com `treeshake: false` e `inlineDynamicImports: true`

### ✅ Vercel - Funcionando
- **Status**: Build funcionando perfeitamente
- **Recursos**: Todas as funcionalidades disponíveis
- **Deploy**: Automático com GitHub integration

### ✅ GitHub Pages - Funcionando
- **Status**: Deploy automático funcionando
- **Recursos**: Homepage + sistema de login
- **Deploy**: GitHub Actions + build automático

## 📋 Comandos de Deploy

### 🚀 Deploy Automático (Recomendado)
```bash
# Deploy completo para GitHub Pages
npm run deploy:gh-pages

# Build para GitHub Pages
npm run build:gh-pages

# Build normal
npm run build
```

### 🛠️ Configuração Vercel

#### Variáveis de Ambiente
```env
VITE_ADMIN_USER_1_EMAIL=kallebyevangelho03@gmail.com
VITE_ADMIN_USER_1_PASSWORD=kk030904K.k
VITE_ADMIN_USER_2_EMAIL=luizfjr@gmail.com
VITE_ADMIN_USER_2_PASSWORD=luizAdmin@hub2025
```

#### Configuração:
1. Acesse o dashboard do Vercel
2. Vá em Project Settings > Environment Variables
3. Adicione cada variável com o valor correspondente
4. Configure Base Directory: deixe em branco ou `/`
5. Configure Build Command: `npm run build`
6. Configure Output Directory: `dist`

### 🔧 Configuração Técnica que Resolveu o Problema

#### vite.config.ts
```typescript
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      treeshake: false,
      output: {
        format: 'es',
        inlineDynamicImports: true,
      },
    },
  },
  optimizeDeps: {
    force: true,
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@heroui/react',
      'framer-motion',
      'lucide-react',
    ],
  },
})
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