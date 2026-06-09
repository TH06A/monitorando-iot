import sqlite3
import random
import time

while True:

    temperatura = round(random.uniform(-10, 3), 1)
    umidade = random.randint(60, 80)
    bateria = random.randint(85, 100)
    vazamento = random.choice([0, 0, 0, 0, 0, 0, 1])

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sensores
    (temperatura, umidade, bateria, vazamento)
    VALUES (?, ?, ?, ?)
    """, (temperatura, umidade, bateria, vazamento))

    conn.commit()
    conn.close()

    print(
        f"Temp:{temperatura}°C | "
        f"Umidade:{umidade}% | "
        f"Bateria:{bateria}%"
    )

    time.sleep(8)
