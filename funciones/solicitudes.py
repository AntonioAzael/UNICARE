from datetime import date
import mysql.connector
from mysql.connector import errorcode
from conexion import conectar

TIPOS_USUARIO = ("Estudiante", "Docente", "Administrativo")
DOMINIO_CORREO = "@ut-tijuana.edu.mx"

# Ubicacion de una solicitud: el sistema atiende solo el edificio Docencia 1
EDIFICIO_SISTEMA = "ED-DOC1"
PISOS = ("Planta baja", "Planta alta")
AREA_OTRA = "Otra area"
AREAS_POR_PISO = {
    "Planta baja": ("Salones", "Oficinas/Cubiculos", "Laboratorios", "Banos", "Rack de servidores", AREA_OTRA),
    "Planta alta": ("Salones", "Oficinas/Cubiculos", "Laboratorios", AREA_OTRA),
}
# Ejemplo que se muestra al escribir el lugar en cada area
EJEMPLOS_LUGAR = {
    "Salones": "Salon 104",
    "Oficinas/Cubiculos": "Cubiculo 3",
    "Laboratorios": "Laboratorio de Redes",
    AREA_OTRA: "Frente a la escalera",
}
AREA_BANOS = "Banos"
LUGARES_BANO = ("Bano de hombres", "Bano de mujeres")
AREA_RACK = "Rack de servidores"
MAX_AREA = 30
MAX_LUGAR = 60
MAX_EQUIPO_AFECTADO = 80
MAX_DESCRIPCION = 250

# Ubicacion completa de un reporte: "<edificio>, <piso>, <area>, <lugar>"
SQL_UBICACION = "CONCAT_WS(', ', ed.nombre_edificio, r.piso, r.area, r.lugar)"
# Equipo o elemento afectado escrito por el solicitante (obligatorio)
SQL_EQUIPO_AFECTADO = "r.equipo_afectado"


def normalizar_folio(folio):
    # El usuario puede escribir el folio en minusculas o con espacios
    return (folio or "").strip().upper()


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
        cursor.close()
        return {"categorias": categorias, "prioridades": prioridades}
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


def registrar_solicitud(numero_cuenta, piso, area, lugar, descripcion_reporte, equipo_afectado=None):
    # Registro 1: el solicitante indica la ubicacion, el equipo afectado (opcional) y describe el problema.
    # Categoria y prioridad quedan en NULL; las asigna el supervisor al crear la orden de trabajo.
    if piso not in PISOS:
        raise ValueError("El piso elegido no es valido.")
    area = (area or "").strip()
    areas_fijas = {a for areas in AREAS_POR_PISO.values() for a in areas if a != AREA_OTRA}
    if area in areas_fijas and area not in AREAS_POR_PISO[piso]:
        raise ValueError(f"El area {area} no existe en {piso}.")
    if area not in AREAS_POR_PISO[piso] or area == AREA_OTRA:
        # Un area que no esta en la lista es la que escribio el solicitante en "Otra area"
        if not area or area == AREA_OTRA:
            raise ValueError("Escribe el nombre del area.")
        if len(area) > MAX_AREA:
            raise ValueError(f"El area no puede pasar de {MAX_AREA} caracteres.")
    equipo = (equipo_afectado or "").strip()
    if not equipo:
        raise ValueError("Escribe el equipo o elemento afectado.")
    if len(equipo) > MAX_EQUIPO_AFECTADO:
        raise ValueError(f"El equipo afectado no puede pasar de {MAX_EQUIPO_AFECTADO} caracteres.")
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
                numero_cuenta, clave_edificio, nombre_estado, nombre_categoria, nombre_prioridad, equipo_afectado
            ) VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, 'Pendiente', NULL, NULL, %s)
            """,
            (folio, descripcion, fecha, piso, area, lugar, numero_cuenta, EDIFICIO_SISTEMA, equipo),
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
        # Categoria y prioridad pueden faltar mientras el supervisor no las asigne (LEFT JOIN)
        sql = f"""
            SELECT
                r.fecha_registro,
                r.folio,
                CONCAT_WS(' ', u.nombre, u.primer_apellido, u.segundo_apellido) AS nombre_usuario,
                {SQL_UBICACION} AS ubicacion,
                {SQL_EQUIPO_AFECTADO} AS equipo_afectado,
                COALESCE(c.descripcion_categoria, 'Sin clasificar') AS descripcion_categoria,
                COALESCE(r.nombre_prioridad, 'Sin asignar') AS nombre_prioridad,
                r.descripcion_reporte,
                es.descripcion_estado,
                r.observaciones
            FROM reporte r
            INNER JOIN usuario u ON u.numero_cuenta = r.numero_cuenta
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            INNER JOIN estado es ON es.nombre_estado = r.nombre_estado
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


def listar_folios(numero_cuenta=None):
    # Folios que se muestran como ayuda al escribir un folio; para un solicitante, solo los suyos
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = f"""
            SELECT r.folio, r.fecha_registro, r.nombre_estado, {SQL_UBICACION} AS ubicacion
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
        """
        params = []
        if numero_cuenta is not None:
            sql += " WHERE r.numero_cuenta = %s"
            params.append(numero_cuenta)
        sql += " ORDER BY r.fecha_registro DESC, r.folio DESC"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_seguimiento_folio(folio, numero_cuenta=None):
    # Consulta 7: Seguimiento de un reporte por folio (RF-03, RF-06).
    # Reporte con su orden de trabajo vigente y su solucion; ambas pueden no existir (LEFT JOIN).
    # Con numero_cuenta (seguimiento del solicitante) el folio debe ser de esa cuenta.
    folio = normalizar_folio(folio)
    if not folio:
        raise ValueError("Escribe un folio.")
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT
                r.folio,
                r.numero_cuenta,
                r.fecha_registro,
                CONCAT_WS(' ', u.nombre, u.primer_apellido, u.segundo_apellido) AS nombre_usuario,
                {SQL_UBICACION} AS ubicacion,
                {SQL_EQUIPO_AFECTADO} AS equipo_afectado,
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
        if numero_cuenta is not None and reporte["numero_cuenta"] != numero_cuenta:
            cursor.close()
            raise ValueError(f"El folio {folio} no corresponde a una de tus solicitudes.")

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


def listar_mis_solicitudes(numero_cuenta):
    # Todas las solicitudes de un solicitante, de la mas reciente a la mas antigua
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT r.folio, r.fecha_registro, {SQL_UBICACION} AS ubicacion,
                   {SQL_EQUIPO_AFECTADO} AS equipo_afectado, r.nombre_estado
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            WHERE r.numero_cuenta = %s
            ORDER BY r.fecha_registro DESC, r.folio DESC
            """,
            (numero_cuenta,),
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_solicitudes_cancelables(numero_cuenta):
    # Solo las solicitudes del solicitante que siguen Pendiente
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT r.folio, r.fecha_registro, {SQL_UBICACION} AS ubicacion,
                   {SQL_EQUIPO_AFECTADO} AS equipo_afectado, r.descripcion_reporte
            FROM reporte r
            INNER JOIN edificio ed ON ed.clave_edificio = r.clave_edificio
            WHERE r.numero_cuenta = %s AND r.nombre_estado = 'Pendiente'
            ORDER BY r.fecha_registro DESC, r.folio DESC
            """,
            (numero_cuenta,),
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def cancelar_solicitud(folio, numero_cuenta):
    # El solicitante cancela una solicitud suya; solo se permite desde Pendiente
    folio = normalizar_folio(folio)
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT numero_cuenta, nombre_estado FROM reporte WHERE folio = %s FOR UPDATE",
            (folio,),
        )
        rep = cursor.fetchone()
        if not rep:
            raise ValueError(f"No existe el reporte {folio}.")
        if rep["numero_cuenta"] != numero_cuenta:
            raise ValueError(f"El folio {folio} no corresponde a una de tus solicitudes.")
        if rep["nombre_estado"] != "Pendiente":
            raise ValueError(
                f"La solicitud {folio} esta en estado {rep['nombre_estado']}; solo se puede cancelar si esta Pendiente."
            )
        cursor.execute("UPDATE reporte SET nombre_estado = 'Cancelado' WHERE folio = %s", (folio,))
        cnx.commit()
        cursor.close()
        return folio
    except Exception:
        cnx.rollback()
        raise
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
