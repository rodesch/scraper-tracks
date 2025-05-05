# Atualização Geral dos Scrapers de CDs

## Problema Resolvido

Os scrapers estavam com dificuldades para capturar novos produtos adicionados aos sites. Isso ocorria porque o sistema verificava se produtos já existiam no arquivo CSV e ignorava produtos com URLs ou títulos semelhantes, mesmo que fossem novos.

## Soluções Implementadas

### 1. Modificações nos Scrapers Individuais

Foram feitas as seguintes modificações nos scrapers para garantir a captura de todos os produtos:

- **Parâmetro `ignorar_produtos_existentes`**: Adicionado a todos os scrapers para permitir forçar a recaptura de todos os produtos
- **Headers Anti-Cache**: Implementados headers específicos para evitar cache na resposta do servidor
- **Timestamp nas URLs**: Adicionado parâmetro de timestamp às URLs para garantir que cada requisição seja única

Scrapers atualizados:
- `extrair_cds_locomotiva.py` (CDs Usados)
- `extrair_cds_locomotiva_novos.py` (CDs Novos)
- `extrair_cds_tracks.py` (Tracks Rio)
- `extrair_cds_supernova.py` (Supernova Discos)

### 2. Scripts de Atualização Unificados

Foram criados dois novos scripts para facilitar a atualização dos produtos:

- **`atualizar_produtos_locomotiva.py`**: Atualiza apenas os produtos da Locomotiva Discos (CDs novos e usados)
- **`atualizar_todos_scrapers.py`**: Atualiza todos os scrapers em sequência

Ambos os scripts realizam backup dos arquivos CSV existentes antes de iniciar a atualização, garantindo segurança dos dados.

### 3. Atualização do Dashboard

O dashboard web foi atualizado com novos botões e funcionalidades:

- **Botão "Atualizar Locomotiva Discos (Completo)"**: Executa apenas os scrapers da Locomotiva
- **Botão "Atualizar Todos os Scrapers"**: Executa todos os scrapers em sequência (operação mais demorada)
- **Monitoramento de Status**: O dashboard atualiza automaticamente o status dos scrapers durante a execução

## Como Usar

### Método 1: Dashboard Web

1. Acesse o dashboard web (geralmente em http://localhost:5002)
2. Na aba "Controle", escolha uma das opções:
   - Para atualizar apenas a Locomotiva: Clique em "Atualizar Locomotiva Discos (Completo)"
   - Para atualizar todas as lojas: Clique em "Atualizar Todos os Scrapers"
3. Aguarde a conclusão da operação

### Método 2: Linha de Comando

Para atualizar apenas a Locomotiva:
```bash
python3 atualizar_produtos_locomotiva.py
```

Para atualizar todos os scrapers:
```bash
python3 atualizar_todos_scrapers.py
```

## Funcionamento do Processo de Atualização

1. **Backup**: Antes de iniciar a atualização, é feito backup de todos os arquivos CSV existentes
2. **Execução Sequencial**: Os scrapers são executados um após o outro
3. **Relatório**: Ao final, é gerado um relatório de execução com status de cada scraper
4. **Log**: Todo o processo é registrado em arquivos de log na pasta `logs/`

## Arquivos Adicionados

- `atualizar_produtos_locomotiva.py` - Script para atualizar apenas a Locomotiva
- `atualizar_todos_scrapers.py` - Script para atualizar todos os scrapers
- `README_ATUALIZACAO.md` - Documentação da atualização da Locomotiva
- `README_ATUALIZACAO_GERAL.md` - Esta documentação

## Arquivos Modificados

- `extrair_cds_tracks.py` - Adicionado parâmetro para ignorar produtos existentes
- `extrair_cds_supernova.py` - Adicionado parâmetro para ignorar produtos existentes
- `dashboard.py` - Adicionadas rotas para as novas funcionalidades
- `templates/dashboard.html` - Adicionados botões para as novas funcionalidades
- `static/js/dashboard.js` - Adicionada lógica para os novos botões

## Próximos Passos Recomendados

1. **Implementar sistema de agendamento**: Configurar execução periódica dos scripts de atualização
2. **Notificações**: Adicionar sistema de notificação por email quando novos produtos forem encontrados
3. **Otimização de desempenho**: Refinar os scrapers para serem mais eficientes e rápidos
4. **Monitoramento**: Implementar um sistema de monitoramento mais detalhado para acompanhar a execução dos scrapers 