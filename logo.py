from rich import box
from rich.panel import Panel
from rich.text import Text


def mostrar_banner_unicare(console):
    contenido = Text(justify="center")
    contenido.append("UNICARE\n", style="bold cyan")
    contenido.append("Sistema de Reportes y Mantenimiento Universitario\n", style="bold white")
    contenido.append("Universidad Tecnológica de Tijuana", style="dim")

    console.print(
        Panel(
            contenido,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 4),
        )
    )
