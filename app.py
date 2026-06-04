from flask import Flask, render_template, jsonify
import sqlite3
import requests
import os

app = Flask(__name__)

# ── CONFIGURAÇÃO TELEGRAM ─────────────────────────────────────────
TELEGRAM_TOKEN  = "8724770527:AAHdBwTFZgMhnhhKn-CqFkgmAwyCgy4RvbQ"
TELEGRAM_CHAT_ID = "6794291173"

# Controle para não spammar — guarda o último nível notificado
ultimo_nivel_notificado = 0

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    })

# ── ROTAS ─────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/dados")
def dados():
    conn = sqlite3.connect("banco.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM sensores
    ORDER BY id DESC
    LIMIT 20
    """)

    registros = cursor.fetchall()
    resultado = []

    for r in registros:
        resultado.append({
            "temperatura": r["temperatura"],
            "umidade":     r["umidade"],
            "bateria":     r["bateria"],
            "vazamento":   r["vazamento"],
            "hora":        r["data_hora"]
        })

    conn.close()
    return jsonify(resultado)

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

    temperatura  = r["temperatura"]
    umidade      = r["umidade"]
    vazamento    = r["vazamento"]

    problemas = []

    if temperatura > -5:
        if temperatura <= -2:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (BOM, mas acima do ideal)")
        elif temperatura <= 2:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (ATENÇÃO)")
        else:
            problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> (CRÍTICO)")

    if umidade > 75:
        if umidade <= 85:
            problemas.append(f"💧 Umidade em <b>{umidade}%</b> (ATENÇÃO)")
        else:
            problemas.append(f"💧 Umidade em <b>{umidade}%</b> (CRÍTICO)")

    if vazamento == 1:
        problemas.append("🚨 <b>Vazamento DETECTADO!</b>")

    total = len(problemas)

    # Só notifica se o nível piorou
    if total > 0 and total > ultimo_nivel_notificado:
        emoji = "⚠️" if total == 1 else ("🔶" if total == 2 else "🔴")
        msg = f"{emoji} <b>MONITORA IOT — {total} PROBLEMA{'S' if total > 1 else ''}</b>\n\n"
        msg += "\n".join(problemas)
        enviar_telegram(msg)
        ultimo_nivel_notificado = total

    # Reseta quando voltar ao normal
    if total == 0:
        if ultimo_nivel_notificado > 0:
            enviar_telegram("✅ <b>MONITORA IOT — Sistema ESTÁVEL</b>\nTodos os sensores normalizaram.")
        ultimo_nivel_notificado = 0

    return jsonify({"problemas": total})

if __name__ == "__main__":
    app.run(debug=True)