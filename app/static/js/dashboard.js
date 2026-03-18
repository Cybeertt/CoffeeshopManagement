let charts = {};

function formatarData(date) {
    return date.toISOString().split('T')[0];
}

// Definir data máxima nos inputs e valores padrão
const hoje = new Date();
const dataHojeStr = formatarData(hoje);

document.getElementById('data_inicio').max = dataHojeStr;
document.getElementById('data_fim').max = dataHojeStr;

// Opcional: Definir data_inicio como 7 dias atrás e data_fim como hoje por padrão
const seteDiasAtras = new Date();
seteDiasAtras.setDate(hoje.getDate() - 7);
document.getElementById('data_inicio').value = formatarData(seteDiasAtras);
document.getElementById('data_fim').value = dataHojeStr;

// Função para definir a data mínima da data_fim
function setMinDataFim() {
    const dataInicioInput = document.getElementById('data_inicio');
    const dataFimInput = document.getElementById('data_fim');
    dataFimInput.min = dataInicioInput.value;
    // Se a data_fim atual for menor que a nova data_inicio, ajusta a data_fim
    if (dataFimInput.value < dataInicioInput.value) {
        dataFimInput.value = dataInicioInput.value;
    }
}

// Chamar a função ao carregar a página para definir o estado inicial
setMinDataFim();

async function fetchAPI(endpoint) {
    const dataInicio = document.getElementById('data_inicio').value;
    const dataFim = document.getElementById('data_fim').value;
    
    let url = endpoint;
    const params = new URLSearchParams();
    if (dataInicio) params.append('data_inicio', dataInicio + 'T00:00:00');
    if (dataFim) params.append('data_fim', dataFim + 'T23:59:59');
    
    if (params.toString()) {
        url += (url.includes('?') ? '&' : '?') + params.toString();
    }

    const res = await fetch(url);
    return res.json();
}

async function downloadExcel() {
    const dataInicio = document.getElementById('data_inicio').value;
    const dataFim = document.getElementById('data_fim').value;
    let url = '/relatorio/excel_completo';
    const params = new URLSearchParams();
    if (dataInicio) params.append('data_inicio', dataInicio + 'T00:00:00');
    if (dataFim) params.append('data_fim', dataFim + 'T23:59:59');
    if (params.toString()) url += '?' + params.toString();
    
    window.location.href = url;
}

async function atualizarDashboard() {
    try {
        const selectedStore = document.getElementById('loja_selecionada').value;
        
        // 1. Comparativo de Lojas (Mantém global para contexto)
        const comp = await fetchAPI('/relatorio/comparativo_lojas');
        if (comp.comparativo) {
            renderLojasChart(comp.comparativo);
            
            // Update global stats from comparative
            const totalFat = comp.comparativo.reduce((acc, l) => acc + l.faturacao_total, 0);
            const avgTicket = comp.comparativo.reduce((acc, l) => acc + l.ticket_medio, 0) / comp.comparativo.length;
            const totalQ = comp.comparativo.reduce((acc, l) => acc + l.total_quebras, 0);
            
            document.getElementById('faturacao-total').innerText = `€ ${totalFat.toFixed(2)}`;
            document.getElementById('ticket-medio').innerText = `€ ${avgTicket.toFixed(2)}`;
            document.getElementById('total-quebras').innerText = totalQ;
        }

        // 2. Vendas por Horário (Filtrado por loja selecionada)
        const horarios = await fetchAPI(`/relatorio/vendas_por_horario/${selectedStore}`);
        if (horarios.vendas_por_hora) renderHorariosChart(horarios.vendas_por_hora);

        // 3. Top Produtos (Filtrado por loja selecionada)
        const produtos = await fetchAPI(`/relatorio/produtos_mais_vendidos/${selectedStore}`);
        if (produtos.produtos_mais_vendidos) renderProdutosChart(produtos.produtos_mais_vendidos);

        // 4. Rentabilidade (Filtrado por loja selecionada)
        const rentabilidade = await fetchAPI(`/relatorio/rentabilidade/${selectedStore}`);
        if (rentabilidade.rentabilidade) {
            renderRentabilidadeChart(rentabilidade.rentabilidade);
            const avgRacio = rentabilidade.rentabilidade.reduce((acc, r) => acc + r.racio_quebra_venda, 0) / (rentabilidade.rentabilidade.length || 1);
            document.getElementById('racio-desperdicio').innerText = `${avgRacio.toFixed(1)}%`;
        }

    } catch (e) {
        console.error("Erro ao atualizar dashboard:", e);
    }
}

function renderLojasChart(data) {
    updateChart('chartLojas', {
        type: 'bar',
        data: {
            labels: data.map(l => l.loja),
            datasets: [{
                label: 'Faturação (€)',
                data: data.map(l => l.faturacao_total),
                backgroundColor: '#3b82f6'
            }]
        }
    });
}

function renderHorariosChart(data) {
    updateChart('chartHorarios', {
        type: 'line',
        data: {
            labels: data.map(h => `${h.hora}h`),
            datasets: [{
                label: 'Vendas por Hora',
                data: data.map(h => h.quantidade_vendas),
                borderColor: '#10b981',
                tension: 0.3,
                fill: true,
                backgroundColor: 'rgba(16, 185, 129, 0.1)'
            }]
        }
    });
}

function renderProdutosChart(data) {
    updateChart('chartProdutos', {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
            }]
        }
    });
}

function renderRentabilidadeChart(data) {
    updateChart('chartRentabilidade', {
        type: 'bar',
        data: {
            labels: data.map(r => r.produto),
            datasets: [
                { label: 'Vendas', data: data.map(r => r.quantidade_vendida), backgroundColor: '#10b981' },
                { label: 'Quebras', data: data.map(r => r.quantidade_quebras), backgroundColor: '#ef4444' }
            ]
        }
    });
}

function updateChart(id, config) {
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(document.getElementById(id), config);
}

// Inicializar
atualizarDashboard();