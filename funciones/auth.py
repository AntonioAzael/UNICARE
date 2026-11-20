import mysql.connector
from mysql.connector import errorcode
from conexion import conectar

DOMINIO_CORREO = "@ut-tijuana.edu.mx"


def iniciar_sesion(identificador, contrasena):
    ident = identificador.strip().lower()
    clave = contrasena.strip()
    if not ident or not clave:
        return None

    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)

        # 1. Revisar si corresponde a personal de mantenimiento (por usuario o correo)
        cursor.execute(
            """
            SELECT id_trabajador, usuario_acceso, correo, especialidad, id_supervisor,
                   CONCAT_WS(' ', nombre, primer_apellido, segundo_apellido) AS nombre_completo
            FROM trabajador_mantenimiento
            WHERE (LOWER(usuario_acceso) = %s OR LOWER(correo) = %s) AND contrasena = %s
            """,
            (ident, ident, clave),
        )
        trabajador = cursor.fetchone()
        if trabajador:
            cursor.close()
            return {
                "rol": "mantenimiento",
                "id": trabajador["id_trabajador"],
                "nombre": trabajador["nombre_completo"],
                "detalle": trabajador["especialidad"],
                "es_supervisor": trabajador["id_supervisor"] is None,
            }

        # 2. Revisar si corresponde a un solicitante (Estudiante / Docente / Administrativo)
        cursor.execute(
            """
            SELECT num_usuario, tipo_usuario, correo,
                   CONCAT_WS(' ', nombre, primer_apellido, segundo_apellido) AS nombre_completo
            FROM usuario
            WHERE LOWER(correo) = %s AND contrasena = %s
            """,
            (ident, clave),
        )
        usuario = cursor.fetchone()
        cursor.close()
        if usuario:
            return {
                "rol": "solicitante",
                "id": usuario["num_usuario"],
                "nombre": usuario["nombre_completo"],
                "detalle": usuario["tipo_usuario"],
                "es_supervisor": False,
            }

        return None
    finally:
        cnx.close()


def existe_usuario_tecnico(usuario_acceso):
    cnx = conectar()
    try:
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT 1 FROM trabajador_mantenimiento WHERE LOWER(usuario_acceso) = %s LIMIT 1",
            (usuario_acceso.strip().lower(),),
        )
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe
    finally:
        cnx.close()


def registrar_tecnico(usuario_acceso, correo, contrasena, nombre, primer_apellido, segundo_apellido, especialidad, exp_laboral, id_supervisor):
    correo_limpio = correo.strip().lower()
    if not correo_limpio.endswith(DOMINIO_CORREO) or len(correo_limpio) <= len(DOMINIO_CORREO) or " " in correo_limpio:
        raise ValueError(f"El correo debe pertenecer al dominio {DOMINIO_CORREO}.")

    usuario_limpio = usuario_acceso.strip().lower()
    if not usuario_limpio or " " in usuario_limpio:
        usuario_limpio = correo_limpio

    cnx = conectar()
    try:
        cursor = cnx.cursor()
        # Si ya existe un tecnico con ese usuario (homonimo), usar el correo como usuario unico
        cursor.execute(
            "SELECT 1 FROM trabajador_mantenimiento WHERE LOWER(usuario_acceso) = %s LIMIT 1",
            (usuario_limpio,),
        )
        if cursor.fetchone():
            usuario_limpio = correo_limpio

        seg = segundo_apellido.strip() if segundo_apellido and segundo_apellido.strip() else None
        cursor.execute(
            """
            INSERT INTO trabajador_mantenimiento (
                usuario_acceso, correo, contrasena, nombre, primer_apellido, segundo_apellido,
                especialidad, exp_laboral, id_supervisor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                usuario_limpio,
                correo_limpio,
                contrasena.strip(),
                nombre.strip(),
                primer_apellido.strip(),
                seg,
                especialidad.strip(),
                int(exp_laboral),
                id_supervisor,
            ),
        )
        cnx.commit()
        cursor.close()
        return usuario_limpio
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            raise ValueError("Ese correo ya se encuentra registrado en el sistema.")
        raise
    finally:
        cnx.close()


def listar_tecnicos_gestion():
    # Tecnicos con su supervisor y cuantas asignaciones / supervisados tienen
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT t.id_trabajador,
                   CONCAT_WS(' ', t.nombre, t.primer_apellido, t.segundo_apellido) AS nombre_completo,
                   t.especialidad, t.correo, t.id_supervisor,
                   CONCAT_WS(' ', s.nombre, s.primer_apellido) AS nombre_supervisor,
                   (SELECT COUNT(*) FROM mantenimiento_trabajador mt WHERE mt.id_trabajador = t.id_trabajador) AS asignaciones,
                   (SELECT COUNT(*) FROM trabajador_mantenimiento sub WHERE sub.id_supervisor = t.id_trabajador) AS supervisados
            FROM trabajador_mantenimiento t
            LEFT JOIN trabajador_mantenimiento s ON s.id_trabajador = t.id_supervisor
            ORDER BY t.id_trabajador
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def eliminar_tecnico(id_tecnico, id_sesion):
    # Baja de un tecnico (solo supervisores). Protege el historial y la jerarquia de supervision.
    if id_tecnico == id_sesion:
        raise ValueError("No puedes eliminar tu propia cuenta mientras tienes la sesion abierta.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT nombre, primer_apellido, id_supervisor FROM trabajador_mantenimiento WHERE id_trabajador = %s",
            (id_tecnico,),
        )
        tec = cursor.fetchone()
        if not tec:
            raise ValueError("El tecnico ya no existe.")
        nombre = f"{tec['nombre']} {tec['primer_apellido']}"

        cursor.execute("SELECT COUNT(*) AS total FROM mantenimiento_trabajador WHERE id_trabajador = %s", (id_tecnico,))
        if cursor.fetchone()["total"]:
            raise ValueError(
                f"{nombre} tiene trabajos asignados en ordenes de mantenimiento y no puede eliminarse "
                "para no perder el historial."
            )

        cursor.execute("SELECT COUNT(*) AS total FROM trabajador_mantenimiento WHERE id_supervisor = %s", (id_tecnico,))
        supervisados = cursor.fetchone()["total"]
        if supervisados:
            if tec["id_supervisor"] is None:
                raise ValueError(
                    f"{nombre} es supervisor de {supervisados} tecnico(s) y no tiene un supervisor a quien "
                    "pasarlos. Reasigna primero esa supervision."
                )
            # Los supervisados pasan al supervisor del tecnico eliminado
            cursor.execute(
                "UPDATE trabajador_mantenimiento SET id_supervisor = %s WHERE id_supervisor = %s",
                (tec["id_supervisor"], id_tecnico),
            )

        cursor.execute("DELETE FROM trabajador_mantenimiento WHERE id_trabajador = %s", (id_tecnico,))
        cnx.commit()
        cursor.close()
        return nombre, supervisados
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()
