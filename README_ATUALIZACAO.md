# Atualização do Scraper da Locomotiva Discos

## Problema Resolvido

O scraper da Locomotiva Discos estava com problemas para capturar novos produtos adicionados ao site. Isso ocorria porque o sistema estava verificando se o produto já existia no arquivo CSV e ignorando produtos com URLs ou títulos semelhantes, mesmo que fossem novos.

## Soluções Implementadas

1. **Modificação nos scripts de scraping**:
   - Adicionado um novo parâmetro `ignorar_produtos_existentes` que permite forçar a recaptura de todos os produtos
   - Implementados headers para evitar cache na resposta do servidor
   - Adicionado timestamp às URLs para garantir que cada requisição seja única

2. **Novo script de atualização completa**:
   - Criado o script `atualizar_produtos_locomotiva.py` que executa em sequência os scrapers da Locomotiva (CDs usados e CDs novos)
   - O script faz backup dos arquivos CSV existentes antes de iniciar a atualização
   - Implementado um sistema de logs para rastrear a execução

3. **Atualização do Dashboard**:
   - Adicionado um novo botão "Atualizar Locomotiva Discos (Completo)" que executa o script de atualização completa
   - Implementada uma nova rota no servidor Flask para executar o script de atualização
   - Adicionada lógica no front-end para monitorar o status da atualização

## Como Usar a Nova Funcionalidade

### Método 1: Pelo Dashboard

1. Acesse o dashboard web (por padrão em http://localhost:5000)
2. Na aba "Controle", localize o card "Atualização Completa" 
3. Clique no botão "Atualizar Locomotiva Discos (Completo)"
4. Aguarde a conclusão da operação, que será indicada pela atualização do status dos scrapers da Locomotiva

### Método 2: Via Linha de Comando

1. Execute o script diretamente pela linha de comando:
   ```
   python atualizar_produtos_locomotiva.py
   ```

2. Acompanhe o progresso pelo terminal e pelos logs gerados na pasta `logs/`

## Configurações Adicionais

Os scrapers da Locomotiva agora estão configurados para:

- Ignorar a verificação de produtos existentes (sempre reindexar tudo)
- Adicionar parâmetros anti-cache às URLs
- Usar headers que evitam cache do servidor
- Aumentar o número máximo de páginas verificadas para 340

## Arquivos Modificados

- `extrair_cds_locomotiva.py` - Script para CDs usados
- `extrair_cds_locomotiva_novos.py` - Script para CDs novos
- `dashboard.py` - Adicionada rota para atualização completa
- `templates/dashboard.html` - Adicionado botão de atualização
- `static/js/dashboard.js` - Adicionada lógica para o botão

## Arquivos Novos

- `atualizar_produtos_locomotiva.py` - Script de atualização completa
- `README_ATUALIZACAO.md` - Este arquivo de documentação

## Próximos Passos Recomendados

1. Considerar implementar um sistema de agendamento para executar a atualização completa periodicamente
2. Adicionar notificações por email quando novos produtos forem encontrados
3. Implementar um sistema de cache mais robusto para evitar requisições desnecessárias 