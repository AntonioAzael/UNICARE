from datetime import date
from conexion import conectar
from funciones.solicitudes import SQL_EQUIPO_AFECTADO, SQL_UBICACION, normalizar_folio

# Nota: "orden de trabajo" es la entidad MANTENIMIENTO del DER (clave_mantenimiento).


def listar_solicitudes_disponibles():
    # Solicitudes a las que se les puede crear una orden: Pendiente y sin orden vigente
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT r.folio, r.fecha_registro, r.nombre_estado, r.descripcion_reporte,
                   r.nombre_categoria, r.nombre_prioridad, r.observaciones,
                   {SQL_EQUIPO_AFECTADO} AS equipo_afectado,
                   ed.nombre_edificio,
                   {SQL_UBICACION} AS ubicacion
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            WHERE r.nombre_estado = 'Pendiente'
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


# ---------------------------------------------------------------------------
# Gestion del catalogo de tipos de mantenimiento (solo supervisores)
# ---------------------------------------------------------------------------

MAX_CODIGO_TIPO = 10
MAX_NOMBRE_TIPO = 30
MAX_DESCRIPCION_TIPO = 150


def listar_tipos_gestion():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT tm.codigo_tipo, tm.nombre_tipo, tm.descripcion_tipo, COUNT(m.clave_mantenimiento) AS ordenes
            FROM tipo_mantenimiento tm
            LEFT JOIN mantenimiento m ON m.codigo_tipo = tm.codigo_tipo
            GROUP BY tm.codigo_tipo, tm.nombre_tipo, tm.descripcion_tipo
            ORDER BY tm.nombre_tipo
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def existe_tipo(codigo_tipo=None, nombre_tipo=None):
    # Revisa si ya hay un tipo con ese codigo o con ese nombre
    cnx = conectar()
    try:
        cursor = cnx.cursor()
        if codigo_tipo is not None:
            cursor.execute("SELECT 1 FROM tipo_mantenimiento WHERE codigo_tipo = %s", (codigo_tipo.strip().upper(),))
        else:
            cursor.execute("SELECT 1 FROM tipo_mantenimiento WHERE nombre_tipo = %s", (nombre_tipo.strip(),))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe
    finally:
        cnx.close()


def registrar_tipo_mantenimiento(codigo_tipo, nombre_tipo, descripcion_tipo):
    codigo = codigo_tipo.strip().upper()
    nombre = nombre_tipo.strip()
    descripcion = descripcion_tipo.strip()
    if not codigo or not nombre or not descripcion:
        raise ValueError("El codigo, el nombre y la descripcion del tipo son obligatorios.")
    if len(codigo) > MAX_CODIGO_TIPO:
        raise ValueError(f"El codigo no puede pasar de {MAX_CODIGO_TIPO} caracteres.")
    if len(nombre) > MAX_NOMBRE_TIPO:
        raise ValueError(f"El nombre no puede pasar de {MAX_NOMBRE_TIPO} caracteres.")
    if len(descripcion) > MAX_DESCRIPCION_TIPO:
        raise ValueError(f"La descripcion no puede pasar de {MAX_DESCRIPCION_TIPO} caracteres.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        cursor.execute("SELECT 1 FROM tipo_mantenimiento WHERE codigo_tipo = %s", (codigo,))
        if cursor.fetchone():
            raise ValueError(f"Ya existe un tipo de mantenimiento con el codigo {codigo}.")
        cursor.execute("SELECT 1 FROM tipo_mantenimiento WHERE nombre_tipo = %s", (nombre,))
        if cursor.fetchone():
            raise ValueError(f"Ya existe el tipo de mantenimiento {nombre}.")
        cursor.execute(
            "INSERT INTO tipo_mantenimiento (codigo_tipo, nombre_tipo, descripcion_tipo) VALUES (%s, %s, %s)",
            (codigo, nombre, descripcion),
        )
        cnx.commit()
        cursor.close()
        return codigo
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def eliminar_tipo_mantenimiento(codigo_tipo):
    # Baja de un tipo. Si alguna orden de trabajo lo usa no se borra para conservar el historial.
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        cursor.execute("SELECT nombre_tipo FROM tipo_mantenimiento WHERE codigo_tipo = %s", (codigo_tipo,))
        tipo = cursor.fetchone()
        if not tipo:
            raise ValueError("El tipo de mantenimiento ya no existe.")
        cursor.execute(
            "SELECT clave_mantenimiento FROM mantenimiento WHERE codigo_tipo = %s ORDER BY clave_mantenimiento",
            (codigo_tipo,),
        )
        claves = [fila[0] for fila in cursor.fetchall()]
        if claves:
            raise ValueError(
                f"El tipo {tipo[0]} se usa en las ordenes {', '.join(claves)} y no puede eliminarse."
            )
        cursor.execute("DELETE FROM tipo_mantenimiento WHERE codigo_tipo = %s", (codigo_tipo,))
        cnx.commit()
        cursor.close()
        return tipo[0]
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def listar_ordenes(estados=None, numero_empleado=None, min_tecnicos=0):
    # Ordenes de trabajo con su ubicacion, equipo afectado y numero de tecnicos.
    # estados: solo esos estados; numero_empleado: solo donde ese tecnico esta asignado;
    # min_tecnicos: solo las que tienen al menos esa cantidad de tecnicos.
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = f"""
            SELECT m.clave_mantenimiento, m.folio, m.nombre_estado, m.fecha_programada,
                   ed.nombre_edificio, {SQL_UBICACION} AS ubicacion,
                   {SQL_EQUIPO_AFECTADO} AS equipo_afectado,
                   (SELECT COUNT(*) FROM mantenimiento_trabajador mt
                    WHERE mt.clave_mantenimiento = m.clave_mantenimiento) AS tecnicos
            FROM mantenimiento m
            INNER JOIN reporte r ON r.folio = m.folio
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            WHERE 1 = 1
        """
        params = []
        if estados:
            sql += " AND m.nombre_estado IN (" + ", ".join(["%s"] * len(estados)) + ")"
            params.extend(estados)
        if numero_empleado is not None:
            sql += (" AND EXISTS (SELECT 1 FROM mantenimiento_trabajador mt2"
                    " WHERE mt2.clave_mantenimiento = m.clave_mantenimiento AND mt2.numero_empleado = %s)")
            params.append(numero_empleado)
        if min_tecnicos:
            sql += (" AND (SELECT COUNT(*) FROM mantenimiento_trabajador mt3"
                    " WHERE mt3.clave_mantenimiento = m.clave_mantenimiento) >= %s")
            params.append(min_tecnicos)
        sql += " ORDER BY m.fecha_creacion DESC, m.clave_mantenimiento DESC"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_mis_ordenes(numero_empleado):
    # Ordenes donde el tecnico esta asignado (opcion "Mis ordenes asignadas")
    return listar_ordenes(numero_empleado=numero_empleado)


def listar_tecnicos(excluir_orden=None):
    # Tecnicos para asignar; con excluir_orden no aparecen los que ya estan en esa orden
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT numero_empleado,
                   CONCAT_WS(' ', nombre, primer_apellido, segundo_apellido) AS nombre_completo,
                   especialidad
            FROM trabajador_mantenimiento
        """
        params = []
        if excluir_orden:
            sql += (" WHERE numero_empleado NOT IN (SELECT numero_empleado FROM mantenimiento_trabajador"
                    " WHERE clave_mantenimiento = %s)")
            params.append(excluir_orden)
        sql += " ORDER BY numero_empleado"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def _orden_bloqueada(cursor, clave_mantenimiento):
    # Lee la orden y la bloquea hasta el fin de la transaccion
    cursor.execute(
        "SELECT clave_mantenimiento, folio, nombre_estado FROM mantenimiento WHERE clave_mantenimiento = %s FOR UPDATE",
        (clave_mantenimiento,),
    )
    orden = cursor.fetchone()
    if not orden:
        raise ValueError(f"No existe la orden de trabajo {clave_mantenimiento}.")
    return orden


def _contar_tecnicos(cursor, clave_mantenimiento):
    cursor.execute(
        "SELECT COUNT(*) AS total FROM mantenimiento_trabajador WHERE clave_mantenimiento = %s",
        (clave_mantenimiento,),
    )
    return cursor.fetchone()["total"]


def verificar_asignado(cursor, clave_mantenimiento, numero_empleado):
    # Un tecnico solo puede registrar en las ordenes donde esta asignado
    cursor.execute(
        "SELECT 1 FROM mantenimiento_trabajador WHERE clave_mantenimiento = %s AND numero_empleado = %s",
        (clave_mantenimiento, numero_empleado),
    )
    if not cursor.fetchone():
        raise ValueError(f"No estas asignado a la orden de trabajo {clave_mantenimiento}.")


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
    observaciones_reporte=None,
):
    # Registro 2 (supervisor): orden de trabajo de una solicitud Pendiente.
    # En la misma transaccion el supervisor asigna al reporte la categoria y la prioridad,
    # guarda las observaciones del reporte si no tenia y el reporte pasa a En revision.
    folio = normalizar_folio(folio)
    descripcion = descripcion_trabajo.strip()
    if not descripcion:
        raise ValueError("La descripcion del trabajo no puede ir vacia.")
    if not nombre_categoria or not nombre_prioridad:
        raise ValueError("Debes asignar la categoria y la prioridad de la solicitud.")
    obs_reporte = observaciones_reporte.strip() if observaciones_reporte and observaciones_reporte.strip() else None
    if obs_reporte and len(obs_reporte) > 250:
        raise ValueError("Las observaciones del reporte no pueden pasar de 250 caracteres.")

    hoy = date.today()
    obs = observaciones.strip() if observaciones and observaciones.strip() else None
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT nombre_estado FROM reporte WHERE folio = %s FOR UPDATE", (folio,))
        rep = cursor.fetchone()
        if not rep:
            raise ValueError(f"No existe el reporte {folio}.")
        if rep["nombre_estado"] != "Pendiente":
            raise ValueError(
                f"La solicitud {folio} esta en estado {rep['nombre_estado']}; solo se crea orden a solicitudes Pendiente."
            )
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
            """
            UPDATE reporte
            SET nombre_categoria = %s,
                nombre_prioridad = %s,
                observaciones = COALESCE(observaciones, %s),
                nombre_estado = 'En revision'
            WHERE folio = %s
            """,
            (nombre_categoria, nombre_prioridad, obs_reporte, folio),
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
        cnx.commit()
        cursor.close()
        return clave
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def asignar_tecnicos_orden(clave_mantenimiento, asignaciones):
    # Registro 3 (supervisor): tecnicos de una orden Pendiente o En proceso.
    # La orden debe quedar con al menos 2 tecnicos; la orden y el reporte pasan a En proceso.
    if not asignaciones:
        raise ValueError("Debes asignar al menos un tecnico.")

    hoy = date.today()
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        orden = _orden_bloqueada(cursor, clave_mantenimiento)
        if orden["nombre_estado"] not in ("Pendiente", "En proceso"):
            raise ValueError(
                f"La orden {clave_mantenimiento} esta en estado {orden['nombre_estado']}; "
                "solo se asignan tecnicos a ordenes Pendiente o En proceso."
            )
        for item in asignaciones:
            cursor.execute(
                "SELECT 1 FROM mantenimiento_trabajador WHERE clave_mantenimiento = %s AND numero_empleado = %s",
                (clave_mantenimiento, item["numero_empleado"]),
            )
            if cursor.fetchone():
                raise ValueError("Uno de los tecnicos ya estaba asignado a esta orden.")
            cursor.execute(
                """
                INSERT INTO mantenimiento_trabajador
                    (clave_mantenimiento, numero_empleado, fecha_asignacion, horas_asignadas, actividad_asignada)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (clave_mantenimiento, item["numero_empleado"], hoy, item["horas"], item["actividad"]),
            )
        if _contar_tecnicos(cursor, clave_mantenimiento) < 2:
            raise ValueError("La orden de trabajo debe quedar con al menos 2 tecnicos asignados.")
        cursor.execute(
            "UPDATE mantenimiento SET nombre_estado = 'En proceso', fecha_inicio = COALESCE(fecha_inicio, %s) "
            "WHERE clave_mantenimiento = %s",
            (hoy, clave_mantenimiento),
        )
        cursor.execute("UPDATE reporte SET nombre_estado = 'En proceso' WHERE folio = %s", (orden["folio"],))
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def registrar_actividades_orden(clave_mantenimiento, actividades, numero_empleado=None, es_supervisor=False):
    # Registro 4: al menos dos actividades en una orden En proceso con al menos 2 tecnicos.
    # Un tecnico solo registra en ordenes donde esta asignado; el supervisor en cualquiera.
    # Cada actividad se guarda en HISTORIAL_MANTENIMIENTO.
    if len(actividades) < 2:
        raise ValueError("Debes registrar al menos 2 actividades especificas en la orden de trabajo.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        orden = _orden_bloqueada(cursor, clave_mantenimiento)
        if orden["nombre_estado"] != "En proceso":
            raise ValueError(
                f"La orden {clave_mantenimiento} esta en estado {orden['nombre_estado']}; "
                "solo se registran actividades en ordenes En proceso."
            )
        if _contar_tecnicos(cursor, clave_mantenimiento) < 2:
            raise ValueError(f"La orden {clave_mantenimiento} necesita al menos 2 tecnicos asignados.")
        if not es_supervisor:
            verificar_asignado(cursor, clave_mantenimiento, numero_empleado)
        for act in actividades:
            cursor.execute(
                """
                INSERT INTO historial_mantenimiento
                    (fecha_historial, descripcion_historial, resultado, observaciones_historial, clave_mantenimiento)
                VALUES (%s, %s, %s, NULL, %s)
                """,
                (act["fecha"], act["descripcion"], act["resultado"], clave_mantenimiento),
            )
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def cancelar_orden(clave_mantenimiento):
    # Supervisor: cancela una orden Pendiente o En proceso. El reporte regresa a Pendiente
    # (conserva su categoria y prioridad) para que se le pueda crear otra orden.
    hoy = date.today()
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        orden = _orden_bloqueada(cursor, clave_mantenimiento)
        if orden["nombre_estado"] not in ("Pendiente", "En proceso"):
            raise ValueError(
                f"La orden {clave_mantenimiento} esta en estado {orden['nombre_estado']}; "
                "solo se cancelan ordenes Pendiente o En proceso."
            )
        cursor.execute(
            "UPDATE mantenimiento SET nombre_estado = 'Cancelado', fecha_fin = %s WHERE clave_mantenimiento = %s",
            (hoy, clave_mantenimiento),
        )
        cursor.execute("UPDATE reporte SET nombre_estado = 'Pendiente' WHERE folio = %s", (orden["folio"],))
        cnx.commit()
        cursor.close()
        return orden["folio"]
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
