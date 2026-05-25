import sqlite3
import os
import sys


def obtener_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))


def obtener_db_path():
    return os.path.join(obtener_base_dir(), "tortilleria_carmelita.db")


DB_PATH = obtener_db_path()


def conectar():
    try:
        conexion = sqlite3.connect(obtener_db_path())
        conexion.execute("PRAGMA foreign_keys = ON")
        print("Conexión exitosa a SQLite")
        return conexion
    except sqlite3.Error as e:
        print(f"Error al conectar a SQLite: {e}")
        return None