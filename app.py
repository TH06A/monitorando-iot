from flask import Flask, render_template, jsonify, request
import psycopg2
import requests
import os
 
app = Flask(__name__)
 
# ── CONFIGURAÇÃO TELEGRAM ─────────────────────────────────────────
TELEGRAM_TOKEN = "8724770527:AAHdBwTFZgMhnhhKn-CqFkgmAwyCgy4RvbQ"
 
DESTINATARIOS = [
    "6794291173",   # Thierry
    "7931348478",   # Diogo
]
 
ultimo_nivel_notificado = 0
 
# ── CONFIGURAÇÃO BANCO ────────────────────────────────────────────
DATABASE_URL = "postgresql://monitora_iot_db_user:nXoVfnBKqp71U3NoIirT4Nckk4D6ha78@dpg-d8k9dfgu3fls73aa9km0-a/monitora_iot_db"
 
def get_conn():
    return psycopg2.connect(DATABASE_URL)
 
def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensores (
        id SERIAL PRIMARY KEY,
        temperatura REAL,
        umidade REAL,
        bateria INTEGER,
        vazamento INTEGER,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
 
init_db()
 
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in DESTINATARIOS:
        requests.post(url, data={
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "HTML"
        })
 
# ── ROTA: RECEBER DADOS DO ESP32 ─────────────────────────────────
@app.route("/sensor", methods=["POST"])
def receber_sensor():
    dados = request.get_json()
    print("Recebido:", dados, flush=True)
    temperatura = dados["temperatura"]
    liquido     = dados["liquido"]
 
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sensores (temperatura, umidade, bateria, vazamento)
    VALUES (%s, %s, %s, %s)
    """, (temperatura, liquido, 100, 1 if liquido > 30 else 0))
    conn.commit()
    conn.close()
 
    return jsonify({"status": "ok"})
 
# ── ROTA: PÁGINA PRINCIPAL ────────────────────────────────────────
@app.route("/")
def dashboard():
    return render_template("dashboard.html")
 
# ── ROTA: BUSCAR DADOS ────────────────────────────────────────────
@app.route("/dados")
def dados():
    conn = get_conn()
    cursor = conn.cursor()
 
    cursor.execute("""
    SELECT temperatura, umidade, vazamento, data_hora
    FROM sensores
    ORDER BY id DESC
    LIMIT 20
    """)
 
    registros = cursor.fetchall()
    conn.close()
 
    resultado = []
    for r in registros:
        resultado.append({
            "temperatura": r[0],
            "liquido":     r[1],
            "vazamento":   r[2],
            "hora":        str(r[3])
        })
 
    return jsonify(resultado)
 
# ── ROTA: ALERTAS E TELEGRAM ──────────────────────────────────────
@app.route("/alertas")
def alertas():
    global ultimo_nivel_notificado
 
    conn = get_conn()
    cursor = conn.cursor()
 
    cursor.execute("""
    SELECT temperatura, umidade, vazamento
    FROM sensores
    ORDER BY id DESC
    LIMIT 1
    """)
 
    r = cursor.fetchone()
    conn.close()
 
    if not r:
        return jsonify({"problemas": 0})
 
    temperatura = r[0]
    liquido     = r[1]
 
    problemas = []
 
    # ── RESTRIÇÃO TEMP ───────────────────────────────────────
    if temperatura > 0:
        if temperatura <= 15:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (BOM, mas acima do ideal)")
        elif temperatura <= 18:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (ATENÇÃO)")
        else:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (CRÍTICO)")
 
    if liquido > 30:
        problemas.append(f"💧 Líquido detectado: <b>{liquido}%</b> — VAZAMENTO!")
 
    total = len(problemas)
 
    if total > 0 and total > ultimo_nivel_notificado:
        # Novos problemas apareceram
        emoji = "⚠️" if total == 1 else "🔴"
        msg = f"{emoji} <b>MONITORA IOT — {total} PROBLEMA{'S' if total > 1 else ''}</b>\n\n"
        msg += "\n".join(problemas)
        enviar_telegram(msg)
 
    elif total > 0 and total < ultimo_nivel_notificado:
        # Um sensor normalizou, mas ainda há problemas
        msg = f"🟡 <b>MONITORA IOT — {total} PROBLEMA{'S' if total > 1 else ''} RESTANTE{'S' if total > 1 else ''}</b>\n\n"
        msg += "\n".join(problemas)
        msg += "\n\n✅ Um sensor normalizou."
        enviar_telegram(msg)
 
    elif total == 0 and ultimo_nivel_notificado > 0:
        # Tudo normalizado
        enviar_telegram("✅ <b>MONITORA IOT — Sistema ESTÁVEL</b>\nTodos os sensores normalizaram.")
 
    ultimo_nivel_notificado = total
 
    return jsonify({"problemas": total})
 
if __name__ == "__main__":
    app.run(debug=True)
