from datetime import date
from conexion import conectar


def listar_edificios():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT no_edificio, nombre_edificio FROM edificio ORDER BY nombre_edificio")
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_equipos_por_edificio(no_edificio):
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT codigo_inventario, nombre_equipo, piso, salon
            FROM equipo_instalacion
            WHERE no_edificio = %s
            ORDER BY salon, codigo_inventario
            """,
            (no_edificio,),
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def _siguiente_num_plan(cursor, anio):
    prefijo = f"PLAN-{anio}-"
    cursor.execute(
        "SELECT num_plan FROM plan_mantenimiento WHERE num_plan LIKE %s ORDER BY num_plan DESC LIMIT 1",
        (f"{prefijo}%",),
    )
    ultimo = cursor.fetchone()
    if not ultimo:
        return f"{prefijo}0001"
    numero = int(ultimo["num_plan"].split("-")[-1]) + 1
    return f"{prefijo}{numero:04d}"


def registrar_plan_preventivo(
    nombre_plan,
    codigo_inventario,
    descripcion_plan,
    frecuencia,
    duracion_estimada_horas,
    estado_plan="Activo",
):
    # Registro 5: Registrar un plan de mantenimiento preventivo para un equipo
    # El edificio del plan se obtiene a partir del equipo (EQUIPO CONTIENE EDIFICIO)
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        num_plan = _siguiente_num_plan(cursor, date.today().year)
        cursor.execute(
            """
            INSERT INTO plan_mantenimiento (
                num_plan, nombre_plan, descripcion_plan, frecuencia,
                duracion_estimada_horas, estado_plan, codigo_inventario
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                num_plan,
                nombre_plan.strip(),
                descripcion_plan.strip(),
                frecuencia.strip(),
                duracion_estimada_horas,
                estado_plan,
                codigo_inventario,
            ),
        )
        cnx.commit()
        cursor.close()
        return num_plan
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def consultar_planes_edificio(no_edificio=None):
    # Consulta 5: Plan de mantenimiento preventivo para una instalacion (edificio)
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                pm.num_plan,
                pm.nombre_plan,
                ed.nombre_edificio,
                e.nombre_equipo,
                pm.descripcion_plan,
                pm.frecuencia,
                pm.duracion_estimada_horas,
                pm.estado_plan
            FROM plan_mantenimiento pm
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = pm.codigo_inventario
            INNER JOIN edificio ed ON ed.no_edificio = e.no_edificio
        """
        params = []
        if no_edificio:
            sql += " WHERE ed.no_edificio = %s"
            params.append(no_edificio)
        sql += " ORDER BY pm.num_plan"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()
