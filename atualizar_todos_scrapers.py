#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar todos os scrapers de CDs em sequência,
garantindo uma atualização completa dos produtos de todas as lojas
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime

# Configuração de logging
os.makedirs('logs', exist_ok=True)
data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/atualizacao_completa_scrapers_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def executar_comando(comando, descricao):
    """
    Executa um comando no sistema e captura a saída
    
    Args:
        comando: Lista com o comando a ser executado
        descricao: Descrição do comando para logs
        
    Returns:
        True se o comando foi executado com sucesso, False caso contrário
    """
    logger.info(f"Iniciando: {descricao}")
    try:
        # Executa o comando e captura a saída em tempo real
        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Imprime e loga a saída em tempo real
        for linha in iter(processo.stdout.readline, ''):
            logger.info(linha.strip())
            print(linha, end='')
        
        # Aguarda o término do processo
        processo.wait()
        
        if processo.returncode == 0:
            logger.info(f"Concluído com sucesso: {descricao}")
            return True
        else:
            logger.error(f"Erro ao executar: {descricao}. Código de retorno: {processo.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Exceção ao executar {descricao}: {e}")
        return False

def atualizar_todos_scrapers():
    """
    Executa todos os scrapers para atualização completa
    """
    logger.info("=== Iniciando atualização completa de todos os scrapers ===")
    
    # Backup dos arquivos CSV existentes
    backup_dir = os.path.join('backup', data_hora)
    os.makedirs(backup_dir, exist_ok=True)
    
    # Identificar os arquivos CSV para backup
    arquivos_csv = [f for f in os.listdir('.') if f.startswith('produtos_cd_') and f.endswith('.csv')]
    
    for arquivo in arquivos_csv:
        if os.path.exists(arquivo):
            backup_path = os.path.join(backup_dir, arquivo)
            try:
                # Copia o arquivo para backup
                import shutil
                shutil.copy2(arquivo, backup_path)
                logger.info(f"Backup criado: {backup_path}")
            except Exception as e:
                logger.warning(f"Erro ao criar backup de {arquivo}: {e}")
    
    # Lista de scrapers a serem executados
    scrapers = [
        {
            'comando': ['python3', 'extrair_cds_locomotiva.py'],
            'descricao': 'Scraper de CDs Usados da Locomotiva Discos'
        },
        {
            'comando': ['python3', 'extrair_cds_locomotiva_novos.py'],
            'descricao': 'Scraper de CDs Novos da Locomotiva Discos'
        },
        {
            'comando': ['python3', 'extrair_cds_tracks.py'],
            'descricao': 'Scraper da Tracks Rio'
        },
        {
            'comando': ['python3', 'extrair_cds_supernova.py'],
            'descricao': 'Scraper da Supernova Discos'
        },
        {
            'comando': ['python3', 'extrair_cds_supernova_selenium.py'],
            'descricao': 'Scraper da Supernova Discos (Selenium)'
        },
        {
            'comando': ['python3', 'extrair_cds_pops_discos.py'],
            'descricao': 'Scraper da Pops Discos'
        },
        {
            'comando': ['python3', 'extrair_cds_sebo_messias.py'],
            'descricao': 'Scraper do Sebo do Messias'
        },
        {
            'comando': ['python3', 'extrair_cds_sebo_messias_selenium.py'],
            'descricao': 'Scraper do Sebo do Messias (Selenium)'
        },
        {
            'comando': ['python3', 'extrair_cds_shopee_selenium.py'],
            'descricao': 'Scraper da Shopee (LinhuaCong)'
        }
    ]
    
    # Executa cada scraper na sequência
    resultados = []
    for scraper in scrapers:
        logger.info(f"{'=' * 50}")
        logger.info(f"Executando: {scraper['descricao']}")
        logger.info(f"{'=' * 50}")
        
        sucesso = executar_comando(scraper['comando'], scraper['descricao'])
        resultados.append({
            'descricao': scraper['descricao'],
            'sucesso': sucesso
        })
        
        # Aguarda um pouco entre os scrapers para não sobrecarregar o sistema
        time.sleep(10)
    
    # Relatório final
    logger.info(f"{'=' * 50}")
    logger.info("Relatório de execução:")
    for resultado in resultados:
        status = "SUCESSO" if resultado['sucesso'] else "FALHA"
        logger.info(f"{resultado['descricao']}: {status}")
    logger.info(f"{'=' * 50}")
    
    # Calcula estatísticas
    total = len(resultados)
    sucessos = sum(1 for r in resultados if r['sucesso'])
    falhas = total - sucessos
    
    logger.info(f"Total de scrapers: {total}")
    logger.info(f"Executados com sucesso: {sucessos}")
    logger.info(f"Falhas: {falhas}")
    
    return all(r['sucesso'] for r in resultados)

if __name__ == "__main__":
    try:
        resultado = atualizar_todos_scrapers()
        codigo_saida = 0 if resultado else 1
        logger.info(f"Atualização completa finalizada. Resultado geral: {'Sucesso' if resultado else 'Falha'}")
        sys.exit(codigo_saida)
    except KeyboardInterrupt:
        logger.info("Atualização interrompida pelo usuário.")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Erro crítico durante atualização: {e}")
        sys.exit(1) 