import os
import re
from datetime import date, datetime
from decimal import Decimal

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, InvalidResponse, Prompt
from rich.table import Table
from rich.text import Text

from conexion import conectar
from logo import mostrar_banner_unicare
from funciones.auth import (
    eliminar_tecnico,
    existe_usuario_tecnico,
    iniciar_sesion,
    listar_tecnicos_gestion,
    registrar_tecnico,
)
from funciones.materiales import (
    consultar_materiales_por_reponer,
    eliminar_material,
    listar_inventario,
    listar_soluciones_registradas,
    reabastecer_material,
    registrar_material,
    registrar_material_tomado,
)
from funciones.ordenes import (
    MAX_CODIGO_TIPO,
    MAX_DESCRIPCION_TIPO,
    MAX_NOMBRE_TIPO,
    eliminar_tipo_mantenimiento,
    existe_tipo,
    listar_tipos_gestion,
    registrar_tipo_mantenimiento,
    asignar_tecnicos_orden,
    cancelar_orden,
    consultar_actividades_orden,
    consultar_ordenes_edificio,
    consultar_tecnicos_orden,
    listar_mis_ordenes,
    listar_ordenes,
    listar_solicitudes_disponibles,
    listar_tecnicos,
    listar_tipos_mantenimiento,
    registrar_actividades_orden,
    registrar_orden_trabajo,
)
from funciones.planes import (
    ESTADOS_PLAN,
    FRECUENCIAS,
    MAX_CODIGO_EQUIPO,
    MAX_FRECUENCIA,
    MAX_NOMBRE_EQUIPO,
    MAX_SALON,
    MAX_TIPO_EQUIPO,
    consultar_planes_edificio,
    editar_equipo,
    eliminar_equipo,
    existe_equipo,
    listar_edificios,
    listar_areas_con_equipos,
    listar_equipos,
    listar_equipos_por_piso_area,
    registrar_equipo,
    registrar_plan_preventivo,
    usos_equipo,
)
from funciones.soluciones import (
    consultar_soluciones,
    listar_materiales,
    listar_reportes_sin_solucion,
    registrar_solucion,
)
from funciones.solicitudes import (
    AREA_BANOS,
    AREA_OTRA,
    AREA_RACK,
    AREAS_POR_PISO,
    EJEMPLOS_LUGAR,
    LUGARES_BANO,
    MAX_AREA,
    MAX_DESCRIPCION,
    MAX_DESCRIPCION_CATALOGO,
    MAX_EQUIPO_AFECTADO,
    MAX_LUGAR,
    MAX_NOMBRE_CATEGORIA,
    PISOS,
    cancelar_solicitud,
    eliminar_categoria,
    existe_categoria,
    listar_categorias,
    registrar_categoria,
    consultar_detalle_piso_area,
    consultar_reportes_piso_area,
    consultar_reportes_por_estado,
    consultar_seguimiento_folio,
    consultar_solicitudes_por_fecha,
    listar_catalogos_solicitud,
    listar_fechas_solicitudes,
    listar_folios,
    listar_mis_solicitudes,
    listar_solicitudes_cancelables,
    resumen_reportes_por_estado,
    registrar_solicitud,
    registrar_usuario,
)

DOMINIO_CORREO = "@ut-tijuana.edu.mx"

# Un solo Console de rich para toda la aplicacion
console = Console(highlight=False)


# ---------------------------------------------------------------------------
# Prompts de rich con los mensajes en espanol
# ---------------------------------------------------------------------------

class EnteroPrompt(IntPrompt):
    validate_error_message = "[prompt.invalid]Escribe un numero entero."


class DecimalPrompt(FloatPrompt):
    validate_error_message = "[prompt.invalid]Escribe un numero valido (ej. 2.5)."


class ConfirmarPrompt(Confirm):
    # Confirm de rich que responde con s/n (tambien acepta si/no)
    choices = ["s", "n"]
    validate_error_message = "[prompt.invalid]Responde s o n."

    def process_response(self, value):
        respuesta = value.strip().lower()
        if respuesta in ("s", "si"):
            return True
        if respuesta in ("n", "no"):
            return False
        raise InvalidResponse(self.validate_error_message)


def _etiqueta(texto, defecto=None):
    # Arma la pregunta como antes: "Etiqueta [defecto]". escape evita que rich lea los corchetes como estilo.
    if defecto is not None and defecto != "":
        texto = f"{texto} [{defecto}]"
    return escape(texto)


# ---------------------------------------------------------------------------
# Utilidades de pantalla y captura de datos
# ---------------------------------------------------------------------------

def linea(caracter="="):
    console.rule(characters=caracter, style="dim")


def titulo(texto):
    console.rule(Text(texto.upper(), style="bold cyan"), characters="=", style="cyan", align="left")


def mensaje(texto, sangria=""):
    # Mensaje normal del sistema; rich lo acomoda al ancho de la consola.
    # Con sangria, todo el mensaje se recorre a la derecha.
    if sangria:
        console.print(Padding(Text(texto), (0, 0, 0, len(sangria))))
    else:
        console.print(Text(texto))


def exito(texto):
    console.print(Text(texto, style="bold green"))


def error(texto):
    console.print(Text(texto, style="red"))


def aviso(texto, sangria=""):
    if sangria:
        console.print(Padding(Text(texto, style="yellow"), (0, 0, 0, len(sangria))))
    else:
        console.print(Text(texto, style="yellow"))


def limpiar_pantalla(sesion=None):
    # En la consola clasica de Windows (conhost sin modo VT) rich no puede borrar la pantalla
    # con console.clear(), por eso ahi se usa cls; en las demas terminales se usa console.clear()
    if console.legacy_windows and console.is_terminal:
        os.system("cls")
    else:
        console.clear()
    mostrar_banner_unicare(console)
    if sesion:
        if sesion["rol"] == "mantenimiento":
            rol_txt = "Supervisor" if sesion.get("es_supervisor") else "Tecnico"
        else:
            rol_txt = "Solicitante"
        linea_sesion = Text()
        linea_sesion.append("Sesion: ", style="bold cyan")
        linea_sesion.append(sesion["nombre"])
        linea_sesion.append(f" ({rol_txt} - {sesion['detalle']})", style="dim")
        console.print(linea_sesion)


def pausar():
    console.input("\n[dim]Presiona Enter para continuar...[/]")


def entrada(etiqueta, defecto=None):
    # Prompt de rich con el valor por defecto entre corchetes; Enter acepta el valor por defecto
    valor = Prompt.ask(_etiqueta(etiqueta, defecto), console=console, default="", show_default=False).strip()
    if not valor and defecto is not None and defecto != "":
        return str(defecto)
    return valor


def pedir_texto(etiqueta, permitir_cancelar=False):
    while True:
        valor = Prompt.ask(_etiqueta(etiqueta), console=console, default="", show_default=False).strip()
        if permitir_cancelar and valor == "0":
            return None
        if valor:
            return valor
        error("Este campo no puede quedar vacio.")


def pedir_contrasena(etiqueta):
    while True:
        valor = Prompt.ask(_etiqueta(etiqueta), console=console, password=True).strip()
        if valor:
            return valor
        error("La contrasena no puede ir vacia.")


def pedir_contrasena_nueva(etiqueta):
    # Al crear una cuenta la contrasena se escribe dos veces
    while True:
        valor = pedir_contrasena(etiqueta)
        if pedir_contrasena("Confirma la contrasena") == valor:
            return valor
        error("Las contrasenas no coinciden. Escribelas de nuevo.")


def pedir_texto_opcional(etiqueta, maximo):
    # Texto que se puede dejar vacio con Enter; respeta el largo maximo
    while True:
        valor = entrada(etiqueta)
        if len(valor) <= maximo:
            return valor or None
        error(f"El texto no puede pasar de {maximo} caracteres (escribiste {len(valor)}).")


def es_supervisor(sesion):
    return bool(sesion.get("es_supervisor"))


def filtrar_por_rol(sesion, opciones):
    # opciones: lista de (texto, funcion, es_submenu, solo_supervisor).
    # Un tecnico no ve las opciones de supervisor; las que quedan se numeran desde 1.
    return [o for o in opciones if es_supervisor(sesion) or not o[3]]


def ejecutar_menu(sesion, titulo_menu, opciones, texto_salir):
    # Menu numerado con las opciones que le tocan al rol de la sesion
    visibles = filtrar_por_rol(sesion, opciones)
    while True:
        limpiar_pantalla(sesion)
        mostrar_menu(
            titulo_menu,
            [(str(i), o[0]) for i, o in enumerate(visibles, start=1)] + [("0", texto_salir)],
        )
        op = pedir_opcion([str(n) for n in range(len(visibles) + 1)])
        if op == "0":
            break
        _, funcion, es_submenu, _ = visibles[int(op) - 1]
        if es_submenu:
            funcion(sesion)
            continue
        ejecutar_opcion(funcion, sesion)
        pausar()


def pedir_entero(etiqueta, defecto=None):
    extra = {} if defecto is None else {"default": int(defecto)}
    return EnteroPrompt.ask(_etiqueta(etiqueta, defecto), console=console, show_default=False, **extra)


def pedir_decimal(etiqueta, defecto=None):
    extra = {} if defecto is None else {"default": float(defecto)}
    while True:
        numero = DecimalPrompt.ask(_etiqueta(etiqueta, defecto), console=console, show_default=False, **extra)
        if numero < 0:
            error("El valor no puede ser negativo.")
            continue
        return numero


def confirmar(pregunta, defecto=False):
    sugerido = "s" if defecto else "n"
    return ConfirmarPrompt.ask(
        _etiqueta(f"{pregunta} (s/n)", sugerido),
        console=console,
        default=defecto,
        show_default=False,
        show_choices=False,
    )


def pedir_opcion(validas, defecto="0"):
    while True:
        op = entrada("Selecciona una opcion", defecto)
        if op in validas:
            return op
        error("Opcion no valida.")


def pedir_fecha(etiqueta, defecto=None):
    sugerida = str(defecto or date.today())[:10]
    while True:
        valor = entrada(f"{etiqueta} (AAAA-MM-DD, 0 para cancelar)", sugerida)
        if valor == "0":
            return None
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            error("Formato invalido. Usa AAAA-MM-DD.")


def pedir_correo(etiqueta="Correo institucional (0 para cancelar)"):
    while True:
        valor = Prompt.ask(_etiqueta(etiqueta), console=console, default="", show_default=False).strip().lower()
        if valor == "0":
            return None
        if valor.endswith(DOMINIO_CORREO) and len(valor) > len(DOMINIO_CORREO) and " " not in valor:
            return valor
        error(f"Correo invalido. Debe ser institucional {DOMINIO_CORREO} (ej. 0323105973{DOMINIO_CORREO}).")


def elegir_de_lista(titulo_lista, opciones, formato):
    if not opciones:
        aviso(f"No hay registros disponibles para {titulo_lista}.")
        return None

    console.print(Text(f"\n{titulo_lista}", style="bold cyan"))
    lista = Table.grid(padding=(0, 1))
    lista.add_column(justify="right", no_wrap=True)
    lista.add_column(overflow="fold")
    for i, item in enumerate(opciones, start=1):
        lista.add_row(Text(f"  [{i}]", style="bold"), Text(str(formato(item))))
    lista.add_row(Text("  [0]", style="bold"), Text("Cancelar"))
    console.print(lista)

    validas = [str(i) for i in range(0, len(opciones) + 1)]
    eleccion = pedir_opcion(validas, "0")
    if eleccion == "0":
        return None
    return opciones[int(eleccion) - 1]


def mostrar_menu(titulo_menu, opciones):
    # opciones: lista de (clave, texto)
    contenido = Table.grid(padding=(0, 1))
    contenido.add_column(justify="right", no_wrap=True)
    contenido.add_column(overflow="fold")
    for clave, texto in opciones:
        contenido.add_row(Text(f"[{clave}]", style="bold"), Text(texto))
    console.print(
        Panel(
            contenido,
            title=Text(titulo_menu.upper(), style="bold cyan"),
            title_align="left",
            border_style="cyan",
            box=box.ROUNDED,
            expand=False,
        )
    )


def _es_numero(valor):
    if isinstance(valor, bool):
        return False
    if isinstance(valor, (int, float, Decimal)):
        return True
    return re.fullmatch(r"\$?-?\d+(\.\d+)?", str(valor).strip()) is not None


def imprimir_tabla(encabezados, filas, anchos):
    # Tabla de rich; cada ancho es el maximo de su columna y el texto largo pasa a varias lineas
    tabla = Table(box=box.ROUNDED, header_style="bold cyan")
    for i, (encabezado, ancho) in enumerate(zip(encabezados, anchos)):
        valores = [fila[i] for fila in filas if fila[i] not in (None, "")]
        derecha = bool(valores) and all(_es_numero(v) for v in valores)
        tabla.add_column(
            Text(str(encabezado)),
            max_width=ancho,
            overflow="fold",
            justify="right" if derecha else "left",
        )
    for fila in filas:
        tabla.add_row(*[Text(str(celda)) for celda in fila])
    console.print(tabla)


def imprimir_ficha(encabezado, campos, color="cyan"):
    # Ficha en un Panel: cian para solicitudes y reportes, amarillo para ordenes, verde para soluciones
    contenido = Table.grid(padding=(0, 1))
    contenido.add_column(style="bold", no_wrap=True)
    contenido.add_column(overflow="fold")
    for etiqueta, valor in campos:
        contenido.add_row(Text(f"{etiqueta}:"), Text(str(valor)))
    console.print(
        Panel(
            contenido,
            title=Text(encabezado, style=f"bold {color}"),
            title_align="left",
            border_style=color,
            box=box.ROUNDED,
            expand=False,
        )
    )


# ---------------------------------------------------------------------------
# Registro de cuentas
# ---------------------------------------------------------------------------

def flujo_registro_estudiante(sesion=None):
    limpiar_pantalla(sesion)
    titulo("Registro de estudiante")
    nombre = pedir_texto("Nombre(s) (0 para cancelar)", permitir_cancelar=True)
    if not nombre:
        return None
    ap1 = pedir_texto("Primer apellido")
    ap2 = entrada("Segundo apellido (opcional)")
    correo = pedir_correo()
    if not correo:
        return None
    contrasena = pedir_contrasena_nueva("Crea una contrasena")

    registrar_usuario("Estudiante", correo, contrasena, nombre, ap1, ap2 or None)
    exito(f"\nCuenta creada correctamente. Ya puedes iniciar sesion con {correo}.")
    return correo


def flujo_registrar_personal(sesion):
    limpiar_pantalla(sesion)
    titulo("Registro de docente, administrativo o tecnico")
    tipo = elegir_de_lista(
        "Tipo de cuenta a crear",
        ["Docente", "Administrativo", "Tecnico de mantenimiento"],
        lambda t: t,
    )
    if not tipo:
        return

    nombre = pedir_texto("Nombre(s) (0 para cancelar)", permitir_cancelar=True)
    if not nombre:
        return
    ap1 = pedir_texto("Primer apellido")
    ap2 = entrada("Segundo apellido (opcional)")

    if tipo in ("Docente", "Administrativo"):
        correo = pedir_correo()
        if not correo:
            return
        contrasena = pedir_contrasena_nueva("Contrasena asignada")
        registrar_usuario(tipo, correo, contrasena, nombre, ap1, ap2 or None)
        exito(f"\n{tipo} registrado correctamente ({correo}).")
    else:
        correo = pedir_correo("Correo institucional del tecnico (0 para cancelar)")
        if not correo:
            return
        sugerido = f"{nombre.split()[0].lower()}.{ap1.split()[0].lower()}"
        if existe_usuario_tecnico(sugerido):
            mensaje(
                f"Ya existe un tecnico con el usuario '{sugerido}'. "
                f"Escribe otro usuario o presiona Enter para usar tu correo ({correo})."
            )
            usuario_acc = entrada("Usuario de acceso", correo).lower()
        else:
            usuario_acc = entrada("Usuario de acceso", sugerido).lower()
        especialidad = pedir_texto("Especialidad")
        exp = pedir_entero("Anios de experiencia laboral", 1)
        contrasena = pedir_contrasena_nueva("Contrasena asignada")
        # Un supervisor es un tecnico sin jefe (empleado_supervisor vacio)
        sera_supervisor = confirmar("Sera supervisor (tendra los mismos permisos que tu)?", False)
        usuario_creado = registrar_tecnico(
            usuario_acc, correo, contrasena, nombre, ap1, ap2 or None, especialidad, exp,
            None if sera_supervisor else sesion["numero"],
        )
        rol = "supervisor" if sera_supervisor else f"tecnico a cargo de {sesion.get('nombre', 'ti')}"
        exito(f"\nTecnico registrado correctamente ({usuario_creado}) como {rol}.")


# ---------------------------------------------------------------------------
# Registro 1 y Consulta 1: solicitudes
# ---------------------------------------------------------------------------

def pedir_texto_limitado(etiqueta, maximo):
    # Texto obligatorio con largo maximo; regresa None si el usuario escribe 0
    while True:
        valor = pedir_texto(etiqueta, permitir_cancelar=True)
        if valor is None or len(valor) <= maximo:
            return valor
        error(f"El texto no puede pasar de {maximo} caracteres (escribiste {len(valor)}).")


def flujo_registrar_solicitud(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar solicitud de mantenimiento")
    mensaje("Las solicitudes se registran para el edificio Docencia 1.")

    piso = elegir_de_lista("Piso donde esta el problema", list(PISOS), lambda p: p)
    if not piso:
        return

    area = elegir_de_lista(f"Area de {piso}", list(AREAS_POR_PISO[piso]), lambda a: a)
    if not area:
        return
    if area == AREA_OTRA:
        area = pedir_texto_limitado("\nEscribe el area (ej. Pasillo principal) (0 para cancelar)", MAX_AREA)
        if not area:
            return

    if area == AREA_RACK:
        lugar = AREA_RACK
        mensaje("\nEl lugar queda registrado como Rack de servidores.")
    elif area == AREA_BANOS:
        lugar = elegir_de_lista("Bano", list(LUGARES_BANO), lambda b: b)
        if not lugar:
            return
    else:
        ejemplo = EJEMPLOS_LUGAR.get(area, EJEMPLOS_LUGAR[AREA_OTRA])
        lugar = pedir_texto_limitado(f"\nEscribe el lugar exacto (ej. {ejemplo}) (0 para cancelar)", MAX_LUGAR)
        if not lugar:
            return

    equipo_afectado = pedir_texto_opcional(
        "\nEquipo afectado (opcional, ej. Proyector, Contacto de la mesa 4; Enter para omitir)",
        MAX_EQUIPO_AFECTADO,
    )

    descripcion = pedir_texto_limitado(
        "\nDescribe el problema con tus propias palabras (0 para cancelar)", MAX_DESCRIPCION
    )
    if not descripcion:
        return

    folio = registrar_solicitud(sesion["numero"], piso, area, lugar, descripcion, equipo_afectado)
    exito(f"\nSolicitud registrada con numero {folio}.")
    mensaje(f"Ubicacion: Docencia 1, {piso}, {area}, {lugar}.")
    mensaje(f"Equipo afectado: {equipo_afectado or 'No indicado'}.")
    mensaje("Mantenimiento asignara la categoria y la prioridad al crear la orden de trabajo.")


def mostrar_consulta_solicitudes(sesion, solo_mias=False):
    limpiar_pantalla(sesion)
    titulo("Mis solicitudes por fecha" if solo_mias else "Consulta de solicitudes por fecha")
    uid = sesion["numero"] if solo_mias else None
    fechas = listar_fechas_solicitudes(uid)
    if solo_mias and not fechas:
        aviso("\nAun no tienes solicitudes registradas.")
        return
    if fechas:
        mensaje("\nFechas con solicitudes registradas:")
        for f in fechas[:5]:
            mensaje(f"  {f['fecha_registro']} ({f['total']} registros)")
        console.print()

    fecha = pedir_fecha("Fecha a consultar", fechas[0]["fecha_registro"] if fechas else None)
    if not fecha:
        return

    filas = consultar_solicitudes_por_fecha(fecha, uid)
    if not filas:
        aviso(f"No se encontraron solicitudes registradas en {fecha}.")
        return

    mensaje(f"\nSolicitudes de Mantenimiento ({fecha}) - {len(filas)} registros")
    for r in filas:
        imprimir_ficha(
            f"Solicitud {r['folio']}",
            [
                ("Fecha de solicitud", r["fecha_registro"]),
                ("No. solicitud", r["folio"]),
                ("Usuario", r["nombre_usuario"]),
                ("Ubicacion", r["ubicacion"]),
                ("Equipo afectado", r["equipo_afectado"]),
                ("Tipo de problema", r["descripcion_categoria"]),
                ("Prioridad", r["nombre_prioridad"]),
                ("Problema", r["descripcion_reporte"]),
                ("Estado", r["descripcion_estado"]),
                ("Observaciones", r["observaciones"] or "Sin observaciones"),
            ],
        )


# ---------------------------------------------------------------------------
# Solicitante: mis solicitudes, seguimiento y cancelacion
# ---------------------------------------------------------------------------

def mostrar_mis_solicitudes(sesion):
    limpiar_pantalla(sesion)
    titulo("Mis solicitudes")
    filas = listar_mis_solicitudes(sesion["numero"])
    if not filas:
        aviso("\nAun no tienes solicitudes registradas.")
        return
    mensaje(f"\nTus solicitudes ({len(filas)} registros)")
    imprimir_tabla(
        ["Folio", "Fecha", "Ubicacion", "Equipo afectado", "Estado"],
        [[f["folio"], f["fecha_registro"], f["ubicacion"], f["equipo_afectado"], f["nombre_estado"]] for f in filas],
        [13, 10, 40, 24, 11],
    )


def pedir_folio(numero_cuenta=None):
    # El usuario escribe el folio; con Enter vacio se muestran los folios disponibles como ayuda
    while True:
        valor = entrada("\nEscribe el folio (ej. REP-2026-0004; Enter para ver la lista, 0 para cancelar)")
        if valor == "0":
            return None
        if valor:
            return valor.strip().upper()
        folios = listar_folios(numero_cuenta)
        if not folios:
            aviso("No hay folios disponibles.")
            return None
        mensaje("\nFolios disponibles:")
        imprimir_tabla(
            ["Folio", "Fecha", "Ubicacion", "Estado"],
            [[f["folio"], f["fecha_registro"], f["ubicacion"], f["nombre_estado"]] for f in folios],
            [13, 10, 50, 11],
        )


def buscar_folio(numero_cuenta=None):
    # Pide el folio hasta que exista (y, para un solicitante, que sea suyo)
    while True:
        folio = pedir_folio(numero_cuenta)
        if not folio:
            return None
        try:
            return consultar_seguimiento_folio(folio, numero_cuenta)
        except ValueError as e:
            error(str(e))


def mostrar_seguimiento_mi_solicitud(sesion):
    limpiar_pantalla(sesion)
    titulo("Seguimiento de mi solicitud")
    r = buscar_folio(sesion["numero"])
    if not r:
        return
    imprimir_ficha(
        f"Solicitud {r['folio']}",
        [
            ("Folio", r["folio"]),
            ("Fecha de registro", r["fecha_registro"]),
            ("Ubicacion", r["ubicacion"]),
            ("Equipo afectado", r["equipo_afectado"]),
            ("Descripcion", r["descripcion_reporte"]),
            ("Estado", r["nombre_estado"]),
        ],
    )
    if r["clave_mantenimiento"]:
        tecnicos = ", ".join(t["nombre_tecnico"] for t in r["tecnicos"]) or "Aun sin tecnicos"
        imprimir_ficha(
            "Atencion de mantenimiento",
            [
                ("Fecha programada", r["fecha_programada"]),
                ("Tecnicos", tecnicos),
            ],
            color="yellow",
        )
    else:
        imprimir_ficha("Atencion de mantenimiento", [("Fecha programada", "Aun sin orden de trabajo")], color="yellow")
    if r["fecha_resolucion"]:
        imprimir_ficha(
            "Solucion",
            [
                ("Fecha de resolucion", r["fecha_resolucion"]),
                ("Solucion aplicada", r["solucion_aplicada"]),
            ],
            color="green",
        )
    else:
        imprimir_ficha("Solucion", [("Solucion", "Sin solucion")], color="green")


def flujo_cancelar_solicitud(sesion):
    limpiar_pantalla(sesion)
    titulo("Cancelar mi solicitud")
    mensaje("Solo se pueden cancelar las solicitudes que siguen Pendiente.")
    solicitud = elegir_de_lista(
        "Solicitud a cancelar",
        listar_solicitudes_cancelables(sesion["numero"]),
        lambda s: f"{s['folio']} | {s['fecha_registro']} | {s['ubicacion']} | {s['descripcion_reporte']}",
    )
    if not solicitud:
        return
    if not confirmar(f"Confirmas cancelar la solicitud {solicitud['folio']}? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    folio = cancelar_solicitud(solicitud["folio"], sesion["numero"])
    exito(f"\nLa solicitud {folio} quedo Cancelada.")


# ---------------------------------------------------------------------------
# Consultas 2, 3, 4 y 5
# ---------------------------------------------------------------------------

def elegir_orden_opcional(sesion, pregunta, formato):
    ordenes = listar_ordenes()
    if ordenes and confirmar(pregunta, False):
        return elegir_de_lista("Orden de trabajo", ordenes, formato) or "cancelar"
    return None


def mostrar_consulta_actividades(sesion):
    limpiar_pantalla(sesion)
    titulo("Actividades de una orden de trabajo")
    elegida = elegir_orden_opcional(
        sesion,
        "Filtrar por una orden de trabajo especifica?",
        lambda o: f"{o['clave_mantenimiento']} | {o['folio']} | {o['equipo_afectado']}",
    )
    if elegida == "cancelar":
        return

    filas = consultar_actividades_orden(elegida["clave_mantenimiento"] if elegida else None)
    if not filas:
        aviso("No hay actividades registradas.")
        return

    console.print()
    imprimir_tabla(
        ["No. Orden", "Descripcion de la actividad", "Fecha", "Resultado obtenido"],
        [
            [a["clave_mantenimiento"], a["descripcion_historial"], a["fecha_historial"], a["resultado"]]
            for a in filas
        ],
        [13, 34, 10, 28],
    )


def mostrar_consulta_ordenes_edificio(sesion):
    limpiar_pantalla(sesion)
    titulo("Ordenes de trabajo por edificio")
    edificios = listar_edificios()
    edificio = None
    if confirmar("Filtrar por un edificio en especifico?", True):
        edificio = elegir_de_lista("Edificio", edificios, lambda e: e["nombre_edificio"])
        if not edificio:
            return

    filas = consultar_ordenes_edificio(edificio["clave_edificio"] if edificio else None)
    if not filas:
        aviso("No hay ordenes de trabajo para el criterio elegido.")
        return

    mensaje(f"\nOrdenes de Trabajo ({len(filas)} registros)")
    for o in filas:
        inicio = str(o["fecha_inicio"]) if o["fecha_inicio"] else "Pendiente"
        fin = str(o["fecha_fin"]) if o["fecha_fin"] else "Pendiente"
        imprimir_ficha(
            f"Orden {o['clave_mantenimiento']}",
            [
                ("No. orden", o["clave_mantenimiento"]),
                ("No. solicitud", o["folio"]),
                ("Edificio", o["nombre_edificio"]),
                ("Piso", o["piso"]),
                ("Area", o["area"]),
                ("Lugar", o["lugar"]),
                ("Tipo de mantenimiento", o["descripcion_tipo"]),
                ("Estado actual", o["descripcion_estado"]),
                ("Trabajo a realizar", o["descripcion_trabajo"]),
                ("Creacion", o["fecha_creacion"]),
                ("Programada", o["fecha_programada"]),
                ("Inicio", inicio),
                ("Fin", fin),
                ("Observaciones", o["observaciones"] or "Sin observaciones"),
                ("Costo mano de obra", f"${float(o['costo_mano_obra']):.2f}"),
                ("Costo materiales", f"${float(o['costo_materiales']):.2f}"),
            ],
            color="yellow",
        )


def mostrar_consulta_tecnicos(sesion):
    limpiar_pantalla(sesion)
    titulo("Tecnicos asignados a ordenes")
    elegida = elegir_orden_opcional(
        sesion,
        "Filtrar por una orden de trabajo?",
        lambda o: f"{o['clave_mantenimiento']} | {o['folio']} | {o['nombre_edificio']}",
    )
    if elegida == "cancelar":
        return

    filas = consultar_tecnicos_orden(elegida["clave_mantenimiento"] if elegida else None)
    if not filas:
        aviso("No hay tecnicos asignados.")
        return

    console.print()
    imprimir_tabla(
        ["No. Orden", "Tecnico", "Fecha asig.", "Horas", "Actividad asignada"],
        [
            [
                t["clave_mantenimiento"],
                t["nombre_tecnico"],
                t["fecha_asignacion"],
                f"{float(t['horas_asignadas']):.2f}",
                t["actividad_asignada"],
            ]
            for t in filas
        ],
        [13, 22, 11, 6, 34],
    )


def mostrar_consulta_planes(sesion):
    limpiar_pantalla(sesion)
    titulo("Planes de mantenimiento preventivo")
    edificios = listar_edificios()
    edificio = None
    if confirmar("Filtrar por un edificio en especifico?", False):
        edificio = elegir_de_lista("Edificio", edificios, lambda e: e["nombre_edificio"])
        if not edificio:
            return

    filas = consultar_planes_edificio(edificio["clave_edificio"] if edificio else None)
    if not filas:
        aviso("No hay planes preventivos registrados.")
        return

    mensaje(f"\nPlanes de Mantenimiento Preventivo ({len(filas)} registros)")
    for p in filas:
        imprimir_ficha(
            f"Plan {p['clave_plan']}",
            [
                ("No. plan", p["clave_plan"]),
                ("Nombre del plan", p["nombre_plan"]),
                ("Edificio", p["nombre_edificio"]),
                ("Equipo", p["nombre_equipo"]),
                ("Descripcion", p["descripcion_plan"]),
                ("Frecuencia", p["frecuencia"]),
                ("Duracion estimada", f"{float(p['duracion_estimada_horas']):.2f} hrs"),
                ("Estado", p["estado_plan"]),
            ],
        )


# ---------------------------------------------------------------------------
# Registros 2, 3, 4 y 5: personal de mantenimiento
# ---------------------------------------------------------------------------

def formato_orden(o):
    return f"{o['clave_mantenimiento']} | {o['folio']} | {o['ubicacion']} | {o['equipo_afectado']} ({o['nombre_estado']})"


def flujo_registrar_orden(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar orden de trabajo")
    solicitudes = listar_solicitudes_disponibles()
    sol = elegir_de_lista(
        "Solicitud de mantenimiento (Pendiente)",
        solicitudes,
        lambda s: f"{s['folio']} | {s['fecha_registro']} | {s['ubicacion']} | {s['equipo_afectado']}",
    )
    if not sol:
        return
    mensaje(f"Ubicacion: {sol['ubicacion']}")
    mensaje(f"Equipo afectado: {sol['equipo_afectado']}")
    mensaje(f"Problema reportado: {sol['descripcion_reporte']}")

    # El supervisor clasifica la solicitud: categoria y prioridad de sus catalogos
    cats = listar_catalogos_solicitud()
    categoria = elegir_de_lista(
        "Categoria del problema",
        cats["categorias"],
        lambda c: f"{c['nombre_categoria']} ({c['descripcion_categoria']})"
        + (" (actual)" if c["nombre_categoria"] == sol["nombre_categoria"] else ""),
    )
    if not categoria:
        return
    prioridad = elegir_de_lista(
        "Prioridad",
        cats["prioridades"],
        lambda p: f"{p['nombre_prioridad']} ({p['descripcion_prioridad']})"
        + (" (actual)" if p["nombre_prioridad"] == sol["nombre_prioridad"] else ""),
    )
    if not prioridad:
        return

    observaciones_reporte = None
    if not sol["observaciones"]:
        observaciones_reporte = pedir_texto_opcional("\nObservaciones del reporte (opcional)", 250)
    else:
        mensaje(f"Observaciones del reporte: {sol['observaciones']}")

    tipo = elegir_de_lista(
        "Tipo de mantenimiento",
        listar_tipos_mantenimiento(),
        lambda t: f"{t['nombre_tipo']} ({t['descripcion_tipo']})",
    )
    if not tipo:
        return

    fecha_prog = pedir_fecha("\nFecha programada")
    if not fecha_prog:
        return

    trabajo = pedir_texto("Descripcion del trabajo a realizar (0 para cancelar)", permitir_cancelar=True)
    if not trabajo:
        return
    obs = entrada("Observaciones de la orden (opcional)")
    mano_obra = pedir_decimal("Costo de mano de obra", 0.0)
    materiales = pedir_decimal("Costo de materiales", 0.0)

    clave = registrar_orden_trabajo(
        sol["folio"],
        tipo["codigo_tipo"],
        fecha_prog,
        trabajo,
        obs or None,
        mano_obra,
        materiales,
        categoria["nombre_categoria"],
        prioridad["nombre_prioridad"],
        observaciones_reporte,
    )
    exito(f"\nOrden de trabajo {clave} registrada correctamente.")
    mensaje(f"La solicitud {sol['folio']} quedo clasificada con su categoria y prioridad y paso a En revision.")


def flujo_asignar_tecnicos(sesion):
    limpiar_pantalla(sesion)
    titulo("Asignar tecnicos a una orden de trabajo")
    orden = elegir_de_lista(
        "Orden de trabajo (Pendiente o En proceso)",
        listar_ordenes(estados=("Pendiente", "En proceso")),
        lambda o: formato_orden(o) + f" - {o['tecnicos']} tecnico(s)",
    )
    if not orden:
        return

    tecnicos = listar_tecnicos(excluir_orden=orden["clave_mantenimiento"])
    asignaciones = []
    elegidos = set()
    ya_asignados = orden["tecnicos"]
    faltan = max(0, 2 - ya_asignados)

    if faltan:
        mensaje(f"\nSe requiere que la orden tenga al menos 2 tecnicos (ahora tiene {ya_asignados}).")
    else:
        mensaje(f"\nLa orden ya tiene {ya_asignados} tecnicos; puedes agregar mas.")
    while True:
        disponibles = [t for t in tecnicos if t["numero_empleado"] not in elegidos]
        if not disponibles:
            break
        tecnico = elegir_de_lista(
            f"Tecnico #{ya_asignados + len(asignaciones) + 1}",
            disponibles,
            lambda t: f"{t['nombre_completo']} ({t['especialidad']})",
        )
        if not tecnico:
            if len(asignaciones) < max(faltan, 1):
                aviso("Asignacion cancelada.")
                return
            break

        horas = pedir_decimal(f"Horas asignadas a {tecnico['nombre_completo']}", 2.0)
        actividad = pedir_texto("Actividad a realizar")

        asignaciones.append(
            {
                "numero_empleado": tecnico["numero_empleado"],
                "horas": horas,
                "actividad": actividad,
            }
        )
        elegidos.add(tecnico["numero_empleado"])

        if len(asignaciones) >= faltan and not confirmar("Asignar otro tecnico adicional?", False):
            break

    if not asignaciones:
        aviso("No hay tecnicos disponibles para asignar.")
        return
    asignar_tecnicos_orden(orden["clave_mantenimiento"], asignaciones)
    exito(f"\n{len(asignaciones)} tecnicos asignados a {orden['clave_mantenimiento']}.")
    mensaje("La orden y su solicitud quedaron En proceso.")


def flujo_cancelar_orden(sesion):
    limpiar_pantalla(sesion)
    titulo("Cancelar orden de trabajo")
    mensaje("Solo se cancelan ordenes Pendiente o En proceso. La solicitud regresa a Pendiente.")
    orden = elegir_de_lista(
        "Orden a cancelar",
        listar_ordenes(estados=("Pendiente", "En proceso")),
        formato_orden,
    )
    if not orden:
        return
    if not confirmar(f"Confirmas cancelar la orden {orden['clave_mantenimiento']}? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    folio = cancelar_orden(orden["clave_mantenimiento"])
    exito(f"\nOrden {orden['clave_mantenimiento']} cancelada.")
    mensaje(f"La solicitud {folio} regreso a Pendiente para crearle otra orden.")


def mostrar_mis_ordenes(sesion):
    limpiar_pantalla(sesion)
    titulo("Mis ordenes asignadas")
    filas = listar_mis_ordenes(sesion["numero"])
    if not filas:
        aviso("\nNo tienes ordenes de trabajo asignadas.")
        return
    mensaje(f"\nOrdenes donde estas asignado ({len(filas)} registros)")
    imprimir_tabla(
        ["Orden", "Folio", "Ubicacion", "Equipo afectado", "Estado", "Programada"],
        [
            [o["clave_mantenimiento"], o["folio"], o["ubicacion"], o["equipo_afectado"], o["nombre_estado"], o["fecha_programada"]]
            for o in filas
        ],
        [13, 13, 32, 20, 11, 10],
    )


def flujo_registrar_actividades(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar actividades en una orden de trabajo")
    # Solo ordenes En proceso con al menos 2 tecnicos; un tecnico ve solo las suyas
    ordenes = listar_ordenes(
        estados=("En proceso",),
        numero_empleado=None if es_supervisor(sesion) else sesion["numero"],
        min_tecnicos=2,
    )
    orden = elegir_de_lista("Orden de trabajo (En proceso)", ordenes, formato_orden)
    if not orden:
        return

    actividades = []
    mensaje("\nSe requiere registrar al menos 2 actividades especificas.")
    while True:
        num_act = len(actividades) + 1
        desc = Prompt.ask(
            _etiqueta(f"Actividad #{num_act} - Descripcion (0 para cancelar)"), console=console, default="", show_default=False
        ).strip()
        if desc == "0":
            if len(actividades) < 2:
                aviso("Registro de actividades cancelado.")
                return
            break
        if not desc:
            continue

        fecha_act = pedir_fecha(f"Actividad #{num_act} - Fecha")
        if not fecha_act:
            return
        resultado = pedir_texto(f"Actividad #{num_act} - Resultado obtenido")

        actividades.append({"descripcion": desc, "fecha": fecha_act, "resultado": resultado})
        if len(actividades) >= 2 and not confirmar("Agregar otra actividad?", False):
            break

    registrar_actividades_orden(
        orden["clave_mantenimiento"], actividades, numero_empleado=sesion["numero"], es_supervisor=es_supervisor(sesion)
    )
    exito(f"\n{len(actividades)} actividades registradas en {orden['clave_mantenimiento']}.")


def flujo_registrar_plan(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar plan de mantenimiento preventivo")
    mensaje("El plan se registra para un equipo del edificio Docencia 1.")
    piso = elegir_de_lista("Piso del equipo", list(PISOS), lambda p: p)
    if not piso:
        return
    area = elegir_de_lista(
        f"Area de {piso}",
        listar_areas_con_equipos(piso),
        lambda a: f"{a['area']} ({a['equipos']} equipo(s))",
    )
    if not area:
        return
    equipo = elegir_de_lista(
        "Equipo de trabajo",
        listar_equipos_por_piso_area(piso, area["area"]),
        lambda eq: f"{eq['nombre_equipo']} (Salon {eq['salon']})",
    )
    if not equipo:
        return

    nombre = pedir_texto("\nNombre del plan (0 para cancelar)", permitir_cancelar=True)
    if not nombre:
        return
    descripcion = pedir_texto("Descripcion del plan")
    otra = "Otra"
    frecuencia = elegir_de_lista("Frecuencia", list(FRECUENCIAS) + [otra], lambda f: f)
    if not frecuencia:
        return
    if frecuencia == otra:
        frecuencia = pedir_texto_limitado("Escribe la frecuencia (ej. Cada 15 dias) (0 para cancelar)", MAX_FRECUENCIA)
        if not frecuencia:
            return
    duracion = pedir_decimal("Duracion estimada en horas", 2.0)
    estado = elegir_de_lista("Estado del plan", list(ESTADOS_PLAN), lambda e: e)
    if not estado:
        return

    clave_plan = registrar_plan_preventivo(
        nombre,
        equipo["codigo_inventario"],
        descripcion,
        frecuencia,
        duracion,
        estado,
    )
    exito(f"\nPlan preventivo {clave_plan} registrado correctamente.")


def flujo_registrar_solucion(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar solucion y materiales utilizados")
    # Solo reportes con su orden En proceso y sin solucion; un tecnico ve solo los de sus ordenes
    reporte = elegir_de_lista(
        "Reporte con orden En proceso",
        listar_reportes_sin_solucion(sesion["numero"], es_supervisor(sesion)),
        lambda r: f"{r['folio']} | {r['clave_mantenimiento']} | {r['ubicacion']} | {r['equipo_afectado']}",
    )
    if not reporte:
        return
    mensaje(f"Equipo afectado: {reporte['equipo_afectado']}")
    mensaje(f"Problema reportado: {reporte['descripcion_reporte']}")

    aplicada = pedir_texto("\nSolucion aplicada (0 para cancelar)", permitir_cancelar=True)
    if not aplicada:
        return
    tiempo = pedir_decimal("Tiempo de resolucion en horas", 1.0)
    obs = entrada("Observaciones (opcional)")

    materiales = []
    usados = set()
    while confirmar("Registrar un material utilizado?", False):
        disponibles = [m for m in listar_materiales() if m["codigo_material"] not in usados and m["existencia"] > 0]
        material = elegir_de_lista(
            "Material",
            disponibles,
            lambda m: f"{m['nombre_material']} (existencia: {m['existencia']})",
        )
        if not material:
            break
        cantidad = pedir_entero(f"Cantidad usada de {material['nombre_material']}", 1)
        if cantidad <= 0 or cantidad > material["existencia"]:
            error(f"La cantidad debe estar entre 1 y {material['existencia']}.")
            continue
        materiales.append({"codigo_material": material["codigo_material"], "cantidad": cantidad})
        usados.add(material["codigo_material"])

    numero_solucion = registrar_solucion(
        reporte["folio"], tiempo, aplicada, obs or None, materiales,
        numero_empleado=sesion["numero"], es_supervisor=es_supervisor(sesion),
    )
    exito(f"\nSolucion {numero_solucion} registrada para {reporte['folio']} ({len(materiales)} materiales).")
    exito(f"La orden {reporte['clave_mantenimiento']} y el reporte quedaron en estado Solucionado.")


def mostrar_consulta_soluciones(sesion):
    limpiar_pantalla(sesion)
    titulo("Soluciones aplicadas y materiales utilizados")
    filas = consultar_soluciones()
    if not filas:
        aviso("No hay soluciones registradas.")
        return

    mensaje(f"\nSoluciones ({len(filas)} registros)")
    for s in filas:
        if s["materiales"]:
            mats = ", ".join(f"{m['nombre_material']} x{m['cantidad_usada']}" for m in s["materiales"])
        else:
            mats = "Sin materiales"
        imprimir_ficha(
            f"Solucion {s['numero_solucion']}",
            [
                ("No. solicitud", s["folio"]),
                ("Equipo afectado", s["equipo_afectado"]),
                ("Fecha de resolucion", s["fecha_resolucion"]),
                ("Tiempo de resolucion", f"{float(s['tiempo_resolucion']):.2f} hrs"),
                ("Solucion aplicada", s["solucion_aplicada"]),
                ("Materiales utilizados", mats),
                ("Observaciones", s["observaciones_solucion"] or "Sin observaciones"),
            ],
            color="green",
        )


# ---------------------------------------------------------------------------
# Consultas 7, 8, 9 y 10
# ---------------------------------------------------------------------------

def mostrar_consulta_seguimiento(sesion):
    limpiar_pantalla(sesion)
    titulo("Seguimiento de un reporte por folio")
    r = buscar_folio()
    if not r:
        return

    imprimir_ficha(
        f"Reporte {r['folio']}",
        [
            ("Folio", r["folio"]),
            ("Fecha de registro", r["fecha_registro"]),
            ("Solicitante", r["nombre_usuario"]),
            ("Ubicacion", r["ubicacion"]),
            ("Equipo afectado", r["equipo_afectado"]),
            ("Categoria", r["nombre_categoria"]),
            ("Prioridad", r["nombre_prioridad"]),
            ("Estado", r["nombre_estado"]),
            ("Descripcion", r["descripcion_reporte"]),
            ("Observaciones", r["observaciones"] or "Sin observaciones"),
        ],
    )

    if r["clave_mantenimiento"]:
        imprimir_ficha(
            "Orden de trabajo",
            [
                ("No. orden", r["clave_mantenimiento"]),
                ("Estado", r["estado_orden"]),
                ("Fecha programada", r["fecha_programada"]),
            ],
            color="yellow",
        )
        if r["tecnicos"]:
            mensaje("\nTecnicos asignados:")
            imprimir_tabla(
                ["Tecnico", "Especialidad", "Horas", "Actividad asignada"],
                [
                    [t["nombre_tecnico"], t["especialidad"], f"{float(t['horas_asignadas']):.2f}", t["actividad_asignada"]]
                    for t in r["tecnicos"]
                ],
                [22, 20, 6, 30],
            )
        else:
            mensaje("\nTecnicos asignados: Sin tecnicos")
    else:
        imprimir_ficha("Orden de trabajo", [("No. orden", "Sin orden")], color="yellow")

    if r["fecha_resolucion"]:
        imprimir_ficha(
            "Solucion",
            [
                ("Fecha de resolucion", r["fecha_resolucion"]),
                ("Solucion aplicada", r["solucion_aplicada"]),
            ],
            color="green",
        )
    else:
        imprimir_ficha("Solucion", [("Solucion", "Sin solucion")], color="green")


def mostrar_consulta_reportes_estado(sesion):
    limpiar_pantalla(sesion)
    titulo("Reportes pendientes y solucionados")
    resumen = resumen_reportes_por_estado()
    mensaje("\nResumen por estado:")
    imprimir_tabla(
        ["Estado", "Reportes"],
        [[e["nombre_estado"], e["total"]] for e in resumen] + [["Total", sum(e["total"] for e in resumen)]],
        [14, 8],
    )

    estado = None
    if confirmar("\nFiltrar por un estado?", False):
        estado = elegir_de_lista("Estado", resumen, lambda e: f"{e['nombre_estado']} ({e['total']})")
        if not estado:
            return

    filas = consultar_reportes_por_estado(estado["nombre_estado"] if estado else None)
    if not filas:
        aviso(f"No hay reportes en estado {estado['nombre_estado']}.")
        return

    mensaje(f"\nReportes ({len(filas)} registros)")
    imprimir_tabla(
        ["Folio", "Fecha", "Ubicacion", "Categoria", "Prioridad", "Estado", "Dias"],
        [
            [
                f["folio"], f["fecha_registro"], f["ubicacion"], f["nombre_categoria"],
                f["nombre_prioridad"], f["nombre_estado"], f["dias_abiertos"],
            ]
            for f in filas
        ],
        [13, 10, 24, 15, 11, 11, 4],
    )
    mensaje("Dias: dias abiertos hasta la solucion o hasta hoy si aun no se resuelve.")


def mostrar_consulta_materiales_reponer(sesion):
    limpiar_pantalla(sesion)
    titulo("Materiales por reponer")
    filas = consultar_materiales_por_reponer()
    if not filas:
        aviso("Todos los materiales estan por encima de su stock minimo.")
        return

    mensaje(f"\nMateriales en o bajo su stock minimo ({len(filas)} registros)")
    imprimir_tabla(
        ["Codigo", "Material", "Existencia", "Minimo", "Faltante", "Total usado", "Soluciones"],
        [
            [
                m["codigo_material"], m["nombre_material"], m["existencia"], m["stock_minimo"],
                m["faltante"], m["total_usado"], m["soluciones"],
            ]
            for m in filas
        ],
        [8, 24, 10, 6, 8, 11, 10],
    )


def mostrar_consulta_piso_area(sesion):
    limpiar_pantalla(sesion)
    titulo("Reportes por piso y area")
    filas = consultar_reportes_piso_area()
    if not filas:
        aviso("No hay reportes registrados.")
        return

    console.print()
    imprimir_tabla(
        ["Piso", "Area", "Pendiente", "En revision", "En proceso", "Solucionado", "Cancelado", "Total"],
        [
            [
                f["piso"], f["area"], f["pendiente"], f["en_revision"],
                f["en_proceso"], f["solucionado"], f["cancelado"], f["total"],
            ]
            for f in filas
        ],
        [11, 18, 9, 11, 10, 11, 9, 5],
    )

    if not confirmar("\nVer el detalle de un piso y area?", False):
        return
    grupo = elegir_de_lista(
        "Piso y area",
        filas,
        lambda f: f"{f['piso']} - {f['area']} ({f['total']} reportes)",
    )
    if not grupo:
        return

    detalle = consultar_detalle_piso_area(grupo["piso"], grupo["area"])
    mensaje(f"\n{grupo['piso']} - {grupo['area']} ({len(detalle)} registros)")
    imprimir_tabla(
        ["Folio", "Fecha", "Lugar", "Estado"],
        [[d["folio"], d["fecha_registro"], d["lugar"], d["nombre_estado"]] for d in detalle],
        [13, 10, 28, 12],
    )


# ---------------------------------------------------------------------------
# Materiales y personal
# ---------------------------------------------------------------------------

def imprimir_inventario(materiales):
    filas = []
    for m in materiales:
        aviso = "REPONER" if m["existencia"] <= m["stock_minimo"] else "ok"
        filas.append([m["codigo_material"], m["nombre_material"], m["existencia"], m["stock_minimo"], aviso])
    imprimir_tabla(["No.", "Material", "Existencia", "Minimo", "Estado"], filas, [8, 32, 10, 7, 8])


def mostrar_inventario(sesion):
    limpiar_pantalla(sesion)
    titulo("Inventario de materiales")
    materiales = listar_inventario()
    if not materiales:
        aviso("No hay materiales registrados.")
        return
    console.print()
    imprimir_inventario(materiales)


def flujo_registrar_material(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar material nuevo")
    nombre = pedir_texto("Nombre del material (0 para cancelar)", permitir_cancelar=True)
    if not nombre:
        return
    descripcion = pedir_texto("Descripcion")
    existencia = pedir_entero("Existencia inicial", 0)
    minimo = pedir_entero("Stock minimo antes de reponer", 5)
    codigo_material = registrar_material(nombre, descripcion, existencia, minimo)
    exito(f"\nMaterial {codigo_material} registrado con existencia de {existencia}.")


def flujo_eliminar_material(sesion):
    limpiar_pantalla(sesion)
    titulo("Eliminar material")
    material = elegir_de_lista(
        "Material a eliminar",
        listar_inventario(),
        lambda m: f"{m['nombre_material']} (existencia: {m['existencia']})"
        + (f" - usado en {m['usos']} solucion(es)" if m["usos"] else ""),
    )
    if not material:
        return
    # Se valida antes de pedir confirmacion; eliminar_material vuelve a revisarlo como respaldo
    if material["usos"]:
        aviso(
            f"\nAviso: {material['nombre_material']} ya se utilizo en {material['usos']} solucion(es) "
            "y no puede eliminarse para no perder el historial. Si ya no hay, deja su existencia en 0."
        )
        return
    mensaje(f"\nSe eliminara por completo el material {material['nombre_material']} del inventario.")
    if not confirmar("Confirmas la eliminacion? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    nombre = eliminar_material(material["codigo_material"])
    exito(f"\nMaterial {nombre} eliminado del inventario.")


def flujo_material_tomado(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar material tomado")
    # Un tecnico solo ve las soluciones de las ordenes donde esta asignado
    solucion = elegir_de_lista(
        "Solucion a la que se asigna el material",
        listar_soluciones_registradas(None if es_supervisor(sesion) else sesion["numero"]),
        lambda s: f"Solucion {s['numero_solucion']} | {s['folio']} | {s['equipo_afectado']}",
    )
    if not solucion:
        return
    material = elegir_de_lista(
        "Material tomado",
        [m for m in listar_inventario() if m["existencia"] > 0],
        lambda m: f"{m['nombre_material']} (existencia: {m['existencia']})",
    )
    if not material:
        return
    cantidad = pedir_entero(f"Cantidad tomada de {material['nombre_material']} (disponibles: {material['existencia']})", 1)
    mat = registrar_material_tomado(
        solucion["numero_solucion"], material["codigo_material"], cantidad,
        numero_empleado=sesion["numero"], es_supervisor=es_supervisor(sesion),
    )
    exito(f"\nSe tomaron {cantidad} de {mat['nombre_material']}. Existencia restante: {mat['existencia']}.")
    if mat["existencia"] <= mat["stock_minimo"]:
        aviso(f"Aviso: la existencia esta en o por debajo del minimo ({mat['stock_minimo']}). Conviene reponer.")


def flujo_reabastecer_material(sesion):
    limpiar_pantalla(sesion)
    titulo("Reabastecer material")
    material = elegir_de_lista(
        "Material a reabastecer",
        listar_inventario(),
        lambda m: f"{m['nombre_material']} (existencia: {m['existencia']})",
    )
    if not material:
        return
    cantidad = pedir_entero(f"Cantidad que ingresa de {material['nombre_material']}", 1)
    mat = reabastecer_material(material["codigo_material"], cantidad)
    exito(f"\nExistencia actualizada de {mat['nombre_material']}: {mat['existencia']}.")


def menu_materiales(sesion):
    # El tecnico solo ve el inventario y registra material tomado
    ejecutar_menu(
        sesion,
        "Gestion de materiales",
        [
            ("Ver inventario", mostrar_inventario, False, False),
            ("Registrar material nuevo", flujo_registrar_material, False, True),
            ("Registrar material tomado (descuenta solo la cantidad)", flujo_material_tomado, False, False),
            ("Reabastecer material", flujo_reabastecer_material, False, True),
            ("Eliminar material", flujo_eliminar_material, False, True),
        ],
        "Regresar",
    )


def mostrar_tecnicos(sesion):
    limpiar_pantalla(sesion)
    titulo("Tecnicos de mantenimiento")
    tecnicos = listar_tecnicos_gestion()
    console.print()
    imprimir_tabla(
        ["Num. empleado", "Tecnico", "Especialidad", "Supervisor", "Trabajos"],
        [
            [t["numero_empleado"], t["nombre_completo"], t["especialidad"], t["nombre_supervisor"] or "Ninguno", t["asignaciones"]]
            for t in tecnicos
        ],
        [8, 26, 22, 14, 8],
    )


def flujo_eliminar_tecnico(sesion):
    limpiar_pantalla(sesion)
    titulo("Eliminar tecnico")
    # El usuario con la sesion abierta no aparece: no puede eliminarse a si mismo
    tecnicos = [t for t in listar_tecnicos_gestion() if t["numero_empleado"] != sesion["numero"]]
    tecnico = elegir_de_lista(
        "Tecnico a eliminar",
        tecnicos,
        lambda t: f"{t['nombre_completo']} ({t['especialidad']}) - {t['asignaciones']} trabajos",
    )
    if not tecnico:
        return
    # Se valida antes de pedir confirmacion; eliminar_tecnico vuelve a revisarlo como respaldo
    if tecnico["asignaciones"]:
        aviso(
            f"\nAviso: {tecnico['nombre_completo']} tiene trabajos asignados en ordenes de "
            "mantenimiento y no puede eliminarse para no perder el historial."
        )
        return
    if tecnico["supervisados"] and tecnico["empleado_supervisor"] is None:
        aviso(
            f"\nAviso: {tecnico['nombre_completo']} es supervisor de {tecnico['supervisados']} "
            "tecnico(s) y no tiene un supervisor a quien pasarlos. Reasigna primero esa supervision."
        )
        return
    mensaje(f"\nSe eliminara a {tecnico['nombre_completo']} del personal de mantenimiento.")
    if not confirmar("Confirmas la eliminacion? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    nombre, supervisados = eliminar_tecnico(tecnico["numero_empleado"], sesion["numero"])
    exito(f"\nTecnico {nombre} eliminado.")
    if supervisados:
        mensaje(f"Sus {supervisados} supervisado(s) pasaron a su supervisor.")


def menu_personal(sesion):
    if not sesion.get("es_supervisor"):
        aviso("Solo un supervisor puede registrar o eliminar personal.")
        return
    while True:
        limpiar_pantalla(sesion)
        mostrar_menu(
            "Gestion de personal",
            [
                ("1", "Registrar docente, administrativo o tecnico"),
                ("2", "Eliminar tecnico"),
                ("3", "Ver tecnicos"),
                ("0", "Regresar"),
            ],
        )
        op = pedir_opcion(["0", "1", "2", "3"])
        if op == "0":
            break
        if op == "1":
            ejecutar_opcion(flujo_registrar_personal, sesion)
        elif op == "2":
            ejecutar_opcion(flujo_eliminar_tecnico, sesion)
        elif op == "3":
            ejecutar_opcion(mostrar_tecnicos, sesion)
        pausar()


# ---------------------------------------------------------------------------
# Gestion de equipos (solo supervisores)
# ---------------------------------------------------------------------------

def formato_equipo(e):
    return f"{e['codigo_inventario']} | {e['nombre_equipo']} ({e['piso']}, {e['area']}, {e['salon']})"


def mostrar_equipos(sesion):
    limpiar_pantalla(sesion)
    titulo("Equipos de Docencia 1")
    equipos = listar_equipos()
    if not equipos:
        aviso("No hay equipos registrados.")
        return
    console.print()
    imprimir_tabla(
        ["Codigo", "Nombre", "Tipo", "Piso", "Area", "Salon", "Reparar"],
        [
            [
                e["codigo_inventario"], e["nombre_equipo"], e["tipo_equipo_instalacion"], e["piso"],
                e["area"], e["salon"], "Si" if e["necesita_reparacion"] else "No",
            ]
            for e in equipos
        ],
        [12, 22, 16, 11, 18, 9, 7],
    )


def pedir_ubicacion_equipo(piso_actual=None, area_actual=None, salon_actual=None):
    # Piso y area de las mismas listas del registro de solicitudes; salon o lugar libre
    piso = elegir_de_lista("Piso", list(PISOS), lambda p: p + (" (actual)" if p == piso_actual else ""))
    if not piso:
        return None
    area = elegir_de_lista(
        f"Area de {piso}",
        list(AREAS_POR_PISO[piso]),
        lambda a: a + (" (actual)" if piso == piso_actual and a == area_actual else ""),
    )
    if not area:
        return None
    if area == AREA_OTRA:
        area = pedir_texto_limitado("Escribe el area (0 para cancelar)", MAX_AREA)
        if not area:
            return None
    while True:
        etiqueta = "Salon o lugar (ej. 104, LAB-REDES, CUB-3)"
        salon = entrada(etiqueta, salon_actual) if salon_actual else pedir_texto(etiqueta)
        if len(salon) <= MAX_SALON:
            return piso, area, salon
        error(f"El salon o lugar no puede pasar de {MAX_SALON} caracteres.")


def pedir_dato(etiqueta, maximo, actual=None):
    while True:
        valor = entrada(etiqueta, actual) if actual else pedir_texto(etiqueta)
        if len(valor) <= maximo:
            return valor
        error(f"El texto no puede pasar de {maximo} caracteres (escribiste {len(valor)}).")


def flujo_registrar_equipo(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar equipo")
    mensaje("El equipo se registra en el edificio Docencia 1.")
    while True:
        codigo = pedir_texto(
            "\nCodigo de inventario (etiqueta del equipo, ej. EQ-D1-PROY02) (0 para cancelar)",
            permitir_cancelar=True,
        )
        if not codigo:
            return
        codigo = codigo.upper()
        if len(codigo) > MAX_CODIGO_EQUIPO:
            error(f"El codigo no puede pasar de {MAX_CODIGO_EQUIPO} caracteres.")
        elif existe_equipo(codigo):
            error(f"Ya existe un equipo con el codigo {codigo}. Escribe otro.")
        else:
            break

    nombre = pedir_dato("Nombre del equipo", MAX_NOMBRE_EQUIPO)
    tipo = pedir_dato("Tipo (ej. Equipo de Computo, Climatizacion)", MAX_TIPO_EQUIPO)
    ubicacion = pedir_ubicacion_equipo()
    if not ubicacion:
        return
    piso, area, salon = ubicacion
    reparar = confirmar("Necesita reparacion", False)

    registrado = registrar_equipo(codigo, nombre, tipo, piso, area, salon, reparar)
    exito(f"\nEquipo {registrado} registrado en Docencia 1, {piso}, {area}, {salon}.")


def flujo_editar_equipo(sesion):
    limpiar_pantalla(sesion)
    titulo("Editar equipo")
    equipo = elegir_de_lista("Equipo a editar", listar_equipos(), formato_equipo)
    if not equipo:
        return
    mensaje("\nPresiona Enter para conservar el valor actual.")
    nombre = pedir_dato("Nombre del equipo", MAX_NOMBRE_EQUIPO, equipo["nombre_equipo"])
    tipo = pedir_dato("Tipo", MAX_TIPO_EQUIPO, equipo["tipo_equipo_instalacion"])

    piso, area, salon = equipo["piso"], equipo["area"], equipo["salon"]
    if confirmar("Cambiar el piso o el area del equipo?", False):
        ubicacion = pedir_ubicacion_equipo(piso, area, salon)
        if not ubicacion:
            return
        piso, area, salon = ubicacion
    else:
        while True:
            salon = entrada("Salon o lugar", equipo["salon"])
            if len(salon) <= MAX_SALON:
                break
            error(f"El salon o lugar no puede pasar de {MAX_SALON} caracteres.")

    reparar = confirmar("Necesita reparacion", bool(equipo["necesita_reparacion"]))

    editar_equipo(equipo["codigo_inventario"], nombre, tipo, piso, area, salon, reparar)
    exito(f"\nEquipo {equipo['codigo_inventario']} actualizado: {nombre} (Docencia 1, {piso}, {area}, {salon}).")


def flujo_eliminar_equipo(sesion):
    limpiar_pantalla(sesion)
    titulo("Eliminar equipo")
    equipo = elegir_de_lista(
        "Equipo a eliminar",
        listar_equipos(),
        lambda e: formato_equipo(e) + (f" - {e['planes']} plan(es)" if e["planes"] else ""),
    )
    if not equipo:
        return
    # Se valida antes de pedir confirmacion; eliminar_equipo vuelve a revisarlo como respaldo
    planes = usos_equipo(equipo["codigo_inventario"])
    if planes:
        aviso(f"\nAviso: {equipo['nombre_equipo']} no puede eliminarse para no perder el historial.")
        aviso(f"Aparece en los planes: {', '.join(planes)}.", "    ")
        return
    mensaje(f"\nSe eliminara el equipo {equipo['nombre_equipo']} ({equipo['codigo_inventario']}).")
    if not confirmar("Confirmas la eliminacion? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    nombre = eliminar_equipo(equipo["codigo_inventario"])
    exito(f"\nEquipo {nombre} eliminado.")


def menu_equipos(sesion):
    if not sesion.get("es_supervisor"):
        aviso("Solo un supervisor puede gestionar los equipos.")
        return
    while True:
        limpiar_pantalla(sesion)
        mostrar_menu(
            "Gestion de equipos",
            [
                ("1", "Ver equipos"),
                ("2", "Registrar equipo"),
                ("3", "Editar ubicacion o datos de un equipo"),
                ("4", "Eliminar equipo"),
                ("0", "Regresar"),
            ],
        )
        op = pedir_opcion(["0", "1", "2", "3", "4"])
        if op == "0":
            break
        if op == "1":
            ejecutar_opcion(mostrar_equipos, sesion)
        elif op == "2":
            ejecutar_opcion(flujo_registrar_equipo, sesion)
        elif op == "3":
            ejecutar_opcion(flujo_editar_equipo, sesion)
        elif op == "4":
            ejecutar_opcion(flujo_eliminar_equipo, sesion)
        pausar()


# ---------------------------------------------------------------------------
# Gestion de catalogos (solo supervisores): categorias y tipos de mantenimiento.
# Estados y prioridades son fijos y no se editan desde el sistema.
# ---------------------------------------------------------------------------

def mostrar_categorias(sesion):
    limpiar_pantalla(sesion)
    titulo("Categorias")
    categorias = listar_categorias()
    if not categorias:
        aviso("No hay categorias registradas.")
        return
    console.print()
    imprimir_tabla(
        ["Categoria", "Descripcion", "Reportes"],
        [[c["nombre_categoria"], c["descripcion_categoria"], c["reportes"]] for c in categorias],
        [16, 44, 8],
    )


def flujo_registrar_categoria(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar categoria")
    while True:
        nombre = pedir_texto("Nombre de la categoria (ej. Plomeria) (0 para cancelar)", permitir_cancelar=True)
        if not nombre:
            return
        if len(nombre) > MAX_NOMBRE_CATEGORIA:
            error(f"El nombre no puede pasar de {MAX_NOMBRE_CATEGORIA} caracteres.")
        elif existe_categoria(nombre):
            error(f"Ya existe la categoria {nombre}. Escribe otra.")
        else:
            break
    descripcion = pedir_dato("Descripcion", MAX_DESCRIPCION_CATALOGO)
    registrada = registrar_categoria(nombre, descripcion)
    exito(f"\nCategoria {registrada} registrada.")


def flujo_eliminar_categoria(sesion):
    limpiar_pantalla(sesion)
    titulo("Eliminar categoria")
    categoria = elegir_de_lista(
        "Categoria a eliminar",
        listar_categorias(),
        lambda c: c["nombre_categoria"] + (f" - usada en {c['reportes']} reporte(s)" if c["reportes"] else ""),
    )
    if not categoria:
        return
    # Se valida antes de pedir confirmacion; eliminar_categoria vuelve a revisarlo como respaldo
    if categoria["reportes"]:
        aviso(
            f"\nAviso: la categoria {categoria['nombre_categoria']} se usa en {categoria['reportes']} "
            "reporte(s) y no puede eliminarse para no perder el historial."
        )
        return
    if not confirmar(f"Confirmas eliminar la categoria {categoria['nombre_categoria']}? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    eliminar_categoria(categoria["nombre_categoria"])
    exito(f"\nCategoria {categoria['nombre_categoria']} eliminada.")


def mostrar_tipos(sesion):
    limpiar_pantalla(sesion)
    titulo("Tipos de mantenimiento")
    tipos = listar_tipos_gestion()
    if not tipos:
        aviso("No hay tipos de mantenimiento registrados.")
        return
    console.print()
    imprimir_tabla(
        ["Codigo", "Tipo", "Descripcion", "Ordenes"],
        [[t["codigo_tipo"], t["nombre_tipo"], t["descripcion_tipo"], t["ordenes"]] for t in tipos],
        [10, 14, 40, 7],
    )


def flujo_registrar_tipo(sesion):
    limpiar_pantalla(sesion)
    titulo("Registrar tipo de mantenimiento")
    while True:
        codigo = pedir_texto("Codigo del tipo (ej. PRED) (0 para cancelar)", permitir_cancelar=True)
        if not codigo:
            return
        codigo = codigo.upper()
        if len(codigo) > MAX_CODIGO_TIPO:
            error(f"El codigo no puede pasar de {MAX_CODIGO_TIPO} caracteres.")
        elif existe_tipo(codigo_tipo=codigo):
            error(f"Ya existe un tipo con el codigo {codigo}. Escribe otro.")
        else:
            break
    while True:
        nombre = pedir_dato("Nombre del tipo (ej. Predictivo)", MAX_NOMBRE_TIPO)
        if not existe_tipo(nombre_tipo=nombre):
            break
        error(f"Ya existe el tipo {nombre}. Escribe otro.")
    descripcion = pedir_dato("Descripcion", MAX_DESCRIPCION_TIPO)
    registrado = registrar_tipo_mantenimiento(codigo, nombre, descripcion)
    exito(f"\nTipo de mantenimiento {nombre} ({registrado}) registrado.")


def flujo_eliminar_tipo(sesion):
    limpiar_pantalla(sesion)
    titulo("Eliminar tipo de mantenimiento")
    tipo = elegir_de_lista(
        "Tipo a eliminar",
        listar_tipos_gestion(),
        lambda t: f"{t['codigo_tipo']} | {t['nombre_tipo']}"
        + (f" - usado en {t['ordenes']} orden(es)" if t["ordenes"] else ""),
    )
    if not tipo:
        return
    # Se valida antes de pedir confirmacion; eliminar_tipo_mantenimiento vuelve a revisarlo como respaldo
    if tipo["ordenes"]:
        aviso(
            f"\nAviso: el tipo {tipo['nombre_tipo']} se usa en {tipo['ordenes']} orden(es) de trabajo "
            "y no puede eliminarse para no perder el historial."
        )
        return
    if not confirmar(f"Confirmas eliminar el tipo {tipo['nombre_tipo']}? No se puede deshacer", False):
        aviso("Operacion cancelada.")
        return
    nombre = eliminar_tipo_mantenimiento(tipo["codigo_tipo"])
    exito(f"\nTipo de mantenimiento {nombre} eliminado.")


def menu_catalogos(sesion):
    if not sesion.get("es_supervisor"):
        aviso("Solo un supervisor puede gestionar los catalogos.")
        return
    while True:
        limpiar_pantalla(sesion)
        mostrar_menu(
            "Gestion de catalogos",
            [
                ("1", "Ver categorias"),
                ("2", "Registrar categoria"),
                ("3", "Eliminar categoria"),
                ("4", "Ver tipos de mantenimiento"),
                ("5", "Registrar tipo de mantenimiento"),
                ("6", "Eliminar tipo de mantenimiento"),
                ("0", "Regresar"),
            ],
        )
        mensaje("Los estados y las prioridades son fijos y no se editan desde el sistema.")
        linea("-")
        op = pedir_opcion(["0", "1", "2", "3", "4", "5", "6"])
        if op == "0":
            break
        if op == "1":
            ejecutar_opcion(mostrar_categorias, sesion)
        elif op == "2":
            ejecutar_opcion(flujo_registrar_categoria, sesion)
        elif op == "3":
            ejecutar_opcion(flujo_eliminar_categoria, sesion)
        elif op == "4":
            ejecutar_opcion(mostrar_tipos, sesion)
        elif op == "5":
            ejecutar_opcion(flujo_registrar_tipo, sesion)
        elif op == "6":
            ejecutar_opcion(flujo_eliminar_tipo, sesion)
        pausar()


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------

def ejecutar_opcion(funcion, *args):
    try:
        funcion(*args)
    except ValueError as e:
        aviso(f"Aviso: {e}")
    except Exception:
        error("Ocurrio un problema al procesar la solicitud.")


def menu_solicitante(sesion):
    while True:
        limpiar_pantalla(sesion)
        mostrar_menu(
            "Menu solicitante",
            [
                ("1", "Registrar solicitud de mantenimiento"),
                ("2", "Mis solicitudes"),
                ("3", "Seguimiento de mi solicitud"),
                ("4", "Cancelar mi solicitud"),
                ("0", "Cerrar sesion"),
            ],
        )
        op = pedir_opcion(["0", "1", "2", "3", "4"])
        if op == "0":
            break
        if op == "1":
            ejecutar_opcion(flujo_registrar_solicitud, sesion)
        elif op == "2":
            ejecutar_opcion(mostrar_mis_solicitudes, sesion)
        elif op == "3":
            ejecutar_opcion(mostrar_seguimiento_mi_solicitud, sesion)
        elif op == "4":
            ejecutar_opcion(flujo_cancelar_solicitud, sesion)
        pausar()


def menu_consultas(sesion):
    while True:
        limpiar_pantalla(sesion)
        mostrar_menu(
            "Consultas",
            [
                ("1", "Solicitudes de mantenimiento por fecha"),
                ("2", "Actividades especificas de una orden de trabajo"),
                ("3", "Informacion de orden de trabajo por edificio"),
                ("4", "Tecnicos asignados a una orden de trabajo"),
                ("5", "Planes de mantenimiento preventivo por edificio"),
                ("6", "Soluciones aplicadas y materiales utilizados"),
                ("7", "Seguimiento de un reporte por folio"),
                ("8", "Reportes pendientes y solucionados"),
                ("9", "Materiales por reponer"),
                ("10", "Reportes por piso y area"),
                ("0", "Regresar"),
            ],
        )
        op = pedir_opcion([str(n) for n in range(11)])
        if op == "0":
            break
        if op == "1":
            ejecutar_opcion(mostrar_consulta_solicitudes, sesion, False)
        elif op == "2":
            ejecutar_opcion(mostrar_consulta_actividades, sesion)
        elif op == "3":
            ejecutar_opcion(mostrar_consulta_ordenes_edificio, sesion)
        elif op == "4":
            ejecutar_opcion(mostrar_consulta_tecnicos, sesion)
        elif op == "5":
            ejecutar_opcion(mostrar_consulta_planes, sesion)
        elif op == "6":
            ejecutar_opcion(mostrar_consulta_soluciones, sesion)
        elif op == "7":
            ejecutar_opcion(mostrar_consulta_seguimiento, sesion)
        elif op == "8":
            ejecutar_opcion(mostrar_consulta_reportes_estado, sesion)
        elif op == "9":
            ejecutar_opcion(mostrar_consulta_materiales_reponer, sesion)
        elif op == "10":
            ejecutar_opcion(mostrar_consulta_piso_area, sesion)
        pausar()


def menu_mantenimiento(sesion):
    # (texto, funcion, es_submenu, solo_supervisor). El tecnico no ve las opciones de supervisor.
    materiales = (
        "Gestion de materiales (inventario, altas, bajas)" if es_supervisor(sesion)
        else "Gestion de materiales (inventario y material tomado)"
    )
    ejecutar_menu(
        sesion,
        "Menu supervisor" if es_supervisor(sesion) else "Menu tecnico",
        [
            ("Registrar orden de trabajo de una solicitud", flujo_registrar_orden, False, True),
            ("Asignar tecnicos a una orden de trabajo (minimo 2)", flujo_asignar_tecnicos, False, True),
            ("Cancelar orden de trabajo", flujo_cancelar_orden, False, True),
            ("Mis ordenes asignadas", mostrar_mis_ordenes, False, False),
            ("Registrar actividades en una orden (minimo 2)", flujo_registrar_actividades, False, False),
            ("Registrar solucion y materiales de un reporte", flujo_registrar_solucion, False, False),
            ("Registrar plan de mantenimiento preventivo", flujo_registrar_plan, False, True),
            (materiales, menu_materiales, True, False),
            ("Consultas del sistema", menu_consultas, True, False),
            ("Gestion de personal (registro y baja de tecnicos)", menu_personal, True, True),
            ("Gestion de equipos (altas, cambios y bajas)", menu_equipos, True, True),
            ("Gestion de catalogos (categorias y tipos)", menu_catalogos, True, True),
        ],
        "Cerrar sesion",
    )


MAX_INTENTOS_LOGIN = 3


def flujo_login():
    limpiar_pantalla()
    titulo("Iniciar sesion")
    mensaje("Ingresa con tu correo institucional (Solicitante) o usuario de tecnico (Mantenimiento).")
    linea("-")
    fallidos = 0
    while fallidos < MAX_INTENTOS_LOGIN:
        identificador = Prompt.ask(
            _etiqueta("Correo o usuario (0 para cancelar)"), console=console, default="", show_default=False
        ).strip()
        if identificador == "0" or not identificador:
            return None
        contrasena = Prompt.ask("Contrasena", console=console, password=True).strip()
        sesion = iniciar_sesion(identificador, contrasena)
        if sesion:
            return sesion
        fallidos += 1
        restantes = MAX_INTENTOS_LOGIN - fallidos
        error("Credenciales incorrectas. Verifica tu usuario/correo y contrasena.")
        if restantes:
            mensaje(f"Te quedan {restantes} intento(s).\n")
    aviso(f"\nSe alcanzaron {MAX_INTENTOS_LOGIN} intentos fallidos seguidos. Regresas al menu de acceso.")
    pausar()
    return None


def main():
    try:
        cnx = conectar()
        cnx.close()
    except Exception:
        titulo("Sin conexion")
        error("No se pudo establecer conexion con el servidor del sistema.")
        aviso("Verifica que MySQL este encendido en XAMPP e intenta nuevamente.")
        return

    while True:
        limpiar_pantalla()
        mostrar_menu(
            "Acceso al sistema",
            [
                ("1", "Iniciar sesion"),
                ("2", "Registrarme como estudiante"),
                ("0", "Salir"),
            ],
        )
        op = pedir_opcion(["0", "1", "2"], "1")
        if op == "0":
            mensaje("Hasta luego.")
            break
        elif op == "1":
            sesion = flujo_login()
            if sesion:
                if sesion["rol"] == "solicitante":
                    menu_solicitante(sesion)
                else:
                    menu_mantenimiento(sesion)
        elif op == "2":
            ejecutar_opcion(flujo_registro_estudiante)
            pausar()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        mensaje("\nHasta luego.")
