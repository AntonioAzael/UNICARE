"""Modulo para despliegue del logo de UNICARE en consola.

El arte ASCII es una version reducida del logo oficial (assets/logo_unicare.png),
generada con el convertidor https://ascii-art.botecodigital.dev.br/es#ascii-convertido
y compactada a la mitad para que quepa bien en cualquier terminal.
"""

ANCHO = 70

LOGO_ASCII = """
         #############
      ###################.
   .####.    .###.    .####.
  ####   .###########    ###.
 ###. ################### .##.
###.   ####. ####. .###.   .##.
###    ##### ##### #### ......
## .   ##### ##### ##. ....
...    ##### ##### ## .....    ..
...    ##### ##### . ...........
...    ##### .## ..............
 .......#. ..............###
  .................. ######.
     ...........#########.
       .##############.
""".strip("\r\n")


def mostrar_banner_unicare():
    # Se calcula un margen comun para que el logo quede centrado sin deformarse
    ancho_logo = max(len(linea) for linea in LOGO_ASCII.split("\n"))
    margen = " " * ((ANCHO - ancho_logo) // 2)
    for linea in LOGO_ASCII.split("\n"):
        print(margen + linea)
    print()
    print("UNICARE".center(ANCHO))
    print("Sistema de Reportes y Mantenimiento Universitario".center(ANCHO))
