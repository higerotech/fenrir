# ADR-0001: Frigate como plataforma NVR

* **Estado:** accepted
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0001
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A01 (authN UI), A05 (superficie de red), A08 (supply chain)

## Contexto
Se necesita un NVR open source para 2 C310 (RTSP/ONVIF), ampliable, con DVR, vivo casi en
tiempo real y eventos hacia MQTT/Node-RED, corriendo en un i3-3240 (2C/4T, sin AVX2) que
además es el router del hogar. Origina: RF01–RF05 del PRD NVR-MVP-001.

## Decisión
Frigate 0.17.2 en Docker: detección de objetos local, go2rtc integrado (vivo <2 s),
retención granular (continuo vs alertas), MQTT nativo y VAAPI para decodificar en la
iGPU HD 2500 (driver i965).

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| Frigate | Detección IA, MQTT nativo, go2rtc, comunidad grande | Config YAML exigente; detector CPU costoso sin acelerador | Bajo: authN nativa, imagen oficial |
| ZoneMinder | Veterano, ONVIF completo | UI anticuada, alto consumo en modect, sin detección moderna | Historial CVEs en la webapp PHP |
| Shinobi | Ligero, UI moderna | Comunidad pequeña, desarrollo irregular | Menos escrutinio |
| MotionEye | Mínimo consumo | Sin detección de objetos ni retención rica | Bajo |
| Agent DVR | Potente | **No es open source** — incumple requisito | Código no auditable |

## Consecuencias
- Positivas: eventos MQTT se integran directo con el stack IoT ya planificado; ampliar
  cámaras = editar YAML; camino de mejora claro (acelerador en ciclo 2).
- Negativas / deuda: detección limitada por CPU (5 fps, sub-stream); sin búsqueda
  semántica por falta de AVX2; dependencia de release notes al actualizar (schema cambia
  entre minors).
- Impacto en threat model: introduce T2 (CPU compartida) y T6 (API 5000), ambas con control.
