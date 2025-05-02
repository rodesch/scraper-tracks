# Deploy do Scraper Tracks com Docker

Este README contém instruções para fazer o deploy do projeto Scraper Tracks em uma VPS usando Docker.

## Pré-requisitos no ambiente local

Para realizar o deploy, você precisa ter instalado:

1. **sshpass** - para automatizar a autenticação SSH
   ```
   # No macOS via Homebrew
   brew install hudochenkov/sshpass/sshpass
   
   # No Linux (Ubuntu/Debian)
   sudo apt-get install sshpass
   ```

## Estrutura do projeto

O projeto está configurado para rodar em um container Docker, com os seguintes arquivos:

- `Dockerfile` - Define como o container será construído
- `docker-compose.yml` - Configura o serviço e os volumes
- `docker_update.sh` - Script para atualizar caminhos nos arquivos para o ambiente Docker
- `deploy_docker.sh` - Script principal para fazer o deploy na VPS

## Como fazer o deploy

1. Execute o script de deploy:
   ```
   ./deploy_docker.sh
   ```

2. O script irá:
   - Atualizar os caminhos nos arquivos para funcionarem no Docker
   - Compactar os arquivos do projeto
   - Enviar os arquivos para a VPS
   - Instalar o Docker e Docker Compose na VPS (se necessário)
   - Construir e iniciar o container Docker
   - Configurar o firewall para permitir tráfego na porta 5002

3. Após a conclusão, o dashboard estará disponível em:
   ```
   http://212.85.23.16:5002
   ```

## Volumes persistentes

Os seguintes diretórios são mapeados como volumes para persistência dos dados:

- `./data:/app/data` - Armazena os dados CSV
- `./logs:/app/logs` - Armazena os logs de execução
- `./debug:/app/debug` - Armazena arquivos de debug

## Monitoramento

Você pode verificar o status do container usando:

```
ssh root@212.85.23.16 "cd /root/scraper-tracks && docker-compose ps"
```

E ver os logs do container com:

```
ssh root@212.85.23.16 "cd /root/scraper-tracks && docker-compose logs -f"
```

## Reiniciar o serviço

Para reiniciar o serviço, execute:

```
ssh root@212.85.23.16 "cd /root/scraper-tracks && docker-compose restart"
``` 