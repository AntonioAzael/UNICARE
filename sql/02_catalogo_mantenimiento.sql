-- ============================================================================
-- UNICARE - Sistema de Reportes de Mantenimiento Universitario
-- Script 02: Carga inicial de catalogos y registros de muestra
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

INSERT INTO tipo_mantenimiento (id_tipo_mantenimiento, nombre_tipo, descripcion_tipo) VALUES
('PREV', 'Preventivo', 'Mantenimiento programado para prevenir fallas en equipos e instalaciones'),
('CORR', 'Correctivo', 'Mantenimiento destinado a reparar fallas o averias reportadas');

INSERT INTO edificio (no_edificio, nombre_edificio) VALUES
('ED-DOC1', 'Docencia 1'),
('ED-DOC2', 'Docencia 2'),
('ED-LABT', 'Laboratorios de Tecnologias'),
('ED-BIBL', 'Biblioteca y Centro de Informacion');

INSERT INTO material (no_material, nombre_material, stock_minimo, existencia, descripcion_material) VALUES
('MAT-001', 'Lampara LED 18W', 10, 24, 'Tubo LED blanco frio 120cm para salones y pasillos'),
('MAT-002', 'Conector RJ45 Cat6', 20, 15, 'Conector modular RJ45 para cableado estructurado'),
('MAT-003', 'Cable UTP Cat6 (metro)', 30, 85, 'Cable de red UTP categoria 6'),
('MAT-004', 'Contacto doble polarizado', 8, 12, 'Toma corriente duplex 127V con placa blanca'),
('MAT-005', 'Kit tornilleria butaca', 15, 9, 'Juego de tuercas y tornillos para mobiliario'),
('MAT-006', 'Empaque hidraulico 1/2', 6, 18, 'Empaque de hule para llaves y sanitarios');

INSERT INTO usuario (num_usuario, tipo_usuario, correo, contrasena, nombre, primer_apellido, segundo_apellido) VALUES
(1, 'Estudiante', 'mauro.sanchez@ut-tijuana.edu.mx', '1234', 'Mauro Alberto', 'Sanchez', 'Trinidad'),
(2, 'Estudiante', 'angel.zarate@ut-tijuana.edu.mx', '1234', 'Angel Leobardo', 'Zarate', 'Guerrero'),
(3, 'Docente', 'claudia.morales@ut-tijuana.edu.mx', '1234', 'Claudia', 'Morales', 'Vazquez'),
(4, 'Administrativo', 'roberto.mendoza@ut-tijuana.edu.mx', '1234', 'Roberto', 'Mendoza', 'Cruz');

-- id_supervisor: Carlos supervisa a Luis y Javier, Javier supervisa a Miguel
INSERT INTO trabajador_mantenimiento (id_trabajador, usuario_acceso, correo, contrasena, nombre, primer_apellido, segundo_apellido, especialidad, exp_laboral, id_supervisor) VALUES
(1, 'carlos.ramirez', 'carlos.ramirez@ut-tijuana.edu.mx', '1234', 'Carlos', 'Ramirez', 'Lopez', 'Electricidad y Climas', 8, NULL),
(2, 'luis.gomez', 'luis.gomez@ut-tijuana.edu.mx', '1234', 'Luis Fernando', 'Gomez', 'Diaz', 'Redes e Internet', 4, 1),
(3, 'javier.hernandez', 'javier.hernandez@ut-tijuana.edu.mx', '1234', 'Javier', 'Hernandez', 'Soto', 'Mobiliario e Infraestructura', 5, 1),
(4, 'miguel.torres', 'miguel.torres@ut-tijuana.edu.mx', '1234', 'Miguel Angel', 'Torres', 'Pena', 'Mantenimiento General', 2, 3);

INSERT INTO equipo_instalacion (codigo_inventario, nombre_equipo, tipo_equipo_instalacion, necesita_reparacion, area, piso, salon, no_edificio) VALUES
('EQ-D1-PROY01', 'Proyector Epson Aula 104', 'Equipo Audiovisual', 1, 'Aulas Planta Baja', 'Planta Baja', '104', 'ED-DOC1'),
('EQ-LABT-PC01', 'PC Lab Redes 01', 'Equipo de Computo', 1, 'Laboratorio Redes', 'Piso 1', 'LAB-201', 'ED-LABT'),
('EQ-LABT-SW01', 'Switch Cisco Rack Principal', 'Infraestructura de Red', 0, 'Site Comunicaciones', 'Piso 1', 'SITE-01', 'ED-LABT'),
('EQ-D2-LUM03', 'Circuito Luminarias Salon 205', 'Instalacion Electrica', 1, 'Aulas Segundo Piso', 'Piso 2', '205', 'ED-DOC2'),
('EQ-D1-BUT12', 'Lote Butacas Fila B Aula 102', 'Mobiliario Escolar', 0, 'Aulas Planta Baja', 'Planta Baja', '102', 'ED-DOC1'),
('EQ-BIB-AA01', 'Minisplit Sala Lectura', 'Climatizacion', 0, 'Sala General', 'Planta Baja', 'SALA-A', 'ED-BIBL');

-- Minimo 3 solicitudes registradas en la misma fecha (CURDATE) para la Consulta 1
INSERT INTO reporte (folio, descripcion_reporte, observaciones, fecha_registro, num_usuario, nombre_estado, nombre_categoria, nombre_prioridad, codigo_inventario) VALUES
('REP-2026-0001', 'El proyector enciende pero no da senal HDMI en el escritorio', 'Se requiere revisar cableado y puerto HDMI del techo', CURDATE(), 3, 'En proceso', 'Electricidad', 'Media', 'EQ-D1-PROY01'),
('REP-2026-0002', 'Dos lamparas parpadean en el techo del salon 205', 'Balastra con zumbido constante', CURDATE(), 1, 'Pendiente', 'Electricidad', 'Alta', 'EQ-D2-LUM03'),
('REP-2026-0003', 'Puerto de red sin enlace en estacion 01 de redes', 'Sin luz indicadora en tarjeta de red', CURDATE(), 2, 'En revision', 'Internet', 'Alta', 'EQ-LABT-PC01'),
('REP-2026-0004', 'Tres butacas tenian tornillos flojos en la fila B', 'Atendido en horario vespertino', DATE_SUB(CURDATE(), INTERVAL 4 DAY), 2, 'Solucionado', 'Mobiliario', 'Baja', 'EQ-D1-BUT12'),
('REP-2026-0005', 'El minisplit de la sala de lectura enfria poco y tiene filtros sucios', 'Se solicito limpieza y revision de gas', DATE_SUB(CURDATE(), INTERVAL 13 DAY), 4, 'Solucionado', 'Limpieza', 'Media', 'EQ-BIB-AA01');

-- REPORTE 1:1 SOLUCION
INSERT INTO solucion (no_solucion, fecha_resolucion, tiempo_resolucion, solucion_aplicada, observaciones_solucion, folio) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 1.50, 'Se ajustaron y reemplazaron tornillos de sujecion en tres butacas', 'Mobiliario verificado y firme', 'REP-2026-0004'),
(2, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 4.00, 'Limpieza de serpentin y filtros, revision de gas y drenaje', 'Equipo operando correctamente', 'REP-2026-0005');

-- SOLUCION M:M MATERIAL
INSERT INTO solucion_material (no_solucion, no_material, cantidad_usada) VALUES
(1, 'MAT-005', 3);

-- Mantenimientos u ordenes de trabajo de muestra (Consulta 3)
INSERT INTO mantenimiento (clave_mantenimiento, fecha_creacion, fecha_programada, fecha_inicio, fecha_fin, descripcion_trabajo, observaciones, costo_mano_obra, costo_materiales, id_tipo_mantenimiento, folio, nombre_estado) VALUES
('MNT-2026-0001', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 DAY), CURDATE(), NULL, 'Revision integral de proyector y ducto HDMI en Docencia 1', 'Trabajo coordinado entre electricidad y redes', 450.00, 180.00, 'CORR', 'REP-2026-0001', 'En proceso'),
('MNT-2026-0002', DATE_SUB(CURDATE(), INTERVAL 4 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Reparacion completa de mobiliario en aula 102', 'Sin pendientes', 250.00, 95.00, 'CORR', 'REP-2026-0004', 'Solucionado'),
('MNT-2026-0003', DATE_SUB(CURDATE(), INTERVAL 12 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Limpieza de filtros y revision de gas en minisplit', 'Mantenimiento preventivo programado', 300.00, 0.00, 'PREV', 'REP-2026-0005', 'Solucionado');

-- Minimo 3 tecnicos asignados a un mantenimiento (Consulta 4)
INSERT INTO mantenimiento_trabajador (clave_mantenimiento, id_trabajador, fecha_asignacion, horas_asignadas, actividad_asignada) VALUES
('MNT-2026-0001', 1, CURDATE(), 2.50, 'Revision de alimentacion electrica del proyector y toma de corriente'),
('MNT-2026-0001', 2, CURDATE(), 3.00, 'Diagnostico de senal de video, puerto HDMI y cableado estructurado'),
('MNT-2026-0001', 4, CURDATE(), 1.50, 'Apoyo en desmontaje de soporte y limpieza interna de filtros'),
('MNT-2026-0002', 3, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 1.50, 'Ajuste y reemplazo de tornilleria en butacas'),
('MNT-2026-0003', 1, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 4.00, 'Limpieza de serpentin, filtros y revision de gas del minisplit');

-- Minimo 5 actividades especificas en un mantenimiento (Consulta 2)
INSERT INTO historial_mantenimiento (fecha_historial, descripcion_historial, resultado, observaciones_historial, clave_mantenimiento) VALUES
(CURDATE(), 'Inspeccion visual del proyector y soporte metalico en techo', 'Soporte firme sin danos fisicos', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Medicion de voltaje en contacto superior de alimentacion', 'Lectura estable de 127V', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Prueba de continuidad en cable HDMI hacia el escritorio docente', 'Cable principal con falso contacto detectado', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Limpieza de filtro de aire y optica externa del equipo', 'Filtro limpio y flujo de aire normal', NULL, 'MNT-2026-0001'),
(CURDATE(), 'Reemplazo de conector y prueba de proyeccion con laptop', 'Imagen estable sin perdida de senal', NULL, 'MNT-2026-0001'),
(DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Ajuste y reemplazo de tornillos en tres butacas de la fila B', 'Butacas firmes', NULL, 'MNT-2026-0002'),
(DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Limpieza de serpentin, filtros y drenaje del equipo de clima', 'Completado sin fallas', 'Equipo operando correctamente', 'MNT-2026-0003');

-- Planes de mantenimiento preventivo por equipo (el edificio se obtiene del equipo) (Consulta 5)
INSERT INTO plan_mantenimiento (num_plan, nombre_plan, descripcion_plan, frecuencia, duracion_estimada_horas, estado_plan, codigo_inventario) VALUES
('PLAN-2026-0001', 'Mantenimiento Preventivo Climas Biblioteca', 'Limpieza de serpentin, filtros y revision de drenaje en minisplits', 'Trimestral', 4.00, 'Activo', 'EQ-BIB-AA01'),
('PLAN-2026-0002', 'Revision Electrica de Aulas Docencia 2', 'Inspeccion de luminarias, balastras y tableros por piso', 'Mensual', 3.50, 'Activo', 'EQ-D2-LUM03'),
('PLAN-2026-0003', 'Limpieza de Rack y Nodos de Red', 'Aspirado de rack principal, revision de patch cords y puertos', 'Semestral', 5.00, 'Inactivo', 'EQ-LABT-SW01');

COMMIT;
