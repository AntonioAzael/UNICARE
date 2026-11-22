from datetime import date
from conexion import conectar


def listar_reportes_sin_solucion():
    # Reportes que aun no tienen solucion registrada (REPORTE 1:1 SOLUCION)
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.folio, r.fecha_registro, r.nombre_estado, e.nombre_equipo, r.descripcion_reporte
            FROM reporte r
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            LEFT JOIN solucion s ON s.folio = r.folio
            WHERE s.numero_solucion IS NULL
            ORDER BY r.fecha_registro DESC, r.folio DESC
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_materiales():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT codigo_material, nombre_material, existencia, stock_minimo FROM material ORDER BY nombre_material"
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def registrar_solucion(folio, tiempo_resolucion, solucion_aplicada, observaciones=None, materiales=None):
    # Registro 6: Registrar la solucion de un reporte y los materiales utilizados
    # materiales: lista de {"codigo_material": ..., "cantidad": ...}
    texto = solucion_aplicada.strip()
    if not texto:
        raise ValueError("La solucion aplicada no puede ir vacia.")
    if tiempo_resolucion <= 0:
        raise ValueError("El tiempo de resolucion debe ser mayor a cero.")

    materiales = materiales or []
    obs = observaciones.strip() if observaciones and observaciones.strip() else None
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("SELECT 1 FROM solucion WHERE folio = %s", (folio,))
        if cursor.fetchone():
            raise ValueError("Ese reporte ya tiene una solucion registrada.")

        cursor.execute(
            """
            INSERT INTO solucion (fecha_resolucion, tiempo_resolucion, solucion_aplicada, observaciones_solucion, folio)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (date.today(), tiempo_resolucion, texto, obs, folio),
        )
        numero_solucion = cursor.lastrowid

        for item in materiales:
            cursor.execute("SELECT existencia, nombre_material FROM material WHERE codigo_material = %s", (item["codigo_material"],))
            mat = cursor.fetchone()
            if not mat or mat["existencia"] < item["cantidad"]:
                raise ValueError(f"No hay existencia suficiente de {mat['nombre_material'] if mat else item['codigo_material']}.")
            cursor.execute(
                "INSERT INTO solucion_material (numero_solucion, codigo_material, cantidad_usada) VALUES (%s, %s, %s)",
                (numero_solucion, item["codigo_material"], item["cantidad"]),
            )
            cursor.execute(
                "UPDATE material SET existencia = existencia - %s WHERE codigo_material = %s",
                (item["cantidad"], item["codigo_material"]),
            )

        cursor.execute("UPDATE reporte SET nombre_estado = 'Solucionado' WHERE folio = %s", (folio,))
        cursor.execute(
            "UPDATE equipo_instalacion SET necesita_reparacion = 0 "
            "WHERE codigo_inventario = (SELECT codigo_inventario FROM reporte WHERE folio = %s)",
            (folio,),
        )
        cnx.commit()
        cursor.close()
        return numero_solucion
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def consultar_soluciones():
    # Consulta 6: Soluciones aplicadas a los reportes y materiales utilizados
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT s.numero_solucion, s.folio, e.nombre_equipo, s.fecha_resolucion, s.tiempo_resolucion,
                   s.solucion_aplicada, s.observaciones_solucion
            FROM solucion s
            INNER JOIN reporte r ON r.folio = s.folio
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            ORDER BY s.fecha_resolucion DESC, s.numero_solucion DESC
            """
        )
        soluciones = cursor.fetchall()
        for sol in soluciones:
            cursor.execute(
                """
                SELECT m.nombre_material, sm.cantidad_usada
                FROM solucion_material sm
                INNER JOIN material m ON m.codigo_material = sm.codigo_material
                WHERE sm.numero_solucion = %s
                ORDER BY m.nombre_material
                """,
                (sol["numero_solucion"],),
            )
            sol["materiales"] = cursor.fetchall()
        cursor.close()
        return soluciones
    finally:
        cnx.close()
