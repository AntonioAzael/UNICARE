from datetime import date
import mysql.connector
from mysql.connector import errorcode
from conexion import conectar

TIPOS_USUARIO = ("Estudiante", "Docente", "Administrativo")
DOMINIO_CORREO = "@ut-tijuana.edu.mx"

# Ubicacion de una solicitud: el sistema atiende solo el edificio Docencia 1
EDIFICIO_SISTEMA = "ED-DOC1"
PISOS = ("Planta baja", "Planta alta")
AREAS_POR_PISO = {
    "Planta baja": ("Salones", "Oficinas/Cubiculos", "Laboratorios", "Banos", "Rack de servidores"),
    "Planta alta": ("Salones", "Oficinas/Cubiculos", "Laboratorios"),
}
# Areas donde el solicitante escribe el lugar con sus palabras (con un ejemplo)
EJEMPLOS_LUGAR = {
    "Salones": "Salon 104",
    "Oficinas/Cubiculos": "Cubiculo 3",
    "Laboratorios": "Laboratorio de Redes",
}
AREA_BANOS = "Banos"
LUGARES_BANO = ("Bano de hombres", "Bano de mujeres")
AREA_RACK = "Rack de servidores"
MAX_LUGAR = 60
MAX_DESCRIPCION = 250

# Ubicacion completa de un reporte: "<edificio>, <piso>, <area>, <lugar>"
SQL_UBICACION = "CONCAT_WS(', ', ed.nombre_edificio, r.piso, r.area, r.lugar)"


def listar_usuarios():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT numero_cuenta, tipo_usuario, correo,
                   CONCAT_WS(' ', nombre, primer_apellido, segundo_apellido) AS nombre_completo
            FROM usuario
            ORDER BY numero_cuenta
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def registrar_usuario(tipo_usuario, correo, contrasena, nombre, primer_apellido, segundo_apellido=None):
    correo_limpio = correo.strip().lower()
    if not correo_limpio.endswith(DOMINIO_CORREO) or len(correo_limpio) <= len(DOMINIO_CORREO) or " " in correo_limpio:
        raise ValueError(f"El correo debe pertenecer al dominio {DOMINIO_CORREO}.")

    cnx = conectar()
    try:
        cursor = cnx.cursor()
        seg = segundo_apellido.strip() if segundo_apellido and segundo_apellido.strip() else None
        cursor.execute(
            """
            INSERT INTO usuario (tipo_usuario, correo, contrasena, nombre, primer_apellido, segundo_apellido)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (tipo_usuario, correo_limpio, contrasena.strip(), nombre.strip(), primer_apellido.strip(), seg),
        )
        cnx.commit()
        nuevo_numero = cursor.lastrowid
        cursor.close()
        return nuevo_numero
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise ValueError("Ese correo ya se encuentra registrado en el sistema.")
        raise
    finally:
        cnx.close()


def listar_catalogos_solicitud():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT nombre_categoria, descripcion_categoria FROM categoria ORDER BY nombre_categoria")
        categorias = cursor.fetchall()

        cursor.execute("SELECT nombre_prioridad, descripcion_prioridad FROM prioridad ORDER BY nivel_urgencia")
        prioridades = cursor.fetchall()

        cursor.execute(
            """
            SELECT e.codigo_inventario, e.nombre_equipo, ed.nombre_edificio, e.piso, e.salon, e.area
            FROM equipo_instalacion e
            INNER JOIN edificio ed ON ed.clave_edificio = e.clave_edificio
            WHERE e.clave_edificio = %s
            ORDER BY e.piso, e.area, e.salon
            """,
            (EDIFICIO_SISTEMA,),
        )
        equipos = cursor.fetchall()
        cursor.close()
        return {"categorias": categorias, "prioridades": prioridades, "equipos": equipos}
    finally:
        cnx.close()


# ---------------------------------------------------------------------------
# Gestion del catalogo de categorias (solo supervisores)
# ---------------------------------------------------------------------------

MAX_NOMBRE_CATEGORIA = 25
MAX_DESCRIPCION_CATALOGO = 150


def listar_categorias():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.nombre_categoria, c.descripcion_categoria, COUNT(r.folio) AS reportes
            FROM categoria c
            LEFT JOIN reporte r ON r.nombre_categoria = c.nombre_categoria
            GROUP BY c.nombre_categoria, c.descripcion_categoria
            ORDER BY c.nombre_categoria
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def existe_categoria(nombre_categoria):
    cnx = conectar()
    try:
        cursor = cnx.cursor()
        cursor.execute("SELECT 1 FROM categoria WHERE nombre_categoria = %s", (nombre_categoria.strip(),))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe
    finally:
        cnx.close()


def registrar_categoria(nombre_categoria, descripcion_categoria):
    nombre = nombre_categoria.strip()
    descripcion = descripcion_categoria.strip()
    if not nombre or not descripcion:
        raise ValueError("El nombre y la descripcion de la categoria son obligatorios.")
    if len(nombre) > MAX_NOMBRE_CATEGORIA:
        raise ValueError(f"El nombre no puede pasar de {MAX_NOMBRE_CATEGORIA} caracteres.")
    if len(descripcion) > MAX_DESCRIPCION_CATALOGO:
        raise ValueError(f"La descripcion no puede pasar de {MAX_DESCRIPCION_CATALOGO} caracteres.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        # La comparacion no distingue mayusculas (collation utf8mb4_unicode_ci)
        cursor.execute("SELECT 1 FROM categoria WHERE nombre_categoria = %s", (nombre,))
        if cursor.fetchone():
            raise ValueError(f"Ya existe la categoria {nombre}.")
        cursor.execute(
            "INSERT INTO categoria (nombre_categoria, descripcion_categoria) VALUES (%s, %s)",
            (nombre, descripcion),
        )
        cnx.commit()
        cursor.close()
        return nombre
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def eliminar_categoria(nombre_categoria):
    # Baja de una categoria. Si algun reporte la usa no se borra para conservar el historial.
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor()
        cursor.execute("SELECT 1 FROM categoria WHERE nombre_categoria = %s", (nombre_categoria,))
        if not cursor.fetchone():
            raise ValueError("La categoria ya no existe.")
        cursor.execute(
            "SELECT folio FROM reporte WHERE nombre_categoria = %s ORDER BY folio",
            (nombre_categoria,),
        )
        folios = [fila[0] for fila in cursor.fetchall()]
        if folios:
            raise ValueError(
                f"La categoria {nombre_categoria} se usa en los reportes {', '.join(folios)} y no puede eliminarse."
            )
        cursor.execute("DELETE FROM categoria WHERE nombre_categoria = %s", (nombre_categoria,))
        cnx.commit()
        cursor.close()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def _siguiente_folio(cursor, anio):
    prefijo = f"REP-{anio}-"
    cursor.execute(
        "SELECT folio FROM reporte WHERE folio LIKE %s ORDER BY folio DESC LIMIT 1",
        (f"{prefijo}%",),
    )
    ultimo = cursor.fetchone()
    if not ultimo:
        return f"{prefijo}0001"
    numero = int(ultimo["folio"].split("-")[-1]) + 1
    return f"{prefijo}{numero:04d}"


def registrar_solicitud(numero_cuenta, piso, area, lugar, descripcion_reporte):
    # Registro 1: el solicitante indica la ubicacion y describe el problema.
    # Categoria, prioridad y equipo quedan en NULL; los asigna mantenimiento en la orden de trabajo.
    if piso not in PISOS:
        raise ValueError("El piso elegido no es valido.")
    if area not in AREAS_POR_PISO[piso]:
        raise ValueError(f"El area {area} no existe en {piso}.")
    if area == AREA_RACK:
        lugar = AREA_RACK
    elif area == AREA_BANOS:
        if lugar not in LUGARES_BANO:
            raise ValueError("Elige el bano de hombres o el de mujeres.")
    else:
        lugar = (lugar or "").strip()
        if not lugar:
            raise ValueError("El lugar no puede ir vacio.")
        if len(lugar) > MAX_LUGAR:
            raise ValueError(f"El lugar no puede pasar de {MAX_LUGAR} caracteres.")

    descripcion = descripcion_reporte.strip()
    if not descripcion:
        raise ValueError("La descripcion del problema no puede ir vacia.")
    if len(descripcion) > MAX_DESCRIPCION:
        raise ValueError(f"La descripcion no puede pasar de {MAX_DESCRIPCION} caracteres.")

    fecha = date.today()
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        folio = _siguiente_folio(cursor, fecha.year)
        cursor.execute(
            """
            INSERT INTO reporte (
                folio, descripcion_reporte, observaciones, fecha_registro, piso, area, lugar,
                numero_cuenta, clave_edificio, nombre_estado, nombre_categoria, nombre_prioridad, codigo_inventario
            ) VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, 'Pendiente', NULL, NULL, NULL)
            """,
            (folio, descripcion, fecha, piso, area, lugar, numero_cuenta, EDIFICIO_SISTEMA),
        )
        cnx.commit()
        cursor.close()
        return folio
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def listar_fechas_solicitudes(numero_cuenta=None):
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = "SELECT fecha_registro, COUNT(*) AS total FROM reporte"
        params = []
        if numero_cuenta is not None:
            sql += " WHERE numero_cuenta = %s"
            params.append(numero_cuenta)
        sql += " GROUP BY fecha_registro ORDER BY fecha_registro DESC"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_solicitudes_por_fecha(fecha_consulta, numero_cuenta=None):
    # Consulta 1: Solicitudes de mantenimiento registradas para equipos en una fecha determinada
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        # Categoria, prioridad y equipo pueden faltar mientras mantenimiento no los asigne (LEFT JOIN)
        sql = f"""
            SELECT
                r.fecha_registro,
                r.folio,
                CONCAT_WS(' ', u.nombre, u.primer_apellido, u.segundo_apellido) AS nombre_usuario,
                {SQL_UBICACION} AS ubicacion,
                COALESCE(e.nombre_equipo, 'Sin equipo') AS nombre_equipo,
                COALESCE(c.descripcion_categoria, 'Sin clasificar') AS descripcion_categoria,
                COALESCE(r.nombre_prioridad, 'Sin asignar') AS nombre_prioridad,
                r.descripcion_reporte,
                es.descripcion_estado,
                r.observaciones
            FROM reporte r
            INNER JOIN usuario u ON u.numero_cuenta = r.numero_cuenta
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            INNER JOIN estado es ON es.nombre_estado = r.nombre_estado
            LEFT JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            LEFT JOIN categoria c ON c.nombre_categoria = r.nombre_categoria
            WHERE r.fecha_registro = %s
        """
        params = [fecha_consulta]
        if numero_cuenta is not None:
            sql += " AND r.numero_cuenta = %s"
            params.append(numero_cuenta)
        sql += " ORDER BY r.folio"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


ORDEN_ESTADOS = "FIELD(r.nombre_estado, 'Pendiente', 'En revision', 'En proceso', 'Solucionado', 'Cancelado')"


def listar_folios():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT r.folio, r.fecha_registro, r.nombre_estado, {SQL_UBICACION} AS ubicacion
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            ORDER BY r.fecha_registro DESC, r.folio DESC
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_seguimiento_folio(folio):
    # Consulta 7: Seguimiento de un reporte por folio (RF-03, RF-06)
    # Reporte con su orden de trabajo vigente y su solucion; ambas pueden no existir (LEFT JOIN)
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT
                r.folio,
                r.fecha_registro,
                CONCAT_WS(' ', u.nombre, u.primer_apellido, u.segundo_apellido) AS nombre_usuario,
                {SQL_UBICACION} AS ubicacion,
                COALESCE(e.nombre_equipo, 'Sin equipo') AS nombre_equipo,
                COALESCE(r.nombre_categoria, 'Sin clasificar') AS nombre_categoria,
                COALESCE(r.nombre_prioridad, 'Sin asignar') AS nombre_prioridad,
                r.nombre_estado,
                r.descripcion_reporte,
                r.observaciones,
                m.clave_mantenimiento,
                m.nombre_estado AS estado_orden,
                m.fecha_programada,
                s.fecha_resolucion,
                s.solucion_aplicada
            FROM reporte r
            INNER JOIN usuario u ON u.numero_cuenta = r.numero_cuenta
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            LEFT JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            LEFT JOIN mantenimiento m ON m.folio = r.folio AND m.nombre_estado <> 'Cancelado'
            LEFT JOIN solucion s ON s.folio = r.folio
            WHERE r.folio = %s
            """,
            (folio,),
        )
        reporte = cursor.fetchone()
        if not reporte:
            cursor.close()
            raise ValueError(f"No existe el reporte {folio}.")

        tecnicos = []
        if reporte["clave_mantenimiento"]:
            cursor.execute(
                """
                SELECT CONCAT_WS(' ', t.nombre, t.primer_apellido, t.segundo_apellido) AS nombre_tecnico,
                       t.especialidad, mt.horas_asignadas, mt.actividad_asignada
                FROM mantenimiento_trabajador mt
                INNER JOIN trabajador_mantenimiento t ON t.numero_empleado = mt.numero_empleado
                WHERE mt.clave_mantenimiento = %s
                ORDER BY t.numero_empleado
                """,
                (reporte["clave_mantenimiento"],),
            )
            tecnicos = cursor.fetchall()
        cursor.close()
        reporte["tecnicos"] = tecnicos
        return reporte
    finally:
        cnx.close()


def resumen_reportes_por_estado():
    # Consulta 8 (resumen): numero de reportes por estado (COUNT + GROUP BY).
    # Se parte del catalogo de estados para que aparezcan tambien los que tienen 0.
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT es.nombre_estado, COUNT(r.folio) AS total
            FROM estado es
            LEFT JOIN reporte r ON r.nombre_estado = es.nombre_estado
            GROUP BY es.nombre_estado
            ORDER BY FIELD(es.nombre_estado, 'Pendiente', 'En revision', 'En proceso', 'Solucionado', 'Cancelado')
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_reportes_por_estado(nombre_estado=None):
    # Consulta 8 (detalle): reportes pendientes y solucionados con los dias que llevan abiertos.
    # Si el reporte ya tiene solucion, los dias se cuentan hasta la fecha de resolucion.
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = f"""
            SELECT
                r.folio,
                r.fecha_registro,
                {SQL_UBICACION} AS ubicacion,
                COALESCE(r.nombre_categoria, 'Sin clasificar') AS nombre_categoria,
                COALESCE(r.nombre_prioridad, 'Sin asignar') AS nombre_prioridad,
                r.nombre_estado,
                DATEDIFF(COALESCE(s.fecha_resolucion, CURDATE()), r.fecha_registro) AS dias_abiertos
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            LEFT JOIN solucion s ON s.folio = r.folio
        """
        params = []
        if nombre_estado:
            sql += " WHERE r.nombre_estado = %s"
            params.append(nombre_estado)
        sql += f" ORDER BY {ORDEN_ESTADOS}, dias_abiertos DESC, r.folio"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_reportes_piso_area():
    # Consulta 10: numero de reportes por piso y area, con una columna por estado.
    # El total es la suma de las cinco columnas de estado.
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                r.piso,
                r.area,
                COUNT(CASE WHEN r.nombre_estado = 'Pendiente' THEN 1 END) AS pendiente,
                COUNT(CASE WHEN r.nombre_estado = 'En revision' THEN 1 END) AS en_revision,
                COUNT(CASE WHEN r.nombre_estado = 'En proceso' THEN 1 END) AS en_proceso,
                COUNT(CASE WHEN r.nombre_estado = 'Solucionado' THEN 1 END) AS solucionado,
                COUNT(CASE WHEN r.nombre_estado = 'Cancelado' THEN 1 END) AS cancelado,
                COUNT(*) AS total
            FROM reporte r
            GROUP BY r.piso, r.area
            ORDER BY FIELD(r.piso, 'Planta baja', 'Planta alta'), r.area
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_detalle_piso_area(piso, area):
    # Consulta 10 (detalle): reportes de un piso y un area
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT folio, fecha_registro, lugar, nombre_estado
            FROM reporte
            WHERE piso = %s AND area = %s
            ORDER BY fecha_registro DESC, folio DESC
            """,
            (piso, area),
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()
