import sqlite3
import os

# La base de datos se guarda en la misma carpeta del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tortilleria_carmelita.db")

def conectar():
    try:
        conexion = sqlite3.connect(DB_PATH)
        conexion.execute("PRAGMA foreign_keys = ON")
        print("Conexión exitosa a SQLite")
        return conexion
    except sqlite3.Error as e:
        print(f"Error al conectar a SQLite: {e}")
        return None