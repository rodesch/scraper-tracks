# Instruções para Deploy do Scraper Tracks

## Preparação para o Deploy com Docker

Criamos vários arquivos para fazer o deploy do projeto Scraper Tracks em um container Docker na sua VPS. Aqui está um resumo do que foi feito e os passos que você precisa seguir:

### Arquivos Criados:

1. **Dockerfile**: Define a imagem Docker com Python, Chrome e dependências necessárias
2. **docker-compose.yml**: Define o serviço e os volumes para persistência de dados
3. **requirements.txt**: Lista as dependências Python necessárias
4. **docker_update.sh**: Script para atualizar caminhos nos arquivos para o ambiente Docker
5. **deploy_docker.sh**: Script principal que faz todo o processo de deploy

### Passos para Fazer o Deploy:

1. **Instale o sshpass** na sua máquina local:
   ```
   brew install hudochenkov/sshpass/sshpass
   ```

2. **Execute o script de deploy**:
   ```
   ./deploy_docker.sh
   ```

3. **Aguarde a conclusão** do processo de deploy. O script:
   - Atualizará os caminhos nos arquivos
   - Enviará tudo para a VPS
   - Instalará Docker (se necessário)
   - Construirá e iniciará o container

4. **Acesse o dashboard** após a conclusão:
   ```
   http://212.85.23.16:5002
   ```

### Comandos Úteis Após o Deploy:

- **Verificar status do container**:
  ```
  ssh root@212.85.23.16 "cd /root/scraper-tracks && docker-compose ps"
  ```

- **Ver logs do container**:
  ```
  ssh root@212.85.23.16 "cd /root/scraper-tracks && docker-compose logs -f"
  ```

- **Reiniciar o serviço**:
  ```
  ssh root@212.85.23.16 "cd /root/scraper-tracks && docker-compose restart"
  ```

## Vantagens da Abordagem com Docker

1. **Isolamento**: O aplicativo roda em um ambiente isolado
2. **Consistência**: Mesmo ambiente de execução independente do sistema operacional
3. **Persistência**: Os dados são mantidos mesmo se o container for reiniciado
4. **Facilidade de manutenção**: Fácil de atualizar, reiniciar ou reconstruir

Para mais detalhes sobre o deployment com Docker, consulte o arquivo README_DOCKER.md. 