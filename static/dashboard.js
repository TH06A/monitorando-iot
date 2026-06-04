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
        document.getElementById("titulo-pagina").innerText = "Histórico de Temperatura";
        grafico.update("active");
    }
}

// ── PLUGIN: Faixas coloridas de fundo ────────────────────────────
const pluginFaixas = {
    id: "faixas",
    beforeDraw(chart) {
        const { ctx, chartArea, scales } = chart;
        if (!chartArea) return;

        const yScale = scales.y;
        const { left, right } = chartArea;

        const faixas = [
            { de: 2,   ate: 10,  cor: "rgba(255,0,0,0.12)" },
            { de: -2,  ate: 2,   cor: "rgba(255,215,0,0.10)" },
            { de: -5,  ate: -2,  cor: "rgba(0,191,255,0.10)" },
            { de: -10, ate: -5,  cor: "rgba(0,255,85,0.08)" },
        ];

        faixas.forEach(f => {
            const yTop    = yScale.getPixelForValue(f.ate);
            const yBottom = yScale.getPixelForValue(f.de);
            ctx.save();
            ctx.fillStyle = f.cor;
            ctx.fillRect(left, yTop, right - left, yBottom - yTop);
            ctx.restore();
        });

        const limites = [
            { valor: 2,  cor: "rgba(255,0,0,0.5)" },
            { valor: -2, cor: "rgba(255,215,0,0.5)" },
            { valor: -5, cor: "rgba(0,255,85,0.5)" },
        ];

        limites.forEach(l => {
            const y = yScale.getPixelForValue(l.valor);
            ctx.save();
            ctx.strokeStyle = l.cor;
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

// ── GRADIENTE DA LINHA ────────────────────────────────────────────
function criarGradiente(ctx, chartArea) {
    if (!chartArea) return "rgba(255,0,0,0.3)";
    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    gradient.addColorStop(0,   "rgba(255,0,0,0.5)");
    gradient.addColorStop(0.5, "rgba(255,100,0,0.2)");
    gradient.addColorStop(1,   "rgba(255,0,0,0.0)");
    return gradient;
}

// ── GRÁFICO ───────────────────────────────────────────────────────
const ctx = document.getElementById("grafico");

const grafico = new Chart(ctx, {
    type: "line",
    plugins: [pluginFaixas],
    data: {
        labels: [],
        datasets: [{
            label: "Temperatura (°C)",
            data: [],
            borderColor: "#ff4444",
            borderWidth: 2.5,
            backgroundColor: function(context) {
                const chart = context.chart;
                const { ctx, chartArea } = chart;
                if (!chartArea) return "rgba(255,0,0,0.3)";
                return criarGradiente(ctx, chartArea);
            },
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointBackgroundColor: function(context) {
                const val = context.parsed?.y;
                if (val === undefined) return "#ff4444";
                if (val <= -5) return "#00ff55";
                if (val <= -2) return "#00bfff";
                if (val <= 2)  return "#ffd700";
                return "#ff0000";
            },
            pointBorderColor: "#111",
            pointBorderWidth: 2,
        }]
    },
    options: {
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
                ticks: {
                    color: "#aaa",
                    callback: val => val + "°C"
                },
                grid: { color: "rgba(255,255,255,0.05)" }
            }
        },
        plugins: {
            legend: {
                labels: { color: "#ccc", font: { size: 13 } }
            },
            tooltip: {
                backgroundColor: "#0d1520",
                borderColor: "#00bfff",
                borderWidth: 1,
                titleColor: "#fff",
                bodyColor: "#ccc",
                callbacks: {
                    label: function(context) {
                        const val = context.parsed.y;
                        let status;
                        if (val <= -5)      status = "✅ IDEAL";
                        else if (val <= -2) status = "🔵 BOM";
                        else if (val <= 2)  status = "⚠️ ATENÇÃO";
                        else                status = "🔴 CRÍTICO";
                        return ` ${val}°C — ${status}`;
                    }
                }
            }
        }
    }
});

// ── LÓGICA PRINCIPAL ──────────────────────────────────────────────
async function carregarDados(){

    try{

        const resposta = await fetch("/dados");
        const dados = await resposta.json();

        if(!dados.length) return;

        const ultimo = dados[0];

        // ── TEMPERATURA ──────────────────────────────
        document.getElementById("temp")
            .innerText = ultimo.temperatura + "°C";

        const temperatura = ultimo.temperatura;
        const cardTemp = document.getElementById("card-temp");
        let problemaTemp = false;

        if (temperatura <= -5) {
            cardTemp.className = "card card-ideal";
        } else if (temperatura <= -2) {
            cardTemp.className = "card card-bom";
            problemaTemp = true;
        } else if (temperatura <= 2) {
            cardTemp.className = "card card-alerta";
            problemaTemp = true;
        } else {
            cardTemp.className = "card card-critico";
            problemaTemp = true;
        }

        // ── UMIDADE ───────────────────────────────────
        document.getElementById("umidade")
            .innerText = ultimo.umidade + "%";

        const umidade = ultimo.umidade;
        const cardUmidade = document.getElementById("card-umidade");
        let problemaUmidade = false;

        if (umidade <= 75) {
            cardUmidade.className = "card card-ideal";
        } else if (umidade <= 85) {
            cardUmidade.className = "card card-alerta";
            problemaUmidade = true;
        } else {
            cardUmidade.className = "card card-critico";
            problemaUmidade = true;
        }

        // ── VAZAMENTO ─────────────────────────────────
        const cardVazamento = document.getElementById("card-vazamento");
        const problemaVazamento = ultimo.vazamento === 1;

        if (problemaVazamento) {
            document.getElementById("vazamento").innerText = "DETECTADO";
            cardVazamento.className = "card card-critico";
        } else {
            document.getElementById("vazamento").innerText = "ESTÁVEL";
            cardVazamento.className = "card card-ideal";
        }

        // ── HORÁRIO ───────────────────────────────────
        const agora = new Date();
        document.getElementById("horario")
            .innerText = agora.toLocaleTimeString("pt-BR");
        document.getElementById("card-horario").className = "card card-neutro";

        // ── STATUS GERAL ──────────────────────────────
        const problemas = [problemaTemp, problemaUmidade, problemaVazamento]
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

        // ── GRÁFICO ───────────────────────────────────
        const labels = [];
        const temperaturas = [];

        [...dados].reverse().forEach(item => {
            labels.push(item.hora);
            temperaturas.push(item.temperatura);
        });

        grafico.data.labels = labels;
        grafico.data.datasets[0].data = temperaturas;
        grafico.update("active");

        // ── TELEGRAM ──────────────────────────────────
        const cardTelegram  = document.getElementById("card-telegram");
        const iconeTelegram = document.getElementById("icone-telegram");

        const resAlertas = await fetch("/alertas");
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