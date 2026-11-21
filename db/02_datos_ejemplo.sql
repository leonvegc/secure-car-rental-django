--
-- PostgreSQL database dump
--

\restrict BQFh9CMCYqDdqsJK0sGCcnJ1hUuAumCcxFp5365o7Nj0sLvMoeideWGvDiXmfuY

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: clientes_cliente; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.clientes_cliente (id, cedula, nombre_completo, numero_licencia, vencimiento_licencia, telefono, correo, creado_en, actualizado_en) VALUES (1, '200000001', 'Laura Pérez Ficticia', 'LIC-0001', '2028-10-21', '88880001', 'laura@cliente.test', '2026-11-21 12:25:55.426507-06', '2026-11-21 12:25:55.426513-06');
INSERT INTO public.clientes_cliente (id, cedula, nombre_completo, numero_licencia, vencimiento_licencia, telefono, correo, creado_en, actualizado_en) VALUES (2, '200000002', 'Mario Rojas Ficticio', 'LIC-0002', '2026-10-22', '88880002', 'mario@cliente.test', '2026-11-21 12:25:55.427877-06', '2026-11-21 12:25:55.427883-06');
INSERT INTO public.clientes_cliente (id, cedula, nombre_completo, numero_licencia, vencimiento_licencia, telefono, correo, creado_en, actualizado_en) VALUES (3, '200000003', 'Ana Mora Ficticia', 'LIC-0003', '2027-11-21', '', '', '2026-11-21 12:25:55.428546-06', '2026-11-21 12:25:55.428552-06');


--
-- Data for Name: cuentas_rol; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cuentas_rol (id, nombre, descripcion, es_superadmin, es_sistema, creado_en, actualizado_en) VALUES (1, 'SuperAdmin', 'CRUD de usuarios y roles, asigna permisos, ve reportes y auditoría.', true, true, '2026-11-21 12:25:54.983947-06', '2026-11-21 12:25:54.983962-06');
INSERT INTO public.cuentas_rol (id, nombre, descripcion, es_superadmin, es_sistema, creado_en, actualizado_en) VALUES (2, 'Auditor', 'Solo lectura de usuarios y de vehículos.', false, true, '2026-11-21 12:25:54.991857-06', '2026-11-21 12:25:54.991869-06');
INSERT INTO public.cuentas_rol (id, nombre, descripcion, es_superadmin, es_sistema, creado_en, actualizado_en) VALUES (3, 'Agente de alquiler', 'CRUD de vehículos, clientes y alquileres; reportes; solo lectura de usuarios.', false, true, '2026-11-21 12:25:54.99652-06', '2026-11-21 12:25:54.996531-06');


--
-- Data for Name: cuentas_usuario; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cuentas_usuario (id, password, last_login, username, nombre_completo, identificacion, email, is_active, creado_en, actualizado_en, rol_id) VALUES (1, 'argon2$argon2id$v=19$m=65536,t=3,p=2$SmJVS3hXUm5zSkpDTTFoYlVBbE9ySQ$nUyg5YGku1kja5mHcUDshtxH04aspB9uJwerHh/q5f4', NULL, 'superadmin', 'Sofía Administradora', '100000001', 'superadmin@alquiler.test', true, '2026-11-21 12:25:55.157502-06', '2026-11-21 12:25:55.157515-06', 1);
INSERT INTO public.cuentas_usuario (id, password, last_login, username, nombre_completo, identificacion, email, is_active, creado_en, actualizado_en, rol_id) VALUES (2, 'argon2$argon2id$v=19$m=65536,t=3,p=2$OURLWHY4N2dsY1lYV3BtN29WRjZzeA$f7+uxyuBPpcTbqLBJ1wDw4rpHQ8GyMHST8BEUB+ebe0', NULL, 'auditor', 'Andrés Auditor', '100000002', 'auditor@alquiler.test', true, '2026-11-21 12:25:55.291855-06', '2026-11-21 12:25:55.291867-06', 2);
INSERT INTO public.cuentas_usuario (id, password, last_login, username, nombre_completo, identificacion, email, is_active, creado_en, actualizado_en, rol_id) VALUES (3, 'argon2$argon2id$v=19$m=65536,t=3,p=2$SnFSQkNEZGs3Wk9ackh0Z0VUTUVGbg$EsRgseDn0KYa6RcxI9c1gkihcl78EYEUl8Qjelts4Hk', NULL, 'agente', 'Gabriela Agente', '100000003', 'agente@alquiler.test', true, '2026-11-21 12:25:55.41909-06', '2026-11-21 12:25:55.419102-06', 3);


--
-- Data for Name: vehiculos_vehiculo; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.vehiculos_vehiculo (id, placa, marca, modelo, categoria, tarifa_diaria, estado, creado_en, actualizado_en) VALUES (1, 'BCD-123', 'Toyota', 'Yaris', 'ECONOMICO', 25000.00, 'DISPONIBLE', '2026-11-21 12:25:55.421-06', '2026-11-21 12:25:55.421014-06');
INSERT INTO public.vehiculos_vehiculo (id, placa, marca, modelo, categoria, tarifa_diaria, estado, creado_en, actualizado_en) VALUES (2, 'BCD-456', 'Hyundai', 'Accent', 'SEDAN', 30000.00, 'DISPONIBLE', '2026-11-21 12:25:55.422209-06', '2026-11-21 12:25:55.422222-06');
INSERT INTO public.vehiculos_vehiculo (id, placa, marca, modelo, categoria, tarifa_diaria, estado, creado_en, actualizado_en) VALUES (3, 'CRS-789', 'Toyota', 'RAV4', 'SUV', 45000.00, 'DISPONIBLE', '2026-11-21 12:25:55.423276-06', '2026-11-21 12:25:55.423293-06');
INSERT INTO public.vehiculos_vehiculo (id, placa, marca, modelo, categoria, tarifa_diaria, estado, creado_en, actualizado_en) VALUES (5, 'MBS-654', 'Hyundai', 'H1', 'MICROBUS', 65000.00, 'DISPONIBLE', '2026-11-21 12:25:55.42451-06', '2026-11-21 12:25:55.424517-06');
INSERT INTO public.vehiculos_vehiculo (id, placa, marca, modelo, categoria, tarifa_diaria, estado, creado_en, actualizado_en) VALUES (4, 'TRK-321', 'Nissan', 'Frontier', 'PICKUP', 50000.00, 'MANTENIMIENTO', '2026-11-21 12:25:55.423903-06', '2026-11-21 12:25:55.425075-06');


--
-- Data for Name: alquileres_alquiler; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.alquileres_alquiler (id, codigo, fecha_inicio, fecha_fin, dias, tarifa_diaria, total, estado, fecha_devolucion, creado_en, cliente_id, recibido_por_id, registrado_por_id, vehiculo_id) VALUES (1, 'ALQ-89B71618', '2026-11-11', '2026-11-14', 3, 45000.00, 135000.00, 'FINALIZADO', '2026-11-14 12:25:55.430437-06', '2026-11-21 12:25:55.430785-06', 1, 3, 3, 3);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_content_type (id, app_label, model) VALUES (1, 'auth', 'group');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (2, 'auth', 'permission');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (3, 'contenttypes', 'contenttype');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (4, 'sessions', 'session');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (5, 'axes', 'accessattempt');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (6, 'axes', 'accessattemptexpiration');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (7, 'axes', 'accessfailurelog');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (8, 'axes', 'accesslog');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (9, 'core', 'registroauditoria');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (10, 'cuentas', 'permiso');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (11, 'cuentas', 'rol');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (12, 'cuentas', 'usuario');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (13, 'vehiculos', 'vehiculo');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (14, 'clientes', 'cliente');
INSERT INTO public.django_content_type (id, app_label, model) VALUES (15, 'alquileres', 'alquiler');


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (1, 'Can add permission', 2, 'add_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (2, 'Can change permission', 2, 'change_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (3, 'Can delete permission', 2, 'delete_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (4, 'Can view permission', 2, 'view_permission');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (5, 'Can add group', 1, 'add_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (6, 'Can change group', 1, 'change_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (7, 'Can delete group', 1, 'delete_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (8, 'Can view group', 1, 'view_group');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (9, 'Can add content type', 3, 'add_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (10, 'Can change content type', 3, 'change_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (11, 'Can delete content type', 3, 'delete_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (12, 'Can view content type', 3, 'view_contenttype');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (13, 'Can add session', 4, 'add_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (14, 'Can change session', 4, 'change_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (15, 'Can delete session', 4, 'delete_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (16, 'Can view session', 4, 'view_session');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (17, 'Can add access attempt', 5, 'add_accessattempt');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (18, 'Can change access attempt', 5, 'change_accessattempt');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (19, 'Can delete access attempt', 5, 'delete_accessattempt');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (20, 'Can view access attempt', 5, 'view_accessattempt');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (21, 'Can add access log', 8, 'add_accesslog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (22, 'Can change access log', 8, 'change_accesslog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (23, 'Can delete access log', 8, 'delete_accesslog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (24, 'Can view access log', 8, 'view_accesslog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (25, 'Can add access failure', 7, 'add_accessfailurelog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (26, 'Can change access failure', 7, 'change_accessfailurelog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (27, 'Can delete access failure', 7, 'delete_accessfailurelog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (28, 'Can view access failure', 7, 'view_accessfailurelog');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (29, 'Can add access attempt expiration', 6, 'add_accessattemptexpiration');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (30, 'Can change access attempt expiration', 6, 'change_accessattemptexpiration');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (31, 'Can delete access attempt expiration', 6, 'delete_accessattemptexpiration');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (32, 'Can view access attempt expiration', 6, 'view_accessattemptexpiration');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (33, 'Can add registro de auditoría', 9, 'add_registroauditoria');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (34, 'Can change registro de auditoría', 9, 'change_registroauditoria');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (35, 'Can delete registro de auditoría', 9, 'delete_registroauditoria');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (36, 'Can view registro de auditoría', 9, 'view_registroauditoria');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (37, 'Can add permiso', 10, 'add_permiso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (38, 'Can change permiso', 10, 'change_permiso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (39, 'Can delete permiso', 10, 'delete_permiso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (40, 'Can view permiso', 10, 'view_permiso');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (41, 'Can add rol', 11, 'add_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (42, 'Can change rol', 11, 'change_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (43, 'Can delete rol', 11, 'delete_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (44, 'Can view rol', 11, 'view_rol');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (45, 'Can add usuario', 12, 'add_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (46, 'Can change usuario', 12, 'change_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (47, 'Can delete usuario', 12, 'delete_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (48, 'Can view usuario', 12, 'view_usuario');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (49, 'Can add vehiculo', 13, 'add_vehiculo');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (50, 'Can change vehiculo', 13, 'change_vehiculo');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (51, 'Can delete vehiculo', 13, 'delete_vehiculo');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (52, 'Can view vehiculo', 13, 'view_vehiculo');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (53, 'Can add cliente', 14, 'add_cliente');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (54, 'Can change cliente', 14, 'change_cliente');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (55, 'Can delete cliente', 14, 'delete_cliente');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (56, 'Can view cliente', 14, 'view_cliente');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (57, 'Can add alquiler', 15, 'add_alquiler');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (58, 'Can change alquiler', 15, 'change_alquiler');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (59, 'Can delete alquiler', 15, 'delete_alquiler');
INSERT INTO public.auth_permission (id, name, content_type_id, codename) VALUES (60, 'Can view alquiler', 15, 'view_alquiler');


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: cuentas_permiso; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (1, 'usuarios.ver', 'usuarios', 'ver', 'Usuarios: Ver');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (2, 'usuarios.crear', 'usuarios', 'crear', 'Usuarios: Crear');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (3, 'usuarios.editar', 'usuarios', 'editar', 'Usuarios: Editar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (4, 'usuarios.borrar', 'usuarios', 'borrar', 'Usuarios: Borrar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (5, 'roles.ver', 'roles', 'ver', 'Roles: Ver');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (6, 'roles.crear', 'roles', 'crear', 'Roles: Crear');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (7, 'roles.editar', 'roles', 'editar', 'Roles: Editar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (8, 'roles.borrar', 'roles', 'borrar', 'Roles: Borrar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (9, 'vehiculos.ver', 'vehiculos', 'ver', 'Vehículos: Ver');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (10, 'vehiculos.crear', 'vehiculos', 'crear', 'Vehículos: Crear');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (11, 'vehiculos.editar', 'vehiculos', 'editar', 'Vehículos: Editar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (12, 'vehiculos.borrar', 'vehiculos', 'borrar', 'Vehículos: Borrar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (13, 'clientes.ver', 'clientes', 'ver', 'Clientes: Ver');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (14, 'clientes.crear', 'clientes', 'crear', 'Clientes: Crear');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (15, 'clientes.editar', 'clientes', 'editar', 'Clientes: Editar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (16, 'clientes.borrar', 'clientes', 'borrar', 'Clientes: Borrar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (17, 'alquileres.ver', 'alquileres', 'ver', 'Alquileres: Ver');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (18, 'alquileres.crear', 'alquileres', 'crear', 'Alquileres: Crear');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (19, 'alquileres.editar', 'alquileres', 'editar', 'Alquileres: Editar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (20, 'alquileres.borrar', 'alquileres', 'borrar', 'Alquileres: Borrar');
INSERT INTO public.cuentas_permiso (id, codigo, modulo, accion, descripcion) VALUES (21, 'reportes.ver_reportes', 'reportes', 'ver_reportes', 'Reportes: Ver reportes');


--
-- Data for Name: cuentas_rol_permisos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (1, 1, 1);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (2, 1, 2);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (3, 1, 3);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (4, 1, 4);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (5, 1, 5);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (6, 1, 6);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (7, 1, 7);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (8, 1, 8);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (9, 1, 9);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (10, 1, 21);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (11, 2, 1);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (12, 2, 9);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (13, 3, 1);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (14, 3, 9);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (15, 3, 10);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (16, 3, 11);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (17, 3, 12);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (18, 3, 13);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (19, 3, 14);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (20, 3, 15);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (21, 3, 16);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (22, 3, 17);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (23, 3, 18);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (24, 3, 19);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (25, 3, 20);
INSERT INTO public.cuentas_rol_permisos (id, rol_id, permiso_id) VALUES (26, 3, 21);


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.django_migrations (id, app, name, applied) VALUES (1, 'vehiculos', '0001_initial', '2026-11-21 12:25:54.067083-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (2, 'cuentas', '0001_initial', '2026-11-21 12:25:54.101145-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (3, 'clientes', '0001_initial', '2026-11-21 12:25:54.110248-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (4, 'alquileres', '0001_initial', '2026-11-21 12:25:54.134242-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (5, 'contenttypes', '0001_initial', '2026-11-21 12:25:54.140418-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (6, 'contenttypes', '0002_remove_content_type_name', '2026-11-21 12:25:54.153954-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (7, 'auth', '0001_initial', '2026-11-21 12:25:54.181796-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (8, 'auth', '0002_alter_permission_name_max_length', '2026-11-21 12:25:54.18631-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (9, 'auth', '0003_alter_user_email_max_length', '2026-11-21 12:25:54.19054-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (10, 'auth', '0004_alter_user_username_opts', '2026-11-21 12:25:54.19458-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (11, 'auth', '0005_alter_user_last_login_null', '2026-11-21 12:25:54.198394-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (12, 'auth', '0006_require_contenttypes_0002', '2026-11-21 12:25:54.200439-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (13, 'auth', '0007_alter_validators_add_error_messages', '2026-11-21 12:25:54.203892-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (14, 'auth', '0008_alter_user_username_max_length', '2026-11-21 12:25:54.207547-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (15, 'auth', '0009_alter_user_last_name_max_length', '2026-11-21 12:25:54.211454-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (16, 'auth', '0010_alter_group_name_max_length', '2026-11-21 12:25:54.217046-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (17, 'auth', '0011_update_proxy_permissions', '2026-11-21 12:25:54.223978-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (18, 'auth', '0012_alter_user_first_name_max_length', '2026-11-21 12:25:54.228235-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (19, 'axes', '0001_initial', '2026-11-21 12:25:54.24001-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (20, 'axes', '0002_auto_20151217_2044', '2026-11-21 12:25:54.271064-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (21, 'axes', '0003_auto_20160322_0929', '2026-11-21 12:25:54.280351-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (22, 'axes', '0004_auto_20181024_1538', '2026-11-21 12:25:54.295716-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (23, 'axes', '0005_remove_accessattempt_trusted', '2026-11-21 12:25:54.299679-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (24, 'axes', '0006_remove_accesslog_trusted', '2026-11-21 12:25:54.30339-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (25, 'axes', '0007_alter_accessattempt_unique_together', '2026-11-21 12:25:54.319183-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (26, 'axes', '0008_accessfailurelog', '2026-11-21 12:25:54.330235-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (27, 'axes', '0009_add_session_hash', '2026-11-21 12:25:54.334081-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (28, 'axes', '0010_accessattemptexpiration', '2026-11-21 12:25:54.340488-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (29, 'core', '0001_initial', '2026-11-21 12:25:54.35551-06');
INSERT INTO public.django_migrations (id, app, name, applied) VALUES (30, 'sessions', '0001_initial', '2026-11-21 12:25:54.36314-06');


--
-- Name: alquileres_alquiler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alquileres_alquiler_id_seq', 1, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 60, true);


--
-- Name: clientes_cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clientes_cliente_id_seq', 3, true);


--
-- Name: cuentas_permiso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cuentas_permiso_id_seq', 21, true);


--
-- Name: cuentas_rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cuentas_rol_id_seq', 3, true);


--
-- Name: cuentas_rol_permisos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cuentas_rol_permisos_id_seq', 26, true);


--
-- Name: cuentas_usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cuentas_usuario_id_seq', 3, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 15, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 30, true);


--
-- Name: vehiculos_vehiculo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vehiculos_vehiculo_id_seq', 5, true);


--
-- PostgreSQL database dump complete
--

\unrestrict BQFh9CMCYqDdqsJK0sGCcnJ1hUuAumCcxFp5365o7Nj0sLvMoeideWGvDiXmfuY

