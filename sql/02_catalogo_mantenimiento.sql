-- ============================================================================
-- UNICARE - Sistema de Reportes de Mantenimiento Universitario
-- Script 02: Carga inicial de catalogos y registros de muestra
-- El sistema atiende unicamente el edificio Docencia 1 (ED-DOC1)
-- ============================================================================

USE sistema_reportes_mantenimiento;

START TRANSACTION;

-- Catalogo unico de estados (lo usan REPORTE y MANTENIMIENTO)
INSERT INTO estado (nombre_estado, descripcion_estado) VALUES
('Pendiente', 'Registrado y en espera de revision o de inicio de trabajos'),
('En revision', 'Revisado por el area de mantenimiento'),
('En proceso', 'En atencion por el personal tecnico'),
('Solucionado', 'Atendido y cerrado satisfactoriamente'),
('Cancelado', 'Cancelado sin llegar a resolverse');

INSERT INTO categoria (nombre_categoria, descripcion_categoria) VALUES
('Electricidad', 'Fallas en luminarias, contactos o suministro electrico'),
('Limpieza', 'Derrames, residuos o saneamiento en aulas y pasillos'),
('Internet', 'Fallas de conectividad WiFi, puertos Ethernet o switches'),
('Mobiliario', 'Dano fisico en butacas, escritorios, pizarrones o puertas'),
('Infraestructura', 'Goteras, plafones, pintura, tuberias o muros deteriorados');

INSERT INTO prioridad (nombre_prioridad, descripcion_prioridad, nivel_urgencia) VALUES
('Baja', 'Incidencia menor que no interrumpe las clases', 1),
('Media', 'Falla parcial que afecta el uso normal del espacio', 2),
('Alta', 'Falla critica que impide actividades o representa riesgo', 3);

INSERT INTO tipo_mantenimiento (codigo_tipo, nombre_tipo, descripcion_tipo) VALUES
('PREV', 'Preventivo', 'Mantenimiento programado para prevenir fallas en equipos e instalaciones'),
('CORR', 'Correctivo', 'Mantenimiento destinado a reparar fallas o averias reportadas');

INSERT INTO edificio (clave_edificio, nombre_edificio) VALUES
('ED-DOC1', 'Docencia 1');

-- MAT-002, MAT-005, MAT-006 y MAT-007 quedan en o bajo su stock minimo (Consulta 9)
INSERT INTO material (codigo_material, nombre_material, stock_minimo, existencia, descripcion_material) VALUES
('MAT-001', 'Lampara LED 18W', 10, 24, 'Tubo LED blanco frio 120cm para salones y pasillos'),
('MAT-002', 'Conector RJ45 Cat6', 20, 15, 'Conector modular RJ45 para cableado estructurado'),
('MAT-003', 'Cable UTP Cat6 (metro)', 30, 85, 'Cable de red UTP categoria 6'),
('MAT-004', 'Contacto doble polarizado', 8, 12, 'Toma corriente duplex 127V con placa blanca'),
('MAT-005', 'Kit tornilleria butaca', 15, 9, 'Juego de tuercas y tornillos para mobiliario'),
('MAT-006', 'Empaque hidraulico 1/2', 6, 5, 'Empaque de hule para llaves y sanitarios'),
('MAT-007', 'Limpiador de serpentin (litro)', 4, 3, 'Liquido desengrasante para serpentines de minisplit');

INSERT INTO usuario (numero_cuenta, tipo_usuario, correo, contrasena, nombre, primer_apellido, segundo_apellido) VALUES
(1, 'Estudiante', 'mauro.sanchez@ut-tijuana.edu.mx', '1234', 'Mauro Alberto', 'Sanchez', 'Trinidad'),
(2, 'Estudiante', 'angel.zarate@ut-tijuana.edu.mx', '1234', 'Angel Leobardo', 'Zarate', 'Guerrero'),
(3, 'Docente', 'claudia.morales@ut-tijuana.edu.mx', '1234', 'Claudia', 'Morales', 'Vazquez'),
(4, 'Administrativo', 'roberto.mendoza@ut-tijuana.edu.mx', '1234', 'Roberto', 'Mendoza', 'Cruz');

-- empleado_supervisor: Carlos supervisa a Luis y Javier, Javier supervisa a Miguel
INSERT INTO trabajador_mantenimiento (numero_empleado, usuario_acceso, correo, contrasena, nombre, primer_apellido, segundo_apellido, especialidad, exp_laboral, empleado_supervisor) VALUES
(1, 'carlos.ramirez', 'carlos.ramirez@ut-tijuana.edu.mx', '1234', 'Carlos', 'Ramirez', 'Lopez', 'Electricidad y Climas', 8, NULL),
(2, 'luis.gomez', 'luis.gomez@ut-tijuana.edu.mx', '1234', 'Luis Fernando', 'Gomez', 'Diaz', 'Redes e Internet', 4, 1),
(3, 'javier.hernandez', 'javier.hernandez@ut-tijuana.edu.mx', '1234', 'Javier', 'Hernandez', 'Soto', 'Mobiliario e Infraestructura', 5, 1),
(4, 'miguel.torres', 'miguel.torres@ut-tijuana.edu.mx', '1234', 'Miguel Angel', 'Torres', 'Pena', 'Mantenimiento General', 2, 3);

-- Equipos e instalaciones de Docencia 1 (piso y area segun las listas del registro de solicitudes)
INSERT INTO equipo_instalacion (codigo_inventario, nombre_equipo, tipo_equipo_instalacion, necesita_reparacion, area, piso, salon, clave_edificio) VALUES
('EQ-D1-PROY01', 'Proyector Epson Salon 104', 'Equipo Audiovisual', 1, 'Salones', 'Planta baja', '104', 'ED-DOC1'),
('EQ-D1-BUT12', 'Lote Butacas Fila B Salon 102', 'Mobiliario Escolar', 0, 'Salones', 'Planta baja', '102', 'ED-DOC1'),
('EQ-D1-WC01', 'Lavabos Bano de mujeres', 'Instalacion Hidraulica', 0, 'Banos', 'Planta baja', 'BANO-M', 'ED-DOC1'),
('EQ-D1-SW01', 'Switch Cisco Rack Principal', 'Infraestructura de Red', 1, 'Rack de servidores', 'Planta baja', 'RACK', 'ED-DOC1'),
('EQ-D1-LUM03', 'Circuito Luminarias Salon 205', 'Instalacion Electrica', 0, 'Salones', 'Planta alta', '205', 'ED-DOC1'),
('EQ-D1-PC01', 'PC Laboratorio de Redes 01', 'Equipo de Computo', 1, 'Laboratorios', 'Planta alta', 'LAB-REDES', 'ED-DOC1'),
('EQ-D1-AA01', 'Minisplit Cubiculo 3', 'Climatizacion', 0, 'Oficinas/Cubiculos', 'Planta alta', 'CUB-3', 'ED-DOC1');

-- Reportes de muestra (equipo_afectado es lo que escribio el solicitante; NULL si no lo indico):
--   Consulta 1: REP-0001, 0002, 0003 y 0008 registrados en la misma fecha (CURDATE)
--   Consulta 8: 3 Pendiente (sin clasificar), 1 En revision, 2 En proceso, 3 Solucionado y 1 Cancelado
--   Consulta 10: reportes en los dos pisos y en 6 areas (REP-0010 usa un area escrita por el estudiante)
-- Los Pendiente aun no tienen orden, por eso no tienen categoria ni prioridad.
-- REP-0002 y REP-0009 son de mauro.sanchez y siguen Pendiente; REP-0010 lo cancelo su autor.
INSERT INTO reporte (folio, descripcion_reporte, observaciones, fecha_registro, piso, area, lugar, numero_cuenta, clave_edificio, nombre_estado, nombre_categoria, nombre_prioridad, equipo_afectado) VALUES
('REP-2026-0001', 'El proyector enciende pero no da senal HDMI en el escritorio', 'Se requiere revisar el cableado y el puerto HDMI del techo', CURDATE(), 'Planta baja', 'Salones', 'Salon 104', 3, 'ED-DOC1', 'En proceso', 'Electricidad', 'Media', 'Proyector del salon'),
('REP-2026-0002', 'Dos lamparas parpadean en el techo y hacen zumbido', NULL, CURDATE(), 'Planta alta', 'Salones', 'Salon 205', 1, 'ED-DOC1', 'Pendiente', NULL, NULL, 'Lamparas del techo'),
('REP-2026-0003', 'El puerto de red de la estacion 01 no tiene enlace', 'Sin luz indicadora en la tarjeta de red de la estacion', CURDATE(), 'Planta alta', 'Laboratorios', 'Laboratorio de Redes', 2, 'ED-DOC1', 'En revision', 'Internet', 'Alta', 'Compu 01 de la primera fila'),
('REP-2026-0004', 'Tres butacas de la fila B tienen tornillos flojos', 'Atender en horario vespertino para no interrumpir clases', DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'Planta baja', 'Salones', 'Salon 102', 2, 'ED-DOC1', 'Solucionado', 'Mobiliario', 'Baja', 'Butacas de la fila B'),
('REP-2026-0005', 'El minisplit del cubiculo enfria poco y huele a humedad', 'Se solicito limpieza y revision de gas', DATE_SUB(CURDATE(), INTERVAL 13 DAY), 'Planta alta', 'Oficinas/Cubiculos', 'Cubiculo 3', 4, 'ED-DOC1', 'Solucionado', 'Limpieza', 'Media', 'Minisplit'),
('REP-2026-0006', 'Un lavabo gotea sin parar y el agua llega al piso', 'Cerrar la llave de paso mientras se repara', DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'Planta baja', 'Banos', 'Bano de mujeres', 1, 'ED-DOC1', 'Solucionado', 'Infraestructura', 'Media', 'Lavabo de en medio'),
('REP-2026-0007', 'El switch del rack hace mucho ruido y se siente muy caliente', 'Revisar tambien la ventilacion del cuarto del rack', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'Planta baja', 'Rack de servidores', 'Rack de servidores', 3, 'ED-DOC1', 'En proceso', 'Internet', 'Alta', 'Switch del rack'),
('REP-2026-0008', 'El inodoro del fondo no deja de correr agua', NULL, CURDATE(), 'Planta baja', 'Banos', 'Bano de hombres', 2, 'ED-DOC1', 'Pendiente', NULL, NULL, NULL),
('REP-2026-0009', 'Dos contactos de la mesa 4 no tienen corriente', NULL, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Planta alta', 'Laboratorios', 'Laboratorio de Electronica', 1, 'ED-DOC1', 'Pendiente', NULL, NULL, 'Contactos de la mesa 4'),
('REP-2026-0010', 'Una lampara del pasillo no prende', NULL, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Planta baja', 'Pasillo principal', 'Frente a la escalera', 2, 'ED-DOC1', 'Cancelado', NULL, NULL, NULL);

-- Mantenimientos u ordenes de trabajo de muestra (Consulta 3)
INSERT INTO mantenimiento (clave_mantenimiento, fecha_creacion, fecha_programada, fecha_inicio, fecha_fin, descripcion_trabajo, observaciones, costo_mano_obra, costo_materiales, codigo_tipo, folio, nombre_estado) VALUES
('MNT-2026-0001', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 DAY), CURDATE(), NULL, 'Revision integral de proyector y ducto HDMI del Salon 104', 'Trabajo coordinado entre electricidad y redes', 450.00, 180.00, 'CORR', 'REP-2026-0001', 'En proceso'),
('MNT-2026-0002', DATE_SUB(CURDATE(), INTERVAL 4 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Reparacion completa de butacas en el Salon 102', 'Sin pendientes', 250.00, 95.00, 'CORR', 'REP-2026-0004', 'Solucionado'),
('MNT-2026-0003', DATE_SUB(CURDATE(), INTERVAL 12 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Limpieza de filtros y serpentin del minisplit del Cubiculo 3', 'Se adelanto el mantenimiento preventivo', 300.00, 120.00, 'PREV', 'REP-2026-0005', 'Solucionado'),
('MNT-2026-0004', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 2 DAY), NULL, NULL, 'Diagnostico del puerto de red de la estacion 01', NULL, 0.00, 0.00, 'CORR', 'REP-2026-0003', 'Pendiente'),
('MNT-2026-0005', DATE_SUB(CURDATE(), INTERVAL 6 DAY), DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'Cambio de empaques y ajuste del lavabo en el Bano de mujeres', 'Se reviso el resto de los lavabos', 200.00, 60.00, 'CORR', 'REP-2026-0006', 'Solucionado'),
('MNT-2026-0006', DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_SUB(CURDATE(), INTERVAL 1 DAY), DATE_SUB(CURDATE(), INTERVAL 1 DAY), NULL, 'Revision de ventilacion y temperatura del switch del rack', 'Pendiente cambio de ventilador', 350.00, 0.00, 'CORR', 'REP-2026-0007', 'En proceso');

-- Al menos 2 tecnicos por orden; MNT-2026-0001 tiene 3 (Consulta 4)
INSERT INTO mantenimiento_trabajador (clave_mantenimiento, numero_empleado, fecha_asignacion, horas_asignadas, actividad_asignada) VALUES
('MNT-2026-0001', 1, CURDATE(), 2.50, 'Revision de alimentacion electrica del proyector y toma de corriente'),
('MNT-2026-0001', 2, CURDATE(), 3.00, 'Diagnostico de senal de video, puerto HDMI y cableado estructurado'),
('MNT-2026-0001', 4, CURDATE(), 1.50, 'Apoyo en desmontaje de soporte y limpieza interna de filtros'),
('MNT-2026-0002', 3, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 1.50, 'Ajuste y reemplazo de tornilleria en butacas'),
('MNT-2026-0002', 4, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 1.00, 'Revision del resto de las butacas del salon'),
('MNT-2026-0003', 1, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 3.00, 'Limpieza de serpentin y revision de gas del minisplit'),
('MNT-2026-0003', 4, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 1.00, 'Limpieza de filtros y drenaje'),
('MNT-2026-0005', 3, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 1.50, 'Cambio de empaques y ajuste de la llave del lavabo'),
('MNT-2026-0005', 4, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 1.00, 'Secado del area y revision de los demas lavabos'),
('MNT-2026-0006', 1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 2.00, 'Revision de alimentacion electrica del rack'),
('MNT-2026-0006', 2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 2.50, 'Diagnostico de temperatura y ventiladores del switch');

-- Al menos 2 actividades por orden atendida; MNT-2026-0001 tiene 5 (Consulta 2)
INSERT INTO historial_mantenimiento (fecha_historial, descripcion_historial, resultado, observaciones_historial, clave_mantenimiento) VALUES
(CURDATE(), 'Inspeccion visual del proyector y soporte metalico en techo', 'Soporte firme sin danos fisicos', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Medicion de voltaje en contacto superior de alimentacion', 'Lectura estable de 127V', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Prueba de continuidad en cable HDMI hacia el escritorio docente', 'Cable principal con falso contacto detectado', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Limpieza de filtro de aire y optica externa del equipo', 'Filtro limpio y flujo de aire normal', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Reemplazo de conector y prueba de proyeccion con laptop', 'Imagen estable sin perdida de senal', NULL, 'MNT-2026-0001'),
(DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Ajuste y reemplazo de tornillos en tres butacas de la fila B', 'Butacas firmes', NULL, 'MNT-2026-0002'),
(DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Revision de las demas butacas del salon', 'Sin otras butacas flojas', NULL, 'MNT-2026-0002'),
(DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Limpieza de serpentin con desengrasante', 'Serpentin limpio', NULL, 'MNT-2026-0003'),
(DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Limpieza de filtros y drenaje del equipo de clima', 'Completado sin fallas', 'Equipo operando correctamente', 'MNT-2026-0003'),
(DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'Cambio de empaques de la llave del lavabo', 'Sin goteo', NULL, 'MNT-2026-0005'),
(DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'Ajuste de la base del lavabo', 'Lavabo firme', NULL, 'MNT-2026-0005'),
(DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Medicion de temperatura del switch', 'Temperatura por encima de lo normal', NULL, 'MNT-2026-0006'),
(DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Revision de ventiladores del switch', 'Un ventilador con ruido, se solicita reemplazo', NULL, 'MNT-2026-0006');

-- REPORTE 1:1 SOLUCION (Consulta 7: REP-2026-0004 tiene orden, tecnicos y solucion)
INSERT INTO solucion (numero_solucion, fecha_resolucion, tiempo_resolucion, solucion_aplicada, observaciones_solucion, folio) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 1.50, 'Se ajustaron y reemplazaron tornillos de sujecion en tres butacas', 'Mobiliario verificado y firme', 'REP-2026-0004'),
(2, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 4.00, 'Limpieza de serpentin y filtros, revision de gas y drenaje', 'Equipo operando correctamente', 'REP-2026-0005'),
(3, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 2.50, 'Cambio de empaques de la llave y ajuste de la base del lavabo', 'Sin fugas despues de la reparacion', 'REP-2026-0006');

-- SOLUCION M:M MATERIAL (los materiales usados quedan en o bajo su minimo para la Consulta 9)
INSERT INTO solucion_material (numero_solucion, codigo_material, cantidad_usada) VALUES
(1, 'MAT-005', 3),
(2, 'MAT-007', 2),
(3, 'MAT-006', 2),
(3, 'MAT-005', 1);

-- Planes de mantenimiento preventivo por equipo (el edificio se obtiene del equipo) (Consulta 5)
INSERT INTO plan_mantenimiento (clave_plan, nombre_plan, descripcion_plan, frecuencia, duracion_estimada_horas, estado_plan, codigo_inventario) VALUES
('PLAN-2026-0001', 'Mantenimiento Preventivo Minisplits de Cubiculos', 'Limpieza de serpentin, filtros y revision de drenaje en minisplits', 'Trimestral', 4.00, 'Activo', 'EQ-D1-AA01'),
('PLAN-2026-0002', 'Revision Electrica de Salones Planta Alta', 'Inspeccion de luminarias, balastras y tableros de los salones', 'Mensual', 3.50, 'Activo', 'EQ-D1-LUM03'),
('PLAN-2026-0003', 'Limpieza de Rack y Nodos de Red', 'Aspirado de rack principal, revision de patch cords y puertos', 'Semestral', 5.00, 'Inactivo', 'EQ-D1-SW01');

COMMIT;
