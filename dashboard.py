import os
import csv
import subprocess
import threading
import json
import re
from flask import Flask, render_template, jsonify, request, Response, send_file
from datetime import datetime
import hashlib
import time

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuração dos scrapers
SCRAPERS = {
    'sebo_messias': {
        'script': 'extrair_cds_sebo_messias.py',
        'nome': 'Sebo do Messias',
        'arquivo_csv': 'produtos_cd_sebo_messias.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()  # Armazenará IDs dos produtos da última execução
    },
    'sebo_messias_selenium': {
        'script': 'extrair_cds_sebo_messias_selenium.py',
        'nome': 'Sebo do Messias (Selenium)',
        'arquivo_csv': 'produtos_cd_sebo_messias_selenium.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'locomotiva_usados': {
        'script': 'extrair_cds_locomotiva.py',
        'nome': 'Locomotiva Discos (CDs Usados)',
        'arquivo_csv': 'produtos_cd_locomotiva.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'locomotiva_novos': {
        'script': 'extrair_cds_locomotiva_novos.py',
        'nome': 'Locomotiva Discos (CDs Novos)',
        'arquivo_csv': 'produtos_cd_locomotiva_novos.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'supernova': {
        'script': 'extrair_cds_supernova.py',
        'nome': 'Supernova',
        'arquivo_csv': 'produtos_cd_supernova.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'supernova_selenium': {
        'script': 'extrair_cds_supernova_selenium.py',
        'nome': 'Supernova (Selenium)',
        'arquivo_csv': 'produtos_cd_supernova_selenium.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'tracks': {
        'script': 'extrair_cds_tracks.py',
        'nome': 'Tracks Rio',
        'arquivo_csv': 'produtos_cd_tracks_rio.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'shopee': {
        'script': 'extrair_cds_shopee_selenium.py',
        'nome': 'Shopee (LinhuaCong)',
        'arquivo_csv': 'produtos_cd_shopee.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    },
    'pops_discos': {
        'script': 'extrair_cds_pops_discos.py',
        'nome': 'Pops Discos',
        'arquivo_csv': 'produtos_cd_pops_discos.csv',
        'status': 'parado',
        'processo': None,
        'ultima_execucao': None,
        'total_produtos': 0,
        'log_file': None,
        'produtos_anteriores': set()
    }
}

# Rota principal - Dashboard
@app.route('/')
def dashboard():
    # Atualiza informações de status para cada scraper
    for key in SCRAPERS:
        atualizar_informacoes_scraper(key)
    
    return render_template('dashboard.html', scrapers=SCRAPERS)

# Rota para executar a atualização completa da Locomotiva Discos
@app.route('/atualizar_locomotiva', methods=['POST'])
def atualizar_locomotiva():
    """Executa o script de atualização completa da Locomotiva Discos"""
    try:
        # Inicia o script em um processo separado
        thread = threading.Thread(target=executar_atualizacao_locomotiva)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'sucesso', 
            'mensagem': 'Atualização completa da Locomotiva Discos iniciada'
        })
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'mensagem': f'Erro ao iniciar atualização: {str(e)}'
        })

# Rota para executar a atualização completa de todos os scrapers
@app.route('/atualizar_todos', methods=['POST'])
def atualizar_todos():
    """Executa o script de atualização completa de todos os scrapers"""
    try:
        # Inicia o script em um processo separado
        thread = threading.Thread(target=executar_atualizacao_todos)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'sucesso', 
            'mensagem': 'Atualização completa de todos os scrapers iniciada'
        })
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'mensagem': f'Erro ao iniciar atualização: {str(e)}'
        })

def executar_atualizacao_todos():
    """Executa o script de atualização completa de todos os scrapers em um processo separado"""
    try:
        # Executa cada scraper no modo "full"
        for scraper_id in SCRAPERS:
            # Pula scrapers que já estão em execução
            if SCRAPERS[scraper_id]['status'] == 'rodando':
                continue
                
            # Executa o scraper no modo "full"
            try:
                executar_scraper(scraper_id, modo='full')
                # Pausa entre os scrapers para não sobrecarregar
                time.sleep(5)
            except Exception as e:
                print(f"Erro ao executar scraper {scraper_id}: {e}")
                
    except Exception as e:
        error_msg = f"Erro ao executar atualização de todos os scrapers: {e}"
        print(error_msg)

def executar_atualizacao_locomotiva():
    """Executa o script de atualização completa da Locomotiva Discos em um processo separado"""
    # Inicia os dois scrapers da Locomotiva no modo "full"
    try:
        # Scraper de CDs usados
        executar_scraper('locomotiva_usados', modo='full')
        
        # Aguarda 5 segundos entre os scrapers
        time.sleep(5)
        
        # Scraper de CDs novos
        executar_scraper('locomotiva_novos', modo='full')
        
    except Exception as e:
        print(f"Erro ao executar atualização da Locomotiva: {e}")

# Rota para iniciar um scraper
@app.route('/iniciar/<scraper_id>', methods=['POST'])
def iniciar_scraper(scraper_id):
    if scraper_id not in SCRAPERS:
        return jsonify({'status': 'erro', 'mensagem': 'Scraper não encontrado'})
    
    if SCRAPERS[scraper_id]['status'] == 'rodando':
        return jsonify({'status': 'aviso', 'mensagem': 'Scraper já está em execução'})
    
    try:
        # Recebe o modo de execução do formulário (padrão é "novos")
        modo = request.form.get('modo', 'novos')
        if modo not in ['full', 'novos']:
            modo = 'novos'  # Valor padrão seguro
        
        # Armazena os IDs dos produtos antes de iniciar um novo scraper
        arquivo_csv = SCRAPERS[scraper_id]['arquivo_csv']
        SCRAPERS[scraper_id]['produtos_anteriores'] = obter_ids_produtos_atuais(arquivo_csv)
        
        # Inicia o script em um processo separado
        thread = threading.Thread(target=executar_scraper, args=(scraper_id, modo))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'sucesso', 
            'mensagem': f'Scraper {SCRAPERS[scraper_id]["nome"]} iniciado com sucesso no modo {modo}'
        })
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': f'Erro ao iniciar scraper: {str(e)}'})

def obter_ids_produtos_atuais(arquivo_csv):
    """Obtém os IDs únicos dos produtos que já existem no CSV"""
    produtos_ids = set()
    
    if os.path.exists(arquivo_csv):
        try:
            with open(arquivo_csv, 'r', encoding='utf-8') as f:
                leitor = csv.DictReader(f)
                for produto in leitor:
                    # Cria um ID único baseado na URL e título do produto
                    produto_id = gerar_produto_id(produto)
                    produtos_ids.add(produto_id)
        except Exception as e:
            print(f"Erro ao ler produtos existentes: {e}")
    
    return produtos_ids

def gerar_produto_id(produto):
    """Gera um ID único para um produto baseado em seus atributos"""
    # Usa URL como identificador principal, pois deve ser único
    # Adiciona o título como backup, caso a URL mude mas seja o mesmo produto
    identificador = (produto.get('url', '') + produto.get('titulo', '')).encode('utf-8')
    return hashlib.md5(identificador).hexdigest()

def executar_scraper(scraper_id, modo="novos"):
    SCRAPERS[scraper_id]['status'] = 'rodando'
    SCRAPERS[scraper_id]['ultima_execucao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    script_path = SCRAPERS[scraper_id]['script']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"scraper_{scraper_id}_{timestamp}.log"
    SCRAPERS[scraper_id]['log_file'] = log_filename
    
    try:
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            # Adiciona o parâmetro --modo ao comando do script
            command = ['python3', script_path, '--modo', modo]
            
            process = subprocess.Popen(command, 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True)
            
            SCRAPERS[scraper_id]['processo'] = process
            
            # Captura a saída em tempo real e escreve no arquivo de log
            for line in iter(process.stdout.readline, ''):
                log_file.write(line)
                log_file.flush()
            
            # Aguarda o processo terminar
            process.wait()
            
            # Após concluído, atualiza o status
            if process.returncode == 0:
                SCRAPERS[scraper_id]['status'] = 'concluído'
            else:
                SCRAPERS[scraper_id]['status'] = 'erro'
            
            atualizar_informacoes_scraper(scraper_id)
            
    except Exception as e:
        SCRAPERS[scraper_id]['status'] = 'erro'
        print(f"Erro ao executar {script_path}: {e}")
        # Registra o erro no arquivo de log se possível
        try:
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                log_file.write(f"ERRO: {str(e)}\n")
        except:
            pass

# Rota para obter status de um scraper
@app.route('/status/<scraper_id>')
def status_scraper(scraper_id):
    if scraper_id not in SCRAPERS:
        return jsonify({'status': 'erro', 'mensagem': 'Scraper não encontrado'})
    
    atualizar_informacoes_scraper(scraper_id)
    
    return jsonify({
        'status': SCRAPERS[scraper_id]['status'],
        'ultima_execucao': SCRAPERS[scraper_id]['ultima_execucao'],
        'total_produtos': SCRAPERS[scraper_id]['total_produtos'],
        'log_file': SCRAPERS[scraper_id]['log_file']
    })

# Rota para obter produtos com paginação e busca
@app.route('/produtos/<scraper_id>')
def obter_produtos(scraper_id):
    if scraper_id not in SCRAPERS:
        return jsonify({'status': 'erro', 'mensagem': 'Scraper não encontrado'})
    
    arquivo_csv = SCRAPERS[scraper_id]['arquivo_csv']
    produtos_anteriores = SCRAPERS[scraper_id]['produtos_anteriores']
    
    # Parâmetros de paginação e busca
    pagina = int(request.args.get('pagina', 1))
    itens_por_pagina = int(request.args.get('itens_por_pagina', 10))
    termo_busca = request.args.get('busca', '').lower()
    
    try:
        produtos = []
        total_produtos = 0
        produtos_filtrados = 0
        
        if os.path.exists(arquivo_csv):
            with open(arquivo_csv, 'r', encoding='utf-8') as f:
                leitor = csv.DictReader(f)
                
                # Filtra e pagina os resultados
                todos_produtos = list(leitor)
                total_produtos = len(todos_produtos)
                
                # Marca produtos novos (não vistos na última execução)
                for produto in todos_produtos:
                    produto_id = gerar_produto_id(produto)
                    if produto_id not in produtos_anteriores:
                        produto['is_new'] = True
                    else:
                        produto['is_new'] = False
                
                # Aplica filtro de busca se necessário
                if termo_busca:
                    produtos_filtrados = [p for p in todos_produtos if 
                                        termo_busca in p.get('titulo', '').lower() or 
                                        termo_busca in p.get('artista', '').lower() or
                                        termo_busca in p.get('categoria', '').lower()]
                else:
                    produtos_filtrados = todos_produtos
                
                # Calcula o total de páginas
                total_itens = len(produtos_filtrados)
                total_paginas = (total_itens + itens_por_pagina - 1) // itens_por_pagina
                
                # Pega apenas os itens da página atual
                inicio = (pagina - 1) * itens_por_pagina
                fim = min(inicio + itens_por_pagina, total_itens)
                produtos = produtos_filtrados[inicio:fim]
        
        return jsonify({
            'status': 'sucesso',
            'produtos': produtos,
            'total_itens': len(produtos_filtrados),
            'total_original': total_produtos,
            'pagina_atual': pagina,
            'total_paginas': total_paginas if 'total_paginas' in locals() else 1
        })
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro ao ler produtos: {str(e)}'
        })

# Rota para obter os logs de execução
@app.route('/logs/<scraper_id>')
def obter_logs(scraper_id):
    if scraper_id not in SCRAPERS:
        return jsonify({'status': 'erro', 'mensagem': 'Scraper não encontrado'})
    
    # Procura os arquivos de log para este scraper
    logs = []
    log_pattern = f"scraper_{scraper_id}_*.log"
    
    # Encontra todos os arquivos de log que correspondem ao padrão
    for filename in os.listdir('.'):
        if re.match(f"scraper_{scraper_id}_[0-9]+_[0-9]+.log", filename):
            # Obtém a data de modificação do arquivo
            mod_time = os.path.getmtime(filename)
            logs.append({
                'arquivo': filename,
                'data': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S'),
                'tamanho': os.path.getsize(filename)
            })
    
    # Ordena os logs do mais recente para o mais antigo
    logs.sort(key=lambda x: x['data'], reverse=True)
    
    return jsonify({
        'status': 'sucesso',
        'logs': logs
    })

# Rota para visualizar o conteúdo de um arquivo de log
@app.route('/log_content/<filename>')
def log_content(filename):
    if not os.path.exists(filename):
        return jsonify({'status': 'erro', 'mensagem': 'Arquivo de log não encontrado'})
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        return jsonify({
            'status': 'sucesso',
            'conteudo': conteudo
        })
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro ao ler arquivo de log: {str(e)}'
        })

# Rota para download do arquivo CSV
@app.route('/download/<scraper_id>')
def download_csv(scraper_id):
    if scraper_id not in SCRAPERS:
        return jsonify({'status': 'erro', 'mensagem': 'Scraper não encontrado'})
    
    arquivo_csv = SCRAPERS[scraper_id]['arquivo_csv']
    
    if not os.path.exists(arquivo_csv):
        return jsonify({'status': 'erro', 'mensagem': 'Arquivo CSV não encontrado'})
    
    return send_file(arquivo_csv, 
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'produtos_{scraper_id}_{datetime.now().strftime("%Y%m%d")}.csv')

# Rota para obter estatísticas dos produtos
@app.route('/estatisticas/<scraper_id>')
def obter_estatisticas(scraper_id):
    if scraper_id not in SCRAPERS:
        return jsonify({'status': 'erro', 'mensagem': 'Scraper não encontrado'})
    
    arquivo_csv = SCRAPERS[scraper_id]['arquivo_csv']
    
    try:
        estatisticas = {
            'total_produtos': 0,
            'preco_medio': 0,
            'preco_minimo': None,
            'preco_maximo': None,
            'categorias': {},
            'artistas': {},
        }
        
        if os.path.exists(arquivo_csv):
            with open(arquivo_csv, 'r', encoding='utf-8') as f:
                leitor = csv.DictReader(f)
                produtos = list(leitor)
                
                estatisticas['total_produtos'] = len(produtos)
                
                if produtos:
                    # Processa preços (converte para float, removendo símbolos de moeda)
                    precos = []
                    for produto in produtos:
                        if 'preco' in produto and produto['preco']:
                            # Remove caracteres não numéricos e converte para float
                            preco_str = re.sub(r'[^\d.,]', '', produto['preco']).replace(',', '.')
                            try:
                                preco = float(preco_str)
                                precos.append(preco)
                            except ValueError:
                                pass
                    
                    if precos:
                        estatisticas['preco_medio'] = round(sum(precos) / len(precos), 2)
                        estatisticas['preco_minimo'] = round(min(precos), 2)
                        estatisticas['preco_maximo'] = round(max(precos), 2)
                    
                    # Contagem de categorias
                    for produto in produtos:
                        if 'categoria' in produto and produto['categoria']:
                            categoria = produto['categoria'].strip()
                            if categoria in estatisticas['categorias']:
                                estatisticas['categorias'][categoria] += 1
                            else:
                                estatisticas['categorias'][categoria] = 1
                    
                    # Contagem de artistas (se disponível)
                    for produto in produtos:
                        if 'artista' in produto and produto['artista']:
                            artista = produto['artista'].strip()
                            if artista in estatisticas['artistas']:
                                estatisticas['artistas'][artista] += 1
                            else:
                                estatisticas['artistas'][artista] = 1
                    
                    # Pega os 10 artistas mais comuns
                    artistas_ordenados = sorted(estatisticas['artistas'].items(), 
                                              key=lambda x: x[1], reverse=True)[:10]
                    estatisticas['artistas'] = dict(artistas_ordenados)
        
        return jsonify({
            'status': 'sucesso',
            'estatisticas': estatisticas
        })
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro ao calcular estatísticas: {str(e)}'
        })

def atualizar_informacoes_scraper(scraper_id):
    """Atualiza informações do scraper, como total de produtos"""
    arquivo_csv = SCRAPERS[scraper_id]['arquivo_csv']
    
    # Verifica status do processo
    if SCRAPERS[scraper_id]['processo']:
        # Se o processo ainda está rodando
        if SCRAPERS[scraper_id]['processo'].poll() is None:
            SCRAPERS[scraper_id]['status'] = 'rodando'
        else:
            # Se o processo terminou
            if SCRAPERS[scraper_id]['processo'].returncode == 0:
                SCRAPERS[scraper_id]['status'] = 'concluído'
            else:
                SCRAPERS[scraper_id]['status'] = 'erro'
    
    # Conta total de produtos no arquivo CSV
    if os.path.exists(arquivo_csv):
        try:
            with open(arquivo_csv, 'r', encoding='utf-8') as f:
                # Subtrai 1 para não contar o cabeçalho
                SCRAPERS[scraper_id]['total_produtos'] = sum(1 for _ in f) - 1
        except:
            pass

if __name__ == '__main__':
    # IMPORTANTE: Não altere esta porta (5002) pois é a que está mapeada no Docker 
    # e configurada no servidor. Alterar a porta causará problemas de acesso.
    # O mapeamento no Docker é: 0.0.0.0:5002->5002/tcp, :::5002->5002/tcp
    app.run(host='0.0.0.0', port=5002, debug=False)