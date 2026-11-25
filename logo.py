"""Modulo para despliegue del logo de UNICARE en consola.

El logo se dibuja con medios bloques (▀ ▄): cada caracter pinta dos filas de la cuadricula,
una con el color del texto y otra con el color de fondo.
"""

import ctypes
import os

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _habilitar_color_completo():
    # En la consola clasica de Windows (conhost) las secuencias VT vienen apagadas y rich
    # cae a 16 colores. Se encienden aqui, antes de que main.py cree su Console, para que
    # rich detecte color verdadero y el logo salga con los colores exactos.
    # En terminales que ya las tienen (VS Code, Windows Terminal) no cambia nada.
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        salida = kernel32.GetStdHandle(-11)
        modo = ctypes.c_uint32()
        if kernel32.GetConsoleMode(salida, ctypes.byref(modo)):
            kernel32.SetConsoleMode(salida, modo.value | 0x0004)
    except (AttributeError, OSError):
        pass


_habilitar_color_completo()

LOGO_FILAS = [
    "...............BBBBBB...................",
    "............BBBBBBBBBBBB................",
    "..........BBBBBBBBBBBBBBBB..............",
    "........BBBBBBWWWWWWWWBBBBBB............",
    ".......BBBBBWWWWWBBWWWWWBBBBB...........",
    "......BBBBWWWWWBBBBBBWWWWWBBBB..........",
    ".....BBBBWWWWBBBBWWBBBBWWWWBBBB.........",
    ".....BBBWWWWBBBBBWWBBBBBWWWWBBB.........",
    "....BBBWWWBBBBBBBBBBBBBBBBWWWBBB........",
    "....BBBWBBBBBBBBBBBBBBBBBBBBWBBB........",
    "...BBBWWWWWWWWWWWWWWWWWWWWWWWWW.........",
    "...BBBWWWWBBBBWWBBBBWWBBBBWWWWW.........",
    "...BBBWWWWBBBBWWBBBBWWBBBBWWYYYYYY......",
    "...BBBWWYYBBBBWWBBBBWWBBBBWYYYYYYYY.....",
    "...BBBWWYYBBBBWWBBBBWWBBBBWYYYYY........",
    "...BBBWYYYBBBBWWBBBBWWBBBBWYYYY.........",
    "...BBBYYYYBBBBWWBBBBWWBBBBWYYYY.....YY..",
    "...BYYYYYYBBBBWWBBBBWWBYYYYYYYYY..YYYY..",
    "....YYYYYYBBBBWWBBBBWWBYYYYYYYYYYYYYY...",
    "....YYYYYYYBBBWWBBBBWWYYYYYYYYYYYYYY....",
    ".....YYYYYYYYBWWBBBBYYYYYYYYYYYYYYY.....",
    ".....BYYYYYYYYYYYYYYYYYYYYYYYYB.........",
    "......BYYYYYYYYYYYYYYYYYYYYBBB..........",
    ".......BBBYYYYYYYYYYYYYYBBBBB...........",
    "........BBBBBBYYYYYYBBBBBBBB............",
    "..........BBBBBBBBBBBBBBBB..............",
    "............BBBBBBBBBBBB................",
    "...............BBBBBB...................",
]

COLORES = {
    "B": "#11559C",
    "W": "#F5F7FA",
    "Y": "#F5A600",
}


def construir_logo():
    texto = Text(no_wrap=True)
    for y in range(0, len(LOGO_FILAS), 2):
        fila1 = LOGO_FILAS[y]
        fila2 = LOGO_FILAS[y + 1] if y + 1 < len(LOGO_FILAS) else "." * len(fila1)
        for c1, c2 in zip(fila1, fila2):
            col1 = COLORES.get(c1)
            col2 = COLORES.get(c2)
            if col1 and col2:
                texto.append("▀", style=f"{col1} on {col2}")
            elif col1:
                texto.append("▀", style=col1)
            elif col2:
                texto.append("▄", style=col2)
            else:
                texto.append(" ")
        if y + 2 < len(LOGO_FILAS):
            texto.append("\n")
    return texto


def mostrar_banner_unicare(console):
    # Se imprime con el mismo Console de main.py
    cuadricula = Table.grid(padding=(0, 3))
    cuadricula.add_column(justify="left", vertical="middle", no_wrap=True)
    cuadricula.add_column(justify="left", vertical="middle")

    titulo = Text()
    titulo.append("█   █ █   █ ███ ", style="bold #2B7FD9")
    titulo.append(" ████  ███  ████  █████\n", style="bold #F5A600")
    titulo.append("█   █ ██  █  █  ", style="bold #2B7FD9")
    titulo.append("█     █   █ █   █ █    \n", style="bold #F5A600")
    titulo.append("█   █ █ █ █  █  ", style="bold #2B7FD9")
    titulo.append("█     █████ ████  ████ \n", style="bold #F5A600")
    titulo.append("█   █ █  ██  █  ", style="bold #2B7FD9")
    titulo.append("█     █   █ █  █  █    \n", style="bold #F5A600")
    titulo.append(" ███  █   █ ███ ", style="bold #2B7FD9")
    titulo.append(" ████ █   █ █   █ █████\n\n", style="bold #F5A600")
    titulo.append("Sistema de Reportes de Mantenimiento Universitario\n", style="bold white")
    titulo.append("Universidad Tecnológica de Tijuana", style="dim")

    cuadricula.add_row(construir_logo(), titulo)
    console.print(Panel(cuadricula, border_style="#2B7FD9", box=box.ROUNDED, padding=(0, 2)))
