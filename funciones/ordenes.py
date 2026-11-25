from datetime import date
from conexion import conectar
from funciones.solicitudes import SQL_UBICACION

# Nota: "orden de trabajo" es la entidad MANTENIMIENTO del DER (clave_mantenimiento).


def listar_solicitudes_disponibles():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT r.folio, r.fecha_registro, r.nombre_estado, r.descripcion_reporte,
                   r.nombre_categoria, r.nombre_prioridad, r.codigo_inventario, r.observaciones,
                   COALESCE(e.nombre_equipo, 'Sin equipo') AS nombre_equipo,
                   ed.nombre_edificio,
                   {SQL_UBICACION} AS ubicacion
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            LEFT JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            WHERE r.nombre_estado NOT IN ('Solucionado', 'Cancelado')
              -- Oculta los reportes que ya tienen una orden de trabajo vigente (no cancelada)
              AND NOT EXISTS (
                  SELECT 1 FROM mantenimiento m
                  WHERE m.folio = r.folio AND m.nombre_estado <> 'Cancelado'
              )
            ORDER BY r.fecha_registro DESC, r.folio DESC
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_tipos_mantenimiento():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT codigo_tipo, nombre_tipo, descripcion_tipo FROM tipo_mantenimiento")
        tipos = cursor.fetchall()
        cursor.close()
        return tipos
    finally:
        cnx.close()


def listar_ordenes():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT m.clave_mantenimiento, m.folio, m.nombre_estado, m.fecha_programada,
                   ed.nombre_edificio, COALESCE(e.nombre_equipo, 'Sin equipo') AS nombre_equipo
            FROM mantenimiento m
            INNER JOIN reporte r ON r.folio = m.folio
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            LEFT JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            ORDER BY m.fecha_creacion DESC, m.clave_mantenimiento DESC
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
            SELECT numero_empleado,
                   CONCAT_WS(' ', nombre, primer_apellido, segundo_apellido) AS nombre_completo,
                   especialidad
            FROM trabajador_mantenimiento
            ORDER BY numero_empleado
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def _siguiente_clave(cursor, anio):
    prefijo = f"MNT-{anio}-"
    cursor.execute(
        "SELECT clave_mantenimiento FROM mantenimiento WHERE clave_mantenimiento LIKE %s ORDER BY clave_mantenimiento DESC LIMIT 1",
        (f"{prefijo}%",),
    )
    ultimo = cursor.fetchone()
    if not ultimo:
        return f"{prefijo}0001"
    numero = int(ultimo["clave_mantenimiento"].split("-")[-1]) + 1
    return f"{prefijo}{numero:04d}"


def registrar_orden_trabajo(
    folio,
    codigo_tipo,
    fecha_programada,
    descripcion_trabajo,
    observaciones=None,
    costo_mano_obra=0.0,
    costo_materiales=0.0,
    nombre_categoria=None,
    nombre_prioridad=None,
    codigo_inventario=None,
    observaciones_reporte=None,
):
    # Registro 2: Registrar la orden de trabajo (mantenimiento) de una solicitud.
    # En la misma transaccion mantenimiento completa en el reporte la categoria, la prioridad
    # y las observaciones (si aun no las tiene) y, opcionalmente, liga el equipo afectado.
    descripcion = descripcion_trabajo.strip()
    if not descripcion:
        raise ValueError("La descripcion del trabajo no puede ir vacia.")
    obs_reporte = observaciones_reporte.strip() if observaciones_reporte and observaciones_reporte.strip() else None
    if obs_reporte and len(obs_reporte) > 250:
        raise ValueError("Las observaciones del reporte no pueden pasar de 250 caracteres.")

    hoy = date.today()
    obs = observaciones.strip() if observaciones and observaciones.strip() else None
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        # Respaldo del filtro de listar_solicitudes_disponibles: una orden vigente por reporte
        cursor.execute(
            "SELECT clave_mantenimiento FROM mantenimiento WHERE folio = %s AND nombre_estado <> 'Cancelado'",
            (folio,),
        )
        vigente = cursor.fetchone()
        if vigente:
            raise ValueError(
                f"La solicitud {folio} ya tiene la orden de trabajo {vigente['clave_mantenimiento']}."
            )

        cursor.execute(
            "SELECT nombre_categoria, nombre_prioridad, codigo_inventario FROM reporte WHERE folio = %s",
            (folio,),
        )
        rep = cursor.fetchone()
        if not rep:
            raise ValueError(f"La solicitud {folio} ya no existe.")
        if not (rep["nombre_categoria"] or nombre_categoria) or not (rep["nombre_prioridad"] or nombre_prioridad):
            raise ValueError("Debes asignar la categoria y la prioridad de la solicitud.")
        # Solo se llenan los datos que faltan; lo que ya tenia el reporte se conserva
        cursor.execute(
            """
            UPDATE reporte
            SET nombre_categoria = COALESCE(nombre_categoria, %s),
                nombre_prioridad = COALESCE(nombre_prioridad, %s),
                codigo_inventario = COALESCE(codigo_inventario, %s),
                observaciones = COALESCE(observaciones, %s)
            WHERE folio = %s
            """,
            (nombre_categoria, nombre_prioridad, codigo_inventario, obs_reporte, folio),
        )
        if codigo_inventario and not rep["codigo_inventario"]:
            cursor.execute(
                "UPDATE equipo_instalacion SET necesita_reparacion = 1 WHERE codigo_inventario = %s",
                (codigo_inventario,),
            )

        clave = _siguiente_clave(cursor, hoy.year)
        cursor.execute(
            """
            INSERT INTO mantenimiento (
                clave_mantenimiento, fecha_creacion, fecha_programada, fecha_inicio, fecha_fin,
                descripcion_trabajo, observaciones, costo_mano_obra, costo_materiales,
                codigo_tipo, folio, nombre_estado
            ) VALUES (%s, %s, %s, NULL, NULL, %s, %s, %s, %s, %s, %s, 'Pendiente')
            """,
            (clave, hoy, fecha_programada, descripcion, obs, costo_mano_obra, costo_materiales,
             codigo_tipo, folio),
        )
        cursor.execute(
            "UPDATE reporte SET nombre_estado = 'En revision' WHERE folio = %s AND nombre_estado = 'Pendiente'",
            (folio,),
        )
        cnx.commit()
        cursor.close()
        return clave
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def asignar_tecnicos_orden(clave_mantenimiento, asignaciones):
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
                "SELECT 1 FROM mantenimiento_trabajador WHERE clave_mantenimiento = %s AND numero_empleado = %s",
                (clave_mantenimiento, item["numero_empleado"]),
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE mantenimiento_trabajador
                    SET fecha_asignacion = %s, horas_asignadas = %s, actividad_asignada = %s
                    WHERE clave_mantenimiento = %s AND numero_empleado = %s
                    """,
                    (hoy, item["horas"], item["actividad"], clave_mantenimiento, item["numero_empleado"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO mantenimiento_trabajador
                        (clave_mantenimiento, numero_empleado, fecha_asignacion, horas_asignadas, actividad_asignada)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (clave_mantenimiento, item["numero_empleado"], hoy, item["horas"], item["actividad"]),
                )
        cursor.execute(
            "UPDATE mantenimiento SET nombre_estado = 'En proceso', fecha_inicio = COALESCE(fecha_inicio, %s) "
            "WHERE clave_mantenimiento = %s",
            (hoy, clave_mantenimiento),
        )
        cursor.execute(
            "UPDATE reporte SET nombre_estado = 'En proceso' "
            "WHERE folio = (SELECT folio FROM mantenimiento WHERE clave_mantenimiento = %s)",
            (clave_mantenimiento,),
        )
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def registrar_actividades_orden(clave_mantenimiento, actividades, finalizar_orden=False):
    # Registro 4: Registrar al menos dos actividades especificas de una orden de trabajo
    # Cada actividad se guarda en HISTORIAL_MANTENIMIENTO
    if len(actividades) < 2:
        raise ValueError("Debes registrar al menos 2 actividades especificas en la orden de trabajo.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        for act in actividades:
            cursor.execute(
                """
                INSERT INTO historial_mantenimiento
                    (fecha_historial, descripcion_historial, resultado, observaciones_historial, clave_mantenimiento)
                VALUES (%s, %s, %s, NULL, %s)
                """,
                (act["fecha"], act["descripcion"], act["resultado"], clave_mantenimiento),
            )
        if finalizar_orden:
            hoy = date.today()
            cursor.execute(
                """
                UPDATE mantenimiento
                SET nombre_estado = 'Solucionado',
                    fecha_inicio = COALESCE(fecha_inicio, %s),
                    fecha_fin = %s
                WHERE clave_mantenimiento = %s
                """,
                (hoy, hoy, clave_mantenimiento),
            )
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def consultar_actividades_orden(clave_mantenimiento=None):
    # Consulta 2: Actividades especificas realizadas en una orden de trabajo
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT clave_mantenimiento, descripcion_historial, fecha_historial, resultado
            FROM historial_mantenimiento
        """
        params = []
        if clave_mantenimiento:
            sql += " WHERE clave_mantenimiento = %s"
            params.append(clave_mantenimiento)
        sql += " ORDER BY clave_mantenimiento, fecha_historial, consecutivo_historial"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_ordenes_edificio(clave_edificio=None):
    # Consulta 3: Informacion de una orden de trabajo para una solicitud de mantenimiento a un edificio
    # El edificio, piso, area y lugar se toman del reporte
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                m.clave_mantenimiento,
                m.folio,
                ed.nombre_edificio,
                r.piso,
                r.area,
                r.lugar,
                tm.descripcion_tipo,
                es.descripcion_estado,
                m.fecha_creacion,
                m.fecha_programada,
                m.fecha_inicio,
                m.fecha_fin,
                m.descripcion_trabajo,
                m.observaciones,
                m.costo_mano_obra,
                m.costo_materiales
            FROM mantenimiento m
            INNER JOIN reporte r ON r.folio = m.folio
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            INNER JOIN tipo_mantenimiento tm ON tm.codigo_tipo = m.codigo_tipo
            INNER JOIN estado es ON es.nombre_estado = m.nombre_estado
        """
        params = []
        if clave_edificio:
            sql += " WHERE r.clave_edificio = %s"
            params.append(clave_edificio)
        sql += " ORDER BY m.fecha_creacion DESC, m.clave_mantenimiento DESC"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_tecnicos_orden(clave_mantenimiento=None):
    # Consulta 4: Tecnicos asignados a una orden de trabajo
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                mt.clave_mantenimiento,
                CONCAT_WS(' ', t.nombre, t.primer_apellido, t.segundo_apellido) AS nombre_tecnico,
                mt.fecha_asignacion,
                mt.horas_asignadas,
                mt.actividad_asignada
            FROM mantenimiento_trabajador mt
            INNER JOIN trabajador_mantenimiento t ON t.numero_empleado = mt.numero_empleado
        """
        params = []
        if clave_mantenimiento:
            sql += " WHERE mt.clave_mantenimiento = %s"
            params.append(clave_mantenimiento)
        sql += " ORDER BY mt.clave_mantenimiento, mt.fecha_asignacion, t.numero_empleado"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()
