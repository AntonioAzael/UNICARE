import os
import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "sistema_reportes_mantenimiento",
    "charset": "utf8mb4",
}

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
SQL_TABLAS = os.path.join(RUTA_BASE, "sql", "01_tablas_mantenimiento.sql")
SQL_CATALOGO = os.path.join(RUTA_BASE, "sql", "02_catalogo_mantenimiento.sql")


def ejecutar_archivo_sql(cursor, ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = [linea for linea in f if not linea.strip().startswith("--")]
    texto = "".join(lineas)
    for sentencia in texto.split(";"):
        sql = sentencia.strip()
        if sql:
            cursor.execute(sql)


def crear_base_desde_sql():
    cfg = DB_CONFIG.copy()
    cfg.pop("database")
    cnx = mysql.connector.connect(**cfg)
    try:
        cursor = cnx.cursor()
        ejecutar_archivo_sql(cursor, SQL_TABLAS)
        ejecutar_archivo_sql(cursor, SQL_CATALOGO)
        cnx.commit()
        cursor.close()
    finally:
        cnx.close()


def reiniciar_base():
    cfg = DB_CONFIG.copy()
    nombre_bd = cfg.pop("database")
    cnx = mysql.connector.connect(**cfg)
    try:
        cursor = cnx.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{nombre_bd}`")
        ejecutar_archivo_sql(cursor, SQL_TABLAS)
        ejecutar_archivo_sql(cursor, SQL_CATALOGO)
        cnx.commit()
        cursor.close()
    finally:
        cnx.close()


_esquema_verificado = False


def esquema_actualizado():
    # El esquema nuevo tiene la tabla "estado" y la tabla intermedia "solucion_material".
    # Si la base viene de la version anterior (estado_reporte, orden_trabajo...), se recrea.
    # Tambien se recrea si REPORTE aun no tiene la ubicacion por piso, area y lugar, o si todavia
    # liga el equipo de inventario (codigo_inventario) en lugar del equipo afectado escrito.
    cnx = mysql.connector.connect(**DB_CONFIG)
    try:
        cursor = cnx.cursor()
        cursor.execute("SHOW TABLES")
        tablas = {fila[0] for fila in cursor.fetchall()}
        if not {"estado", "solucion_material", "mantenimiento_trabajador"}.issubset(tablas):
            cursor.close()
            return False
        cursor.execute(
            """
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'reporte'
            """,
            (DB_CONFIG["database"],),
        )
        columnas = {fila[0] for fila in cursor.fetchall()}
        cursor.close()
        return {"piso", "equipo_afectado"}.issubset(columnas) and "codigo_inventario" not in columnas
    finally:
        cnx.close()


def conectar():
    global _esquema_verificado
    try:
        if not _esquema_verificado:
            if not esquema_actualizado():
                reiniciar_base()
            _esquema_verificado = True
        cnx = mysql.connector.connect(**DB_CONFIG)
        return cnx
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            crear_base_desde_sql()
            return mysql.connector.connect(**DB_CONFIG)
        raise


def obtener_tablas():
    cnx = conectar()
    try:
        cursor = cnx.cursor()
        cursor.execute("SHOW TABLES")
        tablas = [fila[0] for fila in cursor.fetchall()]
        cursor.close()
        return tablas
    finally:
        cnx.close()
