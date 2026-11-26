# UNICARE - Sistema de Reportes de Mantenimiento Universitario

Aplicacion de consola desarrollada en **Python** y conectada a **MySQL / MariaDB (XAMPP)** para registrar, dar seguimiento y consultar solicitudes de mantenimiento, ordenes de trabajo y planes preventivos del edificio **Docencia 1** de la universidad.

## Tecnologias y librerias utilizadas

- **Python 3.11**: lenguaje principal del sistema en consola.
- **rich**: libreria para la interfaz de consola con colores. Se usa `Console` (un solo objeto para limpiar la pantalla e imprimir), `Table` (tablas de consultas con bordes redondeados), `Panel` (logo, menus y fichas de solicitudes, ordenes y soluciones) y `Prompt`, `IntPrompt`, `FloatPrompt` y `Confirm` (captura de datos, contrasenas ocultas y confirmaciones s/n).
- **MySQL Connector/Python (`mysql-connector-python`)**: controlador oficial para conectar Python con la base de datos de XAMPP usando el patron de conexion y manejo de errores (`errorcode`) de la guia oficial de MySQL Connector/Python 5.1.
- **XAMPP (MySQL / phpMyAdmin)**: motor de base de datos local donde se almacenan todas las tablas y registros.

## Estructura del proyecto

- `main.py`: control de acceso (login, auto-registro de estudiante y alta de personal por supervisor), limpieza de pantalla con encabezado fijo, menus segun el rol del usuario y las funciones de captura/impresion en consola.
- `logo.py`: header del sistema donde se imprime en un `Panel` de rich el logo a color de **UNICARE** (dibujado con medios bloques) junto al titulo, el subtitulo y la universidad.
- `conexion.py`: conexion a MySQL en XAMPP e inicializacion automatica de las tablas y catalogos si la base aun no existe o si viene de una version anterior del esquema.
- `funciones/auth.py`: inicio de sesion, alta de personal y baja de tecnicos (solo supervisores; no se elimina a quien tenga trabajos asignados).
- `funciones/solicitudes.py`: listas de pisos y areas de Docencia 1, catalogo de categorias, registro, seguimiento y cancelacion de solicitudes y las consultas de solicitudes por fecha, seguimiento por folio, reportes por estado y reportes por piso y area.
- `funciones/ordenes.py`: catalogo de tipos de mantenimiento, registro y cancelacion de ordenes de trabajo (con la clasificacion de la solicitud), asignacion de tecnicos, registro de actividades especificas, ordenes de cada tecnico y consultas relacionadas.
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
- La ubicacion de un reporte se guarda en el propio `reporte` (`clave_edificio`, `piso`, `area` y `lugar`) y se muestra como "Docencia 1, piso, area, lugar". El **equipo o elemento afectado** (`equipo_afectado`, obligatorio) es texto que escribe el solicitante; el reporte ya no se liga con `equipo_instalacion`. La categoria y la prioridad quedan vacias hasta que el supervisor crea la orden de trabajo.

## Roles y permisos

El rol se decide al iniciar sesion (`sesion["rol"]` y `sesion["es_supervisor"]`). Un **supervisor** es un tecnico sin `empleado_supervisor`.

| Rol | Quien es | Que puede hacer |
|---|---|---|
| Solicitante | Estudiante, Docente o Administrativo (mismos permisos) | Registrar solicitudes, ver todas sus solicitudes, dar seguimiento a una suya escribiendo el folio y cancelar las suyas que siguen Pendiente. No entra a las consultas del sistema. |
| Supervisor | Tecnico sin supervisor | Unico que crea ordenes de trabajo (y asigna categoria y prioridad), asigna tecnicos, cancela ordenes y registra planes preventivos. Registra actividades y soluciones en cualquier orden. Administra materiales, personal, equipos y catalogos. Usa las 10 consultas. |
| Tecnico | Tecnico con supervisor | Ve sus ordenes asignadas. Registra actividades y soluciones solo en ordenes donde esta asignado. Ve el inventario y registra material tomado solo en soluciones de sus ordenes. Usa las 10 consultas. Su menu no muestra las opciones de supervisor. |

Los permisos sobre folios y ordenes se validan en `funciones/` (no solo en pantalla): un solicitante solo ve y cancela sus folios, y un tecnico solo registra en ordenes donde aparece en `mantenimiento_trabajador`.

## Ciclo de estados

- **Reporte**: Pendiente -> En revision (al crear la orden) -> En proceso (al asignar tecnicos) -> Solucionado (al registrar la solucion). Solo se cancela desde Pendiente.
- **Orden de trabajo**: Pendiente (al crearla) -> En proceso (al asignar tecnicos) -> Solucionado (al registrar la solucion, con `fecha_fin` de ese dia).
- Asignar tecnicos: solo ordenes Pendiente o En proceso; la orden debe quedar con al menos 2 tecnicos.
- Registrar actividades: solo ordenes En proceso con al menos 2 tecnicos.
- Registrar solucion: solo reportes con su orden vigente En proceso. La orden y el reporte pasan a Solucionado en la misma transaccion.
- Cancelar orden (supervisor): solo ordenes Pendiente o En proceso; la orden queda Cancelado y el reporte regresa a Pendiente (conserva categoria y prioridad) para crearle otra orden.
- Cada lista de seleccion muestra solo lo que se puede elegir en ese flujo.

## Menus

**Menu solicitante**
1. Registrar solicitud de mantenimiento
2. Mis solicitudes (tabla con todas sus solicitudes: folio, fecha, ubicacion, equipo afectado y estado)
3. Seguimiento de mi solicitud (escribe el folio; muestra estado, fecha programada, tecnicos y solucion, sin costos)
4. Cancelar mi solicitud (solo las suyas en Pendiente, con confirmacion)
0. Cerrar sesion

**Menu supervisor**
1. Registrar orden de trabajo de una solicitud
2. Asignar tecnicos a una orden de trabajo (minimo 2)
3. Cancelar orden de trabajo
4. Mis ordenes asignadas
5. Registrar actividades en una orden (minimo 2)
6. Registrar solucion y materiales de un reporte
7. Registrar plan de mantenimiento preventivo
8. Gestion de materiales (inventario, altas, bajas): ver inventario, registrar material nuevo, registrar material tomado, reabastecer y eliminar
9. Consultas del sistema
10. Gestion de personal (registro y baja de tecnicos)
11. Gestion de equipos (altas, cambios y bajas)
12. Gestion de catalogos (categorias y tipos)
0. Cerrar sesion

**Menu tecnico** (solo muestra lo que el tecnico puede hacer)
1. Mis ordenes asignadas
2. Registrar actividades en una orden (minimo 2)
3. Registrar solucion y materiales de un reporte
4. Gestion de materiales (inventario y material tomado): ver inventario y registrar material tomado
5. Consultas del sistema
0. Cerrar sesion

## Registros y consultas del sistema

### Registro de una solicitud (solicitante)
El sistema atiende solo el edificio **Docencia 1**. Todo lo escribe o elige el solicitante, en este orden (con 0 puede cancelar en los pasos obligatorios):

1. **Piso**: Planta baja o Planta alta.
2. **Area** segun el piso:
   - Planta baja: Salones, Oficinas/Cubiculos, Laboratorios, Banos, Rack de servidores y Otra area.
   - Planta alta: Salones, Oficinas/Cubiculos, Laboratorios y Otra area.
   - Con "Otra area" escribe el nombre del area (maximo 30 caracteres) y se guarda lo que escribio.
3. **Lugar**: lo escribe (maximo 60 caracteres, ej. "Salon 104"), salvo en Banos (Bano de hombres o Bano de mujeres) y en Rack de servidores (se registra solo).
4. **Equipo o elemento afectado** (obligatorio en todas las areas, tambien en Rack de servidores; maximo 80 caracteres): "Equipo o elemento afectado (ej. Proyector, Puerta, Switch principal; 0 para cancelar)".
5. **Descripcion** del problema con sus propias palabras.

La solicitud se guarda en estado *Pendiente* y el sistema muestra el folio generado. No se le pregunta categoria, prioridad ni equipo de inventario.

### Folio escrito
En "Seguimiento de un reporte por folio" (consulta 7) y en "Seguimiento de mi solicitud" el usuario **escribe** el folio (ej. REP-2026-0004). Se aceptan minusculas; el sistema valida que exista y, para el solicitante, que sea suyo. Si presiona Enter sin escribir nada, se muestra la lista de folios disponibles como ayuda.

### Registros
1. Registrar una solicitud de mantenimiento (piso, area, lugar, equipo afectado y descripcion).
2. Registrar la orden de trabajo de una solicitud Pendiente (supervisor): muestra la ubicacion, el equipo afectado y la descripcion; el supervisor elige categoria, prioridad y tipo, y escribe la fecha programada, el trabajo, las observaciones del reporte y de la orden y los costos.
3. Asignar al menos 2 tecnicos a una orden de trabajo (supervisor).
4. Registrar al menos 2 actividades especificas en una orden de trabajo En proceso.
5. Registrar un plan de mantenimiento preventivo (supervisor): el equipo se elige con piso -> area -> equipo; la frecuencia se elige de una lista o con "Otra" se escribe (maximo 40 caracteres).
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
- **Gestion de equipos**: ver equipos, registrar un equipo con su codigo de inventario (siempre en Docencia 1, con piso y area de las mismas listas del registro de solicitudes), editar sus datos, ubicacion y si necesita reparacion, y eliminarlo solo si no aparece en ningun plan preventivo.
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
