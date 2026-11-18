-- ============================================================================
-- UNICARE - Sistema de Reportes de Mantenimiento Universitario
-- Script 01: Creacion de base de datos y tablas
-- Modelo relacional de 16 tablas (14 entidades + 2 tablas de relaciones M:M)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS sistema_reportes_mantenimiento
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sistema_reportes_mantenimiento;

-- 1. Catalogos y tablas padre

CREATE TABLE usuario (
    num_usuario INT PRIMARY KEY AUTO_INCREMENT,
    tipo_usuario VARCHAR(25) NOT NULL,
    correo VARCHAR(80) NOT NULL UNIQUE,
    contrasena VARCHAR(60) NOT NULL DEFAULT '1234',
    nombre VARCHAR(40) NOT NULL,
    primer_apellido VARCHAR(30) NOT NULL,
    segundo_apellido VARCHAR(30)
);

CREATE TABLE categoria (
    nombre_categoria VARCHAR(25) PRIMARY KEY,
    descripcion_categoria VARCHAR(150) NOT NULL
);

CREATE TABLE prioridad (
    nombre_prioridad VARCHAR(15) PRIMARY KEY,
    descripcion_prioridad VARCHAR(150) NOT NULL,
    nivel_urgencia INT NOT NULL
);

-- Un solo catalogo de estados, lo usan REPORTE y MANTENIMIENTO
CREATE TABLE estado (
    nombre_estado VARCHAR(20) PRIMARY KEY,
    descripcion_estado VARCHAR(150) NOT NULL
);

CREATE TABLE edificio (
    no_edificio VARCHAR(10) PRIMARY KEY,
    nombre_edificio VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE tipo_mantenimiento (
    id_tipo_mantenimiento VARCHAR(10) PRIMARY KEY,
    nombre_tipo VARCHAR(30) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(150) NOT NULL
);

CREATE TABLE material (
    no_material VARCHAR(10) PRIMARY KEY,
    nombre_material VARCHAR(60) NOT NULL,
    stock_minimo INT NOT NULL,
    existencia INT NOT NULL,
    descripcion_material VARCHAR(150) NOT NULL
);

-- id_supervisor es la relacion recursiva SUPERVISA (un trabajador supervisa a otros)
CREATE TABLE trabajador_mantenimiento (
    id_trabajador INT PRIMARY KEY AUTO_INCREMENT,
    usuario_acceso VARCHAR(80) NOT NULL UNIQUE,
    correo VARCHAR(80) NOT NULL UNIQUE,
    contrasena VARCHAR(60) NOT NULL DEFAULT '1234',
    nombre VARCHAR(40) NOT NULL,
    primer_apellido VARCHAR(30) NOT NULL,
    segundo_apellido VARCHAR(30),
    especialidad VARCHAR(40) NOT NULL,
    exp_laboral INT NOT NULL,
    id_supervisor INT NULL,
    FOREIGN KEY (id_supervisor) REFERENCES trabajador_mantenimiento(id_trabajador)
);

-- 2. Equipos y solicitudes (reportes)

CREATE TABLE equipo_instalacion (
    codigo_inventario VARCHAR(15) PRIMARY KEY,
    nombre_equipo VARCHAR(60) NOT NULL,
    tipo_equipo_instalacion VARCHAR(40) NOT NULL,
    necesita_reparacion TINYINT(1) NOT NULL DEFAULT 0,
    area VARCHAR(40) NOT NULL,
    piso VARCHAR(20) NOT NULL,
    salon VARCHAR(20) NOT NULL,
    no_edificio VARCHAR(10) NOT NULL,
    FOREIGN KEY (no_edificio) REFERENCES edificio(no_edificio)
);

CREATE TABLE reporte (
    folio VARCHAR(15) PRIMARY KEY,
    descripcion_reporte VARCHAR(250) NOT NULL,
    observaciones VARCHAR(250),
    fecha_registro DATE NOT NULL,
    num_usuario INT NOT NULL,
    nombre_estado VARCHAR(20) NOT NULL,
    nombre_categoria VARCHAR(25) NOT NULL,
    nombre_prioridad VARCHAR(15) NOT NULL,
    codigo_inventario VARCHAR(15) NOT NULL,
    FOREIGN KEY (num_usuario) REFERENCES usuario(num_usuario),
    FOREIGN KEY (nombre_estado) REFERENCES estado(nombre_estado),
    FOREIGN KEY (nombre_categoria) REFERENCES categoria(nombre_categoria),
    FOREIGN KEY (nombre_prioridad) REFERENCES prioridad(nombre_prioridad),
    FOREIGN KEY (codigo_inventario) REFERENCES equipo_instalacion(codigo_inventario)
);

-- REPORTE 1:1 SOLUCION (folio UNIQUE)
CREATE TABLE solucion (
    no_solucion INT PRIMARY KEY AUTO_INCREMENT,
    fecha_resolucion DATE NOT NULL,
    tiempo_resolucion DECIMAL(5,2) NOT NULL,
    solucion_aplicada VARCHAR(250) NOT NULL,
    observaciones_solucion VARCHAR(250),
    folio VARCHAR(15) NOT NULL UNIQUE,
    FOREIGN KEY (folio) REFERENCES reporte(folio)
);

-- 3. Mantenimientos (ordenes de trabajo), historial y planes

CREATE TABLE mantenimiento (
    clave_mantenimiento VARCHAR(15) PRIMARY KEY,
    fecha_creacion DATE NOT NULL,
    fecha_programada DATE NOT NULL,
    fecha_inicio DATE NULL,
    fecha_fin DATE NULL,
    descripcion_trabajo VARCHAR(250) NOT NULL,
    observaciones VARCHAR(250),
    costo_mano_obra DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    costo_materiales DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    id_tipo_mantenimiento VARCHAR(10) NOT NULL,
    folio VARCHAR(15) NOT NULL,
    nombre_estado VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_tipo_mantenimiento) REFERENCES tipo_mantenimiento(id_tipo_mantenimiento),
    FOREIGN KEY (folio) REFERENCES reporte(folio),
    FOREIGN KEY (nombre_estado) REFERENCES estado(nombre_estado)
);

CREATE TABLE historial_mantenimiento (
    no_historial INT PRIMARY KEY AUTO_INCREMENT,
    fecha_historial DATE NOT NULL,
    descripcion_historial VARCHAR(250) NOT NULL,
    resultado VARCHAR(150) NOT NULL,
    observaciones_historial VARCHAR(250),
    clave_mantenimiento VARCHAR(15) NOT NULL,
    FOREIGN KEY (clave_mantenimiento) REFERENCES mantenimiento(clave_mantenimiento)
);

CREATE TABLE plan_mantenimiento (
    num_plan VARCHAR(15) PRIMARY KEY,
    nombre_plan VARCHAR(80) NOT NULL,
    descripcion_plan VARCHAR(250) NOT NULL,
    frecuencia VARCHAR(40) NOT NULL,
    duracion_estimada_horas DECIMAL(5,2) NOT NULL,
    estado_plan VARCHAR(15) NOT NULL,
    codigo_inventario VARCHAR(15) NOT NULL,
    FOREIGN KEY (codigo_inventario) REFERENCES equipo_instalacion(codigo_inventario)
);

-- 4. Tablas intermedias de las relaciones M:M

-- PARTICIPA_EN: TRABAJADOR M:M MANTENIMIENTO
CREATE TABLE mantenimiento_trabajador (
    clave_mantenimiento VARCHAR(15),
    id_trabajador INT,
    fecha_asignacion DATE NOT NULL,
    horas_asignadas DECIMAL(5,2) NOT NULL,
    actividad_asignada VARCHAR(200) NOT NULL,
    PRIMARY KEY (clave_mantenimiento, id_trabajador),
    FOREIGN KEY (clave_mantenimiento) REFERENCES mantenimiento(clave_mantenimiento),
    FOREIGN KEY (id_trabajador) REFERENCES trabajador_mantenimiento(id_trabajador)
);

-- UTILIZA: SOLUCION M:M MATERIAL
CREATE TABLE solucion_material (
    no_solucion INT,
    no_material VARCHAR(10),
    cantidad_usada INT NOT NULL,
    PRIMARY KEY (no_solucion, no_material),
    FOREIGN KEY (no_solucion) REFERENCES solucion(no_solucion),
    FOREIGN KEY (no_material) REFERENCES material(no_material)
);
