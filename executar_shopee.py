#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar o scraper da Shopee com diferentes configurações
"""

import argparse
import logging
import os
from extrair_cds_shopee import ShopeeScraperSelenium
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('executar_shopee')

def main():
    # Configurar o parser de argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Executa o scraper da Shopee com configurações personalizadas')
    
    parser.add_argument('--vendor', type=str, default='linhuacong.br',
                        help='ID do vendedor da Shopee (por padrão: linhuacong.br)')
    
    parser.add_argument('--max-paginas', type=int, default=5,
                        help='Número máximo de páginas a serem processadas (por padrão: 5)')
    
    parser.add_argument('--output', type=str, default=None,
                        help='Nome do arquivo de saída CSV (por padrão: produtos_cd_shopee.csv)')
    
    parser.add_argument('--headless', action='store_true',
                        help='Executar em modo headless (sem interface gráfica)')
    
    parser.add_argument('--espera', type=float, default=3.0,
                        help='Tempo de espera (em segundos) após carregar uma página (por padrão: 3.0)')
    
    parser.add_argument('--username', type=str, default=None,
                        help='Nome de usuário ou email para login na Shopee (prioridade sobre .env)')
    
    parser.add_argument('--password', type=str, default=None,
                        help='Senha para login na Shopee (prioridade sobre .env)')
    
    # Parse dos argumentos
    args = parser.parse_args()
    
    # Se fornecidos via linha de comando, sobrescrevem os valores do .env
    if args.username:
        os.environ["SHOPEE_USERNAME"] = args.username
    
    if args.password:
        os.environ["SHOPEE_PASSWORD"] = args.password
    
    # Exibir configurações
    logger.info(f"Iniciando scraper com as seguintes configurações:")
    logger.info(f"Vendor ID: {args.vendor}")
    logger.info(f"Máximo de páginas: {args.max_paginas}")
    logger.info(f"Arquivo de saída: {args.output or 'produtos_cd_shopee.csv (padrão)'}")
    logger.info(f"Modo headless: {'Sim' if args.headless else 'Não'}")
    logger.info(f"Tempo de espera por página: {args.espera} segundos")
    logger.info(f"Usando credenciais: {'Sim' if os.getenv('SHOPEE_USERNAME') and os.getenv('SHOPEE_PASSWORD') else 'Não'}")
    
    # Inicializar e executar o scraper
    scraper = ShopeeScraperSelenium(
        max_paginas=args.max_paginas,
        arquivo_saida=args.output,
        headless=args.headless,
        vendor_id=args.vendor,
        espera_pagina=args.espera
    )
    
    scraper.executar()
    
    logger.info("Scraper finalizado!")

if __name__ == "__main__":
    main() 