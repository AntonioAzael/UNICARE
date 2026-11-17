from datetime import date
from conexion import conectar


def listar_solicitudes_disponibles():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.folio, r.fecha_registro, r.nombre_estado, e.nombre_equipo, ed.nombre_edificio, r.descripcion_reporte
            FROM reporte r
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            INNER JOIN edificio ed ON ed.no_edificio = e.no_edificio
            ORDER BY r.fecha_registro DESC, r.folio DESC
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_tipos_y_estados_orden():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT id_tipo_mantenimiento, nombre_tipo, descripcion_tipo FROM tipo_mantenimiento")
        tipos = cursor.fetchall()
        cursor.execute("SELECT nombre_estado, descripcion_estado FROM estado_orden")
        estados = cursor.fetchall()
        cursor.close()
        return tipos, estados
    finally:
        cnx.close()


def listar_ordenes():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ot.num_orden, ot.folio, ot.nombre_estado, ot.fecha_programada,
                   ed.nombre_edificio, e.nombre_equipo
            FROM orden_trabajo ot
            INNER JOIN reporte r ON r.folio = ot.folio
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            INNER JOIN edificio ed ON ed.no_edificio = e.no_edificio
            ORDER BY ot.fecha_creacion DESC, ot.num_orden DESC
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_tecnicos():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id_trabajador,
                   CONCAT_WS(' ', nombre, primer_apell, seg_apell) AS nombre_completo,
                   especialidad
            FROM trabajador_mantenimiento
            ORDER BY id_trabajador
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def _siguiente_num_orden(cursor, anio):
    prefijo = f"OT-{anio}-"
    cursor.execute(
        "SELECT num_orden FROM orden_trabajo WHERE num_orden LIKE %s ORDER BY num_orden DESC LIMIT 1",
        (f"{prefijo}%",),
    )
    ultimo = cursor.fetchone()
    if not ultimo:
        return f"{prefijo}0001"
    numero = int(ultimo["num_orden"].split("-")[-1]) + 1
    return f"{prefijo}{numero:04d}"


def registrar_orden_trabajo(
    folio,
    id_tipo_mantenimiento,
    fecha_programada,
    observaciones=None,
    costo_mano_obra=0.0,
    costo_materiales=0.0,
):
    # Registro 2: Registrar la orden de trabajo de una solicitud de mantenimiento
    hoy = date.today()
    obs = observaciones.strip() if observaciones and observaciones.strip() else None
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        num_orden = _siguiente_num_orden(cursor, hoy.year)
        cursor.execute(
            """
            INSERT INTO orden_trabajo (
                num_orden, folio, id_tipo_mantenimiento, nombre_estado,
                fecha_creacion, fecha_programada, fecha_inicio, fecha_fin,
                observaciones, costo_mano_obra, costo_materiales
            ) VALUES (%s, %s, %s, 'Creada', %s, %s, NULL, NULL, %s, %s, %s)
            """,
            (num_orden, folio, id_tipo_mantenimiento, hoy, fecha_programada, obs, costo_mano_obra, costo_materiales),
        )
        cursor.execute(
            "UPDATE reporte SET nombre_estado = 'En revision' WHERE folio = %s AND nombre_estado = 'Pendiente'",
            (folio,),
        )
        cnx.commit()
        cursor.close()
        return num_orden
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def asignar_tecnicos_orden(num_orden, asignaciones):
    # Registro 3: Asignar al menos 2 tecnicos a una orden de trabajo
    if len(asignaciones) < 2:
        raise ValueError("Debes asignar al menos 2 tecnicos a la orden de trabajo.")

    hoy = date.today()
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        for item in asignaciones:
            cursor.execute(
                """
                INSERT INTO asignacion_orden (num_orden, id_trabajador, fecha_asignacion, horas_asignadas, actividad_realizar)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    fecha_asignacion = VALUES(fecha_asignacion),
                    horas_asignadas = VALUES(horas_asignadas),
                    actividad_realizar = VALUES(actividad_realizar)
                """,
                (num_orden, item["id_trabajador"], hoy, item["horas"], item["actividad"]),
            )
        cursor.execute(
            "UPDATE orden_trabajo SET nombre_estado = 'En proceso', fecha_inicio = COALESCE(fecha_inicio, %s) WHERE num_orden = %s",
            (hoy, num_orden),
        )
        cursor.execute(
            """
            UPDATE reporte r
            INNER JOIN orden_trabajo ot ON ot.folio = r.folio
            SET r.nombre_estado = 'En proceso',
                r.id_trabajador = COALESCE(r.id_trabajador, %s)
            WHERE ot.num_orden = %s
            """,
            (asignaciones[0]["id_trabajador"], num_orden),
        )
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def registrar_actividades_orden(num_orden, actividades, finalizar_orden=False):
    # Registro 4: Registrar al menos dos actividades especificas para realizar en una orden de trabajo
    if len(actividades) < 2:
        raise ValueError("Debes registrar al menos 2 actividades especificas en la orden de trabajo.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        for act in actividades:
            cursor.execute(
                """
                INSERT INTO actividad_orden (num_orden, descripcion_actividad, fecha_actividad, resultado)
                VALUES (%s, %s, %s, %s)
                """,
                (num_orden, act["descripcion"], act["fecha"], act["resultado"]),
            )
        if finalizar_orden:
            hoy = date.today()
            cursor.execute(
                """
                UPDATE orden_trabajo
                SET nombre_estado = 'Finalizada',
                    fecha_inicio = COALESCE(fecha_inicio, %s),
                    fecha_fin = %s
                WHERE num_orden = %s
                """,
                (hoy, hoy, num_orden),
            )
            cursor.execute(
                """
                UPDATE reporte r
                INNER JOIN orden_trabajo ot ON ot.folio = r.folio
                SET r.nombre_estado = 'Solucionado'
                WHERE ot.num_orden = %s
                """,
                (num_orden,),
            )
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def consultar_actividades_orden(num_orden=None):
    # Consulta 2: Actividades especificas realizadas en una orden de trabajo
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT num_orden, descripcion_actividad, fecha_actividad, resultado
            FROM actividad_orden
        """
        params = []
        if num_orden:
            sql += " WHERE num_orden = %s"
            params.append(num_orden)
        sql += " ORDER BY num_orden, fecha_actividad, id_actividad"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_ordenes_edificio(no_edificio=None):
    # Consulta 3: Informacion de una orden de trabajo para una solicitud de mantenimiento a un edificio
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                ot.num_orden,
                ot.folio,
                ed.nombre_edificio,
                tm.descripcion_tipo,
                eo.descripcion_estado,
                ot.fecha_creacion,
                ot.fecha_programada,
                ot.fecha_inicio,
                ot.fecha_fin,
                ot.observaciones,
                ot.costo_mano_obra,
                ot.costo_materiales
            FROM orden_trabajo ot
            INNER JOIN reporte r ON r.folio = ot.folio
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            INNER JOIN edificio ed ON ed.no_edificio = e.no_edificio
            INNER JOIN tipo_mantenimiento tm ON tm.id_tipo_mantenimiento = ot.id_tipo_mantenimiento
            INNER JOIN estado_orden eo ON eo.nombre_estado = ot.nombre_estado
        """
        params = []
        if no_edificio:
            sql += " WHERE ed.no_edificio = %s"
            params.append(no_edificio)
        sql += " ORDER BY ot.fecha_creacion DESC, ot.num_orden DESC"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_tecnicos_orden(num_orden=None):
    # Consulta 4: Tecnicos asignados a una orden de trabajo
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                ao.num_orden,
                CONCAT_WS(' ', t.nombre, t.primer_apell, t.seg_apell) AS nombre_tecnico,
                ao.fecha_asignacion,
                ao.horas_asignadas,
                ao.actividad_realizar
            FROM asignacion_orden ao
            INNER JOIN trabajador_mantenimiento t ON t.id_trabajador = ao.id_trabajador
        """
        params = []
        if num_orden:
            sql += " WHERE ao.num_orden = %s"
            params.append(num_orden)
        sql += " ORDER BY ao.num_orden, ao.fecha_asignacion, t.id_trabajador"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()
