# UNICARE - Sistema de Reportes de Mantenimiento Universitario

Aplicacion de consola desarrollada en **Python** y conectada a **MySQL / MariaDB (XAMPP)** para registrar, dar seguimiento y consultar solicitudes de mantenimiento, ordenes de trabajo y planes preventivos dentro de la universidad.

## Tecnologias y librerias utilizadas

- **Python 3.11**: lenguaje principal del sistema en consola.
- **Python vanilla**: toda la interfaz de consola usa solo la libreria estandar (`print`, `input`, `getpass`, `textwrap`), con menus, tablas y fichas hechos con texto.
- **MySQL Connector/Python (`mysql-connector-python`)**: controlador oficial para conectar Python con la base de datos de XAMPP usando el patron de conexion y manejo de errores (`errorcode`) de la guia oficial de MySQL Connector/Python 5.1.
- **XAMPP (MySQL / phpMyAdmin)**: motor de base de datos local donde se almacenan todas las tablas y registros.

## Estructura del proyecto

- `main.py`: control de acceso (login, auto-registro de estudiante y alta de personal por supervisor), limpieza de pantalla con encabezado fijo, menus segun el rol del usuario y las funciones de captura/impresion en consola.
- `logo.py`: header del sistema donde se imprime el logo ASCII de **UNICARE** junto al titulo y subtitulo.
- `conexion.py`: conexion a MySQL en XAMPP e inicializacion automatica de las tablas y catalogos si la base aun no existe o si viene de una version anterior del esquema.
- `funciones/auth.py`: inicio de sesion diferenciando usuarios solicitantes y personal de mantenimiento.
- `funciones/solicitudes.py`: registro de solicitudes de mantenimiento y consulta de solicitudes por fecha.
- `funciones/ordenes.py`: registro de ordenes de trabajo, asignacion de tecnicos, registro de actividades especificas y consultas relacionadas.
- `funciones/soluciones.py`: registro de la solucion de un reporte con los materiales utilizados (descuenta existencia) y consulta de soluciones.
- `funciones/planes.py`: registro y consulta de planes de mantenimiento preventivo por edificio y equipo.
- `sql/01_tablas_mantenimiento.sql`: creacion de la base de datos `sistema_reportes_mantenimiento` y sus 16 tablas (14 entidades del DER + 2 tablas de relaciones M:M) con llaves primarias y foraneas.
- `sql/02_catalogo_mantenimiento.sql`: carga inicial de catalogos y registros de ejemplo dentro de una transaccion.
- `assets/`: archivos graficos originales del logo (`Logo.ai` y `logo_unicare.png`).

## Modelo de datos (DER / MR)

Los diagramas estan en la carpeta `docs/` (`UniCare_DER_MR_14_entidades.drawio`). Tablas del modelo relacional:

- Entidades: `usuario`, `categoria`, `prioridad`, `estado`, `edificio`, `equipo_instalacion`, `tipo_mantenimiento`, `material`, `trabajador_mantenimiento`, `reporte`, `solucion`, `mantenimiento`, `historial_mantenimiento`, `plan_mantenimiento`.
- Relaciones M:M: `mantenimiento_trabajador` (PARTICIPA EN) y `solucion_material` (UTILIZA).
- Una **orden de trabajo** es un registro de `mantenimiento` y sus **actividades** se guardan en `historial_mantenimiento`.

## Registros y consultas del sistema

### Registros
1. Registrar una solicitud de mantenimiento.
2. Registrar la orden de trabajo de una solicitud de mantenimiento.
3. Asignar al menos 2 tecnicos a una orden de trabajo.
4. Registrar al menos 2 actividades especificas en una orden de trabajo.
5. Registrar un plan de mantenimiento preventivo para un equipo y un edificio.
6. Registrar la solucion de un reporte y los materiales utilizados.

### Consultas
1. Solicitudes de mantenimiento registradas para equipos en una fecha determinada.
2. Actividades especificas realizadas en una orden de trabajo.
3. Informacion de una orden de trabajo para una solicitud de mantenimiento a un edificio.
4. Tecnicos asignados a una orden de trabajo.
5. Plan de mantenimiento preventivo para un edificio.
6. Soluciones aplicadas y materiales utilizados.

## Como ejecutarlo

1. Inicia el modulo **MySQL** en el panel de **XAMPP** (y **Apache** si deseas revisar las tablas en `http://localhost/phpmyadmin`).
2. Instala las dependencias si es la primera vez que corres el proyecto en esa computadora:
   ```powershell
   pip install -r requirements.txt
   ```
3. Ejecuta el programa desde la carpeta del proyecto:
   ```powershell
   python main.py
   ```
   Si la base de datos `sistema_reportes_mantenimiento` todavia no existe en tu XAMPP, el sistema detecta el error `ER_BAD_DB_ERROR` al conectar y ejecuta automaticamente los scripts de la carpeta `sql` en el primer arranque.
