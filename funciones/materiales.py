from conexion import conectar


def listar_inventario():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT m.no_material, m.nombre_material, m.descripcion_material, m.existencia, m.stock_minimo,
                   (SELECT COUNT(*) FROM solucion_material sm WHERE sm.no_material = m.no_material) AS usos
            FROM material m
            ORDER BY m.nombre_material
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def listar_soluciones_registradas():
    cnx = conectar()
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT s.no_solucion, s.folio, e.nombre_equipo, s.fecha_resolucion
            FROM solucion s
            INNER JOIN reporte r ON r.folio = s.folio
            INNER JOIN equipo_instalacion e ON e.codigo_inventario = r.codigo_inventario
            ORDER BY s.no_solucion DESC
            """
        )
        filas = cursor.fetchall()
        cursor.close()
        return filas
    finally:
        cnx.close()


def _siguiente_no_material(cursor):
    cursor.execute("SELECT no_material FROM material WHERE no_material LIKE 'MAT-%' ORDER BY no_material DESC LIMIT 1")
    ultimo = cursor.fetchone()
    if not ultimo:
        return "MAT-001"
    return f"MAT-{int(ultimo['no_material'].split('-')[-1]) + 1:03d}"


def registrar_material(nombre_material, descripcion_material, existencia, stock_minimo):
    # Alta de un material nuevo en el inventario
    nombre = nombre_material.strip()
    descripcion = descripcion_material.strip()
    if not nombre or not descripcion:
        raise ValueError("El nombre y la descripcion del material son obligatorios.")
    if existencia < 0 or stock_minimo < 0:
        raise ValueError("La existencia y el stock minimo no pueden ser negativos.")

    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT 1 FROM material WHERE LOWER(nombre_material) = %s", (nombre.lower(),))
        if cursor.fetchone():
            raise ValueError("Ya existe un material con ese nombre. Usa 'Reabastecer' para agregar existencia.")
        no_material = _siguiente_no_material(cursor)
        cursor.execute(
            """
            INSERT INTO material (no_material, nombre_material, stock_minimo, existencia, descripcion_material)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (no_material, nombre, stock_minimo, existencia, descripcion),
        )
        cnx.commit()
        cursor.close()
        return no_material
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def eliminar_material(no_material):
    # Baja de un material. Si ya se uso en alguna solucion no se borra para conservar el historial.
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT nombre_material FROM material WHERE no_material = %s", (no_material,))
        mat = cursor.fetchone()
        if not mat:
            raise ValueError("El material ya no existe.")
        cursor.execute("SELECT COUNT(*) AS total FROM solucion_material WHERE no_material = %s", (no_material,))
        usos = cursor.fetchone()["total"]
        if usos:
            raise ValueError(
                f"{mat['nombre_material']} ya se utilizo en {usos} solucion(es) y no puede eliminarse "
                "para no perder el historial. Si ya no hay, deja su existencia en 0."
            )
        cursor.execute("DELETE FROM material WHERE no_material = %s", (no_material,))
        cnx.commit()
        cursor.close()
        return mat["nombre_material"]
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def reabastecer_material(no_material, cantidad):
    # Entrada de material: suma la cantidad a la existencia actual
    if cantidad <= 0:
        raise ValueError("La cantidad a agregar debe ser mayor a cero.")
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "UPDATE material SET existencia = existencia + %s WHERE no_material = %s",
            (cantidad, no_material),
        )
        cursor.execute("SELECT nombre_material, existencia FROM material WHERE no_material = %s", (no_material,))
        mat = cursor.fetchone()
        if not mat:
            raise ValueError("El material ya no existe.")
        cnx.commit()
        cursor.close()
        return mat
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()


def registrar_material_tomado(no_solucion, no_material, cantidad):
    # Salida de material: descuenta SOLO la cantidad tomada y la registra en la solucion
    if cantidad <= 0:
        raise ValueError("La cantidad tomada debe ser mayor a cero.")
    cnx = conectar()
    try:
        cnx.start_transaction()
        cursor = cnx.cursor(dictionary=True)

        # El WHERE evita que la existencia quede negativa
        cursor.execute(
            "UPDATE material SET existencia = existencia - %s WHERE no_material = %s AND existencia >= %s",
            (cantidad, no_material, cantidad),
        )
        if cursor.rowcount == 0:
            raise ValueError("No hay existencia suficiente de ese material (o el material ya no existe).")

        cursor.execute(
            "SELECT 1 FROM solucion_material WHERE no_solucion = %s AND no_material = %s",
            (no_solucion, no_material),
        )
        if cursor.fetchone():
            cursor.execute(
                "UPDATE solucion_material SET cantidad_usada = cantidad_usada + %s WHERE no_solucion = %s AND no_material = %s",
                (cantidad, no_solucion, no_material),
            )
        else:
            cursor.execute(
                "INSERT INTO solucion_material (no_solucion, no_material, cantidad_usada) VALUES (%s, %s, %s)",
                (no_solucion, no_material, cantidad),
            )

        cursor.execute(
            "SELECT nombre_material, existencia, stock_minimo FROM material WHERE no_material = %s",
            (no_material,),
        )
        mat = cursor.fetchone()
        cnx.commit()
        cursor.close()
        return mat
    except Exception:
        cnx.rollback()
        raise
    finally:
        cnx.close()
