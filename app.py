from flask import Flask, render_template, jsonify, request
import sqlite3
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

    temperatura = dados["temperatura"]
    liquido     = dados["liquido"]

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sensores (temperatura, umidade, bateria, vazamento)
    VALUES (?, ?, ?, ?)
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
    conn = sqlite3.connect("banco.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM sensores
    ORDER BY id DESC
    LIMIT 20
    """)

    registros = cursor.fetchall()
    resultado = []

    for r in registros:
        resultado.append({
            "temperatura": r["temperatura"],
            "liquido":     r["umidade"],
            "vazamento":   r["vazamento"],
            "hora":        r["data_hora"]
        })

    conn.close()
    return jsonify(resultado)

# ── ROTA: ALERTAS E TELEGRAM ──────────────────────────────────────
@app.route("/alertas")
def alertas():
    global ultimo_nivel_notificado

    conn = sqlite3.connect("banco.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM sensores
    ORDER BY id DESC
    LIMIT 1
    """)

    r = cursor.fetchone()
    conn.close()

    if not r:
        return jsonify({"problemas": 0})

    temperatura = r["temperatura"]
    liquido     = r["umidade"]

    problemas = []

    if temperatura > 0:
        if temperatura <= 4:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (BOM, mas acima do ideal)")
        elif temperatura <= 10:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (ATENÇÃO)")
        else:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (CRÍTICO)")

    if liquido > 30:
        problemas.append(f"💧 Líquido detectado: <b>{liquido}%</b> — VAZAMENTO!")

    total = len(problemas)

    if total > 0 and total > ultimo_nivel_notificado:
        emoji = "⚠️" if total == 1 else "🔴"
        msg = f"{emoji} <b>MONITORA IOT — {total} PROBLEMA{'S' if total > 1 else ''}</b>\n\n"
        msg += "\n".join(problemas)
        enviar_telegram(msg)
        ultimo_nivel_notificado = total

    if total == 0:
        if ultimo_nivel_notificado > 0:
            enviar_telegram("✅ <b>MONITORA IOT — Sistema ESTÁVEL</b>\nTodos os sensores normalizaram.")
        ultimo_nivel_notificado = 0

    return jsonify({"problemas": total})

if __name__ == "__main__":
    app.run(debug=True)
