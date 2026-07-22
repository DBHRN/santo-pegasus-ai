---
titulo: "Arquitectura de Microservicios y Mapa de Dominios"
organizacion: "Santo Pegasus Soluciones"
version: "1.0.0"
fecha_emision: "2026-06"
departamento: "Ingeniería de Software / Chapter de Back-end"
clasificacion: "Interno — Uso Técnico Restringido"
documento_relacionado: "Guía Oficial de Ingeniería Back-end (v2.4.0)"
nota_de_limpieza: "Documento normalizado a partir de un PDF fuente. Se estandarizó el idioma (español), se convirtieron tablas y diagramas ASCII a Markdown, y se preservaron íntegramente los bloques de código. El documento fuente está incompleto: se corta en la Sección 11.4 (Sección 11.4 sin contenido) y no incluye las Secciones 12 a 15 listadas en la tabla de contenidos."
---

# Arquitectura de Microservicios y Mapa de Dominios — Santo Pegasus Soluciones

## Tabla de Contenidos

1. Introducción y Visión General de la Arquitectura
2. Diagrama de la Arquitectura General
3. Catálogo Completo de Microservicios
4. Mapa de Dependencias entre Servicios
5. Patrones de Comunicación
6. Estrategia de Bases de Datos
7. API Gateway
8. Infraestructura en AWS
9. Observabilidad Distribuida
10. Estrategia de Versionado de APIs
11. Seguridad entre Servicios
12. Mapa de Squads y Ownership *(no incluido en el documento fuente)*
13. Roadmap Técnico *(no incluido en el documento fuente)*
14. Architecture Decision Records — ADRs *(no incluido en el documento fuente)*
15. Disposiciones Finales y Proceso de Actualización *(no incluido en el documento fuente)*

---

## 1. Introducción y Visión General de la Arquitectura

### 1.1 Propósito del Documento

Este documento constituye el mapa arquitectónico oficial de Santo Pegasus Soluciones. Su propósito es servir como referencia canónica para todos los ingenieros, Tech Leads, Product Managers y stakeholders técnicos que necesiten comprender cómo están organizados, interconectados y desplegados los sistemas que componen el portafolio de productos de la empresa.

Este artefacto debe leerse en conjunto con la **Guía Oficial de Ingeniería Back-end (v2.4.0)**, que establece los estándares de codificación, patrones de diseño y prácticas de seguridad obligatorias para todos los servicios aquí descritos. Ambos documentos forman el núcleo de la base de conocimiento técnico de Santo Pegasus y son fuentes de verdad para la toma de decisiones arquitectónicas.

### 1.2 Contexto Empresarial

Santo Pegasus Soluciones es una empresa de tecnología especializada en el desarrollo de productos digitales para el sector de salud y servicios profesionales. El producto principal de la compañía es **Agendio**, una plataforma SaaS de agendamiento de consultas médicas que conecta pacientes, médicos y clínicas a través de una experiencia digital integrada.

La plataforma Agendio opera en modelo multi-tenant, atendiendo a redes de clínicas, hospitales de pequeño y mediano porte, y consultorios independientes en todo Brasil. La criticidad del dominio de salud exige que la arquitectura priorice disponibilidad, seguridad de datos sensibles, conformidad con la **LGPD** (Lei Geral de Proteção de Dados) y auditabilidad completa de todas las operaciones.

### 1.3 Por Qué Microservicios

La adopción de una arquitectura de microservicios en Santo Pegasus no fue una decisión tomada de forma prematura. La empresa comenzó con un monolito funcional, y la migración a microservicios fue guiada por necesidades reales e inmediatas de escala, autonomía de equipos y velocidad de entrega, en consonancia con los principios fundamentales documentados en la Guía de Ingeniería Back-end.

Las motivaciones concretas que justificaron la transición son:

- **Escalabilidad Independiente**: el servicio de agendamiento (`agendio-scheduling-service`) presenta picos de carga en horarios matutinos (entre 07:00 y 09:00) que no impactan otros dominios. En arquitectura monolítica, escalar ese módulo implicaría escalar toda la aplicación, desperdiciando recursos computacionales y aumentando costos operativos.
- **Autonomía de Squads**: con equipos organizados por dominio de negocio, la arquitectura de microservicios permite que cada squad tenga ownership completo de su ciclo de vida de software — desde el código hasta el deploy en producción — sin coordinación burocrática con otros equipos para releases.
- **Resiliencia e Aislamiento de Fallas**: un defecto crítico en el `payment-service` no debe causar la indisponibilidad del agendamiento de consultas. El aislamiento de procesos garantiza que las fallas se contengan dentro del dominio afectado.
- **Flexibilidad Tecnológica**: diferentes dominios tienen diferentes requisitos técnicos. El `medical-records-service` se beneficia de MongoDB para el almacenamiento de documentos clínicos flexibles y semi-estructurados, mientras que el `auth-service` requiere la consistencia fuerte de PostgreSQL para la gestión de credenciales.
- **Velocidad de Entrega**: la independencia de deploys permite que múltiples squads liberen nuevas funcionalidades en el mismo día sin coordinación de releases ni ventanas de mantenimiento compartidas.

### 1.4 Principios Arquitectónicos que Guían las Decisiones

Todas las decisiones arquitectónicas en Santo Pegasus están ancladas en los siguientes principios, que deben ser internalizados por todo el equipo de ingeniería:

| # | Principio | Descripción |
|---|---|---|
| P-01 | High Cohesion, Low Coupling | Cada microservicio debe encapsular un dominio de negocio bien definido. Las dependencias entre servicios deben ser minimizadas y, cuando existan, preferiblemente asíncronas. |
| P-02 | Database per Service | Cada microservicio posee y controla exclusivamente su propia base de datos. El acceso directo a la base de datos de otro servicio está terminantemente prohibido. |
| P-03 | API First | Los contratos de API (OpenAPI/Swagger) se definen antes de la implementación. Esto garantiza que los consumidores puedan desarrollar en paralelo usando mocks. |
| P-04 | Security by Default | Todas las comunicaciones entre servicios son autenticadas. Ningún endpoint interno es accesible sin validación de identidad. mTLS es obligatorio para comunicación interna. |
| P-05 | Observability by Design | Logs estructurados, métricas y rastreo distribuido no se añaden post-hoc; son parte del scaffolding inicial de cada nuevo servicio. |
| P-06 | Fail Fast, Recover Gracefully | Los servicios implementan circuit breakers, timeouts y políticas de retry con backoff exponencial para garantizar resiliencia ante fallas de dependencias. |
| P-07 | Compliance First | Las decisiones sobre almacenamiento, transmisión y procesamiento de datos sensibles de salud son guiadas por la LGPD y buenas prácticas de seguridad antes que cualquier requisito funcional. |
| P-08 | Infrastructure as Code | Toda la infraestructura AWS se define como código (Terraform/AWS CDK). Ningún recurso de producción se crea manualmente vía Console. |
| P-09 | Evolutionary Architecture | La arquitectura acepta que cambiará. Las decisiones se toman con horizontes de tiempo claros y se revisan periódicamente en los foros de Architecture Review. |
| P-10 | SOLID in Every Service | Los principios SOLID se aplican tanto a nivel de clase como a nivel de servicio. Cada microservicio tiene una única responsabilidad de dominio. |

### 1.5 Ecosistema Tecnológico Principal

El ecosistema tecnológico de Santo Pegasus está estandarizado para garantizar consistencia operacional y reducir la carga cognitiva de los equipos:

- **Lenguaje y Runtime**: Java 17+ (LTS), con adopción gradual de Java 21 (Virtual Threads)
- **Framework Principal**: Spring Boot 3+, Spring Security, Spring Cloud
- **Contenedorización**: Docker (imágenes inmutables), orquestados en AWS ECS Fargate
- **Bases de Datos**: PostgreSQL (relacional), MongoDB/AWS DocumentDB (documentos), Redis/AWS ElastiCache (caché)
- **Mensajería**: AWS SQS (colas y eventos entre dominios)
- **Autenticación**: JWT + OAuth 2.0 / OpenID Connect, gestionado por `auth-service`
- **Observabilidad**: SLF4J + Logback, Spring Boot Actuator, Micrometer, Prometheus, Datadog
- **CI/CD**: GitHub Actions + Pipelines con Docker, Flyway/Liquibase para migrations
- **Secrets Management**: AWS Secrets Manager + Spring Cloud Config

---

## 2. Diagrama de la Arquitectura General

### 2.1 Visión de Alto Nivel

La topología general de la arquitectura de microservicios de Santo Pegasus sigue el siguiente flujo de tráfico, desde los clientes externos hasta los servicios internos, bases de datos y sistemas de mensajería:

**Clientes externos**: Web App (React), Mobile App (iOS/Android), API de clínicas partners — se conectan vía HTTPS/TLS 1.3.

**API Gateway (Kong / AWS API GW)**: punto único de entrada. Responsabilidades: routing, rate limiting, validación de token de autenticación, terminación SSL, CORS, logging de requests.

**Microservicios detrás del Gateway**:

| Servicio | Puerto | Base de datos asociada |
|---|---|---|
| `auth-service` | 8081 | PostgreSQL — `auth_db` |
| `user-service` | 8082 | PostgreSQL — `users_db` |
| `agendio-scheduling-service` | 8083 | PostgreSQL — `scheduling_db` |
| `payment-service` | 8085 | PostgreSQL — `payments_db` |
| `ai-assistant-service` | 8087 | Pinecone (Vector Store) |
| `agendio-notification-service` | 8084 | Sin base de datos propia (stateless) |
| `medical-records-service` | 8086 | MongoDB / AWS DocumentDB — `medical_records_db` |
| `audit-service` | 8088 | PostgreSQL — `audit_db` |

**Capa de mensajería asíncrona — AWS SQS Queues**:

| Cola | Consumidores |
|---|---|
| `appointment-created.fifo` | `agendio-notification-service` |
| `appointment-cancelled.fifo` | `agendio-notification-service`, `audit-service` |
| `payment-confirmed.fifo` | `agendio-scheduling-service`, `audit-service` |
| `user-created.fifo` | `agendio-notification-service`, `audit-service` |
| `audit-events.fifo` | `audit-service` |

**Infraestructura compartida**: AWS ElastiCache (Redis) para caché global, AWS CloudWatch + Datadog para observabilidad, AWS Secrets Manager + Spring Cloud Config para gestión de configuración y secretos.

### 2.2 Flujo de una Solicitud Típica (Agendamiento de Consulta)

1. El cliente (app mobile) envía `POST /v1/appointments` con un Bearer JWT.
2. El **API Gateway** valida el JWT contra `auth-service` (usando caché en Redis, TTL 5 min), aplica rate limit (100 req/min por tenant) y enruta la solicitud hacia `agendio-scheduling-service`.
3. El **`agendio-scheduling-service`**:
   - Valida la disponibilidad del médico consultando su propia base de datos.
   - Verifica el perfil del paciente vía `user-service` (llamada REST síncrona).
   - Crea el registro de la consulta en `scheduling_db` (PostgreSQL).
   - Publica el evento `appointment-created` en SQS.
   - Retorna `201 Created` con el payload de la consulta.
4. **[Asíncrono]** `agendio-notification-service` consume el evento de SQS y envía email de confirmación (AWS SES) y SMS (AWS SNS).
5. **[Asíncrono]** `audit-service` consume el mismo evento y registra la acción en `audit_db` con el Trace ID completo.

---

## 3. Catálogo Completo de Microservicios

### 3.1 Resumen del Catálogo

| Servicio | Puerto | Dominio | Base de Datos | Squad Owner |
|---|---|---|---|---|
| `auth-service` | 8081 | Identidad y Seguridad | PostgreSQL | Squad Hermes |
| `user-service` | 8082 | Usuarios y Perfiles | PostgreSQL | Squad Hermes |
| `agendio-scheduling-service` | 8083 | Agendamiento (Core) | PostgreSQL | Squad Agendio Core |
| `agendio-notification-service` | 8084 | Notificaciones | — (stateless) | Squad Agendio Core |
| `payment-service` | 8085 | Pagos y Facturación | PostgreSQL | Squad Pagamentos |
| `medical-records-service` | 8086 | Historial Clínico | MongoDB | Squad Clínico |
| `ai-assistant-service` | 8087 | Asistencia IA (RAG) | Pinecone (Vector) | Squad IA |
| `audit-service` | 8088 | Auditoría y Compliance | PostgreSQL | Squad Governance |

### 3.2 `auth-service` — Autenticación y Autorización

- **Repositorio Git**: `git@github.com:santopegasus/auth-service.git`
- **Squad Owner**: Squad Hermes
- **Tech Lead**: Isabella Carvalho
- **Puerto**: 8081

**Responsabilidad**: el `auth-service` es la raíz de confianza del ecosistema de Santo Pegasus. Es responsable de la emisión, validación y revocación de tokens JWT, de la gestión del ciclo de vida de credenciales de usuarios, y de la integración con el flujo OAuth 2.0 / OpenID Connect para clientes de terceros. Ningún otro servicio valida credenciales directamente; toda autenticación pasa obligatoriamente por este servicio.

**Tecnologías**:
- Framework: Spring Boot 3.x + Spring Security 6
- Autenticación: JWT (RS256), OAuth 2.0, OpenID Connect (OIDC)
- Base de Datos: PostgreSQL 15 (`auth_db`) vía AWS RDS
- Caché de Tokens: AWS ElastiCache (Redis) — TTL configurable por tipo de token
- Secrets: AWS Secrets Manager para llaves RSA privadas

**APIs Expuestas**:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/v1/auth/login` | Autenticación con email/password, retorna JWT + Refresh Token |
| `POST` | `/v1/auth/refresh` | Renovación de token vía Refresh Token |
| `POST` | `/v1/auth/logout` | Revocación de token (blacklist en Redis) |
| `POST` | `/v1/auth/oauth2/token` | Flujo OAuth 2.0 Client Credentials |
| `GET` | `/v1/auth/validate` | Validación de token (usado por API Gateway) |
| `POST` | `/v1/auth/password/reset` | Solicitud de reset de contraseña |
| `GET` | `/.well-known/jwks.json` | JWKS endpoint para validación pública de tokens |

**Dependencias con otros servicios**:
- `user-service` (REST síncrono): para validar existencia y status del usuario durante el login.
- `audit-service` (SQS asíncrono): publica eventos de `auth.login.success`, `auth.login.failure`, `auth.token.revoked`.

**Modelo de Datos (`auth_db`)**:
```
users_credentials → id, user_id, password_hash, is_active, mfa_secret
refresh_tokens     → id, token_hash, user_id, expires_at, is_revoked
roles              → id, name, permissions (JSONB)
user_roles         → user_id, role_id
oauth_clients      → client_id, client_secret_hash, scopes, redirect_uris
```

### 3.3 `user-service` — Gestión de Perfiles de Usuarios

- **Repositorio Git**: `git@github.com:santopegasus/user-service.git`
- **Squad Owner**: Squad Hermes
- **Tech Lead**: Isabella Carvalho
- **Puerto**: 8082

**Responsabilidad**: gestiona los perfiles de todos los actores del sistema: pacientes, médicos, administradores de clínicas y operadores. Es la fuente de verdad para datos de perfil, como nombre, contacto, especialidades médicas (para el rol Doctor) y configuraciones de cuenta. No almacena credenciales de acceso — esa responsabilidad es exclusiva del `auth-service`.

**Tecnologías**:
- Framework: Spring Boot 3.x
- Base de Datos: PostgreSQL 15 (`users_db`) vía AWS RDS
- Caché: Redis para cachear perfiles frecuentemente accedidos (TTL 10 min)
- Mapeo: MapStruct para conversión Entidad → DTO
- Documentación: springdoc-openapi (Swagger UI)

**APIs Expuestas**:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/v1/users` | Creación de nuevo usuario |
| `GET` | `/v1/users/{id}` | Consulta de perfil por ID |
| `PUT` | `/v1/users/{id}` | Actualización completa de perfil |
| `PATCH` | `/v1/users/{id}/status` | Activación / desactivación de cuenta |
| `GET` | `/v1/doctors` | Listado de médicos con filtros (especialidad, ciudad) |
| `GET` | `/v1/doctors/{id}/availability` | Disponibilidad del médico (proxy hacia scheduling) |
| `GET` | `/v1/users/{id}/preferences` | Preferencias de notificación del usuario |

**Dependencias**:
- `audit-service` (SQS asíncrono): eventos de `user.created`, `user.updated`, `user.deactivated`.
- `agendio-notification-service` (SQS asíncrono): evento `user.created` para disparo de email de bienvenida.

**Modelo de Datos (`users_db`)**:
```
users       → id (UUID), name, email, phone, cpf_hash, role, status, created_at
doctors     → user_id (FK), crm, specialty, bio, consultation_price
patients    → user_id (FK), birth_date, health_plan, emergency_contact
addresses   → id, user_id (FK), street, city, state, zip_code
preferences → user_id (FK), notify_email, notify_sms, language
```

### 3.4 `agendio-scheduling-service` — Núcleo de Agendamiento

- **Repositorio Git**: `git@github.com:santopegasus/agendio-scheduling-service.git`
- **Squad Owner**: Squad Agendio Core
- **Tech Lead**: Rodrigo Mendes
- **Puerto**: 8083

**Responsabilidad**: es el servicio más crítico del ecosistema. Gestiona toda la lógica de negocio de agendamiento de consultas médicas: creación, confirmación, cancelación y reagendamiento de consultas; gestión de la agenda de disponibilidad de médicos; control de conflictos de horarios; y reglas de negocio específicas de cada clínica (como políticas de cancelación y límites de consultas por paciente). Ninguna regla de agendamiento reside fuera de este servicio.

**Tecnologías**:
- Framework: Spring Boot 3.x + Spring Data JPA
- Base de Datos: PostgreSQL 15 (`scheduling_db`) vía AWS RDS — transacciones ACID críticas
- Migrations: Flyway — versionado de schema en Git junto al código
- Mensajería: AWS SQS Producer (publica eventos de ciclo de vida de consultas)
- Circuit Breaker: Resilience4j para llamadas a `user-service` y `payment-service`

**APIs Expuestas**:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/v1/appointments` | Crear nuevo agendamiento |
| `GET` | `/v1/appointments/{id}` | Consultar agendamiento por ID |
| `PATCH` | `/v1/appointments/{id}/cancel` | Cancelar consulta |
| `PATCH` | `/v1/appointments/{id}/reschedule` | Reagendar consulta |
| `GET` | `/v1/appointments/patient/{patientId}` | Historial de consultas del paciente |
| `GET` | `/v1/schedules/doctor/{doctorId}` | Agenda de disponibilidad del médico |
| `POST` | `/v1/schedules/doctor/{doctorId}/slots` | Configurar slots de disponibilidad |
| `PUT` | `/v1/schedules/doctor/{doctorId}/block` | Bloquear período (vacaciones, ausencias) |

**Dependencias**:
- `user-service` (REST síncrono, Resilience4j): validar paciente y médico existentes.
- `payment-service` (REST síncrono): verificar status de pago antes de confirmar consulta.
- `audit-service` (SQS): eventos de toda alteración de estado de consulta.
- `agendio-notification-service` (SQS): publicar eventos para disparo de notificaciones.

**Eventos SQS Publicados**:
```
appointment-created.fifo
appointment-confirmed.fifo
appointment-cancelled.fifo
appointment-rescheduled.fifo
appointment-reminder-due.fifo (publicado por scheduler interno, T-24h y T-1h)
```

**Modelo de Datos (`scheduling_db`)**:
```
appointments     → id (UUID), patient_id, doctor_id, clinic_id, status,
                    scheduled_at, duration_min, type, notes, created_at
schedule_slots   → id, doctor_id, day_of_week, start_time, end_time, is_available
blocked_periods  → id, doctor_id, start_date, end_date, reason
clinics          → id, name, cnpj, address, max_appointments_per_day
```

### 3.5 `agendio-notification-service` — Notificaciones

- **Repositorio Git**: `git@github.com:santopegasus/agendio-notification-service.git`
- **Squad Owner**: Squad Agendio Core
- **Tech Lead**: Rodrigo Mendes
- **Puerto**: 8084

**Responsabilidad**: servicio stateless responsable de orquestar el envío de todas las notificaciones de la plataforma Agendio: confirmaciones de consulta, recordatorios automáticos, alertas de cancelación y mensajes de bienvenida. Consume eventos de SQS y decide el canal de entrega (email vía AWS SES o SMS vía AWS SNS) basado en las preferencias del usuario (consultadas en `user-service`). No posee base de datos propia; su estado es derivado íntegramente de los eventos recibidos.

**Tecnologías**:
- Framework: Spring Boot 3.x + Spring Cloud AWS
- Email: AWS SES (Simple Email Service) con templates HTML/Thymeleaf
- SMS: AWS SNS (Simple Notification Service)
- Mensajería: AWS SQS Consumer (escucha múltiples colas)
- Stateless: sin base de datos propia — idempotencia garantizada vía SQS Deduplication ID

**Dependencias**:
- `user-service` (REST síncrono): consultar preferencias de notificación del usuario.
- AWS SES: para envío de emails transaccionales.
- AWS SNS: para envío de SMS.
- SQS (Consumer): consume eventos de `agendio-scheduling-service` y `user-service`.

**Templates de Notificación Gestionados**:

| Evento | Canal | Template |
|---|---|---|
| `appointment-created` | Email + SMS | Confirmación con código y detalles |
| `appointment-reminder-due` (T-24h) | Email + SMS | Recordatorio 24h antes |
| `appointment-reminder-due` (T-1h) | SMS | Recordatorio 1h antes |
| `appointment-cancelled` | Email | Confirmación de cancelación |
| `appointment-rescheduled` | Email + SMS | Nuevo horario confirmado |
| `user-created` | Email | Bienvenida a la plataforma |
| `password-reset-requested` | Email | Link de reset (expira en 30 min) |

### 3.6 `payment-service` — Procesamiento de Pagos

- **Repositorio Git**: `git@github.com:santopegasus/payment-service.git`
- **Squad Owner**: Squad Pagamentos
- **Tech Lead**: Lucas Andrade
- **Puerto**: 8085

**Responsabilidad**: gestiona el ciclo de vida completo de transacciones financieras de la plataforma: procesamiento de pagos vía Pix y tarjeta de crédito/débito, integración con el gateway de pago externo (Stripe), gestión de reembolsos, y generación de recibos. Toda operación financiera es idempotente y completamente auditada. El servicio no almacena datos de tarjeta en sus propias bases de datos — el tokenizado es responsabilidad del gateway externo (cumplimiento PCI-DSS).

**Tecnologías**:
- Framework: Spring Boot 3.x
- Base de Datos: PostgreSQL 15 (`payments_db`) vía AWS RDS — ACID para consistencia financiera
- Gateway Externo: Stripe API (tarjeta) + API del Banco Central (Pix vía PSP asociado)
- Idempotencia: clave de idempotencia obligatoria en todos los endpoints de creación
- Webhooks: endpoint seguro para recibir callbacks del gateway (validación de firma HMAC)

**APIs Expuestas**:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/v1/payments` | Iniciar transacción de pago |
| `GET` | `/v1/payments/{id}` | Consultar status de pago |
| `POST` | `/v1/payments/{id}/refund` | Solicitar reembolso |
| `GET` | `/v1/payments/appointment/{appointmentId}` | Pago vinculado a una consulta |
| `POST` | `/v1/webhooks/stripe` | Recibir eventos del gateway Stripe |
| `POST` | `/v1/webhooks/pix` | Recibir confirmaciones de Pix |

**Dependencias**:
- `audit-service` (SQS): todo evento de transacción financiera se publica para auditoría.
- `agendio-scheduling-service` (SQS Consumer): recibe `payment-confirmed` para confirmar la consulta.
- Stripe API (REST externo): gateway de tarjeta.
- PSP asociado (REST externo): gateway Pix.

**Modelo de Datos (`payments_db`)**:
```
transactions    → id (UUID), appointment_id, patient_id, amount, currency,
                   status, method, gateway_tx_id, idempotency_key, created_at
refunds         → id, transaction_id (FK), amount, reason, status, created_at
payment_methods → id, patient_id, type (PIX/CARD), stripe_token, last4, is_default
receipts        → id, transaction_id (FK), pdf_url, issued_at
```

### 3.7 `medical-records-service` — Historial Clínico (Cumplimiento LGPD)

- **Repositorio Git**: `git@github.com:santopegasus/medical-records-service.git`
- **Squad Owner**: Squad Clínico
- **Tech Lead**: Ana Paula Fonseca
- **Puerto**: 8086

**Responsabilidad**: el servicio más sensible del ecosistema desde la perspectiva de protección de datos. Gestiona el historial clínico de los pacientes: anamnesis, diagnósticos, prescripciones, resultados de exámenes y archivos adjuntos (PDFs, imágenes). El acceso a los datos clínicos está estrictamente controlado por Role-Based Access Control (RBAC) y toda consulta a registros es auditada. El diseño del servicio cumple íntegramente con los requisitos de la LGPD: se requiere consentimiento explícito del paciente para compartir datos, y los registros son anonimizables por solicitud.

**Tecnologías**:
- Framework: Spring Boot 3.x + Spring Security (RBAC granular)
- Base de Datos: MongoDB vía AWS DocumentDB (`medical_records_db`) — esquema flexible para evolución de formularios clínicos
- Almacenamiento de Archivos: AWS S3 (exámenes en PDF, imágenes DICOM) con URLs pre-firmadas de duración limitada (15 minutos)
- Criptografía: campos sensibles (diagnósticos, anotaciones del médico) encriptados en reposo con AWS KMS
- Anonimización: pipeline de anonimización basado en solicitud formal, ejecutado como job asíncrono

**Reglas de Acceso RBAC**:

| Rol | Permiso |
|---|---|
| `ROLE_PATIENT` | Leer únicamente sus propios registros |
| `ROLE_DOCTOR` | Leer y escribir registros de sus pacientes activos |
| `ROLE_ADMIN_CLINIC` | Leer (sin datos sensibles) registros de su clínica |
| `ROLE_AUDITOR` | Leer metadatos de acceso (sin contenido clínico) |
| `ROLE_SYSTEM` | Acceso de sistema para integraciones internas |

**APIs Expuestas**:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/v1/records` | Crear registro clínico (solo DOCTOR) |
| `GET` | `/v1/records/patient/{patientId}` | Listar historial del paciente |
| `GET` | `/v1/records/{id}` | Consultar registro específico |
| `PUT` | `/v1/records/{id}` | Actualizar registro (solo DOCTOR propietario) |
| `POST` | `/v1/records/{id}/attachments` | Adjuntar archivo (PDF/imagen) |
| `GET` | `/v1/records/{id}/attachments/{fileId}` | URL pre-firmada S3 (TTL 15 min) |
| `POST` | `/v1/records/patient/{patientId}/consent` | Registrar consentimiento de compartición |
| `POST` | `/v1/records/patient/{patientId}/anonymize` | Solicitar anonimización (LGPD Art. 18) |

**Dependencias**:
- `auth-service` (validación JWT): extrae roles del token para RBAC.
- `audit-service` (SQS): todo acceso a registros clínicos genera evento de auditoría.
- AWS S3: almacenamiento de archivos adjuntos.
- AWS KMS: gestión de llaves de encriptación en reposo.

### 3.8 `ai-assistant-service` — Asistente de IA con Arquitectura RAG

- **Repositorio Git**: `git@github.com:santopegasus/ai-assistant-service.git`
- **Squad Owner**: Squad IA
- **Tech Lead**: Fernanda Rocha
- **Puerto**: 8087

**Responsabilidad**: provee capacidades de inteligencia artificial a la plataforma Agendio. La funcionalidad principal es un asistente de triaje inteligente que ayuda al paciente a identificar la especialidad médica más adecuada para sus síntomas, basado en una arquitectura RAG (Retrieval-Augmented Generation). El servicio usa LangChain4j para la orquestación del flujo de IA, Pinecone como vector database para el almacén de conocimiento médico indexado, y un LLM externo (OpenAI GPT-4o) como modelo generativo. Ninguna credencial de la API de IA está hardcodeada en el código; todas las keys se inyectan vía AWS Secrets Manager en tiempo de ejecución.

**Tecnologías**:
- Framework: Spring Boot 3.x + LangChain4j
- LLM: OpenAI GPT-4o (vía API externa)
- Vector Store: Pinecone (embeddings de conocimiento médico)
- Embeddings: OpenAI text-embedding-3-large
- Caché de Respuestas: Redis (TTL 1h para consultas frecuentes/idénticas)
- Rate Limiting Interno: límite de 50 consultas/paciente/día para control de costos

**APIs Expuestas**:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/v1/ai/triage` | Triaje de síntomas, sugiere especialidad |
| `POST` | `/v1/ai/chat` | Chat asistido con historial de contexto |
| `GET` | `/v1/ai/chat/{sessionId}/history` | Historial de conversación de la sesión |
| `POST` | `/v1/ai/knowledge/index` | Indexar nuevo documento médico (solo Admin) |
| `DELETE` | `/v1/ai/chat/{sessionId}` | Finalizar y eliminar sesión (LGPD) |

**Flujo RAG Interno**:
1. El paciente envía una pregunta sobre síntomas.
2. `ai-assistant-service` genera el embedding de la pregunta.
3. Consulta Pinecone para recuperar los top-K chunks de documentos médicos relevantes.
4. Construye un prompt enriquecido (pregunta + contexto recuperado).
5. Envía el prompt al LLM (GPT-4o).
6. Retorna la respuesta junto con referencias a las fuentes usadas.
7. Registra la interacción (anonimizada) para mejora futura del modelo.

**Dependencias**:
- `user-service` (REST): verificar perfil del paciente antes del triaje.
- `audit-service` (SQS): eventos de uso de IA para compliance.
- OpenAI API (externo): LLM y embeddings.
- Pinecone API (externo): vector database.
- Redis: caché de respuestas y sesiones de chat.

### 3.9 `audit-service` — Registro de Auditoría y Compliance

- **Repositorio Git**: `git@github.com:santopegasus/audit-service.git`
- **Squad Owner**: Squad Governance
- **Tech Lead**: Marco Antônio Lima
- **Puerto**: 8088

**Responsabilidad**: el `audit-service` es el sistema de registro histórico inmutable de todas las acciones sensibles del ecosistema de Santo Pegasus. Es consumidor puro — no expone APIs de escritura a otros servicios; recibe todos sus datos exclusivamente vía mensajería SQS. Provee APIs de consulta para auditores internos y para generación de reportes de compliance. Los registros de auditoría jamás se modifican ni se eliminan; únicamente se archivan en AWS S3 Glacier tras 90 días para retención de largo plazo.

**Tecnologías**:
- Framework: Spring Boot 3.x
- Base de Datos: PostgreSQL 15 (`audit_db`) vía AWS RDS — append-only inmutable
- Archivado: AWS S3 Glacier para retención de largo plazo (compliance regulatorio)
- Mensajería: AWS SQS Consumer exclusivo (múltiples colas)
- Búsqueda: índices PostgreSQL optimizados para queries por Trace ID, user_id, timestamp

**APIs Expuestas (solo lectura — roles restringidos)**:

| Método | Endpoint | Rol Requerido |
|---|---|---|
| `GET` | `/v1/audit/events` | `ROLE_AUDITOR`, `ROLE_ADMIN` |
| `GET` | `/v1/audit/events/{traceId}` | `ROLE_AUDITOR` |
| `GET` | `/v1/audit/events/user/{userId}` | `ROLE_AUDITOR` |
| `GET` | `/v1/audit/report/monthly` | `ROLE_ADMIN` |
| `GET` | `/v1/audit/events/service/{serviceName}` | `ROLE_AUDITOR` |

**Modelo de Datos (`audit_db`)**:
```
audit_events → id (UUID), trace_id, span_id, service_name, action,
                actor_id, actor_role, resource_type, resource_id,
                payload_summary (sin datos sensibles), timestamp, ip_address
```

---

## 4. Mapa de Dependencias entre Servicios

### 4.1 Tabla de Dependencias

| Servicio Consumidor | Servicio Proveedor | Tipo | Protocolo | Criticidad |
|---|---|---|---|---|
| `api-gateway` | `auth-service` | Síncrono | REST / Redis Cache | Alta |
| `agendio-scheduling-service` | `user-service` | Síncrono | REST (WebClient) | Alta |
| `agendio-scheduling-service` | `payment-service` | Síncrono | REST (WebClient) | Alta |
| `payment-service` | `audit-service` | Asíncrono | SQS | Media |
| `agendio-scheduling-service` | `agendio-notification-service` | Asíncrono | SQS | Media |
| `agendio-scheduling-service` | `audit-service` | Asíncrono | SQS | Media |
| `user-service` | `agendio-notification-service` | Asíncrono | SQS | Baja |
| `user-service` | `audit-service` | Asíncrono | SQS | Media |
| `auth-service` | `user-service` | Síncrono | REST (WebClient) | Alta |
| `auth-service` | `audit-service` | Asíncrono | SQS | Media |
| `medical-records-service` | `audit-service` | Asíncrono | SQS | Alta |
| `ai-assistant-service` | `user-service` | Síncrono | REST | Baja |
| `ai-assistant-service` | `audit-service` | Asíncrono | SQS | Media |

### 4.2 Resumen del Grafo de Dependencias

- El **API Gateway** valida tokens de forma síncrona contra `auth-service`.
- `auth-service` depende de `user-service` (síncrono) para verificar estado del usuario, y publica eventos asíncronos hacia `audit-service`.
- `user-service` es consumido de forma síncrona por `auth-service` y `agendio-scheduling-service`, y publica eventos asíncronos hacia `agendio-notification-service` y `audit-service`.
- `agendio-scheduling-service` depende síncronamente de `user-service` y `payment-service`, y publica eventos asíncronos hacia `agendio-notification-service` y `audit-service`.
- `payment-service` publica eventos asíncronos hacia `audit-service`.
- `medical-records-service` y `ai-assistant-service` publican eventos asíncronos hacia `audit-service`; `ai-assistant-service` además consulta `user-service` de forma síncrona.
- **`audit-service` es el punto de convergencia**: recibe eventos asíncronos de prácticamente todos los demás servicios y no expone dependencias salientes.

---

## 5. Patrones de Comunicación

### 5.1 REST Síncrono con WebClient

Para comunicaciones síncronas entre servicios, Santo Pegasus adopta el uso de Spring WebClient (no bloqueante, reactivo), disponible en el módulo `spring-webflux`. La elección de WebClient sobre el ya deprecado RestTemplate se justifica por su mejor uso de threads y soporte nativo a operaciones non-blocking.

**Reglas obligatorias para comunicación REST síncrona**:
- Todos los clientes HTTP entre servicios utilizan mTLS para autenticación mutua.
- Timeout de conexión: 3 segundos (configurable por variable de entorno).
- Timeout de lectura: 10 segundos.
- Circuit Breaker vía Resilience4j en todas las llamadas a servicios externos.
- Retry con backoff exponencial (máximo 3 intentos, jitter de 500 ms).
- Las respuestas de error deben seguir RFC 7807 (Problem Details).

```java
// Ejemplo canónico de WebClient con Resilience4j
@Service
public class UserServiceClient {
    private final WebClient webClient;
    private final CircuitBreaker circuitBreaker;

    public Mono<UserProfileDTO> getUserProfile(UUID userId) {
        return circuitBreaker.executeSupplier(() ->
            webClient.get()
                .uri("/v1/users/{id}", userId)
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError, this::handleClientError)
                .bodyToMono(UserProfileDTO.class)
                .timeout(Duration.ofSeconds(10))
        );
    }
}
```

### 5.2 gRPC para Alta Performance

Para comunicaciones de alta frecuencia y baja latencia entre servicios internos que no requieren pasar por el API Gateway — como el `agendio-scheduling-service` consultando disponibilidad en tiempo real — Santo Pegasus adopta gRPC como protocolo de comunicación.

**Servicios que implementan gRPC actualmente**:
- `agendio-scheduling-service` → `user-service` (endpoint de validación rápida de médico)
- `auth-service` → `user-service` (endpoint de verificación de estado en login)

**Ventajas de la adopción**:
- Protocol Buffers (protobuf) garantizan payload menor y serialización más rápida que JSON.
- HTTP/2 multiplexing reduce la latencia en llamadas concurrentes.
- Contrato fuertemente tipado vía archivos `.proto` versionados en repositorio compartido.

```protobuf
// user-service.proto (ejemplo)
syntax = "proto3";

service UserService {
    rpc ValidateUser (ValidateUserRequest) returns (ValidateUserResponse);
}

message ValidateUserRequest {
    string user_id = 1;
}

message ValidateUserResponse {
    bool is_active = 1;
    string role = 2;
    string full_name = 3;
}
```

### 5.3 Mensajería Asíncrona con AWS SQS

Para comunicación entre dominios (cross-domain events) se adoptan AWS SQS FIFO Queues para garantizar ordenación y entrega exactly-once. La mensajería asíncrona es el patrón preferido para eventos que no requieren respuesta inmediata, desacoplando a los productores de los consumidores.

**Patrones obligatorios para SQS**:
- Colas FIFO para garantizar ordenación y deduplicación (`MessageDeduplicationId` obligatorio).
- Dead Letter Queues (DLQ) configuradas con `maxReceiveCount = 3` para todas las colas principales.
- Idempotencia del lado del consumidor: toda operación debe ser segura para reprocesamiento.
- Envelope de evento estandarizado:

```json
{
  "eventId": "uuid-v4",
  "eventType": "appointment.created",
  "source": "agendio-scheduling-service",
  "traceId": "propagado-desde-el-header-http",
  "timestamp": "2026-06-16T10:30:00Z",
  "schemaVersion": "1.0",
  "payload": {
    "appointmentId": "uuid",
    "patientId": "uuid",
    "doctorId": "uuid",
    "scheduledAt": "2026-06-20T14:00:00Z"
  }
}
```

---

## 6. Estrategia de Bases de Datos

### 6.1 Database per Service Pattern

Cada microservicio posee y controla exclusivamente su propia base de datos. El acceso directo a la base de datos de otro servicio está terminantemente prohibido. La integración entre datos de distintos dominios ocurre exclusivamente vía APIs o mensajería.

### 6.2 Mapa de Bases de Datos por Servicio

| Servicio | Motor | Instancia AWS | Base de Datos | Justificación |
|---|---|---|---|---|
| `auth-service` | PostgreSQL 15 | RDS Multi-AZ | `auth_db` | Consistencia fuerte para credenciales |
| `user-service` | PostgreSQL 15 | RDS Multi-AZ | `users_db` | Datos relacionales de perfil |
| `agendio-scheduling-service` | PostgreSQL 15 | RDS Multi-AZ | `scheduling_db` | ACID para agendamientos críticos |
| `payment-service` | PostgreSQL 15 | RDS Multi-AZ | `payments_db` | ACID para transacciones financieras |
| `medical-records-service` | MongoDB 6 | AWS DocumentDB | `medical_records_db` | Esquema flexible para registros clínicos |
| `ai-assistant-service` | Pinecone | Pinecone Cloud | `knowledge_vectors` | Vector store para RAG |
| `audit-service` | PostgreSQL 15 | RDS Multi-AZ | `audit_db` | Append-only, alta integridad |
| Caché Global | Redis 7 | ElastiCache | Múltiples namespaces | Caching cross-service basado en TTL |

### 6.3 Redis — Estrategia de Caché

| Namespace | Contenido | TTL | Propietario |
|---|---|---|---|
| `auth:token:{jti}` | Blacklist de tokens revocados | Hasta expiración del JWT | `auth-service` |
| `auth:jwks` | Llaves públicas JWKS (caché en API GW) | 5 minutos | `auth-service` |
| `user:profile:{userId}` | Perfil del usuario serializado | 10 minutos | `user-service` |
| `schedule:availability:{doctorId}:{date}` | Slots disponibles del médico | 2 minutos | `scheduling-service` |
| `ai:response:{queryHash}` | Respuestas de IA cacheadas | 1 hora | `ai-assistant-service` |

### 6.4 Migrations con Flyway

Todas las bases de datos PostgreSQL utilizan Flyway para versionado de schema. Las reglas son:

- Scripts nombrados como `V{version}__{descripcion}.sql` (ej: `V2__add_appointment_notes_column.sql`).
- Los scripts de migración son inmutables luego de mergearse a `main`.
- Las migrations se ejecutan automáticamente en el startup del servicio (integradas al pipeline CI/CD).
- Los scripts DDL manuales en producción están terminantemente prohibidos.

---

## 7. API Gateway

### 7.1 Responsabilidades

El API Gateway es el único punto de entrada para todos los clientes externos. Su posición en la arquitectura le otorga responsabilidades críticas de seguridad, observabilidad y gestión de tráfico:

| Responsabilidad | Detalles |
|---|---|
| Routing | Redirige cada ruta hacia el microservicio correspondiente según el path prefix (`/auth/`, `/users/`, `/appointments/`) |
| Autenticación Centralizada | Valida el token JWT en cada request (vía caché en Redis del `auth-service`) antes de enrutar |
| Rate Limiting | 100 req/min por tenant (ajustable por plan); 10 req/min para endpoints sensibles |
| Terminación SSL/TLS | Toda comunicación externa usa TLS 1.3; internamente se usa mTLS |
| CORS | Configuración centralizada de orígenes permitidos por ambiente |
| Request Logging | Todo request se registra con Trace ID para observabilidad |
| Circuit Breaking | Si un servicio interno no responde, el Gateway retorna 503 inmediatamente |
| Transformaciones | Adición de headers internos (`X-User-Id`, `X-User-Role`, `X-Tenant-Id`) para propagación de contexto |

### 7.2 Tecnología

- Kong Gateway desplegado en AWS ECS Fargate.
- Plugins utilizados: `jwt`, `rate-limiting`, `request-id`, `prometheus`, `cors`, `acl`.
- Configurado vía Kong Admin API con Declarative Config (`deck`) versionado en Git.

### 7.3 Mapeo de Rutas

```
/v1/auth/         → auth-service:8081
/v1/users/         → user-service:8082
/v1/doctors/       → user-service:8082
/v1/appointments/  → agendio-scheduling-service:8083
/v1/schedules/     → agendio-scheduling-service:8083
/v1/payments/      → payment-service:8085
/v1/records/       → medical-records-service:8086
/v1/ai/            → ai-assistant-service:8087
/v1/audit/         → audit-service:8088 (solo roles AUDITOR/ADMIN)
```

---

## 8. Infraestructura en AWS

### 8.1 Mapa de Servicios AWS Utilizados

| Servicio AWS | Uso | Servicio(s) Consumidor(es) |
|---|---|---|
| ECS Fargate | Orquestación de contenedores Docker (sin EC2 gestionado) | Todos los microservicios |
| RDS PostgreSQL Multi-AZ | Bases de datos relacionales con failover automático | auth, user, scheduling, payment, audit |
| AWS DocumentDB | Compatible con MongoDB, para documentos clínicos flexibles | `medical-records-service` |
| ElastiCache (Redis) | Caché distribuido y blacklist de tokens | auth, user, scheduling, ai-assistant |
| SQS FIFO | Mensajería asíncrona entre dominios | Todos (productor/consumidor) |
| SES | Envío de emails transaccionales | `agendio-notification-service` |
| SNS | Envío de SMS | `agendio-notification-service` |
| S3 | Archivos de exámenes, PDFs, backups de audit | medical-records, audit |
| S3 Glacier | Archivado de logs de auditoría (90+ días) | `audit-service` |
| Secrets Manager | Gestión de credenciales, llaves de API, certificados | Todos los microservicios |
| KMS | Encriptación de datos sensibles en reposo | `medical-records-service` |
| CloudWatch | Logs, métricas nativas AWS, alarmas básicas | Todos |
| ECR | Registro privado de imágenes Docker | Pipeline CI/CD |
| Route 53 | DNS y health checks | API Gateway |
| Certificate Manager (ACM) | Certificados TLS | API Gateway, Load Balancer |
| VPC + Private Subnets | Aislamiento de red — microservicios nunca expuestos públicamente | Todos |

### 8.2 Topología de Red (AWS VPC 10.0.0.0/16)

- **Subredes públicas**: ALB / API Gateway, NAT Gateway.
- **Subredes privadas (App)**: ECS Fargate Tasks (microservicios), ElastiCache Redis.
- **Subredes privadas (Data)**: RDS PostgreSQL Multi-AZ, cluster de DocumentDB.

### 8.3 Estrategia de Deploy — ECS Fargate

- Cada microservicio es un ECS Service dedicado, con auto-scaling basado en CPU (target: 60%).
- Task Definitions versionadas; rollback en menos de 2 minutos vía ECS rolling deployment.
- Imágenes Docker almacenadas en AWS ECR con scanning de vulnerabilidades automático.
- Blue-Green deployment vía AWS CodeDeploy para servicios críticos (`auth-service`, `agendio-scheduling-service`, `payment-service`).
- Health checks configurados en cada ECS Task apuntando a `/actuator/health`.

---

## 9. Observabilidad Distribuida

### 9.1 Los Tres Pilares

La observabilidad en Santo Pegasus se basa en los tres pilares fundamentales descritos en la Guía de Ingeniería Back-end: logs, métricas y rastreo distribuido.

### 9.2 Propagación del Trace ID

El `Trace ID` es el hilo conductor que permite rastrear el ciclo de vida completo de una solicitud a través de todos los microservicios involucrados.

**Flujo de propagación**:
1. El cliente envía la solicitud al API Gateway, que genera un Trace ID si no existe (`X-B3-TraceId: abc123`, `X-B3-SpanId: span01`).
2. `auth-service` propaga los headers y genera su propio Span (`X-B3-SpanId: span02`).
3. `agendio-scheduling-service` propaga y genera su propio Span (`X-B3-SpanId: span03`).
4. El Trace ID se incluye en el envelope del evento cuando se publica en SQS.
5. `agendio-notification-service` y `audit-service` propagan el Trace ID vía el envelope del mensaje SQS.

**Implementación técnica**:
- Spring Cloud Sleuth (integrado con Micrometer Tracing) para propagación automática.
- OpenTelemetry Collector desplegado como sidecar en cada ECS Task.
- Datos de tracing exportados a Datadog APM vía OTLP.

### 9.3 Logging Estructurado

Conforme a la Guía de Ingeniería Back-end (v2.4.0):

- SLF4J + Logback como stack de logging en todos los servicios.
- Logs en formato JSON estructurado con campos estandarizados: `traceId`, `spanId`, `service`, `level`, `message`, `timestamp`, `userId` (cuando esté disponible).
- Nivel predeterminado en producción: INFO; nivel DEBUG solo vía feature flag temporal.
- Prohibido registrar información sensible (PII): contraseñas, CPF, datos de pago.
- Logs ingeridos en Datadog Log Management vía CloudWatch Logs subscription filter.
- En el proyecto Agendio, el ID de la consulta puede registrarse para rastreo, pero los datos personales de los pacientes deben omitirse.

### 9.4 Métricas con Spring Boot Actuator + Micrometer

- Cada servicio expone `/actuator/metrics`, `/actuator/health`, `/actuator/prometheus`.
- Prometheus recolecta métricas vía scraping (ECS Service Discovery).
- Datadog recibe métricas vía integración nativa Prometheus → Datadog Agent.

**Métricas clave monitoreadas por servicio**:

| Métrica | Descripción | Alerta configurada |
|---|---|---|
| `http.server.requests.duration` | Latencia P95 por endpoint | > 2s → Warning; > 5s → Critical |
| `http.server.requests.error.rate` | Tasa de errores 5xx | > 1% → Warning; > 5% → Critical |
| `jvm.memory.used` | Uso de memoria JVM | > 85% → Warning |
| `db.pool.connections.active` | Conexiones activas al pool de DB | > 80% del pool → Warning |
| `sqs.messages.received` | Throughput de mensajes SQS | Anomalía detectada → Alert |
| `circuit.breaker.state` | Estado del Circuit Breaker | OPEN → Critical inmediato |

### 9.5 Dashboards en Datadog

| Dashboard | Squad | Contenido |
|---|---|---|
| Platform Overview | Todos | Visión general de la salud de todos los servicios |
| Auth & Security | Squad Hermes | Tasas de login, errores de token, anomalías de seguridad |
| Scheduling Core | Squad Agendio Core | Agendamientos/hora, tasa de cancelación, latencia |
| Payments | Squad Pagamentos | Volumen transaccional, tasa de error de gateway, chargebacks |
| Clinical Records | Squad Clínico | Accesos a registros, errores RBAC, uploads S3 |
| AI Assistant | Squad IA | Latencia de inferencia, costo estimado de tokens LLM |
| Governance | Squad Governance | Eventos de auditoría, anomalías de compliance |

---

## 10. Estrategia de Versionado de APIs

### 10.1 Política de Versionado

Todas las APIs de Santo Pegasus siguen versionado explícito vía path prefix (`/v1/`, `/v2/`). El versionado vía headers (`Accept: application/vnd.santopegasus.v2+json`) fue evaluado y descartado por dificultar la observabilidad y el ruteo en el API Gateway.

**Reglas**:
- Se crean nuevas versiones de API únicamente cuando hay breaking changes.
- Adiciones retrocompatibles (nuevos campos opcionales, nuevos endpoints) no requieren nueva versión.
- Una versión obsoleta (deprecated) permanece activa por un mínimo de 6 meses tras la publicación de la nueva versión.

### 10.2 Proceso de Deprecación

1. **Fase 1 — Anuncio (Día 0)**: se publica el changelog en el repositorio y en el canal `#engineering-announcements`; se agregan los headers `Deprecation: true` y `Sunset: <fecha>` en todas las respuestas; se actualiza la documentación Swagger con un banner de deprecation.
2. **Fase 2 — Período de Soporte (mes 1 al 6)**: ambas versiones permanecen activas y soportadas; se monitorean métricas de adopción en Datadog; se comunica activamente a los clientes que aún están en la versión antigua.
3. **Fase 3 — Sunset (mes 6+)**: la versión antigua retorna `HTTP 410 Gone` con link para migración; el código se elimina tras 30 días en estado 410.

### 10.3 Versiones Actuales por Servicio

| Servicio | Versión Activa | Versión Deprecated | Sunset |
|---|---|---|---|
| `auth-service` | v1 | — | — |
| `user-service` | v1 | — | — |
| `agendio-scheduling-service` | v2 | v1 | Dic/2026 |
| `payment-service` | v1 | — | — |
| `medical-records-service` | v1 | — | — |
| `ai-assistant-service` | v1 (beta) | — | — |
| `audit-service` | v1 | — | — |

---

## 11. Seguridad entre Servicios

### 11.1 Autenticación y Autorización

Conforme a lo documentado en la Guía de Ingeniería Back-end (v2.4.0), el control de acceso se gestiona de forma centralizada utilizando Spring Security. Todos los endpoints están protegidos; ningún endpoint interno es accesible sin validación de identidad. Los tokens JWT con flujo OAuth 2.0 / OpenID Connect son el mecanismo estándar. La extracción y validación de permisos (roles) ocurre a nivel de endpoint.

### 11.2 mTLS para Comunicación Interna

Toda comunicación servicio-a-servicio dentro de la VPC privada usa mTLS (Mutual TLS). Esto garantiza que ambos lados de una conexión se autentiquen mutuamente, previniendo ataques de spoofing y man-in-the-middle en comunicaciones internas.

**Implementación**:
- Certificados gestionados por AWS Certificate Manager (ACM) Private CA.
- Certificados rotados automáticamente cada 90 días.
- Cada microservicio posee un certificado de cliente único para autenticación mutua.
- Service Mesh (AWS App Mesh) como capa de control de mTLS (en rollout progresivo — ver Roadmap).

### 11.3 Service Accounts y Principio de Privilegio Mínimo

Cada microservicio opera con un IAM Role exclusivo en AWS, siguiendo estrictamente el principio de privilegio mínimo:

| Servicio | IAM Role | Permisos Concedidos |
|---|---|---|
| `auth-service` | `iam-role-auth-service` | Secrets Manager (`auth/`), ElastiCache, SQS (publish audit-events) |
| `agendio-scheduling-service` | `iam-role-scheduling-service` | RDS (`scheduling_db`), SQS (publish/consume scheduling queues) |
| `medical-records-service` | `iam-role-medical-records` | DocumentDB, S3 (`medical-files/`), KMS, SQS (publish audit-events) |
| `payment-service` | `iam-role-payment-service` | RDS (`payments_db`), Secrets Manager (`payment/`), SQS |
| `ai-assistant-service` | `iam-role-ai-assistant` | Secrets Manager (`ai/`), ElastiCache, SQS |
| `audit-service` | `iam-role-audit-service` | RDS (`audit_db`), SQS (consume all audit queues), S3 Glacier |

Las credenciales de servicios externos (Stripe, OpenAI, Pinecone) se almacenan exclusivamente en AWS Secrets Manager y se inyectan en tiempo de ejecución vía Spring Cloud Config. Jamás se escriben en el código o en repositorios Git. Herramientas de escaneo automático (`gitleaks`, `trufflehog`) se ejecutan en los pipelines de CI/CD para detectar y bloquear commits que contengan secrets.

### 11.4

*Nota: el documento fuente se corta en este punto. La Sección 11.4 no tiene contenido disponible, y las Secciones 12 a 15 (Mapa de Squads y Ownership, Roadmap Técnico, Architecture Decision Records, y Disposiciones Finales) listadas en la tabla de contenidos no están presentes en el material de origen.*
