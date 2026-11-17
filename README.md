# UNICARE - Sistema de Reportes de Mantenimiento Universitario

Aplicacion de consola desarrollada en **Python** y conectada a **MySQL / MariaDB (XAMPP)** para registrar, dar seguimiento y consultar solicitudes de mantenimiento, ordenes de trabajo y planes preventivos dentro de la universidad.

## Tecnologias y librerias utilizadas

- **Python 3.11**: lenguaje principal del sistema en consola.
- **Rich (`rich`)**: libreria encargada del diseno visual en terminal. Se utilizo para crear los menus en paneles (`Panel`), las tablas con columnas y bordes (`Table`), los selectores interactivos (`Prompt`, `IntPrompt`, `FloatPrompt`, `Confirm`), los colores por estado y el header/banner con el logo de **UNICARE** (`Text` con medios bloques de color).
- **MySQL Connector/Python (`mysql-connector-python`)**: controlador oficial para conectar Python con la base de datos de XAMPP usando el patron de conexion y manejo de errores (`errorcode`) de la guia oficial de MySQL Connector/Python 5.1.
- **XAMPP (MySQL / phpMyAdmin)**: motor de base de datos local donde se almacenan todas las tablas y registros.

## Estructura del proyecto

- `main.py`: control de acceso (login, auto-registro de estudiante y alta de personal por supervisor), limpieza de pantalla con encabezado fijo y menus segun el rol del usuario.
- `logo.py`: header visual del sistema donde se dibuja el logo de **UNICARE** junto al titulo y subtitulo.
- `conexion.py`: conexion a MySQL en XAMPP e inicializacion automatica de las tablas y catalogos si la base aun no existe.
- `funciones/auth.py`: inicio de sesion diferenciando usuarios solicitantes y personal de mantenimiento.
- `funciones/solicitudes.py`: registro de solicitudes de mantenimiento y consulta de solicitudes por fecha.
- `funciones/ordenes.py`: registro de ordenes de trabajo, asignacion de tecnicos, registro de actividades especificas y consultas relacionadas.
- `funciones/planes.py`: registro y consulta de planes de mantenimiento preventivo por edificio y equipo.
- `sql/01_tablas_mantenimiento.sql`: creacion de la base de datos `sistema_reportes_mantenimiento` y todas sus tablas con llaves primarias y foraneas.
- `sql/02_catalogo_mantenimiento.sql`: carga inicial de catalogos y registros de ejemplo dentro de una transaccion.
- `assets/`: archivos graficos originales del logo (`Logo.ai` y `logo_unicare.png`).

## Registros y consultas del sistema

### Registros
1. Registrar una solicitud de mantenimiento.
2. Registrar la orden de trabajo de una solicitud de mantenimiento.
3. Asignar al menos 2 tecnicos a una orden de trabajo.
4. Registrar al menos 2 actividades especificas en una orden de trabajo.
5. Registrar un plan de mantenimiento preventivo para un equipo y un edificio.

### Consultas
1. Solicitudes de mantenimiento registradas para equipos en una fecha determinada.
2. Actividades especificas realizadas en una orden de trabajo.
3. Informacion de una orden de trabajo para una solicitud de mantenimiento a un edificio.
4. Tecnicos asignados a una orden de trabajo.
5. Plan de mantenimiento preventivo para un edificio.

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
