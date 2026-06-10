// ── PRODUTOS E ESCALAS ────────────────────────────────────────────
const PRODUTOS = {
    refrigerante: {
        nome: "Refrigerante",
        icone: "🥤",
        faixas: [
            { de: 25,  ate: 50,  cor: "rgba(255,0,0,0.12)" },
            { de: 18,  ate: 25,  cor: "rgba(255,140,0,0.10)" },
            { de: 10,  ate: 18,  cor: "rgba(255,215,0,0.10)" },
            { de: -10, ate: 10,  cor: "rgba(0,255,85,0.08)" },
        ],
        linhas: [25, 18, 10],
        classCard: (t) => {
            if (t <= 10) return { cls: "card card-ideal",   problema: false };
            if (t <= 18) return { cls: "card card-bom",     problema: true  };
            if (t <= 25) return { cls: "card card-alerta",  problema: true  };
            return             { cls: "card card-critico",  problema: true  };
        },
        tooltip: (v) => {
            if (v <= 10) return "✅ IDEAL";
            if (v <= 18) return "🔵 BOM";
            if (v <= 25) return "⚠️ ATENÇÃO";
            return "🔴 CRÍTICO";
        },
        pontos: (v) => {
            if (v <= 10) return "#00ff55";
            if (v <= 18) return "#ffd700";
            if (v <= 25) return "#ff8c00";
            return "#ff0000";
        }
    },
    acai: {
        nome: "Açaí",
        icone: "🍧",
        faixas: [
            { de: 20,  ate: 50,  cor: "rgba(255,0,0,0.12)" },
            { de: 14,  ate: 20,  cor: "rgba(255,140,0,0.10)" },
            { de: 5,   ate: 14,  cor: "rgba(255,215,0,0.10)" },
            { de: -10, ate: 5,   cor: "rgba(0,255,85,0.08)" },
        ],
        linhas: [20, 14, 5],
        classCard: (t) => {
            if (t <= 5)  return { cls: "card card-ideal",   problema: false };
            if (t <= 14) return { cls: "card card-bom",     problema: true  };
            if (t <= 20) return { cls: "card card-alerta",  problema: true  };
            return              { cls: "card card-critico",  problema: true  };
        },
        tooltip: (v) => {
            if (v <= 5)  return "✅ IDEAL";
            if (v <= 14) return "🔵 BOM";
            if (v <= 20) return "⚠️ ATENÇÃO";
            return "🔴 CRÍTICO";
        },
        pontos: (v) => {
            if (v <= 5)  return "#00ff55";
            if (v <= 14) return "#ffd700";
            if (v <= 20) return "#ff8c00";
            return "#ff0000";
        }
    },
    pizza: {
        nome: "Pizza",
        icone: "🍕",
        faixas: [
            { de: -10, ate: 21,  cor: "rgba(255,0,0,0.12)" },
            { de: 21,  ate: 25,  cor: "rgba(255,140,0,0.10)" },
            { de: 25,  ate: 28,  cor: "rgba(255,215,0,0.10)" },
            { de: 28,  ate: 60,  cor: "rgba(0,255,85,0.08)" },
        ],
        linhas: [21, 25, 28],
        classCard: (t) => {
            if (t >= 30) return { cls: "card card-ideal",   problema: false };
            if (t >= 28) return { cls: "card card-bom",     problema: true  };
            if (t >= 25) return { cls: "card card-alerta",  problema: true  };
            return              { cls: "card card-critico",  problema: true  };
        },
        tooltip: (v) => {
            if (v >= 30) return "✅ IDEAL";
            if (v >= 28) return "🔵 BOM";
            if (v >= 25) return "⚠️ ATENÇÃO";
            return "🔴 CRÍTICO";
        },
        pontos: (v) => {
            if (v >= 30) return "#00ff55";
            if (v >= 28) return "#ffd700";
            if (v >= 25) return "#ff8c00";
            return "#ff0000";
        }
    }
};

let produtoAtual = "refrigerante";

function selecionarProduto(key) {
    produtoAtual = key;
    const p = PRODUTOS[key];

    // Atualiza botões
    document.querySelectorAll(".btn-produto").forEach(b => b.classList.remove("ativo"));
    document.getElementById("btn-" + key).classList.add("ativo");

    // Atualiza título do card
    document.getElementById("label-produto").innerText = p.icone + " " + p.nome;

    // Atualiza faixas do gráfico
    pluginFaixasTemp.faixasAtivas  = p.faixas;
    pluginFaixasTemp.linhasAtivas  = p.linhas;

    grafico.update("active");
}

// ── NAVEGAÇÃO ENTRE PÁGINAS ───────────────────────────────────────
function mostrarPagina(pagina) {
    document.getElementById("pagina-dashboard").style.display = "none";
    document.getElementById("pagina-historico").style.display  = "none";
    document.getElementById("nav-dashboard").classList.remove("nav-ativo");
    document.getElementById("nav-historico").classList.remove("nav-ativo");

    if (pagina === "dashboard") {
        document.getElementById("pagina-dashboard").style.display = "block";
        document.getElementById("nav-dashboard").classList.add("nav-ativo");
        document.getElementById("titulo-pagina").innerText = "Monitoramento em Tempo Real";
    } else {
        document.getElementById("pagina-historico").style.display = "block";
        document.getElementById("nav-historico").classList.add("nav-ativo");
        document.getElementById("titulo-pagina").innerText = "Histórico";
        grafico.update("active");
        graficoLiquido.update("active");
    }
}

// ── PLUGIN: Faixas temperatura ────────────────────────────────────
const pluginFaixasTemp = {
    id: "faixasTemp",
    faixasAtivas: PRODUTOS.refrigerante.faixas,
    linhasAtivas: PRODUTOS.refrigerante.linhas,
    beforeDraw(chart) {
        const { ctx, chartArea, scales } = chart;
        if (!chartArea) return;
        const yScale = scales.y;
        const { left, right } = chartArea;

        this.faixasAtivas.forEach(f => {
            const yTop    = yScale.getPixelForValue(f.ate);
            const yBottom = yScale.getPixelForValue(f.de);
            ctx.save();
            ctx.fillStyle = f.cor;
            ctx.fillRect(left, yTop, right - left, yBottom - yTop);
            ctx.restore();
        });

        const cores = ["rgba(255,0,0,0.5)", "rgba(255,140,0,0.5)", "rgba(255,215,0,0.5)"];
        this.linhasAtivas.forEach((valor, i) => {
            const y = yScale.getPixelForValue(valor);
            ctx.save();
            ctx.strokeStyle = cores[i] || "rgba(255,255,255,0.3)";
            ctx.lineWidth = 1;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.moveTo(left, y);
            ctx.lineTo(right, y);
            ctx.stroke();
            ctx.restore();
        });
    }
};

// ── PLUGIN: Faixas líquido ────────────────────────────────────────
const pluginFaixasLiquido = {
    id: "faixasLiquido",
    beforeDraw(chart) {
        const { ctx, chartArea, scales } = chart;
        if (!chartArea) return;
        const yScale = scales.y;
        const { left, right } = chartArea;

        [
            { de: 30, ate: 100, cor: "rgba(255,0,0,0.12)" },
            { de: 0,  ate: 30,  cor: "rgba(0,255,85,0.08)" },
        ].forEach(f => {
            const yTop    = yScale.getPixelForValue(f.ate);
            const yBottom = yScale.getPixelForValue(f.de);
            ctx.save();
            ctx.fillStyle = f.cor;
            ctx.fillRect(left, yTop, right - left, yBottom - yTop);
            ctx.restore();
        });

        const y = yScale.getPixelForValue(30);
        ctx.save();
        ctx.strokeStyle = "rgba(255,0,0,0.5)";
        ctx.lineWidth = 1;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(right, y);
        ctx.stroke();
        ctx.restore();
    }
};

// ── GRADIENTES ────────────────────────────────────────────────────
function gradienteTemp(ctx, chartArea) {
    if (!chartArea) return "rgba(255,0,0,0.3)";
    const g = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    g.addColorStop(0,   "rgba(255,0,0,0.5)");
    g.addColorStop(0.5, "rgba(255,100,0,0.2)");
    g.addColorStop(1,   "rgba(255,0,0,0.0)");
    return g;
}

function gradienteLiquido(ctx, chartArea) {
    if (!chartArea) return "rgba(0,191,255,0.3)";
    const g = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    g.addColorStop(0,   "rgba(0,191,255,0.5)");
    g.addColorStop(0.5, "rgba(0,191,255,0.2)");
    g.addColorStop(1,   "rgba(0,191,255,0.0)");
    return g;
}

// ── OPÇÕES COMPARTILHADAS ─────────────────────────────────────────
function opcoesGrafico(sufixo, tooltipCallback) {
    return {
        responsive: true,
        animation: { duration: 600, easing: "easeInOutQuart" },
        interaction: { mode: "index", intersect: false },
        scales: {
            x: {
                ticks: {
                    color: "#aaa",
                    maxTicksLimit: 8,
                    callback: function(value) {
                        const label = this.getLabelForValue(value);
                        if (!label) return "";
                        const match = label.match(/(\d{2}:\d{2})/);
                        return match ? match[1] : label;
                    }
                },
                grid: { color: "rgba(255,255,255,0.05)" }
            },
            y: {
                ticks: { color: "#aaa", callback: val => val + sufixo },
                grid: { color: "rgba(255,255,255,0.05)" }
            }
        },
        plugins: {
            legend: { labels: { color: "#ccc", font: { size: 13 } } },
            tooltip: {
                backgroundColor: "#0d1520",
                borderColor: "#00bfff",
                borderWidth: 1,
                titleColor: "#fff",
                bodyColor: "#ccc",
                callbacks: { label: tooltipCallback }
            }
        }
    };
}

// ── GRÁFICO TEMPERATURA ───────────────────────────────────────────
const grafico = new Chart(document.getElementById("grafico"), {
    type: "line",
    plugins: [pluginFaixasTemp],
    data: {
        labels: [],
        datasets: [{
            label: "Temperatura (°C)",
            data: [],
            borderColor: "#ff4444",
            borderWidth: 2.5,
            backgroundColor: function(context) {
                const { ctx, chartArea } = context.chart;
                if (!chartArea) return "rgba(255,0,0,0.3)";
                return gradienteTemp(ctx, chartArea);
            },
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointBackgroundColor: function(context) {
                const val = context.parsed?.y;
                if (val === undefined) return "#ff4444";
                return PRODUTOS[produtoAtual].pontos(val);
            },
            pointBorderColor: "#111",
            pointBorderWidth: 2,
        }]
    },
    options: opcoesGrafico("°C", function(context) {
        const val = context.parsed.y;
        const status = PRODUTOS[produtoAtual].tooltip(val);
        return ` ${val}°C — ${status}`;
    })
});

// ── GRÁFICO LÍQUIDO ───────────────────────────────────────────────
const graficoLiquido = new Chart(document.getElementById("grafico-liquido"), {
    type: "line",
    plugins: [pluginFaixasLiquido],
    data: {
        labels: [],
        datasets: [{
            label: "Líquido Detectado (%)",
            data: [],
            borderColor: "#00bfff",
            borderWidth: 2.5,
            backgroundColor: function(context) {
                const { ctx, chartArea } = context.chart;
                if (!chartArea) return "rgba(0,191,255,0.3)";
                return gradienteLiquido(ctx, chartArea);
            },
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointBackgroundColor: function(context) {
                const val = context.parsed?.y;
                if (val === undefined) return "#00bfff";
                if (val <= 30) return "#00ff55";
                return "#ff0000";
            },
            pointBorderColor: "#111",
            pointBorderWidth: 2,
        }]
    },
    options: opcoesGrafico("%", function(context) {
        const val = context.parsed.y;
        return val <= 30 ? ` ${val}% — ✅ ESTÁVEL` : ` ${val}% — 🔴 VAZAMENTO!`;
    })
});

// ── LÓGICA PRINCIPAL ──────────────────────────────────────────────
async function carregarDados(){
    try{
        const resposta = await fetch("/dados");
        const dados = await resposta.json();

        if(!dados.length) return;

        const ultimo = dados[0];
        const p = PRODUTOS[produtoAtual];

        // ── TEMPERATURA ──────────────────────────────
        const temperatura = ultimo.temperatura;
        document.getElementById("temp").innerText = temperatura + "°C";

        const { cls, problema: problemaTemp } = p.classCard(temperatura);
        document.getElementById("card-temp").className = cls;

        // ── TENDÊNCIA DE TEMPERATURA ──────────────────
        if (dados.length >= 3) {
            const t0 = dados[0].temperatura;
            const t1 = dados[1].temperatura;
            const t2 = dados[2].temperatura;
            const tendencia = document.getElementById("tendencia-temp");

            if (t0 > t1 && t1 > t2) {
                tendencia.innerText = "↑";
                tendencia.style.color = "#ff4444";
                tendencia.title = "Temperatura subindo";
            } else if (t0 < t1 && t1 < t2) {
                tendencia.innerText = "↓";
                tendencia.style.color = "#00ff55";
                tendencia.title = "Temperatura descendo";
            } else {
                tendencia.innerText = "→";
                tendencia.style.color = "#aaa";
                tendencia.title = "Temperatura estável";
            }
        }

        // ── LÍQUIDO DETECTADO ─────────────────────────
        const liquido = ultimo.liquido;
        const cardLiquido = document.getElementById("card-liquido");
        const statusLiquido = document.getElementById("status-liquido");
        let problemaLiquido = false;

        document.getElementById("liquido").innerText = liquido + "%";

        if (liquido <= 30) {
            cardLiquido.className = "card card-ideal";
            statusLiquido.innerText = "ESTÁVEL";
            statusLiquido.style.color = "#00ff55";
        } else {
            cardLiquido.className = "card card-critico";
            statusLiquido.innerText = "VAZAMENTO!";
            statusLiquido.style.color = "#ff4444";
            problemaLiquido = true;
        }

        // ── VAZAMENTO ─────────────────────────────────
        const cardVazamento = document.getElementById("card-vazamento");
        const problemaVazamento = ultimo.vazamento === 1;
        const ultimoVazamento = dados.find(d => d.vazamento === 1);

        if (problemaVazamento) {
            document.getElementById("vazamento").innerText = "DETECTADO";
            cardVazamento.className = "card card-critico";
        } else {
            document.getElementById("vazamento").innerText = "ESTÁVEL";
            cardVazamento.className = "card card-ideal";
        }

        const ultimoEvento = document.getElementById("ultimo-vazamento");
        if (ultimoVazamento) {
            const hora = ultimoVazamento.hora.match(/(\d{2}:\d{2})/);
            ultimoEvento.innerText = "Último: " + (hora ? hora[1] : "--:--");
        } else {
            ultimoEvento.innerText = "Sem registros";
        }

        // ── HORÁRIO ───────────────────────────────────
        const agora = new Date();
        document.getElementById("horario").innerText = agora.toLocaleTimeString("pt-BR");
        document.getElementById("card-horario").className = "card card-neutro";

        // ── STATUS GERAL ──────────────────────────────
        const problemas = [problemaTemp, problemaLiquido, problemaVazamento]
            .filter(Boolean).length;

        const status = document.getElementById("status-temp");
        const alerta = document.getElementById("icone-alerta");

        alerta.classList.remove("alerta-piscando");
        status.className = "";

        if (problemas === 0) {
            status.innerText = "ESTÁVEL";
            status.classList.add("status-ideal");
        } else if (problemas === 1) {
            status.innerText = "1 PROBLEMA";
            status.classList.add("status-atencao");
            alerta.classList.add("alerta-piscando");
        } else if (problemas === 2) {
            status.innerText = "2 PROBLEMAS";
            status.classList.add("status-laranja");
            alerta.classList.add("alerta-piscando");
        } else {
            status.innerText = "3 PROBLEMAS";
            status.classList.add("status-critico");
            alerta.classList.add("alerta-piscando");
        }

        // ── GRÁFICOS ──────────────────────────────────
        const labels = [];
        const temperaturas = [];
        const liquidos = [];

        [...dados].reverse().forEach(item => {
            const d = new Date(item.hora.replace(" ", "T") + "Z");
            labels.push(d.toLocaleTimeString("pt-BR"));
            temperaturas.push(item.temperatura);
            liquidos.push(item.liquido);
        });

        grafico.data.labels = labels;
        grafico.data.datasets[0].data = temperaturas;
        grafico.update("active");

        graficoLiquido.data.labels = labels;
        graficoLiquido.data.datasets[0].data = liquidos;
        graficoLiquido.update("active");

        // ── TELEGRAM ──────────────────────────────────
        const cardTelegram  = document.getElementById("card-telegram");
        const iconeTelegram = document.getElementById("icone-telegram");

        const resAlertas = await fetch(`/alertas?produto=${produtoAtual}`);
        const dadosAlertas = await resAlertas.json();

        if (dadosAlertas.problemas > 0) {
            cardTelegram.style.display = "block";
            cardTelegram.className = "card card-critico";
            iconeTelegram.classList.add("alerta-piscando");
        } else {
            cardTelegram.style.display = "none";
            iconeTelegram.classList.remove("alerta-piscando");
        }

    } catch(erro) {
        console.log(erro);
    }
}

carregarDados();
setInterval(carregarDados, 5000);
        



