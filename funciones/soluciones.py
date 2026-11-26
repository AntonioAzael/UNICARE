from datetime import date
from conexion import conectar
from funciones.ordenes import verificar_asignado
from funciones.solicitudes import SQL_EQUIPO_AFECTADO, SQL_UBICACION, normalizar_folio


def listar_reportes_sin_solucion(numero_empleado=None, es_supervisor=True):
    # Reportes que pueden recibir solucion: su orden vigente esta En proceso y aun no tienen solucion
    # (REPORTE 1:1 SOLUCION). Para un tecnico, solo los de ordenes donde esta asignado.
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = f"""
            SELECT r.folio, r.fecha_registro, r.nombre_estado, r.descripcion_reporte,
                   m.clave_mantenimiento,
                   {SQL_EQUIPO_AFECTADO} AS equipo_afectado,
                   {SQL_UBICACION} AS ubicacion
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            INNER JOIN mantenimiento m ON m.folio = r.folio AND m.nombre_estado = 'En proceso'
            LEFT JOIN solucion s ON s.folio = r.folio
            WHERE s.numero_solucion IS NULL
        """
        params = []
        if not es_supervisor:
            sql += (" AND EXISTS (SELECT 1 FROM mantenimiento_trabajador mt"
                    " WHERE mt.clave_mantenimiento = m.clave_mantenimiento AND mt.numero_empleado = %s)")
            params.append(numero_empleado)
        sql += " ORDER BY r.fecha_registro DESC, r.folio DESC"
        cursor.execute(sql, tuple(params))
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


def registrar_solucion(folio, tiempo_resolucion, solucion_aplicada, observaciones=None, materiales=None,
                       numero_empleado=None, es_supervisor=False):
    # Registro 6: solucion de un reporte con su orden vigente En proceso y los materiales utilizados.
    # En la misma transaccion la orden pasa a Solucionado (fecha_fin = hoy) y el reporte a Solucionado.
    # materiales: lista de {"codigo_material": ..., "cantidad": ...}
    folio = normalizar_folio(folio)
    texto = solucion_aplicada.strip()
    if not texto:
        raise ValueError("La solucion aplicada no puede ir vacia.")
    if tiempo_resolucion <= 0:
        raise ValueError("El tiempo de resolucion debe ser mayor a cero.")

    materiales = materiales or []
    obs = observaciones.strip() if observaciones and observaciones.strip() else None
    hoy = date.today()
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("SELECT 1 FROM reporte WHERE folio = %s FOR UPDATE", (folio,))
        if not cursor.fetchone():
            raise ValueError(f"No existe el reporte {folio}.")
        cursor.execute("SELECT 1 FROM solucion WHERE folio = %s", (folio,))
        if cursor.fetchone():
            raise ValueError("Ese reporte ya tiene una solucion registrada.")
        cursor.execute(
            "SELECT clave_mantenimiento FROM mantenimiento "
            "WHERE folio = %s AND nombre_estado = 'En proceso' FOR UPDATE",
            (folio,),
        )
        orden = cursor.fetchone()
        if not orden:
            raise ValueError(
                f"El reporte {folio} no tiene una orden de trabajo En proceso; primero se crea la orden y se asignan tecnicos."
            )
        if not es_supervisor:
            verificar_asignado(cursor, orden["clave_mantenimiento"], numero_empleado)

        cursor.execute(
            """
            INSERT INTO solucion (fecha_resolucion, tiempo_resolucion, solucion_aplicada, observaciones_solucion, folio)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (hoy, tiempo_resolucion, texto, obs, folio),
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

        cursor.execute(
            """
            UPDATE mantenimiento
            SET nombre_estado = 'Solucionado', fecha_inicio = COALESCE(fecha_inicio, %s), fecha_fin = %s
            WHERE clave_mantenimiento = %s
            """,
            (hoy, hoy, orden["clave_mantenimiento"]),
        )
        cursor.execute("UPDATE reporte SET nombre_estado = 'Solucionado' WHERE folio = %s", (folio,))
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
            f"""
            SELECT s.numero_solucion, s.folio, {SQL_EQUIPO_AFECTADO} AS equipo_afectado,
                   s.fecha_resolucion, s.tiempo_resolucion, s.solucion_aplicada, s.observaciones_solucion
            FROM solucion s
            INNER JOIN reporte r ON r.folio = s.folio
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
