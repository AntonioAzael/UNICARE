# UNICARE - Sistema de Reportes de Mantenimiento Universitario

Aplicacion de consola desarrollada en **Python** y conectada a **MySQL / MariaDB (XAMPP)** para registrar, dar seguimiento y consultar solicitudes de mantenimiento, ordenes de trabajo y planes preventivos del edificio **Docencia 1** de la universidad.

## Tecnologias y librerias utilizadas

- **Python 3.11**: lenguaje principal del sistema en consola.
- **Python vanilla**: toda la interfaz de consola usa solo la libreria estandar (`print`, `input`, `getpass`, `textwrap`), con menus, tablas y fichas hechos con texto.
- **MySQL Connector/Python (`mysql-connector-python`)**: controlador oficial para conectar Python con la base de datos de XAMPP usando el patron de conexion y manejo de errores (`errorcode`) de la guia oficial de MySQL Connector/Python 5.1.
- **XAMPP (MySQL / phpMyAdmin)**: motor de base de datos local donde se almacenan todas las tablas y registros.

## Estructura del proyecto

- `main.py`: control de acceso (login, auto-registro de estudiante y alta de personal por supervisor), limpieza de pantalla con encabezado fijo, menus segun el rol del usuario y las funciones de captura/impresion en consola.
- `logo.py`: header del sistema donde se imprime el logo ASCII de **UNICARE** junto al titulo y subtitulo.
- `conexion.py`: conexion a MySQL en XAMPP e inicializacion automatica de las tablas y catalogos si la base aun no existe o si viene de una version anterior del esquema.
- `funciones/auth.py`: inicio de sesion, alta de personal y baja de tecnicos (solo supervisores; no se elimina a quien tenga trabajos asignados).
- `funciones/solicitudes.py`: listas de pisos y areas de Docencia 1, catalogo de categorias, registro de solicitudes y las consultas de solicitudes por fecha, seguimiento por folio, reportes por estado y reportes por piso y area.
- `funciones/ordenes.py`: catalogo de tipos de mantenimiento, registro de ordenes de trabajo (con la clasificacion de la solicitud), asignacion de tecnicos, registro de actividades especificas y consultas relacionadas.
- `funciones/soluciones.py`: registro de la solucion de un reporte con los materiales utilizados (descuenta existencia) y consulta de soluciones.
- `funciones/materiales.py`: inventario, alta y baja de materiales, reabastecimiento, registro de material tomado (descuenta solo la cantidad indicada) y consulta de materiales por reponer.
- `funciones/planes.py`: registro y consulta de planes de mantenimiento preventivo por edificio y equipo, y gestion de equipos (alta, edicion y baja).
- `sql/01_tablas_mantenimiento.sql`: creacion de la base de datos `sistema_reportes_mantenimiento` y sus 16 tablas (14 entidades del DER + 2 tablas de relaciones M:M) con llaves primarias y foraneas.
- `sql/02_catalogo_mantenimiento.sql`: carga inicial de catalogos y registros de ejemplo dentro de una transaccion.
- `assets/`: archivos graficos originales del logo (`Logo.ai` y `logo_unicare.png`).
- `docs/`: diagramas DER y MR (`UniCare_DER_MR_14_entidades.drawio`) y la documentacion vigente del proyecto en Word: `Sistema De Reportes Y Mantenimiento - UNICARE.docx`, `Manual tecnico - UNICARE.docx` y `Manual de usuario - UNICARE.docx`.

## Modelo de datos (DER / MR)

Los diagramas estan en la carpeta `docs/` (`UniCare_DER_MR_14_entidades.drawio`). Tablas del modelo relacional:

- Entidades: `usuario`, `categoria`, `prioridad`, `estado`, `edificio`, `equipo_instalacion`, `tipo_mantenimiento`, `material`, `trabajador_mantenimiento`, `reporte`, `solucion`, `mantenimiento`, `historial_mantenimiento`, `plan_mantenimiento`.
- Relaciones M:M: `mantenimiento_trabajador` (PARTICIPA EN) y `solucion_material` (UTILIZA).
- Una **orden de trabajo** es un registro de `mantenimiento` y sus **actividades** se guardan en `historial_mantenimiento`.
- La ubicacion de un reporte se guarda en el propio `reporte` (`clave_edificio`, `piso`, `area` y `lugar`) y se muestra como "Docencia 1, piso, area, lugar". La categoria, la prioridad y el equipo de un reporte pueden quedar vacios hasta que mantenimiento los asigna.

## Registros y consultas del sistema

### Registro de una solicitud (solicitante)
El sistema atiende solo el edificio **Docencia 1**. El solicitante elige o escribe, en este orden (con 0 puede cancelar en cada paso):

1. **Piso**: Planta baja o Planta alta.
2. **Area** segun el piso:
   - Planta baja: Salones, Oficinas/Cubiculos, Laboratorios, Banos y Rack de servidores.
   - Planta alta: Salones, Oficinas/Cubiculos y Laboratorios.
3. **Lugar**:
   - En Salones, Oficinas/Cubiculos y Laboratorios lo escribe con sus palabras (ej. "Salon 104", "Cubiculo 3", "Laboratorio de Redes").
   - En Banos elige Bano de hombres o Bano de mujeres.
   - En Rack de servidores no se pregunta; queda como "Rack de servidores".
4. **Descripcion** del problema con sus propias palabras.

La solicitud se guarda en estado *Pendiente* y el sistema muestra el folio generado. El solicitante ya no elige equipo, tipo de problema ni prioridad: la **categoria**, la **prioridad**, el **equipo afectado** (opcional) y las **observaciones del reporte** los asigna mantenimiento al crear la orden de trabajo, en la misma transaccion. Mientras no se asignan, las pantallas muestran "Sin clasificar", "Sin asignar" o "Sin equipo".

### Registros
1. Registrar una solicitud de mantenimiento (piso, area, lugar y descripcion).
2. Registrar la orden de trabajo de una solicitud de mantenimiento, asignando categoria, prioridad, equipo afectado y observaciones del reporte.
3. Asignar al menos 2 tecnicos a una orden de trabajo.
4. Registrar al menos 2 actividades especificas en una orden de trabajo.
5. Registrar un plan de mantenimiento preventivo para un equipo y un edificio.
6. Registrar la solucion de un reporte y los materiales utilizados.

### Consultas (menu Consultas)
1. Solicitudes de mantenimiento por fecha.
2. Actividades especificas de una orden de trabajo.
3. Informacion de orden de trabajo por edificio (con piso, area y lugar del reporte).
4. Tecnicos asignados a una orden de trabajo.
5. Planes de mantenimiento preventivo por edificio.
6. Soluciones aplicadas y materiales utilizados.
7. Seguimiento de un reporte por folio: datos del reporte, orden de trabajo, tecnicos y solucion.
8. Reportes pendientes y solucionados: resumen por estado y dias abiertos de cada reporte.
9. Materiales por reponer: existencia en o bajo el stock minimo, faltante, total usado y numero de soluciones.
10. Reportes por piso y area: numero de reportes por estado y detalle de un piso y area.

### Gestion (solo supervisores)
- **Gestion de personal**: registro de docentes, administrativos y tecnicos, y baja de tecnicos.
- **Gestion de equipos**: ver equipos, registrar un equipo con su codigo de inventario (siempre en Docencia 1, con piso y area de las mismas listas del registro de solicitudes), editar sus datos o ubicacion y eliminarlo solo si no aparece en ningun reporte ni plan.
- **Gestion de catalogos**: ver, registrar y eliminar categorias y tipos de mantenimiento. No se elimina una categoria que use algun reporte ni un tipo que use alguna orden de trabajo. Los estados y las prioridades son fijos y no se editan desde el sistema.

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
