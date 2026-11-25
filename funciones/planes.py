from datetime import date
from conexion import conectar
from funciones.solicitudes import AREAS_POR_PISO, EDIFICIO_SISTEMA, PISOS

# Largo maximo de cada dato de EQUIPO_INSTALACION (igual que en el script de tablas)
MAX_CODIGO_EQUIPO = 15
MAX_NOMBRE_EQUIPO = 60
MAX_TIPO_EQUIPO = 40
MAX_SALON = 20


def listar_edificios():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT clave_edificio, nombre_edificio FROM edificio ORDER BY nombre_edificio")
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_equipos_por_edificio(clave_edificio):
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT codigo_inventario, nombre_equipo, piso, salon
            FROM equipo_instalacion
            WHERE clave_edificio = %s
            ORDER BY salon, codigo_inventario
            """,
            (clave_edificio,),
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def _siguiente_clave_plan(cursor, anio):
    prefijo = f"PLAN-{anio}-"
    cursor.execute(
        "SELECT clave_plan FROM plan_mantenimiento WHERE clave_plan LIKE %s ORDER BY clave_plan DESC LIMIT 1",
        (f"{prefijo}%",),
    )
    ultimo = cursor.fetchone()
    if not ultimo:
        return f"{prefijo}0001"
    numero = int(ultimo["clave_plan"].split("-")[-1]) + 1
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
        clave_plan = _siguiente_clave_plan(cursor, date.today().year)
        cursor.execute(
            """
            INSERT INTO plan_mantenimiento (
                clave_plan, nombre_plan, descripcion_plan, frecuencia,
                duracion_estimada_horas, estado_plan, codigo_inventario
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                clave_plan,
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
        return clave_plan
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def consultar_planes_edificio(clave_edificio=None):
    # Consulta 5: Plan de mantenimiento preventivo para una instalacion (edificio)
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                pm.clave_plan,
                pm.nombre_plan,
                ed.nombre_edificio,
                e.nombre_equipo,
                pm.descripcion_plan,
                pm.frecuencia,
                pm.duracion_estimada_horas,
                pm.estado_plan
            FROM plan_mantenimiento pm
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = pm.codigo_inventario
            INNER JOIN edificio ed ON ed.clave_edificio = e.clave_edificio
        """
        params = []
        if clave_edificio:
            sql += " WHERE ed.clave_edificio = %s"
            params.append(clave_edificio)
        sql += " ORDER BY pm.clave_plan"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


# ---------------------------------------------------------------------------
# Gestion de equipos (solo supervisores). Todos los equipos son de Docencia 1.
# ---------------------------------------------------------------------------

def listar_equipos():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT e.codigo_inventario, e.nombre_equipo, e.tipo_equipo_instalacion, e.piso, e.area,
                   e.salon, e.necesita_reparacion,
                   (SELECT COUNT(*) FROM reporte r WHERE r.codigo_inventario = e.codigo_inventario) AS reportes,
                   (SELECT COUNT(*) FROM plan_mantenimiento pm WHERE pm.codigo_inventario = e.codigo_inventario) AS planes
            FROM equipo_instalacion e
            WHERE e.clave_edificio = %s
            ORDER BY FIELD(e.piso, 'Planta baja', 'Planta alta'), e.area, e.salon, e.codigo_inventario
            """,
            (EDIFICIO_SISTEMA,),
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def existe_equipo(codigo_inventario):
    cnx = conectar()
    try:
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT 1 FROM equipo_instalacion WHERE codigo_inventario = %s",
            (codigo_inventario.strip().upper(),),
        )
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe
    finally:
        cnx.close()


def _validar_datos_equipo(nombre_equipo, tipo_equipo, piso, area, salon):
    nombre = nombre_equipo.strip()
    tipo = tipo_equipo.strip()
    lugar = salon.strip()
    if not nombre or not tipo or not lugar:
        raise ValueError("El nombre, el tipo y el salon o lugar del equipo son obligatorios.")
    if len(nombre) > MAX_NOMBRE_EQUIPO:
        raise ValueError(f"El nombre no puede pasar de {MAX_NOMBRE_EQUIPO} caracteres.")
    if len(tipo) > MAX_TIPO_EQUIPO:
        raise ValueError(f"El tipo no puede pasar de {MAX_TIPO_EQUIPO} caracteres.")
    if len(lugar) > MAX_SALON:
        raise ValueError(f"El salon o lugar no puede pasar de {MAX_SALON} caracteres.")
    if piso not in PISOS:
        raise ValueError("El piso elegido no es valido.")
    if area not in AREAS_POR_PISO[piso]:
        raise ValueError(f"El area {area} no existe en {piso}.")
    return nombre, tipo, lugar


def registrar_equipo(codigo_inventario, nombre_equipo, tipo_equipo, piso, area, salon):
    # Alta de un equipo con su etiqueta real de inventario, siempre en Docencia 1
    codigo = codigo_inventario.strip().upper()
    if not codigo:
        raise ValueError("El codigo de inventario es obligatorio.")
    if len(codigo) > MAX_CODIGO_EQUIPO:
        raise ValueError(f"El codigo de inventario no puede pasar de {MAX_CODIGO_EQUIPO} caracteres.")
    nombre, tipo, lugar = _validar_datos_equipo(nombre_equipo, tipo_equipo, piso, area, salon)

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        cursor.execute("SELECT 1 FROM equipo_instalacion WHERE codigo_inventario = %s", (codigo,))
        if cursor.fetchone():
            raise ValueError(f"Ya existe un equipo con el codigo de inventario {codigo}.")
        cursor.execute(
            """
            INSERT INTO equipo_instalacion (
                codigo_inventario, nombre_equipo, tipo_equipo_instalacion, necesita_reparacion,
                area, piso, salon, clave_edificio
            ) VALUES (%s, %s, %s, 0, %s, %s, %s, %s)
            """,
            (codigo, nombre, tipo, area, piso, lugar, EDIFICIO_SISTEMA),
        )
        cnx.commit()
        cursor.close()
        return codigo
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def editar_equipo(codigo_inventario, nombre_equipo, tipo_equipo, piso, area, salon):
    # Cambio de datos o de ubicacion de un equipo. El codigo de inventario no cambia
    # porque lo usan REPORTE y PLAN_MANTENIMIENTO como llave foranea.
    nombre, tipo, lugar = _validar_datos_equipo(nombre_equipo, tipo_equipo, piso, area, salon)
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        cursor.execute(
            """
            UPDATE equipo_instalacion
            SET nombre_equipo = %s, tipo_equipo_instalacion = %s, piso = %s, area = %s, salon = %s
            WHERE codigo_inventario = %s
            """,
            (nombre, tipo, piso, area, lugar, codigo_inventario),
        )
        if cursor.rowcount == 0:
            cursor.execute("SELECT 1 FROM equipo_instalacion WHERE codigo_inventario = %s", (codigo_inventario,))
            if not cursor.fetchone():
                raise ValueError("El equipo ya no existe.")
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def usos_equipo(codigo_inventario):
    # Folios de reportes y claves de planes donde aparece el equipo
    cnx = conectar()
    try:
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT folio FROM reporte WHERE codigo_inventario = %s ORDER BY folio",
            (codigo_inventario,),
        )
        folios = [fila[0] for fila in cursor.fetchall()]
        cursor.execute(
            "SELECT clave_plan FROM plan_mantenimiento WHERE codigo_inventario = %s ORDER BY clave_plan",
            (codigo_inventario,),
        )
        planes = [fila[0] for fila in cursor.fetchall()]
        cursor.close()
        return folios, planes
    finally:
        cnx.close()


def eliminar_equipo(codigo_inventario):
    # Baja de un equipo. Si esta ligado a un reporte o a un plan no se borra para conservar el historial.
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT nombre_equipo FROM equipo_instalacion WHERE codigo_inventario = %s",
            (codigo_inventario,),
        )
        equipo = cursor.fetchone()
        if not equipo:
            raise ValueError("El equipo ya no existe.")
        cursor.execute("SELECT folio FROM reporte WHERE codigo_inventario = %s ORDER BY folio", (codigo_inventario,))
        folios = [f["folio"] for f in cursor.fetchall()]
        cursor.execute(
            "SELECT clave_plan FROM plan_mantenimiento WHERE codigo_inventario = %s ORDER BY clave_plan",
            (codigo_inventario,),
        )
        planes = [p["clave_plan"] for p in cursor.fetchall()]
        if folios or planes:
            partes = []
            if folios:
                partes.append("los reportes " + ", ".join(folios))
            if planes:
                partes.append("los planes " + ", ".join(planes))
            raise ValueError(
                f"{equipo['nombre_equipo']} aparece en {' y en '.join(partes)} y no puede eliminarse."
            )
        cursor.execute("DELETE FROM equipo_instalacion WHERE codigo_inventario = %s", (codigo_inventario,))
        cnx.commit()
        cursor.close()
        return equipo["nombre_equipo"]
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()
