#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para instalar as dependências necessárias para os scrapers
"""

import subprocess
import sys

def instalar_dependencias():
    """Instala todas as dependências necessárias para os scrapers"""
    
    print("Iniciando instalação de dependências...")
    
    # Lista de pacotes necessários
    pacotes = [
        "requests",
        "beautifulsoup4",
        "lxml",
        "flask",
        "selenium",
        "webdriver-manager",
        "pandas"
    ]
    
    # Instalação de cada pacote
    for pacote in pacotes:
        print(f"Instalando {pacote}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
            print(f"{pacote} instalado com sucesso!")
        except subprocess.CalledProcessError:
            print(f"Erro ao instalar {pacote}. Verifique sua conexão com a internet ou permissões.")
            return False
    
    print("\nTodas as dependências foram instaladas com sucesso!")
    print("\nPacotes instalados:")
    print("- requests: Para fazer requisições HTTP")
    print("- beautifulsoup4: Para análise de HTML")
    print("- lxml: Parser HTML/XML para BeautifulSoup")
    print("- flask: Para o dashboard web")
    print("- selenium: Para automação de navegador web")
    print("- webdriver-manager: Para gerenciamento do driver do Selenium")
    print("- pandas: Para manipulação de dados (opcional)")
    
    print("\nComo executar os scrapers:")
    print("1. Individualmente: python extrair_cds_NOME.py")
    print("2. Via dashboard: python dashboard.py")
    print("   Acesse http://localhost:5001 no navegador")
    
    return True

if __name__ == "__main__":
    instalar_dependencias() 