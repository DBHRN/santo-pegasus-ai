# Protocolo de Respuesta a Incidentes y Post-Mortems

**Santo Pegasus Soluciones — Site Reliability Engineering (SRE)**

**Versión del Documento:** 1.0.0
**Última Actualización:** Junio de 2026
**Departamento:** Ingeniería de Software / Chapter de SRE
**Clasificación:** Documento Interno — Uso Restringido al Equipo de Ingeniería y Dirección
**Propietario:** Chapter Lead de SRE — Santo Pegasus Soluciones

> "La confiabilidad no es una característica opcional. Es el fundamento sobre el cual todos los demás atributos de un sistema son evaluados."
> — Principio SRE, Santo Pegasus Soluciones

## Tabla de Contenidos

1. Introducción y Filosofía SRE en Santo Pegasus
2. Definiciones Fundamentales: Incidente, Problema y Cambio Planificado
3. Clasificación de Severidad de Incidentes
4. Roles y Responsabilidades Durante un Incidente
5. Proceso de Detección y Alerta
6. Proceso Paso a Paso de Respuesta al Incidente
7. Procedimiento de Rollback en Docker y AWS ECS
8. Comunicación Durante el Incidente
9. Criterios de Resolución y Cierre del Incidente
10. Plantilla Oficial de Post-Mortem
11. Proceso de Revisión y Archivo del Post-Mortem
12. Métricas de Confiabilidad: SLI, SLO y SLA
13. Error Budget: Definición, Cálculo y Política de Agotamiento
14. Simulacros de Incidentes — GameDay
15. Disposiciones Finales, Vigencia y Revisión del Protocolo

## 1. Introducción y Filosofía SRE en Santo Pegasus

### 1.1 Propósito del Documento

Este documento establece el Protocolo Oficial de Respuesta a Incidentes y Post-Mortems de Santo Pegasus Soluciones. Su objetivo es garantizar que cualquier degradación o interrupción de los servicios en producción sea detectada, gestionada, mitigada y documentada de forma estructurada, eficiente y reproducible.

La alineación con este protocolo es obligatoria para todos los ingenieros de back-end, DevOps, SRE, líderes técnicos y gestores de producto que operen o supervisen sistemas en ambientes productivos. El cumplimiento de estas directrices asegura que Santo Pegasus mantenga los compromisos de disponibilidad acordados con sus clientes y preserve la integridad operativa de todos sus productos, incluido el sistema Agendio (plataforma de agendamiento de consultas médicas) y demás microservicios críticos.

### 1.2 La Filosofía SRE en Santo Pegasus Soluciones

Site Reliability Engineering (SRE) es la disciplina que combina principios de ingeniería de software con operaciones de infraestructura para construir sistemas escalables, confiables y gestionables. En Santo Pegasus, esta disciplina no es responsabilidad exclusiva de un equipo aislado: es una responsabilidad compartida entre todos los desarrolladores, arquitectos, gestores de producto y ejecutivos que participan en el ciclo de vida del software.

Los principios que guían nuestra práctica SRE son:

#### 1.2.1 Confiabilidad como Responsabilidad Compartida

Todo ingeniero que escribe código es también responsable por su comportamiento en producción. En Santo Pegasus, quien desarrolla una funcionalidad también participa de su operación, monitoreo y respuesta ante fallos. No existe una separación rígida entre "quienes construyen" y "quienes operan": todos son corresponsables por la salud de los sistemas.

Esto implica que:

- Los equipos de desarrollo participan activamente en las rotaciones de on-call.
- Las métricas de confiabilidad (SLIs y SLOs) son métricas de producto, no solo métricas de infraestructura.
- Las decisiones de velocidad de entrega (cadencia de deploys, volumen de features) están directamente influenciadas por el saldo del Error Budget.

#### 1.2.2 Blameless Culture (Cultura Sin Culpa)

Uno de los pilares más críticos de nuestra filosofía SRE es la cultura blameless (sin culpa). En Santo Pegasus, cuando un incidente ocurre, el foco del análisis es siempre el sistema, nunca el individuo. Los incidentes son síntomas de fragilidades sistémicas, no de incompetencias personales.

Esta cultura garantiza que:

- Los ingenieros reporten incidentes con honestidad y detalle, sin temor a represalias.
- Los Post-Mortems sean documentos técnicos de aprendizaje, no instrumentos disciplinarios.
- Las causas raíz sean identificadas en procesos, herramientas y arquitecturas, promoviendo mejoras reales y duraderas.
- El conocimiento generado por cada incidente sea compartido ampliamente con todo el equipo de ingeniería.

#### 1.2.3 Automatización como Mecanismo de Confiabilidad

En Santo Pegasus, el trabajo manual repetitivo es un riesgo operacional. Toda tarea que pueda automatizarse debe ser automatizada. Nuestros pipelines CI/CD, estrategias de deploy Blue-Green y Canary Releases, y procesos de rollback automatizado existen precisamente para reducir la dependencia de intervenciones humanas en situaciones de alta presión.

#### 1.2.4 Confiabilidad y Velocidad en Equilibrio

La confiabilidad no debe ser un freno a la innovación, sino un marco que permite innovar de forma segura y sostenida. El concepto de Error Budget (detallado en la Sección 13) es el mecanismo que Santo Pegasus utiliza para equilibrar la velocidad de entrega de nuevas funcionalidades con la necesidad de mantener la estabilidad de los sistemas existentes.

## 2. Definiciones Fundamentales

Para garantizar un lenguaje común entre todos los equipos, este protocolo adopta las siguientes definiciones operativas:

### 2.1 Incidente

Un incidente es cualquier evento no planificado que cause o amenace con causar degradación o interrupción de uno o más servicios en producción, con impacto real o potencial sobre los usuarios finales o sobre los SLOs establecidos.

Ejemplos:

- El servicio Agendio presenta error 503 para el 60% de las requisiciones de agendamiento.
- La latencia P99 del endpoint `/consultas/agendar` supera 2000ms por más de 5 minutos.
- Una migración de base de datos en AWS RDS provoca bloqueo de tablas críticas.
- El pipeline de notificaciones por e-mail vía AWS SES deja de procesar mensajes de la cola SQS.

### 2.2 Problema

Un problema es la causa raíz subyacente de uno o más incidentes. Un mismo problema puede manifestarse como múltiples incidentes recurrentes hasta que su causa sea identificada y eliminada.

**Distinción clave:** El incidente es el síntoma observable; el problema es la causa sistémica. La gestión de incidentes trata el síntoma para restaurar el servicio. La gestión de problemas investiga y elimina la causa para evitar recurrencia.

Ejemplo:

- **Incidentes:** El servicio de notificaciones falló tres veces en un mes.
- **Problema:** Un mecanismo de retry sin backoff exponencial provoca tormentas de mensajes en SQS, saturando el consumidor.

### 2.3 Cambio Planificado

Un cambio planificado es cualquier alteración deliberada en los sistemas de producción ejecutada de forma coordinada, comunicada con anticipación y dentro de una ventana de mantenimiento autorizada. Los cambios planificados no se clasifican como incidentes aunque causen indisponibilidad temporal y programada.

Requisitos para un cambio planificado válido:

- Aprobación del Incident Commander de turno y del líder técnico del servicio afectado.
- Comunicación previa de al menos 48 horas para clientes y stakeholders internos.
- Plan de rollback documentado y validado.
- Ventana de mantenimiento definida y acordada.

## 3. Clasificación de Severidad de Incidentes

### 3.1 Tabla de Severidades

| Nivel | Nombre | Descripción del Impacto | Ejemplos Concretos | SLA de Respuesta | SLA de Actualización |
|---|---|---|---|---|---|
| SEV-1 | Crítico | Sistema completamente caído. Impacto total en producción. Todos los clientes afectados. Revenue en riesgo inmediato. | Agendio inaccesible, API Gateway caída, base de datos de producción inalcanzable, fallo total de autenticación. | 15 minutos | Cada 30 minutos |
| SEV-2 | Alto | Degradación severa. Funcionalidad crítica no disponible para parte significativa de los clientes. | Agendamiento de consultas falla para 40% de los usuarios, notificaciones por e-mail (SES) completamente detenidas, latencia P99 > 5 segundos sostenida. | 30 minutos | Cada 1 hora |
| SEV-3 | Medio | Degradación leve. Funcionalidad no crítica afectada. Existe workaround disponible para los usuarios. | Reportes de histórico con lentitud, búsqueda de disponibilidad retornando resultados desactualizados, dashboard administrativo con visualización parcial. | 4 horas | Cada 4 horas |
| SEV-4 | Bajo | Anomalía detectada en métricas o logs. Sin impacto visible al usuario final. Requiere investigación preventiva. | Aumento inusual en tasa de errores 4xx sin impacto funcional, métrica de CPU por encima del umbral de alerta pero dentro del límite operativo, log de warning recurrente no relacionado a flujo crítico. | Próximo día hábil | Al cierre |

### 3.2 Criterios de Escalada de Severidad

La severidad de un incidente puede y debe ser revisada durante su ciclo de vida. Los criterios para **escalar** (aumentar la severidad) son:

- El impacto se expande a un mayor número de usuarios o servicios.
- El workaround disponible deja de funcionar.
- El tiempo de resolución supera el doble del SLA de respuesta de la severidad actual.
- Hay evidencia de impacto económico o contractual.

Los criterios para **desescalar** (reducir la severidad) son:

- La mitigación aplicada reduce significativamente el impacto.
- Un workaround efectivo queda disponible para todos los usuarios afectados.
- Las métricas de SLO retornan a niveles normales.

### 3.3 Autoridad para Declarar y Modificar la Severidad

El Incident Commander (IC) es la única figura con autoridad para declarar formalmente un incidente y definir o modificar su nivel de severidad. En ausencia del IC principal, el Technical Lead de turno asume esta responsabilidad hasta que el IC sea asignado.

## 4. Roles y Responsabilidades Durante un Incidente

### 4.1 Descripción de Roles

#### 4.1.1 Incident Commander (IC)

El Incident Commander es la autoridad máxima durante un incidente activo. Su función no es resolver técnicamente el problema, sino coordinar al equipo, garantizar el flujo de información y tomar decisiones de alto nivel.

Responsabilidades:

- Declarar formalmente el incidente y su severidad.
- Asignar los demás roles (Communications Lead, Technical Lead, SMEs).
- Abrir el canal de War Room en Slack y convocar a los participantes necesarios.
- Mantener el timeline del incidente actualizado en tiempo real.
- Tomar la decisión final sobre rollback, mitigación o continuación del diagnóstico.
- Comunicar el cierre del incidente y garantizar la apertura del proceso de Post-Mortem.
- Asegurar que nadie en la War Room actúe sin coordinación.

**Perfil:** Senior Engineer o Tech Lead con experiencia en el ecosistema productivo de Santo Pegasus. Debe haber completado al menos un ciclo de shadow (observación) del rol antes de asumir de forma independiente.

#### 4.1.2 Communications Lead

El Communications Lead es el responsable de toda la comunicación externa e interna durante el incidente, liberando al IC para enfocarse en la coordinación técnica.

Responsabilidades:

- Publicar actualizaciones de estado en el canal `#incidents` de Slack según los SLAs de actualización.
- Redactar y enviar comunicados externos a clientes afectados (vía e-mail o status page).
- Comunicar el estado del incidente a la dirección y stakeholders ejecutivos.
- Gestionar la status page pública (cuando aplique).
- Documentar en el canal de War Room todas las acciones tomadas y sus timestamps.
- Coordinar con el equipo de Soporte al Cliente cuando sea necesario.

**Perfil:** Puede ser un engineer senior, un product manager técnico o un líder de equipo. Debe tener habilidades claras de comunicación escrita y comprensión suficiente del impacto técnico para traducirlo a lenguaje ejecutivo y orientado al cliente.

#### 4.1.3 Technical Lead

El Technical Lead lidera la investigación técnica del incidente. Es quien dirige activamente el diagnóstico, propone hipótesis, coordina a los SMEs y ejecuta o autoriza las acciones de mitigación y rollback.

Responsabilidades:

- Liderar el diagnóstico técnico del incidente en la War Room.
- Formular y priorizar hipótesis de causa raíz.
- Coordinar a los SMEs en sus áreas de especialidad.
- Proponer y ejecutar acciones de mitigación al IC para aprobación.
- Autorizar y supervisar la ejecución de procedimientos de rollback.
- Verificar que el sistema retorna a estado estable tras la mitigación.
- Documentar las hipótesis descartadas y confirmadas para el Post-Mortem.

**Perfil:** Engineer senior o pleno con dominio técnico del servicio afectado. Idealmente el responsable técnico del microservicio en cuestión.

#### 4.1.4 Subject Matter Expert (SME)

Los SMEs son especialistas convocados según la naturaleza técnica del incidente. Pueden ser incorporados al equipo de respuesta en cualquier momento del ciclo de vida del incidente.

Responsabilidades:

- Responder a consultas técnicas específicas dentro de su dominio de conocimiento.
- Ejecutar tareas técnicas delegadas por el Technical Lead.
- Proporcionar contexto sobre sistemas, integraciones o configuraciones específicas.
- Participar activamente en el análisis de causa raíz durante el Post-Mortem.

Ejemplos de SMEs en Santo Pegasus:

- Especialista en AWS RDS y PostgreSQL (incidentes de base de datos).
- Especialista en AWS ECS y Docker (incidentes de infraestructura y deploy).
- Especialista en AWS SQS/SES (incidentes de mensajería y notificaciones).
- Especialista en Spring Security y JWT (incidentes de autenticación y autorización).

### 4.2 Matriz de Responsabilidades (RACI)

| Actividad | Incident Commander | Communications Lead | Technical Lead | SME |
|---|---|---|---|---|
| Declarar el incidente | R/A | I | C | I |
| Definir la severidad | R/A | I | C | C |
| Abrir War Room | R/A | R | I | I |
| Comunicación externa | A | R | I | — |
| Comunicación a dirección | A | R | I | — |
| Diagnóstico técnico | I | — | R/A | R |
| Ejecutar rollback | A | I | R | C |
| Actualizar timeline | A | R | C | — |
| Declarar resolución | R/A | I | C | I |
| Iniciar Post-Mortem | R/A | I | R | I |

*R = Responsable / A = Aprobador / C = Consultado / I = Informado*

## 5. Proceso de Detección y Alerta

### 5.1 Fuentes de Detección

Santo Pegasus opera un sistema de observabilidad en capas, conforme a los tres pilares definidos en la Guía Oficial de Ingeniería Back-end: logs, métricas y rastreo. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 10]*

#### 5.1.1 Métricas — Prometheus y Datadog

Las métricas de rendimiento y salud son expuestas mediante Spring Boot Actuator y Micrometer, con exportación nativa hacia Prometheus. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 10]* Datadog actúa como plataforma centralizada de visualización, correlación y alerting.

Tipos de alertas configuradas:

| Métrica | Umbral de Alerta (Warning) | Umbral de Alerta (Critical) | Severidad Sugerida |
|---|---|---|---|
| Disponibilidad del servicio | < 99.95% en 5 min | < 99.5% en 5 min | SEV-2 / SEV-1 |
| Latencia P99 del endpoint | > 300ms en 10 min | > 500ms en 5 min | SEV-3 / SEV-2 |
| Tasa de error HTTP 5xx | > 0.05% en 5 min | > 0.1% en 5 min | SEV-3 / SEV-2 |
| CPU de instancia ECS | > 75% por 10 min | > 90% por 5 min | SEV-3 / SEV-1 |
| Profundidad de cola SQS | > 1.000 mensajes | > 5.000 mensajes | SEV-3 / SEV-2 |
| Conexiones disponibles RDS | < 20% del pool | < 5% del pool | SEV-2 / SEV-1 |
| Health check del contenedor | Falla 1 vez | Falla 3 veces consecutivas | SEV-3 / SEV-1 |

Los endpoints de health check deben reflejar el estado real de las dependencias críticas (bases de datos, brokers de mensajes), permitiendo que el orquestador de contenedores tome decisiones precisas sobre el ciclo de vida de las instancias. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 11]*

#### 5.1.2 Logs — SLF4J y Logback

El sistema de logging estandarizado en SLF4J (Simple Logging Facade for Java) con Logback como framework de implementación nativo de Spring Boot *[Fuente: Guía Oficial de Ingeniería Back-end, p. 9]* genera alertas automáticas cuando:

- El volumen de logs en nivel ERROR supera el umbral configurado en Datadog.
- Patrones de error específicos (como `NullPointerException` en flujos críticos, o errores de conexión con RDS) son detectados por reglas de parsing.
- Stacktraces de excepciones de negocio personalizadas (`ResourceNotFoundException`, `BusinessRuleException`) aparecen en frecuencia anómala.

**Nota:** El uso de `System.out.println()` está estrictamente prohibido en todos los servicios de Santo Pegasus. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 9]* Toda la instrumentación de logs debe pasar por SLF4J.

#### 5.1.3 Rastreo Distribuido (Distributed Tracing)

En la arquitectura de microservicios, es obligatorio implementar soluciones de rastreo para propagar el Trace ID y el Span ID entre las peticiones. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 10]* Estas trazas permiten identificar cuellos de botella entre servicios y correlacionar eventos de múltiples microservicios durante un incidente.

#### 5.1.4 Reporte Manual por Usuarios o Soporte

Un incidente también puede ser detectado a través de:

- Reporte directo de usuarios finales al equipo de Soporte al Cliente.
- Alerta interna comunicada por un desarrollador que observa comportamiento anómalo.
- Alerta de un cliente corporativo vía canal dedicado de comunicación.

Todo reporte manual debe ser inmediatamente evaluado por el IC de turno para determinar si justifica la declaración formal de un incidente.

### 5.2 Canales de Comunicación de Incidentes

| Canal | Propósito | Audiencia |
|---|---|---|
| `#incidents` | Canal general de monitoreo y declaración de todos los incidentes | Todos los ingenieros, PMs, dirección técnica |
| `#sev1-war-room` | War Room exclusiva para SEV-1. Canal dedicado, creado en el momento del incidente | IC, Communications Lead, Technical Lead, SMEs convocados |
| `#sev2-war-room` | War Room para SEV-2 | IC, Communications Lead, Technical Lead, SMEs |
| `#incidents-resolved` | Registro histórico de incidentes resueltos y links a Post-Mortems | Todos los ingenieros |
| PagerDuty | Alertas automáticas de on-call, escalada y asignación de roles | Engineer on-call, IC de turno |

### 5.3 Política de On-Call y PagerDuty

- Todos los ingenieros Senior y Semi-Senior (Pleno) participan obligatoriamente en la rotación de on-call.
- La rotación ocurre semanalmente, con un Primary On-Call y un Secondary On-Call (backup).
- Las alertas SEV-1 y SEV-2 activan notificación inmediata vía PagerDuty para el Primary On-Call.
- Si el Primary no reconoce la alerta en 5 minutos, el Secondary es notificado automáticamente.
- Si el Secondary no responde en 5 minutos adicionales, el IC de plantón y el Tech Lead de la semana son notificados.
- El ingeniero on-call tiene hasta 15 minutos para declarar formalmente el incidente o descartarlo con justificación documentada en `#incidents`.

## 6. Proceso Paso a Paso de Respuesta al Incidente

### 6.1 Diagrama del Flujo de Respuesta

```
[DETECCIÓN] → [DECLARACIÓN] → [WAR ROOM] → [DIAGNÓSTICO]
                                                   ↓
[COMUNICACIÓN AL STAKEHOLDER] ← [RESOLUCIÓN] ← [MITIGACIÓN]
        ↓
  [CIERRE FORMAL]
        ↓
  [POST-MORTEM]
```

### 6.2 Fase 1 — Detección (T+0)

**Responsable:** Engineer On-Call / Sistema automatizado

Checklist:

- [ ] Alerta recibida vía PagerDuty o Datadog.
- [ ] Engineer on-call reconoce la alerta en PagerDuty (botón "Acknowledge").
- [ ] Verificar en Datadog/Prometheus si la alerta es legítima o falso positivo.
- [ ] Consultar logs en Datadog (filtro por nivel ERROR o WARN en el servicio afectado).
- [ ] Verificar Trace ID en la solución de rastreo distribuido para identificar el microservicio de origen.
- [ ] Consultar el health check del servicio en AWS ECS.
- [ ] Si confirmado: proceder a Fase 2. Si falso positivo: documentar en `#incidents` y cerrar alerta.

### 6.3 Fase 2 — Declaración del Incidente (T+0 a T+5 minutos)

**Responsable:** Engineer On-Call → Incident Commander

Checklist:

- [ ] Engineer on-call publica mensaje inicial en `#incidents` (ver template en Sección 8.1).
- [ ] IC de turno recibe notificación vía PagerDuty y asume el comando.
- [ ] IC declara formalmente el incidente con severidad inicial (puede ser revisada).
- [ ] IC crea el canal de War Room correspondiente en Slack (`#sev1-war-room` o `#sev2-war-room`).
- [ ] IC asigna formalmente los roles: Communications Lead, Technical Lead, SMEs necesarios.
- [ ] IC abre el documento de timeline del incidente (Google Doc o Confluence) y comparte el link en el canal de War Room.
- [ ] IC publica la declaración formal en el canal de War Room (ver template en Sección 8.2).

### 6.4 Fase 3 — War Room y Diagnóstico (T+5 a T+variable)

**Responsable:** Technical Lead + SMEs

Checklist de Diagnóstico:

- [ ] Technical Lead formula hipótesis iniciales basadas en la alerta y los síntomas observados.
- [ ] Revisar el historial de deploys recientes: ¿hubo un deploy en las últimas 2 horas?
- [ ] Revisar el historial de cambios de configuración en AWS ECS, RDS o variables de entorno.
- [ ] Analizar métricas de Prometheus: latencia, tasa de error, CPU, memoria, conexiones RDS.
- [ ] Analizar logs estructurados en Datadog: filtrar por nivel ERROR, buscar stacktraces relevantes.
- [ ] Utilizar el Trace ID para rastrear el flujo completo de una requisición fallida entre microservicios.
- [ ] Revisar el estado de la cola SQS: mensajes en DLQ (Dead Letter Queue), profundidad de cola.
- [ ] Verificar el estado del servicio AWS RDS: conexiones activas, queries de larga duración, locks.
- [ ] Consultar el Health Check de los contenedores en AWS ECS.
- [ ] Cada hipótesis descartada debe ser documentada en el timeline con timestamp.
- [ ] Technical Lead reporta el estado del diagnóstico al IC a cada actualización significativa.

### 6.5 Fase 4 — Mitigación (T+variable)

**Responsable:** Technical Lead (con aprobación del IC)

La mitigación es la acción que restaura el servicio al usuario, aunque no necesariamente elimine la causa raíz. El objetivo de la mitigación es reducir el impacto en el menor tiempo posible.

Acciones de mitigación comunes:

| Causa Identificada | Acción de Mitigación | Ejecutor |
|---|---|---|
| Deploy defectuoso | Rollback inmediato (ver Sección 7) | Technical Lead + SME DevOps |
| Agotamiento del pool de conexiones RDS | Reiniciar instancias ECS, aumentar pool temporalmente | SME RDS |
| Cola SQS con mensajes venenosos | Mover mensajes problemáticos a DLQ, reiniciar consumidor | SME Backend |
| Tormenta de retries | Activar Circuit Breaker, aumentar visibilidad de mensajes en SQS | Technical Lead |
| Instancia ECS defectuosa | Forzar nuevo deployment para reemplazar la tarea | SME DevOps |
| Leak de memoria en el contenedor | Reiniciar el servicio, escalar horizontalmente para ganar tiempo | SME DevOps |

**Regla de oro de la mitigación:**

> Primero estabilizar. Después entender. La presión para encontrar la causa raíz no debe retardar la restauración del servicio.

- [ ] Technical Lead propone la acción de mitigación al IC.
- [ ] IC aprueba la acción.
- [ ] SME o Technical Lead ejecuta la acción.
- [ ] Monitorear las métricas en Datadog/Prometheus durante los 5 minutos siguientes a la mitigación.
- [ ] Confirmar que el impacto se redujo o eliminó.
- [ ] Communications Lead publica actualización en `#incidents` y para clientes (si aplica).

### 6.6 Fase 5 — Resolución (T+variable)

**Responsable:** Technical Lead → IC

La resolución ocurre cuando:

1. El servicio retorna a operación normal, dentro de los SLOs establecidos.
2. El impacto sobre los usuarios ha cesado completamente.
3. Las métricas de SLI se estabilizan dentro de los umbrales normales por al menos 10 minutos consecutivos.

- [ ] Technical Lead informa al IC que las condiciones de resolución han sido cumplidas.
- [ ] IC valida las métricas en Datadog y Prometheus.
- [ ] IC declara formalmente la resolución del incidente.
- [ ] Communications Lead publica comunicado de resolución (ver template Sección 8.4).

### 6.7 Fase 6 — Comunicación al Stakeholder y Cierre Formal

**Responsable:** IC + Communications Lead

- [ ] Communications Lead envía comunicado final a todos los públicos afectados.
- [ ] IC registra el cierre formal del incidente en el sistema de tracking (Jira, PagerDuty).
- [ ] IC anuncia en `#incidents` el cierre del incidente y el link del timeline completo.
- [ ] IC designa el responsable del Post-Mortem (normalmente el Technical Lead del incidente).
- [ ] IC define el plazo para la entrega del borrador del Post-Mortem (máximo 72 horas para SEV-1 y SEV-2; 5 días hábiles para SEV-3 y SEV-4).

## 7. Procedimiento de Rollback en Docker y AWS ECS

### 7.1 Filosofía del Rollback

El rollback es la acción de reversión de un deploy defectuoso hacia la última versión estable conocida del servicio. En Santo Pegasus, el uso de Docker es obligatorio para asegurar la inmutabilidad del artefacto, garantizando que el mismo código validado en Staging (homologación) sea promovido a Producción sin variaciones. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 12]*

Esta inmutabilidad hace del rollback una operación rápida y segura: revertir significa simplemente redirigir el orquestador para servir la imagen Docker de la versión anterior, que ya fue validada en Staging.

### 7.2 Estrategias de Deploy y su Impacto en el Rollback

Santo Pegasus utiliza orquestadores que soportan Blue-Green o Canary Releases, permitiendo reversiones rápidas en caso de anomalías. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 12]*

#### 7.2.1 Rollback en Blue-Green Deployment

En Blue-Green, dos ambientes idénticos (Blue = versión estable, Green = nueva versión) son mantenidos en paralelo. El rollback consiste en redirigir el tráfico del Load Balancer del ambiente Green de vuelta al ambiente Blue.

```bash
# ROLLBACK BLUE-GREEN — AWS ECS + Application Load Balancer

# Paso 1: Identificar el ARN del Target Group azul (versión estable)
aws elbv2 describe-target-groups \
  --names "santo-pegasus-blue-tg" \
  --query "TargetGroups[0].TargetGroupArn" \
  --output text

# Paso 2: Redirigir el listener del Load Balancer al Target Group azul
aws elbv2 modify-listener \
  --listener-arn <ARN_DEL_LISTENER> \
  --default-actions Type=forward,TargetGroupArn=<ARN_DEL_TARGET_GROUP_BLUE>

# Paso 3: Verificar que el tráfico está siendo dirigido al Target Group correcto
aws elbv2 describe-listeners \
  --listener-arns <ARN_DEL_LISTENER> \
  --query "Listeners[0].DefaultActions"

# Paso 4: Monitorear las métricas de health check del Target Group azul
aws elbv2 describe-target-health \
  --target-group-arn <ARN_DEL_TARGET_GROUP_BLUE>
```

#### 7.2.2 Rollback en Canary Release

En Canary, la nueva versión recibe un porcentaje pequeño del tráfico (ej. 10%). El rollback consiste en redirigir el 100% del tráfico de vuelta a la versión estable.

```bash
# ROLLBACK CANARY — Redirigir 100% del tráfico a la versión estable

# Paso 1: Modificar las reglas del listener para 100% en versión estable
aws elbv2 modify-rule \
  --rule-arn <ARN_DE_LA_REGLA_CANARY> \
  --actions '[
    {
      "Type": "forward",
      "ForwardConfig": {
        "TargetGroups": [
          {"TargetGroupArn": "<ARN_STABLE_TG>", "Weight": 100},
          {"TargetGroupArn": "<ARN_CANARY_TG>", "Weight": 0}
        ]
      }
    }
  ]'

# Paso 2: Confirmar la distribución de tráfico
aws elbv2 describe-rules \
  --rule-arns <ARN_DE_LA_REGLA_CANARY>
```

#### 7.2.3 Rollback Directo en AWS ECS (Force New Deployment)

Cuando es necesario revertir la imagen Docker de un servicio ECS directamente:

```bash
# ROLLBACK DIRECTO DE IMAGEN EN AWS ECS

# Paso 1: Listar las revisiones recientes de la Task Definition del servicio
aws ecs list-task-definitions \
  --family-prefix "santo-pegasus-agendio" \
  --sort DESC \
  --max-items 5

# Paso 2: Identificar la última revisión ESTABLE (ej: revisión N-1)
# Supongamos que la revisión actual defectuosa es :42 y la estable es :41

# Paso 3: Actualizar el servicio ECS para usar la revisión estable
aws ecs update-service \
  --cluster "santo-pegasus-production" \
  --service "agendio-service" \
  --task-definition "santo-pegasus-agendio:41" \
  --force-new-deployment

# Paso 4: Monitorear el estado del deployment
aws ecs describe-services \
  --cluster "santo-pegasus-production" \
  --services "agendio-service" \
  --query "services[0].deployments"

# Paso 5: Verificar que las nuevas tareas están en estado RUNNING
aws ecs list-tasks \
  --cluster "santo-pegasus-production" \
  --service-name "agendio-service" \
  --desired-status RUNNING

# Paso 6: Verificar health checks de los contenedores
aws ecs describe-tasks \
  --cluster "santo-pegasus-production" \
  --tasks <TASK_ARN_1> <TASK_ARN_2>
```

### 7.3 Checklist Completo de Rollback

- [ ] IC autoriza formalmente el inicio del procedimiento de rollback.
- [ ] SME DevOps o Technical Lead identifica la versión estable anterior (imagen Docker o Task Definition revision).
- [ ] Verificar que la versión estable no contiene la causa del incidente actual (consultar el changelog del deploy).
- [ ] Verificar si hay migraciones de base de datos pendientes que puedan ser afectadas por el rollback.
  - [ ] Si sí: evaluar rollback de la migración con Flyway o Liquibase antes de revertir la aplicación.
  - [ ] Si no: proceder directamente con el rollback de la imagen.
- [ ] Ejecutar el procedimiento de rollback (Blue-Green, Canary o Force New Deployment según el contexto).
- [ ] Monitorear métricas en Datadog durante los 10 minutos siguientes.
- [ ] Confirmar que el servicio está healthy y las métricas de SLI están dentro de los umbrales normales.
- [ ] Documentar el rollback en el timeline del incidente con timestamp, versión revertida y versión de destino.
- [ ] Communications Lead publica actualización informando la acción tomada.

### 7.4 Rollback de Migraciones de Base de Datos

La evolución del esquema de bases de datos relacionales en Santo Pegasus debe ser estrictamente controlada, versionada y automatizada. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 11]* Las herramientas Flyway o Liquibase se utilizan obligatoriamente.

```bash
# ROLLBACK DE MIGRACIÓN — FLYWAY

# Paso 1: Verificar el historial de migraciones
flyway -url=jdbc:postgresql://<RDS_HOST>:5432/<DB_NAME> \
  -user=<DB_USER> \
  -password=<DB_PASSWORD> \
  info

# Paso 2: Ejecutar el script de undo (si disponible — requiere Flyway Teams)
flyway -url=jdbc:postgresql://<RDS_HOST>:5432/<DB_NAME> \
  -user=<DB_USER> \
  -password=<DB_PASSWORD> \
  undo

# IMPORTANTE: Toda migración debe ser idempotente y probada
# exhaustivamente en ambientes de homologación antes del deploy en producción.
# [Fuente: Guía Oficial de Ingeniería Back-end, p. 11]
```

> ⚠️ **Advertencia crítica:** La alteración manual de estructuras de datos, como la creación de tablas o modificación de columnas, así como la ejecución de scripts DDL directamente en entornos de producción por medio de clientes SQL, está terminantemente prohibida en Santo Pegasus. *[Fuente: Guía Oficial de Ingeniería Back-end, p. 11]*

## 8. Comunicación Durante el Incidente

### 8.1 Template — Alerta Inicial en `#incidents`

```
🚨 [INCIDENTE DECLARADO] — SEV-{NIVEL}

Hora de Detección: {HH:MM} (UTC-3)
Servicio Afectado: {NOMBRE DEL SERVICIO / MICROSERVICIO}
Impacto: {DESCRIPCIÓN BREVE DEL IMPACTO OBSERVABLE}
Usuarios Afectados: {ESTIMATIVA — Ej: ~40% de los usuarios del Agendio}
Métricas: {DESCRIPCIÓN BREVE — Ej: Latencia P99 = 2.300ms, Error rate = 3.2%}

Incident Commander: @{NOMBRE_IC}
Technical Lead: @{NOMBRE_TL}
Communications Lead: @{NOMBRE_CL}
War Room: #{CANAL_WAR_ROOM}
Timeline: {LINK AL DOCUMENTO DE TIMELINE}

Status: INVESTIGANDO
```

### 8.2 Template — Declaración Formal en el Canal de War Room

```
📋 DECLARACIÓN FORMAL DE INCIDENTE

ID del Incidente: INC-{AÑO}-{NÚMERO SECUENCIAL}
Severidad: SEV-{NIVEL}
Hora de Declaración: {HH:MM} (UTC-3)

DESCRIPCIÓN DEL SÍNTOMA:
{Descripción técnica detallada del comportamiento observado}

SERVICIOS AFECTADOS:
- {Servicio 1}
- {Servicio 2}

HIPÓTESIS INICIAL:
{Primera hipótesis técnica basada en los síntomas}

ACCIONES EN CURSO:
- {Acción 1} — Responsable: @{NOMBRE}
- {Acción 2} — Responsable: @{NOMBRE}

PRÓXIMA ACTUALIZACIÓN: {HH:MM} (UTC-3)
```

### 8.3 Template — Actualización de Estado (a publicar en `#incidents`)

```
🔄 [ACTUALIZACIÓN SEV-{NIVEL}] INC-{AÑO}-{NÚMERO} — {HH:MM}

Tiempo de Incidente: {DURACIÓN DESDE LA DECLARACIÓN}
Estado Actual: {INVESTIGANDO / MITIGANDO / MONITOREANDO}

PROGRESO:
✅ {Acción completada 1}
✅ {Acción completada 2}
🔄 {Acción en curso}

PRÓXIMOS PASOS:
→ {Próxima acción}

Próxima actualización en {X} minutos.
```

### 8.4 Template — Comunicado de Resolución

```
✅ [INCIDENTE RESUELTO] INC-{AÑO}-{NÚMERO} — {HH:MM}

Duración Total: {DURACIÓN}
Servicio: {NOMBRE DEL SERVICIO}

RESUMEN:
{Descripción breve del incidente y de la acción que lo resolvió}

ACCIÓN TOMADA:
{Descripción de la mitigación aplicada — Ej: Rollback a la versión 2.3.1 del servicio Agendio}

ESTADO ACTUAL:
✅ Servicio operando normalmente
✅ Métricas dentro de los parámetros normales
✅ Sin impacto residual para los usuarios

PRÓXIMOS PASOS:
- Post-Mortem será publicado en hasta {PLAZO}
- Link del timeline completo: {LINK}

Agradecemos la paciencia y colaboración de todos.
```

### 8.5 Template — Comunicado Externo a Clientes Afectados

```
Asunto: [Actualización de Status] Intermitencia en {NOMBRE DEL SERVICIO} — Santo Pegasus

Estimado cliente,

Informamos que identificamos una intermitencia que afectó {DESCRIPCIÓN DEL SERVICIO
AFECTADO} entre las {HORA DE INICIO} y las {HORA DE RESOLUCIÓN} (horario de Brasília).

IMPACTO IDENTIFICADO:
{Descripción clara y no técnica del impacto sobre el usuario}

ACCIONES TOMADAS:
Nuestro equipo de ingeniería identificó la causa del problema y aplicó las
correcciones necesarias. El servicio fue restaurado a las {HORA DE RESOLUCIÓN}
y opera normalmente desde entonces.

PRÓXIMOS PASOS:
Realizaremos un análisis detallado de lo ocurrido (Post-Mortem) e
implementaremos mejoras para prevenir la recurrencia de este tipo de evento.

Pedimos disculpas por los inconvenientes causados. Nuestro equipo permanece
comprometido con la calidad y disponibilidad de los servicios.

Para dudas adicionales, contáctenos en: sre@santopegasus.com.br

Atentamente,
Equipo de Ingeniería — Santo Pegasus Soluciones
```

### 8.6 Template — Comunicado a la Dirección (Mensaje Ejecutivo)

```
📊 RESUMEN EJECUTIVO DE INCIDENTE — SEV-{NIVEL}

Para: Dirección / C-Level
De: Chapter Lead SRE / Incident Commander
Fecha: {FECHA}

RESUMEN EN UNA LÍNEA:
{Una frase describiendo el incidente y su resolución}

DATOS CLAVE:
- Inicio: {HORA DE INICIO}
- Resolución: {HORA DE RESOLUCIÓN}
- Duración Total: {DURACIÓN}
- Clientes/Usuarios Afectados: {NÚMERO O PORCENTAJE ESTIMADO}
- SLO Impactado: {SLO AFECTADO — Ej: Disponibilidad del Agendio}

IMPACTO ESTIMADO:
- {Descripción del impacto de negocio si es conocido}

ACCIÓN TOMADA:
{Descripción ejecutiva de la solución aplicada}

PRÓXIMOS PASOS:
- Post-Mortem con análisis de causa raíz: {FECHA DE ENTREGA}
- Reunión de revisión del Post-Mortem: {FECHA PROPUESTA}
```

## 9. Criterios de Resolución y Cierre del Incidente

### 9.1 Criterios Técnicos de Resolución

Un incidente es considerado resuelto cuando todas las condiciones a continuación son satisfechas simultáneamente:

| Criterio | Condición de Satisfacción |
|---|---|
| Disponibilidad del servicio | ≥ 99.9% en los últimos 10 minutos consecutivos |
| Latencia P99 | < 500ms sostenida por al menos 10 minutos |
| Tasa de error HTTP 5xx | < 0.1% por al menos 10 minutos |
| Health checks de ECS | Todos los contenedores en estado HEALTHY |
| Profundidad de cola SQS | Retornando a los niveles basales normales |
| Confirmación del Technical Lead | Technical Lead declara formalmente el servicio estable |
| Ausencia de nuevas alertas | Ninguna nueva alerta crítica en los últimos 10 minutos |

### 9.2 Procedimiento de Cierre

- [ ] Technical Lead confirma al IC que todos los criterios técnicos fueron satisfechos.
- [ ] IC valida independientemente las métricas en Datadog y Prometheus.
- [ ] IC declara el cierre formal en el canal de War Room y en `#incidents`.
- [ ] Communications Lead envía comunicados de resolución (clientes, `#incidents`, dirección si aplica).
- [ ] IC registra el cierre en el sistema de tracking (Jira/PagerDuty) con timestamps completos.
- [ ] IC abre formalmente el ticket de Post-Mortem y asigna el responsable.
- [ ] El canal de War Room es archivado (no eliminado) para preservar el historial.

### 9.3 Periodo de Observación Post-Resolución

Para SEV-1 y SEV-2, se recomienda un periodo de observación activa de 1 hora después de la declaración de resolución. Durante este periodo:

- El engineer on-call mantiene monitoreo activo de las métricas.
- Se está preparado para re-escalar el incidente si ocurre una regresión.
- Si la regresión ocurre, se reabre el incidente existente (no se crea uno nuevo) y se reinicia el proceso desde la Fase 3.

## 10. Plantilla Oficial de Post-Mortem

### 10.1 Principios del Post-Mortem en Santo Pegasus

El Post-Mortem es el documento más importante que resulta de un incidente. Es la fuente de aprendizaje organizacional. Debe ser:

- **Blameless:** Ningún individuo es culpado. El foco es el sistema.
- **Honesto:** Todos los errores y malas decisiones tomadas durante el incidente son documentados.
- **Accionable:** Cada causa raíz identificada debe resultar en una o más acciones correctivas concretas.
- **Compartido:** Accesible a todo el equipo de ingeniería de Santo Pegasus.

### 10.2 Plantilla de Post-Mortem — Santo Pegasus Soluciones

```
POST-MORTEM OFICIAL
Santo Pegasus Soluciones — Chapter de SRE

ID del Incidente: INC-{AÑO}-{NÚMERO}
Severidad: SEV-{NIVEL}
Fecha del Incidente: {DD/MM/AAAA}
Fecha del PM: {DD/MM/AAAA}
Autor: {NOMBRE DEL AUTOR}
Revisores: {NOMBRES DE LOS REVISORES}
Status del PM: [BORRADOR / EN REVISIÓN / APROBADO]


SECCIÓN 1 — RESUMEN EJECUTIVO

{Párrafo de 3 a 5 líneas describiendo el incidente, su duración,
el impacto principal y la acción que lo resolvió.
Debe ser comprensible por un lector no técnico.}

Ejemplo:
"El día {FECHA}, el servicio Agendio presentó indisponibilidad
total del endpoint de agendamiento de consultas por un período de
{DURACIÓN}. El incidente fue causado por {CAUSA RAÍZ BREVE} y
afectó aproximadamente {N} usuarios. El servicio fue restaurado
mediante {ACCIÓN DE RESOLUCIÓN}."


SECCIÓN 2 — TIMELINE DEL INCIDENTE

| Timestamp (UTC-3) | Evento | Responsable |
|---|---|---|
| HH:MM | Datadog detecta aumento en error rate > 0.1% | Sistema |
| HH:MM | PagerDuty notifica Engineer On-Call | Sistema |
| HH:MM | Engineer On-Call reconoce la alerta | {NOMBRE} |
| HH:MM | Incidente declarado — SEV-{N} | {IC} |
| HH:MM | War Room abierta en #{CANAL} | {IC} |
| HH:MM | Technical Lead asume el diagnóstico | {TL} |
| HH:MM | Hipótesis 1 formulada: {DESCRIPCIÓN} | {TL} |
| HH:MM | Hipótesis 1 descartada: {RAZÓN} | {TL/SME} |
| HH:MM | Hipótesis 2 formulada: {DESCRIPCIÓN} | {TL} |
| HH:MM | Causa raíz identificada: {DESCRIPCIÓN} | {TL/SME} |
| HH:MM | Rollback/Mitigación autorizado por IC | {IC} |
| HH:MM | Acción de mitigación ejecutada | {TL/SME} |
| HH:MM | Métricas retornan a niveles normales | Sistema |
| HH:MM | Incidente declarado RESUELTO | {IC} |
| HH:MM | Comunicado de resolución enviado a clientes | {CL} |

Duración Total: {DURACIÓN} (desde la declaración hasta la resolución)
Duración del Impacto: {DURACIÓN} (desde el inicio real del problema)


SECCIÓN 3 — IMPACTO

3.1 Usuarios Afectados
- Número estimado de usuarios impactados: {NÚMERO}
- Porcentaje de la base de usuarios: {PORCENTAJE}%
- Tipo de impacto: {Indisponibilidad total / Degradación / Error intermitente}
- Servicios afectados: {LISTA DE SERVICIOS}

3.2 Tiempo de Indisponibilidad
- Inicio del impacto real (detectado en logs/métricas): {TIMESTAMP}
- Fin del impacto: {TIMESTAMP}
- Duración total del impacto: {DURACIÓN}
- Impacto sobre el SLO de disponibilidad: {CONSUMO DE ERROR BUDGET}

3.3 Estimativa de Impacto de Negocio
- Agendamientos no realizados (si aplica): {NÚMERO ESTIMADO}
- Impacto financiero estimado: {VALOR o "En análisis"}
- Clientes corporativos afectados: {LISTA o "No aplica"}
- Tickets de soporte recibidos: {NÚMERO}


SECCIÓN 4 — ANÁLISIS DE CAUSA RAÍZ — 5 WHYS

La metodología "5 Whys" es aplicada para identificar la causa
raíz sistémica, más allá del síntoma superficial.

SÍNTOMA OBSERVADO:
{Descripción del síntoma que desencadenó el incidente}

¿Por qué 1?
→ {Primera causa. Ej: "El servicio Agendio presentó error 503
   para 100% de las requisiciones."}

¿Por qué 2?
→ {Segunda causa. Ej: "Porque el pool de conexiones con el
   RDS PostgreSQL fue agotado."}

¿Por qué 3?
→ {Tercera causa. Ej: "Porque un deploy de la versión 2.4.0
   introdujo una query N+1 en el endpoint de agendamiento."}

¿Por qué 4?
→ {Cuarta causa. Ej: "Porque la query N+1 no fue detectada en
   Code Review ni en las pruebas de integración en Staging."}

¿Por qué 5?
→ {Quinta causa (raíz sistémica). Ej: "Porque no existe un
   proceso de pruebas de carga automatizado en el pipeline de
   CI/CD que simule el volumen de producción."}

CAUSA RAÍZ IDENTIFICADA:
{Declaración formal de la causa raíz sistémica}


SECCIÓN 5 — LO QUE FUNCIONÓ BIEN

{Lista de elementos del proceso, herramientas o decisiones que
funcionaron según lo esperado durante el incidente.}
- {Ej: Las alertas de Datadog detectaron el problema antes que
  los usuarios reportaran.}
- {Ej: El proceso de rollback fue ejecutado sin errores en
  menos de 8 minutos.}
- {Ej: La comunicación entre IC, TL y SMEs fue fluida y clara.}


SECCIÓN 6 — LO QUE PUEDE MEJORAR

{Lista de gaps, fricciones o puntos de mejora identificados
durante el incidente.}
- {Ej: La alerta de agotamiento del pool de conexiones RDS
  tardó 8 minutos en dispararse, extendiendo el impacto.}
- {Ej: El runbook de rollback no contemplaba el escenario de
  migración de base de datos activa.}
- {Ej: Ausencia de pruebas de carga en el pipeline de CI/CD.}


SECCIÓN 7 — ACCIONES CORRECTIVAS

| ID | Acción | Tipo | Responsable | Fecha Límite | Status |
|---|---|---|---|---|---|
| AC1 | {Descripción de la acción correctiva 1} | Prevención | {NOMBRE} | {FECHA} | Pendiente |
| AC2 | {Descripción de la acción correctiva 2} | Detección | {NOMBRE} | {FECHA} | Pendiente |
| AC3 | {Descripción de la acción correctiva 3} | Mitigación | {NOMBRE} | {FECHA} | Pendiente |
| AC4 | {Descripción de la acción correctiva 4} | Proceso | {NOMBRE} | {FECHA} | Pendiente |

Tipos de Acción:
- Prevención: Elimina la causa raíz para que el incidente no ocurra de nuevo.
- Detección: Mejora la capacidad de detectar el problema más rápidamente.
- Mitigación: Reduce el tiempo o el impacto de futuras ocurrencias.
- Proceso: Mejora el proceso de respuesta al incidente en sí.


SECCIÓN 8 — LECCIONES APRENDIDAS

{Párrafo o lista con los aprendizajes más importantes que este
incidente deja para el equipo de ingeniería de Santo Pegasus.}


SECCIÓN 9 — REFERENCIAS Y EVIDENCIAS

- Link del canal de War Room en Slack: {URL}
- Link del dashboard de Datadog durante el incidente: {URL}
- Link del timeline completo (Google Doc/Confluence): {URL}
- Link del ticket en Jira/PagerDuty: {URL}
- Logs relevantes (extractos o links): {URL}
- Trace IDs relevantes: {IDs}
```

## 11. Proceso de Revisión y Archivo del Post-Mortem

### 11.1 Plazos para Entrega del Post-Mortem

| Severidad | Plazo para Borrador Inicial | Plazo para Revisión | Plazo para Aprobación Final |
|---|---|---|---|
| SEV-1 | 48 horas | 72 horas | 5 días hábiles |
| SEV-2 | 72 horas | 5 días hábiles | 7 días hábiles |
| SEV-3 | 5 días hábiles | 7 días hábiles | 10 días hábiles |
| SEV-4 | 7 días hábiles | 10 días hábiles | 15 días hábiles |

### 11.2 Proceso de Revisión

**Paso 1 — Borrador Inicial:**
El Technical Lead del incidente redacta el borrador inicial del Post-Mortem, incluyendo el timeline completo y el análisis de causa raíz con la metodología de 5 Whys.

**Paso 2 — Revisión Técnica:**
El borrador es compartido con todos los participantes del incidente (IC, Communications Lead, SMEs) para validación factual. Cualquier participante puede añadir contexto, corregir informaciones o enriquecer el documento.

**Paso 3 — Revisión del Chapter Lead SRE:**
El Chapter Lead de SRE revisa el documento con los siguientes criterios:

- ¿La causa raíz está correctamente identificada?
- ¿Las acciones correctivas son realmente accionables y tienen responsables y fechas definidos?
- ¿El tono del documento es blameless?
- ¿Las lecciones aprendidas agregan valor real al conocimiento del equipo?

**Paso 4 — Reunión de Revisión del Post-Mortem:**
Para SEV-1 y SEV-2, es obligatoria la realización de una reunión de revisión con duración máxima de 60 minutos, con la participación de:

- IC del incidente
- Technical Lead del incidente
- Chapter Lead de SRE
- Al menos 1 engineer de otro equipo (perspectiva externa)
- Opcionalmente: Product Manager del servicio afectado

La reunión tiene como objetivos:

1. Revisar el timeline y garantizar que todos los hechos están correctos.
2. Discutir y validar la causa raíz identificada.
3. Revisar y comprometer a los responsables con las acciones correctivas.
4. Extraer lecciones aprendidas adicionales a través del diálogo colectivo.

**Paso 5 — Aprobación y Publicación:**
El Chapter Lead de SRE aprueba formalmente el Post-Mortem. El documento es entonces publicado en el repositorio oficial de Post-Mortems de Santo Pegasus (Confluence / Google Drive / Notion — según el sistema vigente) y el link es compartido en el canal `#incidents-resolved` de Slack.

### 11.3 Política de Archivo

- Todos los Post-Mortems son archivados indefinidamente en el repositorio oficial.
- El repositorio es indexado por: ID del incidente, fecha, severidad, servicio afectado, causa raíz.
- El repositorio es de acceso read-only para toda la empresa y read-write solo para el Chapter de SRE.
- Trimestralmente, el Chapter Lead de SRE realiza una revisión del repositorio para extraer tendencias y patrones de incidentes recurrentes, alimentando el backlog de mejoras de confiabilidad.

### 11.4 Seguimiento de Acciones Correctivas

- Todas las acciones correctivas del Post-Mortem son convertidas en tickets formales en Jira y asignadas al sprint correspondiente.
- El Chapter Lead de SRE es responsable por monitorear el cumplimiento de las fechas límite.
- Acciones correctivas de SEV-1 tienen prioridad P1 en el backlog y no pueden ser postergadas sin aprobación explícita del Chapter Lead.
- En la reunión de revisión de incidentes (mensual), el status de todas las acciones correctivas en curso es revisado.

## 12. Métricas de Confiabilidad: SLI, SLO y SLA

### 12.1 Definiciones

**SLI (Service Level Indicator):** Métrica cuantitativa que mide un aspecto específico del comportamiento del servicio. Es el "termómetro" de la confiabilidad.

**SLO (Service Level Objective):** El objetivo interno de desempeño que Santo Pegasus se compromete a mantener para cada SLI. El SLO define el nivel de calidad esperado.

**SLA (Service Level Agreement):** El acuerdo formal con los clientes que define las garantías de disponibilidad y las consecuencias (compensaciones) en caso de incumplimiento. El SLA es siempre igual o menor que el SLO, para que haya margen de seguridad.

> Principio: SLO es la promesa interna. SLA es la promesa al cliente.

### 12.2 SLIs, SLOs y SLAs por Servicio

#### 12.2.1 Servicio Agendio (Agendamiento de Consultas)

| SLI | Descripción | SLO (Objetivo Interno) | SLA (Compromiso con Cliente) |
|---|---|---|---|
| Disponibilidad | % de tiempo en que el servicio está operativo | ≥ 99.95% mensual | ≥ 99.9% mensual |
| Latencia P99 | 99º percentil de latencia de respuesta | < 400ms | < 500ms |
| Latencia P50 | Mediana de latencia de respuesta | < 150ms | < 200ms |
| Tasa de Error | % de requisiciones que retornan 5xx | < 0.05% | < 0.1% |
| Tasa de Éxito de Agendamiento | % de intentos de agendamiento que finalizan con éxito | ≥ 99.9% | ≥ 99.5% |

#### 12.2.2 Servicio de Notificaciones (AWS SES + SQS)

| SLI | Descripción | SLO (Objetivo Interno) | SLA (Compromiso con Cliente) |
|---|---|---|---|
| Disponibilidad de Entrega | % de mensajes procesados exitosamente de la cola SQS | ≥ 99.9% mensual | ≥ 99.5% mensual |
| Latencia de Entrega de E-mail | Tiempo entre el evento y el envío del e-mail | < 60 segundos P99 | < 120 segundos P99 |
| Tasa de Mensaje en DLQ | % de mensajes que van a la Dead Letter Queue | < 0.1% | < 0.5% |

#### 12.2.3 API Gateway / Servicios de Autenticación

| SLI | Descripción | SLO (Objetivo Interno) | SLA (Compromiso con Cliente) |
|---|---|---|---|
| Disponibilidad | % de tiempo operativo del API Gateway | ≥ 99.99% mensual | ≥ 99.9% mensual |
| Latencia P99 de Autenticación | Latencia de validación de token JWT | < 100ms | < 200ms |
| Tasa de Error de Autenticación | % de fallos en la validación de tokens válidos | < 0.01% | < 0.1% |

### 12.3 Medición y Reporte de SLIs

- Los SLIs son medidos continuamente por Prometheus y visualizados en dashboards dedicados en Datadog.
- Los dashboards de SLO deben estar disponibles en tiempo real para todos los ingenieros.
- Los reportes mensuales de SLO son generados automáticamente y distribuidos al Chapter Lead de SRE y a los Product Managers de los servicios.
- Las violaciones de SLO son documentadas y analizadas en el proceso de revisión mensual de incidentes.

## 13. Error Budget: Definición, Cálculo y Política de Agotamiento

### 13.1 ¿Qué es el Error Budget?

El Error Budget (presupuesto de errores) es la cantidad máxima de indisponibilidad o degradación que Santo Pegasus puede "gastar" en un período determinado (normalmente mensual) sin violar el SLO establecido. Es el mecanismo que define el equilibrio entre la velocidad de entrega de nuevas funcionalidades y la necesidad de mantener la estabilidad del sistema.

El Error Budget transforma la confiabilidad en un recurso gestionable: cuando el budget está disponible, la velocidad de deploy puede ser alta. Cuando el budget se agota, la prioridad se invierte completamente hacia la estabilidad.

### 13.2 Cálculo del Error Budget

**Fórmula base:**

```
Error Budget (%) = 100% - SLO (%)
```

Para el servicio Agendio (SLO de Disponibilidad = 99.9%):

```
Error Budget Mensual (%) = 100% - 99.9% = 0.1%
Minutos en un mes (30 días) = 30 × 24 × 60 = 43.200 minutos
Error Budget Mensual (minutos) = 43.200 × 0.001 = 43,2 minutos
```

Esto significa que el servicio Agendio puede estar indisponible por un máximo de 43 minutos por mes antes de que el SLO sea violado.

**Cálculo del Error Budget consumido en un incidente:**

```
Budget Consumido = Duración del Incidente × % de Usuarios Afectados
```

Ejemplo: Un incidente de 20 minutos que afecta al 100% de los usuarios consume 20 minutos del Error Budget. Un incidente de 60 minutos que afecta al 50% de los usuarios consume 30 minutos del Error Budget.

### 13.3 Dashboard de Error Budget

El dashboard de Error Budget en Datadog debe mostrar, en tiempo real:

- Error Budget total del mes (en minutos y porcentaje).
- Error Budget consumido hasta el momento.
- Error Budget restante.
- Tasa de consumo: si el ritmo actual se mantiene, ¿cuándo se agotará el budget?
- Tendencia comparativa con el mes anterior.

### 13.4 Política de Agotamiento del Error Budget

La política de Error Budget de Santo Pegasus establece tres niveles de respuesta según el porcentaje del budget consumido:

| Budget Consumido | Estado | Acción Requerida |
|---|---|---|
| 0% – 50% | Saludable | Operación normal. Deploy de nuevas features autorizado. |
| 51% – 75% | Alerta | Engineering y Product son notificados. Revisión de estabilidad obligatoria antes de nuevos deploys de alto riesgo. |
| 76% – 99% | Crítico | Engineering Lead y Product Lead deben revisar y autorizar explícitamente cada nuevo deploy. Prioridad del equipo se orienta hacia mejoras de estabilidad. |
| 100% (Agotado) | Agotado | Pausa inmediata de deploys de nuevas funcionalidades. El equipo dirige el 100% de su capacidad a acciones de mejora de confiabilidad hasta la recuperación del budget en el próximo ciclo. |

### 13.5 Política de Pausa de Features por Agotamiento del Error Budget

Cuando el Error Budget de un servicio es completamente agotado, las siguientes medidas entran en vigor de forma automática:

1. **Freeze de deploys de features:** Ningún Pull Request de nueva funcionalidad puede ser mergeado o deployado en producción para el servicio afectado hasta el inicio del próximo ciclo mensual o hasta que se demuestre una mejora estructural en la confiabilidad del servicio.
2. **Priorización obligatoria de confiabilidad:** El 100% de la capacidad de desarrollo del equipo responsable por el servicio es redirigida a:
   - Implementación de las acciones correctivas identificadas en Post-Mortems pendientes.
   - Mejoras en la cobertura de pruebas (la cobertura mínima de 80% en pruebas unitarias es obligatoria en la etapa de Code Review *[Fuente: Guía Oficial de Ingeniería Back-end, p. 12]*).
   - Mejoras en observabilidad, alerting y runbooks de respuesta.
   - Refactoring de componentes frágiles identificados como contribuyentes a incidentes recurrentes.
3. **Revisión ejecutiva:** El Chapter Lead de SRE presenta a la dirección técnica un plan de recuperación de confiabilidad con métricas, acciones y plazos definidos.
4. **Excepción de Hotfixes:** Deploys de correcciones críticas de seguridad o de bugs que en sí mismos mejoren la confiabilidad del sistema pueden ser autorizados por el Chapter Lead de SRE de forma individual, incluso durante el freeze.

## 14. Simulacros de Incidentes — GameDay

### 14.1 ¿Qué es el GameDay?

El GameDay es un ejercicio controlado y planificado en el que el equipo de ingeniería de Santo Pegasus simula un incidente real en un ambiente controlado (preferiblemente Staging, pero con posibilidad de ambientes de producción reducidos cuando aplique) con el objetivo de:

- Validar la eficacia de los runbooks y procedimientos de respuesta.
- Identificar gaps en el proceso de detección y alertas.
- Entrenar a los ingenieros en los roles de IC, Communications Lead y Technical Lead.
- Evaluar el comportamiento del sistema ante fallos inyectados (Chaos Engineering).
- Fortalecer la cultura de preparación ante incidentes y reducir el "pánico" en situaciones reales.

### 14.2 Frecuencia y Planificación

Los GameDays en Santo Pegasus ocurren con frecuencia trimestral (4 ediciones por año), con cada edición enfocándose en un servicio o escenario diferente.

Calendario anual sugerido:

| Trimestre | Mes Sugerido | Foco del Simulacro |
|---|---|---|
| Q1 | Febrero/Marzo | Agendio — Fallo de conexión con RDS PostgreSQL |
| Q2 | Mayo/Junio | Pipeline de Notificaciones — Saturación de cola SQS |
| Q3 | Agosto/Septiembre | API Gateway / Autenticación — Fallo de servicio de tokens JWT |
| Q4 | Noviembre/Diciembre | Simulacro integral multi-servicio — Fallo en cascada |

### 14.3 Proceso de Planificación del GameDay

**Etapa 1 — Definición del Escenario (2 semanas antes):**

- El Chapter Lead de SRE y el Technical Lead del servicio en foco definen el escenario de fallo.
- El escenario es documentado de forma confidencial (solo el equipo organizador conoce los detalles).
- Se define el ambiente de ejecución (Staging o producción reducida).
- Se define el "botón de pánico" (cómo abortar el ejercicio en caso de impacto real no deseado).

**Etapa 2 — Preparación (1 semana antes):**

- Los participantes son notificados de que habrá un GameDay, pero no del escenario específico.
- Se revisa si los runbooks y documentación relevante están actualizados.
- Se configura el mecanismo de inyección de fallos (puede ser manual o vía herramientas de Chaos Engineering).

**Etapa 3 — Ejecución del Simulacro:**

- El equipo organizador inyecta el fallo según el escenario planificado.
- Los participantes responden como si fuera un incidente real, siguiendo todos los pasos de este protocolo.
- El equipo organizador observa y registra todas las acciones, decisiones y tiempos de respuesta.
- El organizador puede insertar "complicaciones" adicionales durante el ejercicio para simular escenarios más complejos.

**Etapa 4 — Debriefing (inmediatamente después):**

- Sesión de debriefing de 90 a 120 minutos con todos los participantes.
- El equipo organizador revela el escenario completo y los fallos inyectados.
- Cada participante comparte su perspectiva: ¿qué fue fácil? ¿qué fue difícil? ¿qué necesitaría para responder mejor?
- Los gaps identificados son documentados en formato similar a un Post-Mortem del GameDay.

### 14.4 Objetivos Medidos en Cada GameDay

| Métrica del GameDay | Objetivo |
|---|---|
| Tiempo hasta la detección de la alerta | < 5 minutos |
| Tiempo hasta la declaración del incidente | < 10 minutos |
| Tiempo hasta la identificación de la causa raíz | Referencia del incidente real más reciente |
| Tiempo hasta la mitigación | Referencia del incidente real más reciente |
| Calidad de la comunicación (evaluación 1-5) | ≥ 4/5 |
| Seguimiento correcto del protocolo (checklist) | ≥ 90% de los pasos |

### 14.5 Herramientas de Chaos Engineering

Para GameDays de nivel avanzado, Santo Pegasus puede adoptar herramientas de Chaos Engineering tales como:

- **AWS Fault Injection Simulator (FIS):** Para inyectar fallos directamente en servicios AWS (RDS, ECS, etc.).
- **Chaos Monkey (Netflix):** Para terminación aleatoria de instancias de contenedores.
- **Scripts customizados** de inyección de carga en SQS para simular tormentas de mensajes.

### 14.6 Documentación del GameDay

Cada GameDay genera un informe post-ejercicio con:

- Escenario planificado vs. respuesta real del equipo.
- Gaps identificados en el protocolo o en los runbooks.
- Mejoras a implementar antes del próximo GameDay.
- Evaluación de desempeño de los roles (IC, TL, CL).

El informe del GameDay es archivado junto a los Post-Mortems reales en el repositorio de confiabilidad.

## 15. Disposiciones Finales, Vigencia y Revisión del Protocolo

### 15.1 Vigencia

Este protocolo entra en vigor a partir de la fecha de su aprobación por el Chapter Lead de SRE y la Dirección de Ingeniería de Santo Pegasus Soluciones, y permanece válido hasta que una versión revisada sea oficialmente publicada y comunicada a todos los equipos.

### 15.2 Política de Revisión

Este documento debe ser revisado en las siguientes circunstancias:

| Disparador de Revisión | Plazo para Revisión |
|---|---|
| Revisión periódica obligatoria | Semestral (cada 6 meses) |
| Incidente SEV-1 que exponga gaps críticos en el protocolo | 30 días después del incidente |
| Cambio significativo en la arquitectura de producción | Dentro del ciclo de planning del cambio |
| Adopción de nuevas herramientas de observabilidad o CI/CD | En el momento de la adopción |
| Solicitud formal de cualquier equipo de ingeniería | A criterio del Chapter Lead de SRE |

### 15.3 Proceso de Actualización

1. Cualquier ingeniero de Santo Pegasus puede proponer una alteración en este protocolo abriendo un ticket en Jira con la label `sre-protocol-update`.
2. Las propuestas son revisadas mensualmente por el Chapter Lead de SRE.
3. Las alteraciones significativas deben ser revisadas por al menos 2 engineers Senior o Semi-Senior antes de ser aprobadas.
4. Toda nueva versión del protocolo debe ser comunicada a todos los equipos de ingeniería con al menos 2 semanas de antelación antes de entrar en vigor.
5. El historial de versiones del protocolo es mantenido en el repositorio oficial.

### 15.4 Responsabilidades de Cumplimiento

| Responsable | Obligación |
|---|---|
| Chapter Lead de SRE | Garantizar la aplicación, actualización y mejora continua de este protocolo |
| Tech Leads de Equipo | Garantizar que sus equipos conozcan y apliquen el protocolo |
| Engineers Senior y Pleno | Participar activamente en la rotación de on-call y cumplir todos los roles |
| Engineers Junior | Conocer el protocolo, participar como observadores en War Rooms y GameDays, y prepararse para asumir roles progresivamente |
| Dirección de Ingeniería | Apoyar la cultura blameless, garantizar recursos para las acciones correctivas y participar en las revisiones ejecutivas de incidentes críticos |

### 15.5 Contactos de Emergencia

| Rol | Canal Principal | Canal de Backup |
|---|---|---|
| IC de Turno | PagerDuty | Canal `#incidents` en Slack |
| Chapter Lead SRE | PagerDuty + WhatsApp | E-mail corporativo |
| CTO / Director de Ingeniería | WhatsApp | Llamada directa |
| AWS Support (Plan Business/Enterprise) | Console AWS Support | support.aws.amazon.com |

### 15.6 Historial de Versiones

| Versión | Fecha | Autor | Descripción de los Cambios |
|---|---|---|---|
| 1.0.0 | Junio 2026 | Chapter Lead SRE | Versión inicial del protocolo |

## Apéndices

### Apéndice A — Glosario

| Término | Definición |
|---|---|
| Blameless Culture | Cultura organizacional que enfoca el análisis de incidentes en el sistema, no en individuos. |
| Canary Release | Estrategia de deploy en que la nueva versión recibe un porcentaje pequeño del tráfico para validación. |
| Blue-Green | Estrategia de deploy con dos ambientes idénticos, permitiendo rollback instantáneo. |
| DLQ | Dead Letter Queue — Cola de mensajes fallidos en AWS SQS. |
| Error Budget | Tiempo máximo de indisponibilidad permitido por el SLO en un período determinado. |
| GameDay | Simulacro planificado de incidente para entrenamiento del equipo. |
| IC (Incident Commander) | Rol responsable de coordinar la respuesta a un incidente. |
| SLI | Service Level Indicator — Métrica que mide el comportamiento del servicio. |
| SLO | Service Level Objective — Objetivo interno de desempeño para cada SLI. |
| SLA | Service Level Agreement — Acuerdo formal de nivel de servicio con los clientes. |
| SME | Subject Matter Expert — Especialista convocado durante un incidente. |
| War Room | Canal de comunicación temporal dedicado a la respuesta de un incidente específico. |

### Apéndice B — Checklist Rápido de SEV-1 (Para Imprimir / Fijar en el Workspace)

```
┌────────────────────────────────────────────────┐
│  CHECKLIST RÁPIDO — SEV-1 SANTO PEGASUS         │
├────────────────────────────────────────────────┤
│ □ 1. Reconocer alerta en PagerDuty (< 5 min)    │
│ □ 2. Confirmar el incidente en Datadog/Prometheus│
│ □ 3. Declarar el incidente en #incidents        │
│ □ 4. IC asigna roles (TL, CL, SMEs)             │
│ □ 5. Abrir #sev1-war-room en Slack              │
│ □ 6. Abrir documento de timeline                │
│ □ 7. CL publica primera actualización en        │
│      #incidents                                 │
│ □ 8. TL inicia diagnóstico (último deploy? RDS? │
│      ECS?)                                      │
│ □ 9. IC aprueba acción de mitigación            │
│ □ 10. TL ejecuta mitigación / rollback          │
│ □ 11. Monitorear métricas por 10 minutos        │
│ □ 12. IC declara resolución                     │
│ □ 13. CL publica comunicado de resolución       │
│ □ 14. IC abre ticket de Post-Mortem (< 48h)     │
└────────────────────────────────────────────────┘
```

---

*Santo Pegasus Soluciones*
*Departamento: Ingeniería de Software / Chapter de SRE*
*Versión: 1.0.0 | Junio 2026*
*Propietario del Documento: Chapter Lead de SRE*

*Este documento debe ser tratado como la "fuente de la verdad" para todos los procedimientos de respuesta a incidentes en Santo Pegasus Soluciones. Cualquier duda, sugerencia o solicitud de alteración debe ser dirigida al Chapter Lead de SRE a través del canal `#sre-chapter` en Slack.*
