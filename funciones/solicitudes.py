from datetime import date
import mysql.connector
from mysql.connector import errorcode
from conexion import conectar

TIPOS_USUARIO = ("Estudiante", "Docente", "Administrativo")


def listar_usuarios():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT num_usuario, tipo_usuario, correo,
                   CONCAT_WS(' ', nombre, primer_apellido, segundo_apellido) AS nombre_completo
            FROM usuario
            ORDER BY num_usuario
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def registrar_usuario(tipo_usuario, correo, contrasena, nombre, primer_apellido, segundo_apellido=None):
    correo_limpio = correo.strip().lower()
    if "@" not in correo_limpio or correo_limpio.startswith("@") or "." not in correo_limpio.split("@", 1)[1]:
        raise ValueError("El correo debe tener un formato valido con @ y dominio.")

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
        nuevo_id = cursor.lastrowid
        cursor.close()
        return nuevo_id
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
            INNER JOIN edificio ed ON ed.no_edificio = e.no_edificio
            ORDER BY ed.nombre_edificio, e.salon
            """
        )
        equipos = cursor.fetchall()
        cursor.close()
        return {"categorias": categorias, "prioridades": prioridades, "equipos": equipos}
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


def registrar_solicitud(num_usuario, codigo_inventario, nombre_categoria, nombre_prioridad, descripcion_reporte, observaciones=None):
    descripcion = descripcion_reporte.strip()
    if not descripcion:
        raise ValueError("La descripcion del problema no puede ir vacia.")

    fecha = date.today()
    obs = observaciones.strip() if observaciones and observaciones.strip() else None

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        folio = _siguiente_folio(cursor, fecha.year)
        cursor.execute(
            """
            INSERT INTO reporte (
                folio, descripcion_reporte, observaciones, fecha_registro,
                num_usuario, id_trabajador, nombre_estado, nombre_categoria, nombre_prioridad, codigo_inventario
            ) VALUES (%s, %s, %s, %s, %s, NULL, 'Pendiente', %s, %s, %s)
            """,
            (folio, descripcion, obs, fecha, num_usuario, nombre_categoria, nombre_prioridad, codigo_inventario),
        )
        cursor.execute(
            "UPDATE equipo_instalacion SET necesita_reparacion = 1 WHERE codigo_inventario = %s",
            (codigo_inventario,),
        )
        cnx.commit()
        cursor.close()
        return folio
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def listar_fechas_solicitudes(num_usuario=None):
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = "SELECT fecha_registro, COUNT(*) AS total FROM reporte"
        params = []
        if num_usuario is not None:
            sql += " WHERE num_usuario = %s"
            params.append(num_usuario)
        sql += " GROUP BY fecha_registro ORDER BY fecha_registro DESC"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def consultar_solicitudes_por_fecha(fecha_consulta, num_usuario=None):
    # Consulta 1: Solicitudes de mantenimiento registradas para equipos en una fecha determinada
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        sql = """
            SELECT
                r.fecha_registro,
                r.folio,
                CONCAT_WS(' ', u.nombre, u.primer_apellido, u.segundo_apellido) AS nombre_usuario,
                e.nombre_equipo,
                CONCAT(ed.nombre_edificio, ', ', e.piso, ', Salon ', e.salon, ' (', e.area, ')') AS ubicacion_equipo,
                c.descripcion_categoria,
                r.descripcion_reporte,
                er.descripcion_estado,
                r.observaciones
            FROM reporte r
            INNER JOIN usuario u ON u.num_usuario = r.num_usuario
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            INNER JOIN edificio ed ON ed.no_edificio = e.no_edificio
            INNER JOIN categoria c ON c.nombre_categoria = r.nombre_categoria
            INNER JOIN estado_reporte er ON er.nombre_estado = r.nombre_estado
            WHERE r.fecha_registro = %s
        """
        params = [fecha_consulta]
        if num_usuario is not None:
            sql += " AND r.num_usuario = %s"
            params.append(num_usuario)
        sql += " ORDER BY r.folio"
        cursor.execute(sql, tuple(params))
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()
