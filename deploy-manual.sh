#!/bin/bash
# Script de deploy manual para GitHub Pages
# Use este script enquanto o build automático não funciona

echo "🚀 Deploy manual para GitHub Pages"
echo "⚠️  Aviso: Este script deve ser executado apenas se o build automático falhar"

# Verifica se está no diretório correto
if [ ! -f "package.json" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do projeto"
    exit 1
fi

# Verifica se o git está limpo
if ! git diff --quiet; then
    echo "❌ Erro: Há mudanças não commitadas. Faça commit antes de executar."
    exit 1
fi

echo "📦 Tentando build..."
if npm run build; then
    echo "✅ Build realizado com sucesso!"
    
    # Deploy usando gh-pages
    echo "🌍 Fazendo deploy para GitHub Pages..."
    npx gh-pages -d dist -b gh-pages
    
    echo "✅ Deploy concluído!"
    echo "🔗 Acesse: https://luizfr-jr.github.io/meu-site-ia/"
else
    echo "❌ Build falhou. Verificando alternativas..."
    
    # Criar versão simplificada se necessário
    echo "🔄 Criando versão simplificada..."
    mkdir -p dist-manual
    
    # Copiar arquivos essenciais
    cp index.html dist-manual/
    cp -r public/* dist-manual/ 2>/dev/null || true
    
    # Criar CSS básico se necessário
    if [ ! -f "dist-manual/style.css" ]; then
        echo "/* Versão simplificada */" > dist-manual/style.css
    fi
    
    echo "📁 Versão simplificada criada em dist-manual/"
    echo "📝 Você pode fazer upload manual dos arquivos ou usar:"
    echo "   npx gh-pages -d dist-manual -b gh-pages"
fi

echo "✨ Processo finalizado!"