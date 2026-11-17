-- ============================================================================
-- UNICARE - Sistema de Reportes de Mantenimiento Universitario
-- Script 02: Carga inicial de catalogos y registros de muestra
-- ============================================================================

USE sistema_reportes_mantenimiento;

START TRANSACTION;

INSERT INTO estado_reporte (nombre_estado, descripcion_estado) VALUES
('Pendiente', 'Solicitud registrada en espera de revision y orden de trabajo'),
('En revision', 'Solicitud revisada por el area de mantenimiento'),
('En proceso', 'Solicitud en atencion mediante orden de trabajo activa'),
('Solucionado', 'Falla atendida y cerrada satisfactoriamente');

INSERT INTO estado_orden (nombre_estado, descripcion_estado) VALUES
('Creada', 'Orden de trabajo generada y pendiente de inicio'),
('En proceso', 'Orden de trabajo en ejecucion por el personal tecnico'),
('Finalizada', 'Orden de trabajo concluida con actividades verificadas'),
('Cancelada', 'Orden de trabajo cancelada');

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

INSERT INTO trabajador_mantenimiento (id_trabajador, usuario_acceso, correo, contrasena, nombre, primer_apell, seg_apell, especialidad, exp_laboral, id_supervisor) VALUES
(1, 'carlos.ramirez', 'carlos.ramirez@ut-tijuana.edu.mx', '1234', 'Carlos', 'Ramirez', 'Lopez', 'Electricidad y Climas', 8, NULL),
(2, 'luis.gomez', 'luis.gomez@ut-tijuana.edu.mx', '1234', 'Luis Fernando', 'Gomez', 'Diaz', 'Redes e Internet', 4, NULL),
(3, 'javier.hernandez', 'javier.hernandez@ut-tijuana.edu.mx', '1234', 'Javier', 'Hernandez', 'Soto', 'Mobiliario e Infraestructura', 5, NULL),
(4, 'miguel.torres', 'miguel.torres@ut-tijuana.edu.mx', '1234', 'Miguel Angel', 'Torres', 'Pena', 'Mantenimiento General', 2, NULL);

INSERT INTO equipo_instalacion (codigo_inventario, nombre_equipo, tipo_equipo_instalacion, necesita_reparacion, area, piso, salon, no_edificio) VALUES
('EQ-D1-PROY01', 'Proyector Epson Aula 104', 'Equipo Audiovisual', 1, 'Aulas Planta Baja', 'Planta Baja', '104', 'ED-DOC1'),
('EQ-LABT-PC01', 'PC Lab Redes 01', 'Equipo de Computo', 1, 'Laboratorio Redes', 'Piso 1', 'LAB-201', 'ED-LABT'),
('EQ-LABT-SW01', 'Switch Cisco Rack Principal', 'Infraestructura de Red', 0, 'Site Comunicaciones', 'Piso 1', 'SITE-01', 'ED-LABT'),
('EQ-D2-LUM03', 'Circuito Luminarias Salon 205', 'Instalacion Electrica', 1, 'Aulas Segundo Piso', 'Piso 2', '205', 'ED-DOC2'),
('EQ-D1-BUT12', 'Lote Butacas Fila B Aula 102', 'Mobiliario Escolar', 0, 'Aulas Planta Baja', 'Planta Baja', '102', 'ED-DOC1'),
('EQ-BIB-AA01', 'Minisplit Sala Lectura', 'Climatizacion', 0, 'Sala General', 'Planta Baja', 'SALA-A', 'ED-BIBL');

INSERT INTO requiere (codigo_inventario, no_material) VALUES
('EQ-LABT-PC01', 'MAT-002'),
('EQ-LABT-PC01', 'MAT-003'),
('EQ-LABT-SW01', 'MAT-002'),
('EQ-D2-LUM03', 'MAT-001'),
('EQ-D2-LUM03', 'MAT-004'),
('EQ-D1-BUT12', 'MAT-005');

-- Minimo 3 solicitudes registradas en la misma fecha (CURDATE) para la Consulta 1
INSERT INTO reporte (folio, descripcion_reporte, observaciones, fecha_registro, num_usuario, id_trabajador, nombre_estado, nombre_categoria, nombre_prioridad, codigo_inventario) VALUES
('REP-2026-0001', 'El proyector enciende pero no da senal HDMI en el escritorio', 'Se requiere revisar cableado y puerto HDMI del techo', CURDATE(), 3, 2, 'En proceso', 'Electricidad', 'Media', 'EQ-D1-PROY01'),
('REP-2026-0002', 'Dos lamparas parpadean en el techo del salon 205', 'Balastra con zumbido constante', CURDATE(), 1, NULL, 'Pendiente', 'Electricidad', 'Alta', 'EQ-D2-LUM03'),
('REP-2026-0003', 'Puerto de red sin enlace en estacion 01 de redes', 'Sin luz indicadora en tarjeta de red', CURDATE(), 2, 1, 'En revision', 'Internet', 'Alta', 'EQ-LABT-PC01'),
('REP-2026-0004', 'Tres butacas tenian tornillos flojos en la fila B', 'Atendido en horario vespertino', DATE_SUB(CURDATE(), INTERVAL 4 DAY), 2, 3, 'Solucionado', 'Mobiliario', 'Baja', 'EQ-D1-BUT12');

INSERT INTO utiliza (folio, no_material, cantidad_usada) VALUES
('REP-2026-0004', 'MAT-005', 3);

INSERT INTO solucion (no_solucion, fecha_resolucion, solucion_aplicada, observaciones_solucion, folio, num_usuario) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Se ajustaron y reemplazaron tornillos de sujecion en tres butacas', 'Mobiliario verificado y firme', 'REP-2026-0004', 4);

-- Ordenes de trabajo de muestra (Consulta 3)
INSERT INTO orden_trabajo (num_orden, folio, id_tipo_mantenimiento, nombre_estado, fecha_creacion, fecha_programada, fecha_inicio, fecha_fin, observaciones, costo_mano_obra, costo_materiales) VALUES
('OT-2026-0001', 'REP-2026-0001', 'CORR', 'En proceso', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 DAY), CURDATE(), NULL, 'Revision integral de proyector y ducto HDMI en Docencia 1', 450.00, 180.00),
('OT-2026-0002', 'REP-2026-0004', 'CORR', 'Finalizada', DATE_SUB(CURDATE(), INTERVAL 4 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Reparacion completa de mobiliario en aula 102', 250.00, 95.00);

-- Minimo 3 tecnicos asignados a una orden de trabajo (Consulta 4)
INSERT INTO asignacion_orden (num_orden, id_trabajador, fecha_asignacion, horas_asignadas, actividad_realizar) VALUES
('OT-2026-0001', 1, CURDATE(), 2.50, 'Revision de alimentacion electrica del proyector y toma de corriente'),
('OT-2026-0001', 2, CURDATE(), 3.00, 'Diagnostico de senal de video, puerto HDMI y cableado estructurado'),
('OT-2026-0001', 4, CURDATE(), 1.50, 'Apoyo en desmontaje de soporte y limpieza interna de filtros');

-- Minimo 5 actividades especificas realizadas en una orden de trabajo (Consulta 2)
INSERT INTO actividad_orden (num_orden, descripcion_actividad, fecha_actividad, resultado) VALUES
('OT-2026-0001', 'Inspeccion visual del proyector y soporte metalico en techo', CURDATE(), 'Soporte firme sin danos fisicos'),
('OT-2026-0001', 'Medicion de voltaje en contacto superior de alimentacion', CURDATE(), 'Lectura estable de 127V'),
('OT-2026-0001', 'Prueba de continuidad en cable HDMI hacia el escritorio docente', CURDATE(), 'Cable principal con falso contacto detectado'),
('OT-2026-0001', 'Limpieza de filtro de aire y optica externa del equipo', CURDATE(), 'Filtro limpio y flujo de aire normal'),
('OT-2026-0001', 'Reemplazo de conector y prueba de proyeccion con laptop', CURDATE(), 'Imagen estable sin perdida de senal');

-- Planes de mantenimiento preventivo por edificio y equipo (Consulta 5)
INSERT INTO plan_mantenimiento (num_plan, nombre_plan, no_edificio, codigo_inventario, descripcion_plan, frecuencia, duracion_estimada_horas, estado_plan) VALUES
('PLAN-2026-0001', 'Mantenimiento Preventivo Climas Biblioteca', 'ED-BIBL', 'EQ-BIB-AA01', 'Limpieza de serpentin, filtros y revision de drenaje en minisplits', 'Trimestral', 4.00, 'Activo'),
('PLAN-2026-0002', 'Revision Electrica de Aulas Docencia 2', 'ED-DOC2', 'EQ-D2-LUM03', 'Inspeccion de luminarias, balastras y tableros por piso', 'Mensual', 3.50, 'Activo'),
('PLAN-2026-0003', 'Limpieza de Rack y Nodos de Red', 'ED-LABT', 'EQ-LABT-SW01', 'Aspirado de rack principal, revision de patch cords y puertos', 'Semestral', 5.00, 'Inactivo');

INSERT INTO mantenimiento (clave_mantenimiento, fecha_programada, fecha_realizacion, descripcion_trabajo, id_tipo_mantenimiento) VALUES
('MNT-2026-0001', DATE_SUB(CURDATE(), INTERVAL 12 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Limpieza de filtros y revision de gas en minisplit', 'PREV');

INSERT INTO participa (clave_mantenimiento, id_trabajador) VALUES
('MNT-2026-0001', 1);

INSERT INTO recibe_mantenimiento (clave_mantenimiento, codigo_inventario) VALUES
('MNT-2026-0001', 'EQ-BIB-AA01');

INSERT INTO historial_mantenimiento (no_historial, descripcion_historial, fecha_historial, resultado, observaciones_historial, codigo_inventario, clave_mantenimiento) VALUES
(1, 'Limpieza de serpentin, filtros y drenaje del equipo de clima', DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'Completado sin fallas', 'Equipo operando correctamente', 'EQ-BIB-AA01', 'MNT-2026-0001');

UPDATE trabajador_mantenimiento SET id_supervisor = 1 WHERE id_trabajador = 2;
UPDATE trabajador_mantenimiento SET id_supervisor = 1 WHERE id_trabajador = 3;
UPDATE trabajador_mantenimiento SET id_supervisor = 3 WHERE id_trabajador = 4;

COMMIT;
