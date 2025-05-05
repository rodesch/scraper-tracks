/**
 * Dashboard para Scrapers de CDs
 * Arquivo JavaScript principal
 */

$(document).ready(function() {
    // Configuração de variáveis
    let loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    let scrapeIntervalId = null;
    let currentScraperId = null;
    let currentPagina = 1;
    let itensPorPagina = 10;
    let termoBusca = '';
    
    // Garantir que não haja elementos duplicados
    const checkDuplicateElementsAndClean = function() {
        const scraperIds = [];
        const duplicates = [];
        
        // Encontra todos os elementos de scrapers
        $('#scrapers-container .card-header h5').each(function() {
            const title = $(this).text().trim();
            if (scraperIds.includes(title)) {
                duplicates.push($(this).closest('.col-md-4'));
            } else {
                scraperIds.push(title);
            }
        });
        
        // Remove elementos duplicados
        duplicates.forEach(function(element) {
            element.remove();
        });
        
        if (duplicates.length > 0) {
            console.log(`Removidos ${duplicates.length} elementos duplicados de scrapers.`);
        }
    };
    
    // Executa a verificação quando a página carrega
    checkDuplicateElementsAndClean();
    
    // Inicializa a página atualizando o status de todos os scrapers
    atualizarTodosStatus();
    
    // Evento para botão de atualização completa da Locomotiva Discos
    $('#btn-atualizar-locomotiva').on('click', function() {
        // Mostra o modal de loading
        $('#loading-message').text('Iniciando atualização completa da Locomotiva Discos...');
        loadingModal.show();
        
        // Faz a requisição para iniciar a atualização completa
        $.ajax({
            url: '/atualizar_locomotiva',
            method: 'POST',
            success: function(resposta) {
                if (resposta.status === 'sucesso') {
                    // Configura um intervalo para atualizar o status dos scrapers da Locomotiva
                    if (scrapeIntervalId) {
                        clearInterval(scrapeIntervalId);
                    }
                    
                    scrapeIntervalId = setInterval(function() {
                        verificarStatus('locomotiva_usados');
                        verificarStatus('locomotiva_novos');
                    }, 3000);
                    
                    // Oculta o modal após 2 segundos
                    setTimeout(function() {
                        loadingModal.hide();
                        // Mostra uma mensagem de sucesso
                        alert('Atualização completa da Locomotiva Discos iniciada com sucesso!');
                    }, 2000);
                } else {
                    // Em caso de erro, mostra a mensagem e esconde o modal
                    alert(`Erro: ${resposta.mensagem}`);
                    loadingModal.hide();
                }
            },
            error: function() {
                alert('Erro ao iniciar a atualização completa. Tente novamente.');
                loadingModal.hide();
            }
        });
    });
    
    // Evento para botão de atualização completa de todos os scrapers
    $('#btn-atualizar-todos').on('click', function() {
        // Confirmação para evitar inicialização acidental
        if (!confirm('Esta operação irá atualizar TODOS os scrapers e pode levar bastante tempo. Deseja continuar?')) {
            return;
        }
        
        // Mostra o modal de loading
        $('#loading-message').text('Iniciando atualização completa de todos os scrapers...');
        loadingModal.show();
        
        // Faz a requisição para iniciar a atualização completa
        $.ajax({
            url: '/atualizar_todos',
            method: 'POST',
            success: function(resposta) {
                if (resposta.status === 'sucesso') {
                    // Configura um intervalo para atualizar o status de todos os scrapers
                    if (scrapeIntervalId) {
                        clearInterval(scrapeIntervalId);
                    }
                    
                    scrapeIntervalId = setInterval(function() {
                        atualizarTodosStatus();
                    }, 5000);
                    
                    // Oculta o modal após 2 segundos
                    setTimeout(function() {
                        loadingModal.hide();
                        // Mostra uma mensagem de sucesso
                        alert('Atualização completa de todos os scrapers iniciada com sucesso! Esse processo pode levar bastante tempo para ser concluído.');
                    }, 2000);
                } else {
                    // Em caso de erro, mostra a mensagem e esconde o modal
                    alert(`Erro: ${resposta.mensagem}`);
                    loadingModal.hide();
                }
            },
            error: function() {
                alert('Erro ao iniciar a atualização completa. Tente novamente.');
                loadingModal.hide();
            }
        });
    });
    
    // Evento para botões de iniciar scrapers
    $('.btn-iniciar').on('click', function() {
        const scraperId = $(this).data('id');
        currentScraperId = scraperId;
        
        // Obtém o modo selecionado do dropdown
        const modoSelecionado = $(`#modo-${scraperId}`).val();
        
        // Mostra o modal de loading
        $('#loading-message').text(`Iniciando scraper ${scraperId} no modo ${modoSelecionado}...`);
        loadingModal.show();
        
        // Faz a requisição para iniciar o scraper
        $.ajax({
            url: `/iniciar/${scraperId}`,
            method: 'POST',
            data: { modo: modoSelecionado },
            success: function(resposta) {
                if (resposta.status === 'sucesso' || resposta.status === 'aviso') {
                    // Inicia o intervalo para verificar o status periodicamente
                    if (scrapeIntervalId) {
                        clearInterval(scrapeIntervalId);
                    }
                    
                    scrapeIntervalId = setInterval(function() {
                        verificarStatus(scraperId);
                    }, 2000);
                    
                    // Oculta o modal após 2 segundos
                    setTimeout(function() {
                        loadingModal.hide();
                    }, 2000);
                } else {
                    // Em caso de erro, mostra a mensagem e esconde o modal
                    alert(`Erro: ${resposta.mensagem}`);
                    loadingModal.hide();
                }
            },
            error: function() {
                alert('Erro ao iniciar o scraper. Tente novamente.');
                loadingModal.hide();
            }
        });
    });
    
    // Evento para botões de ver produtos
    $('.btn-produtos').on('click', function() {
        const scraperId = $(this).data('id');
        // Muda para a aba de produtos
        $('#produtos-tab').tab('show');
        // Carrega os produtos
        carregarProdutos(scraperId, 1);
    });
    
    // Configuração dos selects nas abas de logs e estatísticas
    $('#select-scraper-log').on('change', function() {
        const scraperId = $(this).val();
        if (scraperId) {
            carregarLogs(scraperId);
        }
    });
    
    $('#select-scraper-stats').on('change', function() {
        const scraperId = $(this).val();
        if (scraperId) {
            carregarEstatisticas(scraperId);
        }
    });
    
    // Evento para o botão de busca
    $('#btn-buscar').on('click', function() {
        const termoBusca = $('#busca-produtos').val().trim();
        if (currentScraperId) {
            carregarProdutos(currentScraperId, 1, termoBusca);
        }
    });
    
    // Evento para buscar ao pressionar Enter no campo de busca
    $('#busca-produtos').on('keypress', function(e) {
        if (e.which === 13) { // Código da tecla Enter
            const termoBusca = $(this).val().trim();
            if (currentScraperId) {
                carregarProdutos(currentScraperId, 1, termoBusca);
            }
        }
    });
    
    // Função para verificar o status de um scraper
    function verificarStatus(scraperId) {
        $.ajax({
            url: `/status/${scraperId}`,
            method: 'GET',
            success: function(resposta) {
                // Atualiza as informações na interface
                const statusElement = $(`#status-${scraperId}`);
                const ultimaElement = $(`#ultima-${scraperId}`);
                const totalElement = $(`#total-${scraperId}`);
                
                // Remove classes antigas e adiciona a nova
                statusElement.removeClass('bg-secondary bg-primary bg-success bg-danger');
                
                // Atualiza o status com a classe correta
                if (resposta.status === 'rodando') {
                    statusElement.addClass('bg-primary');
                    // Atualiza o botão de iniciar para mostrar que está em execução
                    $(`button.btn-iniciar[data-id="${scraperId}"]`).parent().html(`
                        <button class="btn btn-warning" disabled>
                            <i class="fas fa-spinner fa-spin"></i> Executando...
                        </button>
                    `);
                } else if (resposta.status === 'concluído') {
                    statusElement.addClass('bg-success');
                    // Restaura o botão de iniciar
                    $(`button.btn-warning[disabled]`).parent().html(`
                        <button class="btn btn-primary btn-iniciar" data-id="${scraperId}">
                            <i class="fas fa-play"></i> Iniciar Scraper
                        </button>
                    `);
                    // Reativa o evento de clique
                    $(`button.btn-iniciar[data-id="${scraperId}"]`).on('click', function() {
                        const id = $(this).data('id');
                        $('#loading-message').text(`Iniciando scraper ${id}...`);
                        loadingModal.show();
                        $.ajax({
                            url: `/iniciar/${id}`,
                            method: 'POST',
                            success: function(resp) {
                                if (resp.status === 'sucesso' || resp.status === 'aviso') {
                                    if (scrapeIntervalId) {
                                        clearInterval(scrapeIntervalId);
                                    }
                                    scrapeIntervalId = setInterval(function() {
                                        verificarStatus(id);
                                    }, 2000);
                                    setTimeout(function() {
                                        loadingModal.hide();
                                    }, 2000);
                                } else {
                                    alert(`Erro: ${resp.mensagem}`);
                                    loadingModal.hide();
                                }
                            },
                            error: function() {
                                alert('Erro ao iniciar o scraper. Tente novamente.');
                                loadingModal.hide();
                            }
                        });
                    });
                    // Interrompe o intervalo de verificação quando concluído
                    if (scrapeIntervalId) {
                        clearInterval(scrapeIntervalId);
                        scrapeIntervalId = null;
                    }
                } else if (resposta.status === 'erro') {
                    statusElement.addClass('bg-danger');
                    // Restaura o botão de iniciar
                    $(`button.btn-warning[disabled]`).parent().html(`
                        <button class="btn btn-primary btn-iniciar" data-id="${scraperId}">
                            <i class="fas fa-play"></i> Iniciar Scraper
                        </button>
                    `);
                    // Reativa o evento de clique
                    $(`button.btn-iniciar[data-id="${scraperId}"]`).on('click', function() {
                        const id = $(this).data('id');
                        $('#loading-message').text(`Iniciando scraper ${id}...`);
                        loadingModal.show();
                        $.ajax({
                            url: `/iniciar/${id}`,
                            method: 'POST',
                            success: function(resp) {
                                if (resp.status === 'sucesso' || resp.status === 'aviso') {
                                    if (scrapeIntervalId) {
                                        clearInterval(scrapeIntervalId);
                                    }
                                    scrapeIntervalId = setInterval(function() {
                                        verificarStatus(id);
                                    }, 2000);
                                    setTimeout(function() {
                                        loadingModal.hide();
                                    }, 2000);
                                } else {
                                    alert(`Erro: ${resp.mensagem}`);
                                    loadingModal.hide();
                                }
                            },
                            error: function() {
                                alert('Erro ao iniciar o scraper. Tente novamente.');
                                loadingModal.hide();
                            }
                        });
                    });
                    // Interrompe o intervalo de verificação em caso de erro
                    if (scrapeIntervalId) {
                        clearInterval(scrapeIntervalId);
                        scrapeIntervalId = null;
                    }
                } else {
                    statusElement.addClass('bg-secondary');
                }
                
                // Atualiza o texto
                statusElement.text(resposta.status);
                ultimaElement.text(resposta.ultima_execucao || 'Nunca executado');
                totalElement.text(resposta.total_produtos);
                
                // Se o scraper atual que está sendo monitorado terminar, recarrega os produtos
                if ((resposta.status === 'concluído' || resposta.status === 'erro') && scraperId === currentScraperId) {
                    if ($('#produtos-tab').hasClass('active')) {
                        carregarProdutos(scraperId, currentPagina);
                    }
                }
            }
        });
    }
    
    // Função para atualizar o status de todos os scrapers
    function atualizarTodosStatus() {
        $('.btn-iniciar').each(function() {
            const scraperId = $(this).data('id');
            if (scraperId) {
                verificarStatus(scraperId);
            }
        });
    }
    
    // Função para carregar produtos
    function carregarProdutos(scraperId, pagina = 1, termoBusca = '') {
        // Armazena estado atual para paginação e busca
        window.currentScraperId = scraperId;
        window.currentPagina = pagina;
        window.currentTermoBusca = termoBusca;
        
        // Define padrão de itens por página
        const itensPorPagina = 10;
        
        // Atualiza título
        $('#visualizacao-titulo').text(`Visualização de Produtos - ${scraperId.charAt(0).toUpperCase() + scraperId.slice(1).replace('_', ' ')}`);
        
        // Seleciona a aba de produtos
        $('#produtos-tab').tab('show');
        
        // Atualiza campo de busca
        $('#busca-produtos').val(termoBusca);
        
        // Limpa a tabela e mostra loading
        $('#tabela-produtos tbody').html(`
            <tr>
                <td colspan="5" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p>Carregando produtos...</p>
                </td>
            </tr>
        `);
        
        // Limpa a paginação
        $('.pagination-container').empty();
        
        // Faz a requisição para obter os produtos
        $.ajax({
            url: `/produtos/${scraperId}`,
            method: 'GET',
            data: {
                pagina: pagina,
                itens_por_pagina: itensPorPagina,
                busca: termoBusca
            },
            success: function(resposta) {
                if (resposta.status === 'sucesso') {
                    if (resposta.produtos.length > 0) {
                        // Limpa a tabela
                        $('#tabela-produtos tbody').empty();
                        
                        // Conta quantos produtos novos existem
                        const novos_produtos = resposta.produtos.filter(p => p.is_new).length;
                        
                        // Adiciona cabeçalho com contador de novos produtos se houver
                        if (novos_produtos > 0) {
                            $('#tabela-produtos tbody').append(`
                                <tr class="table-info">
                                    <td colspan="5" class="text-center">
                                        <strong>${novos_produtos} produto(s) novo(s) encontrado(s) desde a última execução!</strong>
                                    </td>
                                </tr>
                            `);
                        }
                        
                        // Adiciona cada produto à tabela
                        resposta.produtos.forEach(function(produto) {
                            // Adiciona indicador "NEW" se o produto for novo
                            const newTag = produto.is_new ? 
                                `<span class="badge bg-danger ms-2">NEW</span>` : '';
                            
                            $('#tabela-produtos tbody').append(`
                                <tr>
                                    <td>${produto.titulo || '-'} ${newTag}</td>
                                    <td>${produto.artista || '-'}</td>
                                    <td>${produto.preco || '-'}</td>
                                    <td>${produto.categoria || '-'}</td>
                                    <td>
                                        ${produto.url ? `<a href="${produto.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-external-link-alt"></i> Ver
                                        </a>` : '-'}
                                    </td>
                                </tr>
                            `);
                        });
                        
                        // Cria a paginação
                        if (resposta.total_paginas > 1) {
                            criarPaginacao(resposta.pagina_atual, resposta.total_paginas, scraperId);
                        }
                    } else {
                        // Caso não haja produtos
                        $('#tabela-produtos tbody').html(`
                            <tr>
                                <td colspan="5" class="text-center">Nenhum produto encontrado para este scraper</td>
                            </tr>
                        `);
                    }
                } else {
                    // Em caso de erro
                    $('#tabela-produtos tbody').html(`
                        <tr>
                            <td colspan="5" class="text-center text-danger">
                                Erro ao carregar produtos: ${resposta.mensagem}
                            </td>
                        </tr>
                    `);
                }
            },
            error: function() {
                // Em caso de erro na requisição
                $('#tabela-produtos tbody').html(`
                    <tr>
                        <td colspan="5" class="text-center text-danger">
                            Erro ao se comunicar com o servidor. Tente novamente.
                        </td>
                    </tr>
                `);
            }
        });
    }
    
    // Função para criar a paginação
    function criarPaginacao(paginaAtual, totalPaginas, scraperId) {
        const paginationContainer = $('.pagination-container');
        paginationContainer.empty();
        
        const pagination = $('<ul class="pagination"></ul>');
        
        // Botão 'Anterior'
        const prevButton = $(`<li class="page-item ${paginaAtual === 1 ? 'disabled' : ''}">
                               <a class="page-link" href="#" aria-label="Anterior">
                                 <span aria-hidden="true">&laquo;</span>
                               </a>
                             </li>`);
        
        prevButton.click(function(e) {
            e.preventDefault();
            if (paginaAtual > 1) {
                carregarProdutos(scraperId, paginaAtual - 1, window.currentTermoBusca || '');
            }
        });
        
        pagination.append(prevButton);
        
        // Adiciona os números de página
        let startPage = Math.max(1, paginaAtual - 2);
        let endPage = Math.min(totalPaginas, startPage + 4);
        
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageButton = $(`<li class="page-item ${i === paginaAtual ? 'active' : ''}">
                                   <a class="page-link" href="#">${i}</a>
                                 </li>`);
            
            pageButton.click(function(e) {
                e.preventDefault();
                carregarProdutos(scraperId, i, window.currentTermoBusca || '');
            });
            
            pagination.append(pageButton);
        }
        
        // Botão 'Próximo'
        const nextButton = $(`<li class="page-item ${paginaAtual === totalPaginas ? 'disabled' : ''}">
                               <a class="page-link" href="#" aria-label="Próximo">
                                 <span aria-hidden="true">&raquo;</span>
                               </a>
                             </li>`);
        
        nextButton.click(function(e) {
            e.preventDefault();
            if (paginaAtual < totalPaginas) {
                carregarProdutos(scraperId, paginaAtual + 1, window.currentTermoBusca || '');
            }
        });
        
        pagination.append(nextButton);
        paginationContainer.append(pagination);
    }
    
    // Função para carregar logs
    function carregarLogs(scraperId) {
        $('#logs-container').html(`
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p>Carregando logs...</p>
            </div>
        `);
        
        $.ajax({
            url: `/logs/${scraperId}`,
            method: 'GET',
            success: function(resposta) {
                if (resposta.status === 'sucesso') {
                    if (resposta.logs.length > 0) {
                        let conteudo = `<div class="list-group">`;
                        
                        resposta.logs.forEach(function(log) {
                            conteudo += `
                                <a href="#" class="list-group-item list-group-item-action log-item" data-file="${log.arquivo}">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h5 class="mb-1">Log de ${new Date(log.data).toLocaleString()}</h5>
                                        <small>${(log.tamanho / 1024).toFixed(2)} KB</small>
                                    </div>
                                    <p class="mb-1">${log.arquivo}</p>
                                </a>
                            `;
                        });
                        
                        conteudo += `</div>`;
                        $('#logs-container').html(conteudo);
                        
                        // Adiciona evento para visualizar o conteúdo do log
                        $('.log-item').on('click', function(e) {
                            e.preventDefault();
                            const filename = $(this).data('file');
                            
                            $('#logs-container').html(`
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Carregando...</span>
                                    </div>
                                    <p>Carregando conteúdo do log...</p>
                                </div>
                            `);
                            
                            $.ajax({
                                url: `/log_content/${filename}`,
                                method: 'GET',
                                success: function(respostaLog) {
                                    if (respostaLog.status === 'sucesso') {
                                        $('#logs-container').html(`
                                            <div class="mb-3">
                                                <button class="btn btn-outline-secondary btn-voltar-logs" data-id="${scraperId}">
                                                    <i class="fas fa-arrow-left"></i> Voltar
                                                </button>
                                            </div>
                                            <div class="log-content">
                                                <pre>${respostaLog.conteudo}</pre>
                                            </div>
                                        `);
                                        
                                        // Adiciona evento para botão de voltar
                                        $('.btn-voltar-logs').on('click', function() {
                                            const id = $(this).data('id');
                                            carregarLogs(id);
                                        });
                                    } else {
                                        $('#logs-container').html(`
                                            <div class="alert alert-danger">
                                                Erro ao carregar conteúdo do log: ${respostaLog.mensagem}
                                            </div>
                                            <button class="btn btn-outline-secondary btn-voltar-logs" data-id="${scraperId}">
                                                <i class="fas fa-arrow-left"></i> Voltar
                                            </button>
                                        `);
                                        
                                        // Adiciona evento para botão de voltar
                                        $('.btn-voltar-logs').on('click', function() {
                                            const id = $(this).data('id');
                                            carregarLogs(id);
                                        });
                                    }
                                },
                                error: function() {
                                    $('#logs-container').html(`
                                        <div class="alert alert-danger">
                                            Erro ao se comunicar com o servidor.
                                        </div>
                                        <button class="btn btn-outline-secondary btn-voltar-logs" data-id="${scraperId}">
                                            <i class="fas fa-arrow-left"></i> Voltar
                                        </button>
                                    `);
                                    
                                    // Adiciona evento para botão de voltar
                                    $('.btn-voltar-logs').on('click', function() {
                                        const id = $(this).data('id');
                                        carregarLogs(id);
                                    });
                                }
                            });
                        });
                    } else {
                        $('#logs-container').html(`
                            <div class="alert alert-info">
                                Nenhum log encontrado para este scraper.
                            </div>
                        `);
                    }
                } else {
                    $('#logs-container').html(`
                        <div class="alert alert-danger">
                            Erro ao carregar logs: ${resposta.mensagem}
                        </div>
                    `);
                }
            },
            error: function() {
                $('#logs-container').html(`
                    <div class="alert alert-danger">
                        Erro ao se comunicar com o servidor. Tente novamente.
                    </div>
                `);
            }
        });
    }
    
    // Função para carregar estatísticas
    function carregarEstatisticas(scraperId) {
        $('#stats-container').html(`
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p>Carregando estatísticas...</p>
            </div>
        `);
        
        $.ajax({
            url: `/estatisticas/${scraperId}`,
            method: 'GET',
            success: function(resposta) {
                if (resposta.status === 'sucesso') {
                    const estatisticas = resposta.estatisticas;
                    
                    let conteudo = `<div class="row">`;
                    
                    // Resumo de estatísticas
                    conteudo += `
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header bg-primary text-white">
                                    <h5>Resumo</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Total de Produtos:</strong> ${estatisticas.total_produtos}</p>
                                    <p><strong>Preço Médio:</strong> R$ ${estatisticas.preco_medio}</p>
                                    <p><strong>Preço Mínimo:</strong> R$ ${estatisticas.preco_minimo}</p>
                                    <p><strong>Preço Máximo:</strong> R$ ${estatisticas.preco_maximo}</p>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Categorias
                    if (Object.keys(estatisticas.categorias).length > 0) {
                        conteudo += `
                            <div class="col-md-6">
                                <div class="card mb-3">
                                    <div class="card-header bg-success text-white">
                                        <h5>Categorias</h5>
                                    </div>
                                    <div class="card-body">
                                        <table class="table table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Categoria</th>
                                                    <th>Quantidade</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                        `;
                        
                        // Ordena as categorias por quantidade
                        const categorias = Object.entries(estatisticas.categorias)
                            .sort((a, b) => b[1] - a[1]);
                        
                        categorias.forEach(([categoria, quantidade]) => {
                            conteudo += `
                                <tr>
                                    <td>${categoria}</td>
                                    <td>${quantidade}</td>
                                </tr>
                            `;
                        });
                        
                        conteudo += `
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Artistas mais comuns
                    if (Object.keys(estatisticas.artistas).length > 0) {
                        conteudo += `
                            <div class="col-md-6">
                                <div class="card mb-3">
                                    <div class="card-header bg-info text-white">
                                        <h5>Artistas Mais Comuns</h5>
                                    </div>
                                    <div class="card-body">
                                        <table class="table table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Artista</th>
                                                    <th>Quantidade</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                        `;
                        
                        // Artistas já estão ordenados pelo backend
                        const artistas = Object.entries(estatisticas.artistas);
                        
                        artistas.forEach(([artista, quantidade]) => {
                            conteudo += `
                                <tr>
                                    <td>${artista}</td>
                                    <td>${quantidade}</td>
                                </tr>
                            `;
                        });
                        
                        conteudo += `
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    conteudo += `</div>`;
                    $('#stats-container').html(conteudo);
                } else {
                    $('#stats-container').html(`
                        <div class="alert alert-danger">
                            Erro ao carregar estatísticas: ${resposta.mensagem}
                        </div>
                    `);
                }
            },
            error: function() {
                $('#stats-container').html(`
                    <div class="alert alert-danger">
                        Erro ao se comunicar com o servidor. Tente novamente.
                    </div>
                `);
            }
        });
    }
    
    // Atualiza o status a cada 30 segundos
    setInterval(atualizarTodosStatus, 30000);
}); 