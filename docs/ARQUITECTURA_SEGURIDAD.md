# Arquitectura de seguridad

```mermaid
flowchart LR
    U[Navegador] -- HTTPS --> R[Render: proxy TLS]
    R -- X-Forwarded-Proto/For --> G[Gunicorn]
    G --> M1

    subgraph Django["Django 6 (cadena de middleware)"]
        M1[SecurityMiddleware<br/>HTTPS, HSTS, nosniff,<br/>Referrer-Policy, COOP] --> M2[WhiteNoise<br/>estáticos mismo origen]
        M2 --> M3[Sesión en BD<br/>cookie sid: HttpOnly, Secure, SameSite=Strict]
        M3 --> M4[CSRF<br/>token + SameSite]
        M4 --> M5[Autenticación]
        M5 --> M6[Inactividad 60 s<br/>logout + auditoría]
        M6 --> M7[LoginRequired<br/>todas las rutas]
        M7 --> M8[X-Frame-Options DENY<br/>CSP estricta<br/>Permissions-Policy, no-store]
        M8 --> M9[django-axes<br/>bloqueo por fuerza bruta]
        M9 --> V[Vista<br/>@requiere_permiso / @solo_superadmin]
        V -- sin permiso --> E403[handler403<br/>página genérica + auditoría]
        V --> F[ModelForm con campos explícitos<br/>validación y saneamiento]
        F --> ORM[ORM parametrizado]
        V --> T[Plantillas con autoescape<br/>sin JS en línea]
    end

    ORM --> DB[(PostgreSQL<br/>sin acceso externo<br/>CHECK y UNIQUE)]
    V --> A[(RegistroAuditoria<br/>solo inserción)]
```

## Capas de defensa por amenaza

| Amenaza | Controles |
|---|---|
| SQL Injection (UTN-07a) | Solo ORM de Django (consultas parametrizadas); prohibido SQL crudo; validación de entradas con formularios; usuario de BD sin acceso externo (`ipAllowList: []`). |
| XSS (UTN-07b) | Autoescape de plantillas; prohibido `|safe`/`mark_safe`; JS sin `innerHTML`; CSP `script-src 'self'` sin `unsafe-inline` (aunque se colara HTML, el script no corre); validadores con listas blancas de caracteres. |
| Sesión (UTN-07c) | Cookie `sid` con ID aleatorio (sin datos del usuario), HttpOnly, Secure, SameSite=Strict; expiración de 60 s del lado del servidor; rotación del ID al iniciar sesión (anti-fijación); logout solo por POST; `Cache-Control: no-store`. |
| CSRF (UTN-07d) | Middleware CSRF con token en todos los formularios; verificación de Referer en HTTPS; cookies SameSite=Strict. |
| Control de acceso (UTN-05/06) | Permisos módulo.acción asignados a roles; decoradores obligatorios en cada vista; auditoría y roles solo SuperAdmin; respuesta 403 auditada; falla cerrada (vista sin permiso configurado = 403). |
| Fuerza bruta / enumeración | django-axes: 5 intentos por usuario+IP → bloqueo de 15 min (HTTP 429); mensaje de error genérico; Argon2id con costo alto. |
| Credenciales (UTN-02) | Argon2id (m=64 MiB, t=3, p=2); política de contraseñas: 12+ caracteres, complejidad, no comunes. |
| Clickjacking / sniffing (UTN-08) | `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `nosniff`, HSTS 1 año. |
| Fuga de información | `DEBUG=False`; páginas 400/403/404/500 propias; sin panel `/admin/`; encabezado `Server` genérico; logs sin contraseñas. |
| Falsificación de IP | La IP se toma del último proxy de confianza en X-Forwarded-For, no del primer valor (que controla el atacante). |
| Datos sensibles (licencia) | Auditor sin acceso a clientes; licencia enmascarada en listados; nunca en URLs ni en la auditoría. |
