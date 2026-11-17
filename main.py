import os
import sys
from datetime import date, datetime
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from conexion import conectar
from logo import mostrar_banner_unicare
from funciones.auth import existe_usuario_tecnico, iniciar_sesion, registrar_tecnico
from funciones.ordenes import (
    asignar_tecnicos_orden,
    consultar_actividades_orden,
    consultar_ordenes_edificio,
    consultar_tecnicos_orden,
    listar_ordenes,
    listar_solicitudes_disponibles,
    listar_tecnicos,
    listar_tipos_y_estados_orden,
    registrar_actividades_orden,
    registrar_orden_trabajo,
)
from funciones.planes import (
    consultar_planes_edificio,
    listar_edificios,
    listar_equipos_por_edificio,
    registrar_plan_preventivo,
)
from funciones.solicitudes import (
    TIPOS_USUARIO,
    consultar_solicitudes_por_fecha,
    listar_catalogos_solicitud,
    listar_fechas_solicitudes,
    registrar_solicitud,
    registrar_usuario,
)

console = Console()


def limpiar_pantalla(sesion=None):
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    else:
        console.clear()
    mostrar_banner_unicare(console)
    if sesion:
        rol_txt = "Mantenimiento" if sesion["rol"] == "mantenimiento" else "Solicitante"
        console.print(
            f"[bold cyan]Sesion:[/] {sesion['nombre']} [dim]({rol_txt} - {sesion['detalle']})[/]"
        )


def pausar():
    console.input("\n[dim]Presiona Enter para continuar...[/]")


def pedir_fecha(etiqueta, default=None):
    sugerida = (default or date.today()).isoformat()
    while True:
        valor = Prompt.ask(f"{etiqueta} (AAAA-MM-DD, 0 para cancelar)", default=sugerida).strip()
        if valor == "0":
            return None
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            console.print("[red]Formato invalido. Usa AAAA-MM-DD.[/]")


def elegir_de_lista(titulo, opciones, formato):
    if not opciones:
        console.print(f"[yellow]No hay registros disponibles para {titulo}.[/]")
        return None

    console.print(f"\n[bold cyan]{titulo}[/]")
    for i, item in enumerate(opciones, start=1):
        console.print(f"  [bold][{i}][/] {formato(item)}")
    console.print("  [bold][0][/] Cancelar")

    validas = [str(i) for i in range(0, len(opciones) + 1)]
    eleccion = Prompt.ask("Selecciona una opcion", choices=validas, default="0")
    if eleccion == "0":
        return None
    return opciones[int(eleccion) - 1]


def pedir_texto(etiqueta, permitir_cancelar=False):
    while True:
        valor = Prompt.ask(etiqueta).strip()
        if permitir_cancelar and valor == "0":
            return None
        if valor:
            return valor
        console.print("[red]Este campo no puede quedar vacio.[/]")


def pedir_correo(etiqueta="Correo institucional (0 para cancelar)"):
    dominio = "@ut-tijuana.edu.mx"
    while True:
        valor = Prompt.ask(etiqueta).strip().lower()
        if valor == "0":
            return None
        if valor.endswith(dominio) and len(valor) > len(dominio) and " " not in valor:
            return valor
        console.print(f"[red]Correo invalido. Debe ser institucional {dominio} (ej. 0323105973{dominio}).[/]")


def flujo_registro_estudiante(sesion=None):
    limpiar_pantalla(sesion)
    console.print("[bold cyan]REGISTRO DE ESTUDIANTE[/]")
    nombre = pedir_texto("Nombre(s) (0 para cancelar)", permitir_cancelar=True)
    if not nombre:
        return None
    ap1 = pedir_texto("Primer apellido")
    ap2 = Prompt.ask("Segundo apellido (opcional)", default="", show_default=False).strip()
    correo = pedir_correo()
    if not correo:
        return None
    contrasena = Prompt.ask("Crea una contrasena", password=True).strip()
    while not contrasena:
        contrasena = Prompt.ask("La contrasena no puede ir vacia", password=True).strip()

    registrar_usuario("Estudiante", correo, contrasena, nombre, ap1, ap2 or None)
    console.print(f"\n[bold green]Cuenta creada correctamente. Ya puedes iniciar sesion con {correo}.[/]")
    return correo


def flujo_registrar_personal(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold yellow]REGISTRO DE DOCENTE, ADMINISTRATIVO O TECNICO[/]")
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
    ap2 = Prompt.ask("Segundo apellido (opcional)", default="", show_default=False).strip()

    if tipo in ("Docente", "Administrativo"):
        correo = pedir_correo()
        if not correo:
            return
        contrasena = Prompt.ask("Contrasena asignada", password=True).strip()
        while not contrasena:
            contrasena = Prompt.ask("La contrasena no puede ir vacia", password=True).strip()
        registrar_usuario(tipo, correo, contrasena, nombre, ap1, ap2 or None)
        console.print(f"\n[bold green]{tipo} registrado correctamente ({correo}).[/]")
    else:
        correo = pedir_correo("Correo institucional del tecnico (0 para cancelar)")
        if not correo:
            return
        sugerido = f"{nombre.split()[0].lower()}.{ap1.split()[0].lower()}"
        if existe_usuario_tecnico(sugerido):
            console.print(
                f"[yellow]Ya existe un tecnico con el usuario '{sugerido}'. "
                f"Puedes escribir otro usuario distinto o presionar Enter para iniciar sesion con tu correo ({correo}).[/]"
            )
            usuario_acc = Prompt.ask("Usuario de acceso", default=correo, show_default=False).strip().lower()
        else:
            usuario_acc = Prompt.ask("Usuario de acceso", default=sugerido).strip().lower()
        especialidad = pedir_texto("Especialidad")
        exp = IntPrompt.ask("Anios de experiencia laboral", default=1)
        contrasena = Prompt.ask("Contrasena asignada", password=True).strip()
        while not contrasena:
            contrasena = Prompt.ask("La contrasena no puede ir vacia", password=True).strip()
        usuario_creado = registrar_tecnico(
            usuario_acc, correo, contrasena, nombre, ap1, ap2 or None, especialidad, exp, sesion["id"]
        )
        console.print(f"\n[bold green]Tecnico registrado correctamente ({usuario_creado}).[/]")


def flujo_registrar_solicitud(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold cyan]REGISTRAR SOLICITUD DE MANTENIMIENTO[/]")
    cats = listar_catalogos_solicitud()
    equipo = elegir_de_lista(
        "Equipo afectado",
        cats["equipos"],
        lambda e: f"{e['nombre_equipo']} - {e['nombre_edificio']}, Salon {e['salon']}",
    )
    if not equipo:
        return

    categoria = elegir_de_lista(
        "Tipo de problema",
        cats["categorias"],
        lambda c: f"{c['nombre_categoria']} ({c['descripcion_categoria']})",
    )
    if not categoria:
        return

    prioridad = elegir_de_lista(
        "Prioridad",
        cats["prioridades"],
        lambda p: f"{p['nombre_prioridad']} ({p['descripcion_prioridad']})",
    )
    if not prioridad:
        return

    descripcion = Prompt.ask("Descripcion del problema (0 para cancelar)").strip()
    if descripcion == "0" or not descripcion:
        return
    observaciones = Prompt.ask("Observaciones (opcional)", default="", show_default=False).strip()

    folio = registrar_solicitud(
        sesion["id"],
        equipo["codigo_inventario"],
        categoria["nombre_categoria"],
        prioridad["nombre_prioridad"],
        descripcion,
        observaciones or None,
    )
    console.print(f"\n[bold green]Solicitud registrada con numero {folio}.[/]")


def mostrar_consulta_solicitudes(sesion, solo_mias=False):
    limpiar_pantalla(sesion)
    titulo = "MIS SOLICITUDES POR FECHA" if solo_mias else "CONSULTA DE SOLICITUDES POR FECHA"
    console.print(f"[bold cyan]{titulo}[/]")
    uid = sesion["id"] if solo_mias else None
    fechas = listar_fechas_solicitudes(uid)
    if solo_mias and not fechas:
        console.print("\n[yellow]Aun no tienes solicitudes registradas.[/]")
        return
    if fechas:
        console.print("\n[dim]Fechas con solicitudes registradas:[/]")
        for f in fechas[:5]:
            console.print(f"  {f['fecha_registro']} ({f['total']} registros)")

    fecha = pedir_fecha("Fecha a consultar", default=fechas[0]["fecha_registro"] if fechas else None)
    if not fecha:
        return

    filas = consultar_solicitudes_por_fecha(fecha, uid)
    if not filas:
        console.print(f"[yellow]No se encontraron solicitudes registradas en {fecha}.[/]")
        return

    console.print(f"\n[bold cyan]Solicitudes de Mantenimiento ({fecha}) - {len(filas)} registros[/]")
    for r in filas:
        detalle = (
            f"[bold]Fecha de solicitud:[/] {r['fecha_registro']}   |   "
            f"[bold]No. solicitud:[/] {r['folio']}\n"
            f"[bold]Usuario:[/] {r['nombre_usuario']}\n"
            f"[bold]Equipo afectado:[/] {r['nombre_equipo']}\n"
            f"[bold]Ubicacion:[/] {r['ubicacion_equipo']}\n"
            f"[bold]Tipo de problema:[/] {r['descripcion_categoria']}\n"
            f"[bold]Problema:[/] {r['descripcion_reporte']}\n"
            f"[bold]Estado:[/] {r['descripcion_estado']}\n"
            f"[bold]Observaciones:[/] {r['observaciones'] or 'Sin observaciones'}"
        )
        console.print(Panel(detalle, title=f"Solicitud {r['folio']}", border_style="cyan"))


def mostrar_consulta_actividades(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold cyan]CONSULTA DE ACTIVIDADES EN ORDEN DE TRABAJO[/]")
    ordenes = listar_ordenes()
    elegida = None
    if ordenes and Confirm.ask("Filtrar por una orden de trabajo especifica?", default=False):
        elegida = elegir_de_lista(
            "Orden de trabajo",
            ordenes,
            lambda o: f"{o['num_orden']} | {o['folio']} | {o['nombre_equipo']}",
        )
        if not elegida:
            return

    filas = consultar_actividades_orden(elegida["num_orden"] if elegida else None)
    if not filas:
        console.print("[yellow]No hay actividades registradas.[/]")
        return

    tabla = Table(title="Actividades Realizadas en Orden de Trabajo", box=box.ROUNDED, header_style="bold cyan")
    tabla.add_column("No. Orden", style="bold", no_wrap=True)
    tabla.add_column("Descripcion de la actividad")
    tabla.add_column("Fecha", no_wrap=True)
    tabla.add_column("Resultado obtenido")

    for a in filas:
        tabla.add_row(a["num_orden"], a["descripcion_actividad"], str(a["fecha_actividad"]), a["resultado"])
    console.print(tabla)


def mostrar_consulta_ordenes_edificio(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold cyan]CONSULTA DE ORDENES DE TRABAJO POR EDIFICIO[/]")
    edificios = listar_edificios()
    edificio = None
    if Confirm.ask("Filtrar por un edificio en especifico?", default=True):
        edificio = elegir_de_lista("Edificio", edificios, lambda e: e["nombre_edificio"])
        if not edificio:
            return

    filas = consultar_ordenes_edificio(edificio["no_edificio"] if edificio else None)
    if not filas:
        console.print("[yellow]No hay ordenes de trabajo para el criterio elegido.[/]")
        return

    console.print(f"\n[bold cyan]Ordenes de Trabajo ({len(filas)} registros)[/]")
    for o in filas:
        inicio = str(o["fecha_inicio"]) if o["fecha_inicio"] else "Pendiente"
        fin = str(o["fecha_fin"]) if o["fecha_fin"] else "Pendiente"
        detalle = (
            f"[bold]No. orden:[/] {o['num_orden']}   |   [bold]No. solicitud:[/] {o['folio']}   |   "
            f"[bold]Edificio:[/] {o['nombre_edificio']}\n"
            f"[bold]Tipo mantenimiento:[/] {o['descripcion_tipo']}\n"
            f"[bold]Estado actual:[/] {o['descripcion_estado']}\n"
            f"[bold]Creacion:[/] {o['fecha_creacion']}   |   [bold]Programada:[/] {o['fecha_programada']}\n"
            f"[bold]Inicio:[/] {inicio}   |   [bold]Fin:[/] {fin}\n"
            f"[bold]Observaciones:[/] {o['observaciones'] or 'Sin observaciones'}\n"
            f"[bold]Costo mano de obra:[/] ${o['costo_mano_obra']:.2f}   |   "
            f"[bold]Costo materiales:[/] ${o['costo_materiales']:.2f}"
        )
        console.print(Panel(detalle, title=f"Orden {o['num_orden']}", border_style="yellow"))


def mostrar_consulta_tecnicos(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold cyan]CONSULTA DE TECNICOS ASIGNADOS A ORDENES[/]")
    ordenes = listar_ordenes()
    elegida = None
    if ordenes and Confirm.ask("Filtrar por una orden de trabajo?", default=False):
        elegida = elegir_de_lista(
            "Orden de trabajo",
            ordenes,
            lambda o: f"{o['num_orden']} | {o['folio']} | {o['nombre_edificio']}",
        )
        if not elegida:
            return

    filas = consultar_tecnicos_orden(elegida["num_orden"] if elegida else None)
    if not filas:
        console.print("[yellow]No hay tecnicos asignados.[/]")
        return

    tabla = Table(title="Tecnicos Asignados a Ordenes de Trabajo", box=box.ROUNDED, header_style="bold cyan")
    tabla.add_column("No. Orden", style="bold", no_wrap=True)
    tabla.add_column("Tecnico")
    tabla.add_column("Fecha asignacion", no_wrap=True)
    tabla.add_column("Horas", justify="right", no_wrap=True)
    tabla.add_column("Actividad a realizar")

    for t in filas:
        tabla.add_row(
            t["num_orden"],
            t["nombre_tecnico"],
            str(t["fecha_asignacion"]),
            f"{t['horas_asignadas']:.2f}",
            t["actividad_realizar"],
        )
    console.print(tabla)


def mostrar_consulta_planes(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold cyan]CONSULTA DE PLANES DE MANTENIMIENTO PREVENTIVO[/]")
    edificios = listar_edificios()
    edificio = None
    if Confirm.ask("Filtrar por un edificio en especifico?", default=False):
        edificio = elegir_de_lista("Edificio", edificios, lambda e: e["nombre_edificio"])
        if not edificio:
            return

    filas = consultar_planes_edificio(edificio["no_edificio"] if edificio else None)
    if not filas:
        console.print("[yellow]No hay planes preventivos registrados.[/]")
        return

    tabla = Table(title="Planes de Mantenimiento Preventivo", box=box.ROUNDED, header_style="bold cyan")
    tabla.add_column("No. Plan", style="bold", no_wrap=True)
    tabla.add_column("Nombre del plan")
    tabla.add_column("Edificio")
    tabla.add_column("Descripcion")
    tabla.add_column("Frecuencia")
    tabla.add_column("Duracion (hrs)", justify="right")
    tabla.add_column("Estado")

    for p in filas:
        estado = f"[green]{p['estado_plan']}[/]" if p["estado_plan"] == "Activo" else f"[yellow]{p['estado_plan']}[/]"
        tabla.add_row(
            p["num_plan"],
            p["nombre_plan"],
            p["nombre_edificio"],
            p["descripcion_plan"],
            p["frecuencia"],
            f"{p['duracion_estimada_horas']:.2f}",
            estado,
        )
    console.print(tabla)


def flujo_registrar_orden(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold yellow]REGISTRAR ORDEN DE TRABAJO[/]")
    solicitudes = listar_solicitudes_disponibles()
    sol = elegir_de_lista(
        "Solicitud de mantenimiento",
        solicitudes,
        lambda s: f"{s['folio']} | {s['fecha_registro']} | {s['nombre_equipo']} ({s['nombre_estado']})",
    )
    if not sol:
        return

    tipos, _ = listar_tipos_y_estados_orden()
    tipo = elegir_de_lista(
        "Tipo de mantenimiento",
        tipos,
        lambda t: f"{t['nombre_tipo']} ({t['descripcion_tipo']})",
    )
    if not tipo:
        return

    fecha_prog = pedir_fecha("Fecha programada")
    if not fecha_prog:
        return

    obs = Prompt.ask("Observaciones (opcional)", default="", show_default=False).strip()
    mano_obra = FloatPrompt.ask("Costo de mano de obra", default=0.0)
    materiales = FloatPrompt.ask("Costo de materiales", default=0.0)

    num_orden = registrar_orden_trabajo(
        sol["folio"],
        tipo["id_tipo_mantenimiento"],
        fecha_prog,
        obs or None,
        mano_obra,
        materiales,
    )
    console.print(f"\n[bold green]Orden de trabajo {num_orden} registrada correctamente.[/]")


def flujo_asignar_tecnicos(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold yellow]ASIGNAR TECNICOS A ORDEN DE TRABAJO[/]")
    ordenes = listar_ordenes()
    orden = elegir_de_lista(
        "Orden de trabajo",
        ordenes,
        lambda o: f"{o['num_orden']} | Solicitud {o['folio']} | {o['nombre_equipo']}",
    )
    if not orden:
        return

    tecnicos = listar_tecnicos()
    asignaciones = []
    elegidos_ids = set()

    console.print("\n[bold yellow]Se requiere asignar al menos 2 tecnicos a la orden.[/]")
    while True:
        disponibles = [t for t in tecnicos if t["id_trabajador"] not in elegidos_ids]
        if not disponibles:
            break
        tecnico = elegir_de_lista(
            f"Tecnico #{len(asignaciones) + 1}",
            disponibles,
            lambda t: f"{t['nombre_completo']} ({t['especialidad']})",
        )
        if not tecnico:
            if len(asignaciones) < 2:
                console.print("[yellow]Asignacion cancelada.[/]")
                return
            break

        horas = FloatPrompt.ask(f"Horas asignadas a {tecnico['nombre_completo']}", default=2.0)
        actividad = Prompt.ask("Actividad a realizar").strip()
        while not actividad:
            actividad = Prompt.ask("La actividad es obligatoria").strip()

        asignaciones.append(
            {
                "id_trabajador": tecnico["id_trabajador"],
                "horas": horas,
                "actividad": actividad,
            }
        )
        elegidos_ids.add(tecnico["id_trabajador"])

        if len(asignaciones) >= 2 and not Confirm.ask("Asignar otro tecnico adicional?", default=False):
            break

    asignar_tecnicos_orden(orden["num_orden"], asignaciones)
    console.print(f"\n[bold green]{len(asignaciones)} tecnicos asignados a {orden['num_orden']}.[/]")


def flujo_registrar_actividades(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold yellow]REGISTRAR ACTIVIDADES EN ORDEN DE TRABAJO[/]")
    ordenes = listar_ordenes()
    orden = elegir_de_lista(
        "Orden de trabajo",
        ordenes,
        lambda o: f"{o['num_orden']} | {o['nombre_equipo']} ({o['nombre_estado']})",
    )
    if not orden:
        return

    actividades = []
    console.print("\n[bold yellow]Se requiere registrar al menos 2 actividades especificas.[/]")
    while True:
        num_act = len(actividades) + 1
        desc = Prompt.ask(f"Actividad #{num_act} - Descripcion (0 para cancelar)").strip()
        if desc == "0":
            if len(actividades) < 2:
                console.print("[yellow]Registro de actividades cancelado.[/]")
                return
            break
        if not desc:
            continue

        fecha_act = pedir_fecha(f"Actividad #{num_act} - Fecha")
        if not fecha_act:
            return
        resultado = Prompt.ask(f"Actividad #{num_act} - Resultado obtenido").strip()
        while not resultado:
            resultado = Prompt.ask("El resultado obtenido es obligatorio").strip()

        actividades.append({"descripcion": desc, "fecha": fecha_act, "resultado": resultado})
        if len(actividades) >= 2 and not Confirm.ask("Agregar otra actividad?", default=False):
            break

    finalizar = Confirm.ask("Marcar la orden de trabajo como Finalizada?", default=False)
    registrar_actividades_orden(orden["num_orden"], actividades, finalizar_orden=finalizar)
    console.print(f"\n[bold green]{len(actividades)} actividades registradas en {orden['num_orden']}.[/]")


def flujo_registrar_plan(sesion):
    limpiar_pantalla(sesion)
    console.print("[bold yellow]REGISTRAR PLAN DE MANTENIMIENTO PREVENTIVO[/]")
    edificios = listar_edificios()
    edificio = elegir_de_lista("Edificio / instalacion", edificios, lambda e: e["nombre_edificio"])
    if not edificio:
        return

    equipos = listar_equipos_por_edificio(edificio["no_edificio"])
    equipo = elegir_de_lista(
        "Equipo de trabajo",
        equipos,
        lambda eq: f"{eq['nombre_equipo']} (Salon {eq['salon']})",
    )
    if not equipo:
        return

    nombre = pedir_texto("Nombre del plan (0 para cancelar)", permitir_cancelar=True)
    if not nombre:
        return
    descripcion = pedir_texto("Descripcion del plan")
    frecuencia = elegir_de_lista(
        "Frecuencia",
        ["Semanal", "Mensual", "Trimestral", "Semestral", "Anual"],
        lambda f: f,
    )
    if not frecuencia:
        return
    duracion = FloatPrompt.ask("Duracion estimada en horas", default=2.0)
    estado = elegir_de_lista("Estado del plan", ["Activo", "Inactivo"], lambda e: e)
    if not estado:
        return

    num_plan = registrar_plan_preventivo(
        nombre,
        edificio["no_edificio"],
        equipo["codigo_inventario"],
        descripcion,
        frecuencia,
        duracion,
        estado,
    )
    console.print(f"\n[bold green]Plan preventivo {num_plan} registrado correctamente.[/]")


def menu_solicitante(sesion):
    while True:
        limpiar_pantalla(sesion)
        console.print(
            Panel(
                "[bold][1][/] Registrar solicitud de mantenimiento\n"
                "[bold][2][/] Consultar mis solicitudes por fecha\n"
                "[bold][0][/] Cerrar sesion",
                title="MENU SOLICITANTE",
                border_style="cyan",
            )
        )
        op = Prompt.ask("Selecciona una opcion", choices=["0", "1", "2"], default="0")
        if op == "0":
            break
        try:
            if op == "1":
                flujo_registrar_solicitud(sesion)
            elif op == "2":
                mostrar_consulta_solicitudes(sesion, solo_mias=True)
        except ValueError as e:
            console.print(f"[bold red]Aviso:[/] {e}")
        except Exception:
            console.print("[bold red]Ocurrio un problema al procesar la solicitud.[/]")
        pausar()


def menu_consultas(sesion):
    while True:
        limpiar_pantalla(sesion)
        console.print(
            Panel(
                "[bold][1][/] Solicitudes de mantenimiento por fecha\n"
                "[bold][2][/] Actividades especificas de una orden de trabajo\n"
                "[bold][3][/] Informacion de orden de trabajo por edificio\n"
                "[bold][4][/] Tecnicos asignados a una orden de trabajo\n"
                "[bold][5][/] Planes de mantenimiento preventivo por edificio\n"
                "[bold][0][/] Regresar",
                title="CONSULTAS",
                border_style="green",
            )
        )
        op = Prompt.ask("Selecciona una opcion", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if op == "0":
            break
        try:
            if op == "1":
                mostrar_consulta_solicitudes(sesion, solo_mias=False)
            elif op == "2":
                mostrar_consulta_actividades(sesion)
            elif op == "3":
                mostrar_consulta_ordenes_edificio(sesion)
            elif op == "4":
                mostrar_consulta_tecnicos(sesion)
            elif op == "5":
                mostrar_consulta_planes(sesion)
        except ValueError as e:
            console.print(f"[bold red]Aviso:[/] {e}")
        except Exception:
            console.print("[bold red]Ocurrio un problema al procesar la solicitud.[/]")
        pausar()


def menu_mantenimiento(sesion):
    while True:
        limpiar_pantalla(sesion)
        opciones_txt = (
            "[bold][1][/] Registrar orden de trabajo de una solicitud\n"
            "[bold][2][/] Asignar tecnicos a una orden de trabajo (minimo 2)\n"
            "[bold][3][/] Registrar actividades especificas en una orden (minimo 2)\n"
            "[bold][4][/] Registrar plan de mantenimiento preventivo\n"
            "[bold][5][/] Consultas del sistema\n"
        )
        validas = ["0", "1", "2", "3", "4", "5"]
        if sesion.get("es_supervisor"):
            opciones_txt += "[bold][6][/] Registrar docente, administrativo o tecnico\n"
            validas.append("6")
        opciones_txt += "[bold][0][/] Cerrar sesion"

        console.print(Panel(opciones_txt, title="MENU MANTENIMIENTO", border_style="yellow"))
        op = Prompt.ask("Selecciona una opcion", choices=validas, default="0")
        if op == "0":
            break
        if op == "5":
            menu_consultas(sesion)
            continue
        try:
            if op == "1":
                flujo_registrar_orden(sesion)
            elif op == "2":
                flujo_asignar_tecnicos(sesion)
            elif op == "3":
                flujo_registrar_actividades(sesion)
            elif op == "4":
                flujo_registrar_plan(sesion)
            elif op == "6":
                flujo_registrar_personal(sesion)
        except ValueError as e:
            console.print(f"[bold red]Aviso:[/] {e}")
        except Exception:
            console.print("[bold red]Ocurrio un problema al procesar la solicitud.[/]")
        pausar()


def flujo_login():
    limpiar_pantalla()
    console.print(
        Panel(
            "Ingresa con tu correo institucional (Solicitante) o usuario de tecnico (Mantenimiento).\n"
            "[dim]Ejemplo solicitante: mauro.sanchez@ut-tijuana.edu.mx / 1234\n"
            "Ejemplo mantenimiento: carlos.ramirez / 1234[/]",
            title="INICIAR SESION",
            border_style="#2B7FD9",
        )
    )
    identificador = Prompt.ask("Correo o usuario (0 para cancelar)").strip()
    if identificador == "0" or not identificador:
        return None
    contrasena = Prompt.ask("Contrasena", password=True).strip()
    sesion = iniciar_sesion(identificador, contrasena)
    if not sesion:
        console.print("[bold red]Credenciales incorrectas. Verifica tu usuario/correo y contrasena.[/]")
        pausar()
        return None
    return sesion


def main():
    try:
        cnx = conectar()
        cnx.close()
    except Exception:
        console.print(
            Panel(
                "[bold red]No se pudo establecer conexion con el servidor del sistema.[/]\n"
                "Verifica que el servicio este encendido e intenta nuevamente.",
                title="Sin Conexion",
                border_style="red",
            )
        )
        return

    while True:
        limpiar_pantalla()
        console.print(
            Panel(
                "[bold][1][/] Iniciar sesion\n"
                "[bold][2][/] Registrarme como estudiante\n"
                "[bold][0][/] Salir",
                title="ACCESO AL SISTEMA",
                border_style="white",
            )
        )
        op = Prompt.ask("Selecciona una opcion", choices=["0", "1", "2"], default="1")
        if op == "0":
            console.print("[cyan]Hasta luego.[/]")
            break
        elif op == "1":
            sesion = flujo_login()
            if sesion:
                if sesion["rol"] == "solicitante":
                    menu_solicitante(sesion)
                else:
                    menu_mantenimiento(sesion)
        elif op == "2":
            try:
                flujo_registro_estudiante()
            except ValueError as e:
                console.print(f"[bold red]Aviso:[/] {e}")
            except Exception:
                console.print("[bold red]No se pudo crear la cuenta. Intenta nuevamente.[/]")
            pausar()


if __name__ == "__main__":
    main()
