from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

LOGO_FILAS = [
    "........BBBBBBBB........",
    ".....BBBBBBBBBBBBB......",
    "....BBBB.......BBBB.....",
    "...BBB...........BBB....",
    "..BB.....BBBBB....BBB...",
    ".BB....BBBB.BBBB...BBB..",
    "BBB..BBBBB...BBBBB..BB..",
    "BB..BBBBBBBBBBBBBBB..BB.",
    "BBB...BBB.BBBB.BBBB...BB",
    "BB....BBB.BBBB.BBBB..YYB",
    "BB....BBB..BBB.BBB.YYYY.",
    "BB.Y..BBB..BBB.BB.YYYY..",
    "B.Y...BBB..BBB.BB.YYY...",
    ".YY...BBB..BBB.BB.YYY...",
    "YY....BBB..BBB.B.BYYYY.B",
    "YY....BBB..BBB..YYYYYYYY",
    "YYY...BBB..B..BYYYYYYYYY",
    "YYY...BBB...YYYYYYYY.YYB",
    ".YYYYB..BYYYYYYYYY..BBB.",
    ".BYYYYYYYYYYYYYY..BBBB..",
    "..YYYYYYYYYYY..BBBBB....",
    ".....BYB....BBBBBBB.....",
    ".....BBBBBBBBBBBB.......",
    ".......BBBBBBBB.........",
]


def construir_logo():
    texto = Text(no_wrap=True)
    for y in range(0, len(LOGO_FILAS), 2):
        f1 = LOGO_FILAS[y]
        f2 = LOGO_FILAS[y + 1] if y + 1 < len(LOGO_FILAS) else "." * len(f1)
        for c1, c2 in zip(f1, f2):
            h1 = c1 in ("B", "Y")
            h2 = c2 in ("B", "Y")
            if h1 and h2:
                texto.append("█")
            elif h1:
                texto.append("▀")
            elif h2:
                texto.append("▄")
            else:
                texto.append(" ")
        if y + 2 < len(LOGO_FILAS):
            texto.append("\n")
    return texto


def mostrar_banner_unicare(console):
    cuadricula = Table.grid(padding=(0, 2))
    cuadricula.add_column(justify="center", vertical="middle", no_wrap=True)
    cuadricula.add_column(justify="left", vertical="middle", no_wrap=True)

    titulo = Text(no_wrap=True)
    titulo.append(" _   _ _   _ ___ ____    _    ____  _____\n", style="bold")
    titulo.append("| | | | \\ | |_ _/ ___|  / \\  |  _ \\| ____|\n", style="bold")
    titulo.append("| | | |  \\| || | |     / _ \\ | |_) |  _|  \n", style="bold")
    titulo.append("| |_| | |\\  || | |___ / ___ \\|  _ <| |___ \n", style="bold")
    titulo.append(" \\___/|_| \\_|___\\____/_/   \\_\\_| \\_\\_____|\n\n", style="bold")
    titulo.append("Sistema de Reportes y Mantenimiento Universitario\n")
    titulo.append("Universidad Tecnológica de Tijuana", style="dim")

    cuadricula.add_row(construir_logo(), titulo)
    console.print(Panel(cuadricula, box=box.ROUNDED, padding=(0, 1), expand=False))
