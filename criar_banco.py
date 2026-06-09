import sqlite3

conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sensores (
id INTEGER PRIMARY KEY AUTOINCREMENT,
temperatura REAL,
umidade REAL,
bateria INTEGER,
vazamento INTEGER,
data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
INSERT INTO sensores
(temperatura, umidade, bateria, vazamento)
VALUES
(2.5, 10, 100, 0)
""")

conn.commit()
conn.close()

print("Banco criado!")
