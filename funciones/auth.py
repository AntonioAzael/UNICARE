import mysql.connector
from mysql.connector import errorcode
from conexion import conectar


def iniciar_sesion(identificador, contrasena):
    ident = identificador.strip().lower()
    clave = contrasena.strip()
    if not ident or not clave:
        return None

    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)

        # 1. Revisar si corresponde a personal de mantenimiento
        cursor.execute(
            """
            SELECT id_trabajador, usuario_acceso, especialidad, id_supervisor,
                   CONCAT_WS(' ', nombre, primer_apell, seg_apell) AS nombre_completo
            FROM trabajador_mantenimiento
            WHERE LOWER(usuario_acceso) = %s AND contrasena = %s
            """,
            (ident, clave),
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


def registrar_tecnico(usuario_acceso, contrasena, nombre, primer_apell, seg_apell, especialidad, exp_laboral, id_supervisor):
    usuario_limpio = usuario_acceso.strip().lower()
    if not usuario_limpio or " " in usuario_limpio:
        raise ValueError("El usuario de acceso no puede estar vacio ni contener espacios.")

    cnx = conectar()
    try:
        cursor = cnx.cursor()
        seg = seg_apell.strip() if seg_apell and seg_apell.strip() else None
        cursor.execute(
            """
            INSERT INTO trabajador_mantenimiento (
                usuario_acceso, contrasena, nombre, primer_apell, seg_apell,
                especialidad, exp_laboral, id_supervisor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                usuario_limpio,
                contrasena.strip(),
                nombre.strip(),
                primer_apell.strip(),
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
            raise ValueError("Ese usuario de acceso ya existe en el sistema.")
        raise
    finally:
        cnx.close()
