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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estado_alerta (
        id INTEGER PRIMARY KEY DEFAULT 1,
        ultimo_nivel INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    INSERT INTO estado_alerta (id, ultimo_nivel)
    VALUES (1, 0)
    ON CONFLICT (id) DO NOTHING
    """)

    conn.commit()
    conn.close()

init_db()

# ── ESCALAS POR PRODUTO ───────────────────────────────────────────
ESCALAS = {
    "refrigerante": {
        "nome":  "Refrigerante",
        "icone": "🥤",
        # Notifica só acima de 24C
        "check": lambda t: (
            "ATENCAO" if t <= 27 else
            "CRITICO"
        ) if t > 24 else None
    },
    "acai": {
        "nome":  "Acai",
        "icone": "🍧",
        # Notifica só acima de 20C
        "check": lambda t: (
            "ATENCAO" if t <= 24 else
            "CRITICO"
        ) if t > 20 else None
    },
    "pizza": {
        "nome":  "Pizza",
        "icone": "🍕",
        # Notifica só abaixo de 25C (escala inversa)
        "check": lambda t: (
            "ATENCAO" if t >= 25 else
            "CRITICO"
        ) if t < 28 else None
    }
}

def get_ultimo_nivel(cursor):
    cursor.execute("SELECT ultimo_nivel FROM estado_alerta WHERE id = 1")
    row = cursor.fetchone()
    return row[0] if row else 0

def set_ultimo_nivel(cursor, nivel):
    cursor.execute("UPDATE estado_alerta SET ultimo_nivel = %s WHERE id = 1", (nivel,))

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
    # Produto vem como parâmetro da URL: /alertas?produto=pizza
    produto_key = request.args.get("produto", "refrigerante")
    escala = ESCALAS.get(produto_key, ESCALAS["refrigerante"])

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT temperatura, umidade, vazamento
    FROM sensores
    ORDER BY id DESC
    LIMIT 1
    """)
    r = cursor.fetchone()

    if not r:
        conn.close()
        return jsonify({"problemas": 0})

    temperatura = r[0]
    liquido     = r[1]

    ultimo_nivel = get_ultimo_nivel(cursor)

    problemas = []

    # ── VERIFICA TEMPERATURA CONFORME PRODUTO ────────────────────
    status_temp = escala["check"](temperatura)
    if status_temp:
        problemas.append(f"🌡️ Temperatura em <b>{temperatura}°C</b> ({status_temp})")

    # ── VERIFICA LÍQUIDO ─────────────────────────────────────────
    if liquido > 30:
        problemas.append(f"💧 Líquido detectado: <b>{liquido}%</b> — VAZAMENTO!")

    total = len(problemas)
    icone = escala["icone"]
    nome  = escala["nome"]

    if total > 0 and total > ultimo_nivel:
        emoji = "⚠️" if total == 1 else "🔴"
        msg  = f"{emoji} <b>MONITORA IOT</b>\n"
        msg += f"{icone} Você está monitorando: <b>{nome}</b>\n\n"
        msg += "\n".join(problemas)
        enviar_telegram(msg)

    elif total > 0 and total < ultimo_nivel:
        msg  = f"🟡 <b>MONITORA IOT</b>\n"
        msg += f"{icone} Você está monitorando: <b>{nome}</b>\n\n"
        msg += "\n".join(problemas)
        msg += "\n\n✅ Um sensor normalizou."
        enviar_telegram(msg)

    elif total == 0 and ultimo_nivel > 0:
        msg  = f"✅ <b>MONITORA IOT</b>\n"
        msg += f"{icone} Você está monitorando: <b>{nome}</b>\n\n"
        msg += "Todos os sensores normalizaram."
        enviar_telegram(msg)

    set_ultimo_nivel(cursor, total)
    conn.commit()
    conn.close()

    return jsonify({"problemas": total})

if __name__ == "__main__":
    app.run(debug=True)
