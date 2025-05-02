#!/bin/bash

# Script para atualizar o dashboard.py para funcionar dentro do Docker

# Atualizar caminhos nos arquivos
sed -i 's|scraper-tracks/|/app/|g' dashboard.py
sed -i 's|app.run(debug=True, port=5001)|app.run(host="0.0.0.0", debug=False, port=5002)|' dashboard.py

# Atualizar caminhos em extrair_cds_*.py
for file in extrair_cds_*.py; do
    if [ -f "$file" ]; then
        echo "Atualizando caminhos em $file"
        sed -i 's|debug/|/app/debug/|g' "$file"
        sed -i 's|produtos_cd_|/app/produtos_cd_|g' "$file"
    fi
done

# Atualizar os scripts Selenium para funcionar em modo headless
for file in extrair_cds_*_selenium.py; do
    if [ -f "$file" ]; then
        echo "Configurando modo headless para $file"
        # Adicionar opções para Chrome headless
        sed -i 's|options = webdriver.ChromeOptions()|options = webdriver.ChromeOptions()\n    options.add_argument("--headless")\n    options.add_argument("--no-sandbox")\n    options.add_argument("--disable-dev-shm-usage")|g' "$file"
    fi
done

echo "Arquivos atualizados para funcionarem dentro do Docker!" 