# ── IMPORTAÇÕES ───────────────────────────────────────────────────
from flask import Flask, render_template, jsonify, request
# request: permite receber dados enviados pelo ESP32
 
import sqlite3
# Biblioteca para trabalhar com o banco de dados SQLite
 
import requests
# Biblioteca para fazer requisições HTTP (usada para enviar mensagens ao Telegram)
 
import os
# Biblioteca do sistema operacional (não usada ativamente, mas útil para futuras configs)
 
# ── INICIALIZAÇÃO DO SERVIDOR ─────────────────────────────────────
app = Flask(__name__)
# Cria o servidor Flask — é ele que fica "ouvindo" as requisições
 
# ── CONFIGURAÇÃO TELEGRAM ─────────────────────────────────────────
TELEGRAM_TOKEN = "8724770527:AAHdBwTFZgMhnhhKn-CqFkgmAwyCgy4RvbQ"
# Token do bot criado no BotFather — identifica qual bot vai enviar a mensagem
 
DESTINATARIOS = [
    "6794291173",   # Thierry
    "7931348478",   # Diogo
]
# Lista de Chat IDs que vão receber as notificações
# Para adicionar mais pessoas: coloque o Chat ID delas aqui
 
ultimo_nivel_notificado = 0
# Controle anti-spam: guarda quantos problemas foram notificados por último
# Evita mandar a mesma mensagem repetida a cada 5 segundos
 
# ── FUNÇÃO: ENVIAR MENSAGEM NO TELEGRAM ──────────────────────────
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Monta a URL da API do Telegram usando o token do bot
 
    for chat_id in DESTINATARIOS:
        # Percorre cada destinatário e envia a mensagem individualmente
        requests.post(url, data={
            "chat_id": chat_id,       # Para quem vai a mensagem
            "text": mensagem,         # Conteúdo da mensagem
            "parse_mode": "HTML"      # Permite usar <b>negrito</b> na mensagem
        })
 
# ── ROTA: RECEBER DADOS DO ESP32 ─────────────────────────────────
@app.route("/sensor", methods=["POST"])
def receber_sensor():
    # Essa rota é chamada pelo ESP32 a cada 5 segundos
    # O ESP32 envia um POST com os dados dos sensores em formato JSON
 
    dados = request.get_json()
    # Lê o JSON enviado pelo ESP32
    # Exemplo: {"temperatura": 2.5, "umidade": 70, "vazamento": 0}
 
    temperatura = dados["temperatura"]  # Ex: 2.5
    umidade     = dados["umidade"]      # Ex: 70
    vazamento   = dados["vazamento"]    # 0 = sem vazamento, 1 = vazamento detectado
 
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
 
    cursor.execute("""
    INSERT INTO sensores (temperatura, umidade, bateria, vazamento)
    VALUES (?, ?, ?, ?)
    """, (temperatura, umidade, 100, vazamento))
    # Salva os dados no banco de dados
    # bateria está fixo em 100 pois o ESP32 não mede bateria nesse projeto
 
    conn.commit()   # Confirma a gravação no banco
    conn.close()    # Fecha a conexão com o banco
 
    return jsonify({"status": "ok"})
    # Retorna confirmação para o ESP32 que os dados foram recebidos
 
# ── ROTA: PÁGINA PRINCIPAL ────────────────────────────────────────
@app.route("/")
def dashboard():
    # Quando alguém acessa o link no navegador, carrega o dashboard HTML
    return render_template("dashboard.html")
 
# ── ROTA: BUSCAR DADOS PARA O DASHBOARD ──────────────────────────
@app.route("/dados")
def dados():
    # O dashboard.js chama essa rota a cada 5 segundos
    # para atualizar os cards e gráficos na tela
 
    conn = sqlite3.connect("banco.db")
    conn.row_factory = sqlite3.Row
    # row_factory permite acessar as colunas pelo nome (ex: r["temperatura"])
 
    cursor = conn.cursor()
 
    cursor.execute("""
    SELECT *
    FROM sensores
    ORDER BY id DESC
    LIMIT 20
    """)
    # Busca os 20 registros mais recentes do banco
    # ORDER BY id DESC = do mais novo para o mais antigo
 
    registros = cursor.fetchall()
    resultado = []
 
    for r in registros:
        # Converte cada registro em um dicionário Python
        resultado.append({
            "temperatura": r["temperatura"],
            "umidade":     r["umidade"],
            "bateria":     r["bateria"],
            "vazamento":   r["vazamento"],
            "hora":        r["data_hora"]   # Timestamp de quando foi salvo
        })
 
    conn.close()
    return jsonify(resultado)
    # Retorna os dados em formato JSON para o dashboard.js
 
# ── ROTA: VERIFICAR ALERTAS E NOTIFICAR TELEGRAM ─────────────────
@app.route("/alertas")
def alertas():
    # O dashboard.js também chama essa rota a cada 5 segundos
    # Verifica se há problemas e dispara notificações no Telegram
 
    global ultimo_nivel_notificado
    # Usa a variável global para controlar o anti-spam
 
    conn = sqlite3.connect("banco.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
 
    cursor.execute("""
    SELECT * FROM sensores
    ORDER BY id DESC
    LIMIT 1
    """)
    # Busca apenas o registro mais recente para verificar o estado atual
 
    r = cursor.fetchone()
    conn.close()
 
    if not r:
        return jsonify({"problemas": 0})
        # Se o banco estiver vazio, retorna sem problemas
 
    temperatura = r["temperatura"]
    umidade     = r["umidade"]
    vazamento   = r["vazamento"]
 
    problemas = []
    # Lista que vai acumulando os problemas encontrados
 
    # ── VERIFICAÇÃO DE TEMPERATURA ────────────────────
    if temperatura > 0:
        # Acima de 0°C já é considerado fora do ideal para bolsa térmica
        if temperatura <= 4:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (BOM, mas acima do ideal)")
        elif temperatura <= 10:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (ATENÇÃO)")
        else:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (CRÍTICO)")
 
    # ── VERIFICAÇÃO DE UMIDADE ────────────────────────
    if umidade > 75:
        # Acima de 75% já é atenção
        if umidade <= 85:
            problemas.append(f"💧 Umidade em <b>{umidade}%</b> (ATENÇÃO)")
        else:
            problemas.append(f"💧 Umidade em <b>{umidade}%</b> (CRÍTICO)")
 
    # ── VERIFICAÇÃO DE VAZAMENTO ──────────────────────
    if vazamento == 1:
        problemas.append("🚨 <b>Vazamento DETECTADO!</b>")
 
    total = len(problemas)
    # Conta quantos problemas foram encontrados (0, 1, 2 ou 3)
 
    # ── ENVIO DA NOTIFICAÇÃO ──────────────────────────
    if total > 0 and total > ultimo_nivel_notificado:
        # Só notifica se o número de problemas PIOROU
        # Evita spam: se já tem 1 problema e continua 1, não notifica de novo
        emoji = "⚠️" if total == 1 else ("🔶" if total == 2 else "🔴")
        msg = f"{emoji} <b>MONITORA IOT — {total} PROBLEMA{'S' if total > 1 else ''}</b>\n\n"
        msg += "\n".join(problemas)
        enviar_telegram(msg)
        ultimo_nivel_notificado = total
        # Atualiza o último nível notificado
 
    # ── RESET QUANDO NORMALIZAR ───────────────────────
    if total == 0:
        if ultimo_nivel_notificado > 0:
            # Só manda mensagem de "estável" se antes havia problema
            enviar_telegram("✅ <b>MONITORA IOT — Sistema ESTÁVEL</b>\nTodos os sensores normalizaram.")
        ultimo_nivel_notificado = 0
        # Reseta o controle para 0
 
    return jsonify({"problemas": total})
    # Retorna o total de problemas para o dashboard.js
    # O dashboard usa isso para mostrar/esconder o card do Telegram
 
# ── INICIALIZAÇÃO ─────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
    # Roda o servidor localmente em modo debug
    # No Render o gunicorn substitui essa linha automaticamente
