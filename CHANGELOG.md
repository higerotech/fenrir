# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Añadido

- Charter con mindmap de alcance, glosario (lenguaje ubicuo) y clasificación de datos.
- PRD del MVP con escenarios de abuso, C4 Context, journey, requirementDiagram (ASVS L1)
  y threat assessment inicial (DFD + quadrant DREAD).
- `architecture.md` con C4 Container, sequence del flujo detección→evento, stateDiagram
  del segmento de grabación y erDiagram del dominio.
- `threat-model.md` STRIDE + DREAD con controles trazados a ADRs y nftables.
- ADR-0001 (Frigate como NVR), ADR-0002 (placement on-prem en el appliance, PxD por
  proporcionalidad), ADR-0003 (Docker Compose con imagen pineada 0.17.2).
- Runbook de despliegue paso a paso (fase 05, borrador): cámaras Tapo, Docker, Frigate,
  Mosquitto, verificación VAAPI y endurecimiento.
- Artefactos ejecutables: `deploy/docker-compose.yml`, `deploy/frigate/config.yml`,
  `deploy/mosquitto/mosquitto.conf`, `.env.example`.

- Checklists de Gates 2–5 adaptados a un proyecto COTS-configuración (sin código propio).
- `docs/03-implementation/config-baseline.md`: inventario de artefactos, gitGraph de ramas y
  releases, validación de config (equivalente SAST) y cadena de suministro con digests (A03).
- `docs/04-testing/test-plan.md`: 16 casos de aceptación + 9 de seguridad, C4Container con el
  alcance de prueba, requirementDiagram con `verifies` y matriz de transiciones del segmento
  (incluidas las que NO deben ocurrir).
- `docs/06-monitoring/observability.md`: SLIs/SLOs trazados a charter y threat model,
  sequence señal→alerta→on-call, stateDiagram del incidente, 5 runbooks y timeline al ciclo 2.
- ADR-0004 (política de retención, cierra el HITL de retención del Gate 1) y ADR-0005
  (observabilidad sobre Node-RED en vez de Prometheus/Grafana, por proporcionalidad).

### Corregido

- `config.yml`: `version` pasa de `0.17-1` (inexistente) a `0.17-0`, que es el
  `CURRENT_CONFIG_VERSION` del tag 0.17.2; un valor futuro se salta las migraciones.
- `go2rtc`: añadido `webrtc.candidates` — sin ellos WebRTC no negocia y la vista en vivo
  degrada a MSE, incumpliendo RF04 (≤2 s) tanto en LAN como por WireGuard.
- `go2rtc`: `#backchannel=0` en los streams de las Tapo para no negociar audio bidireccional.

### Cambiado
- **Anonimización para repositorio público**: ninguna IP, MAC ni ubicación real vive en el
  repo. Las IPs de cámara salen del `config.yml` a variables `FRIGATE_CAM1_IP` /
  `FRIGATE_CAM2_IP` en el `.env` gitignorado — el mismo patrón que ya usaban las
  credenciales (SR03), así que no hay tabla de traducción que recordar. Las cámaras pasan a
  llamarse `cam_01` / `cam_02` y los ejemplos usan `192.0.2.0/24` (RFC 5737, reservado para
  documentación). Convención documentada en el README.

### Seguridad

- Exclusión explícita de exposición WAN; acceso remoto solo vía WireGuard existente.
- Credenciales RTSP fuera del repo vía variables `FRIGATE_*` en `.env`.
- **SR06 / FL §934.03**: `ffmpeg.output_args.record: preset-record-generic`. El default de
  Frigate es `preset-record-generic-audio-aac`, que graba audio si el stream lo trae; el
  micrófono apagado en la cámara era un control de un único punto de fallo.
- **T5**: los puertos publicados se bindean a `${FRIGATE_LAN_IP}` en vez de `0.0.0.0`.
  Docker publica vía DNAT en `PREROUTING`, así que el `policy drop` de la cadena `input`
  del router no protegía un puerto publicado; las reglas `DOCKER-USER` quedan como segunda
  barrera y no como única.
- **T1**: rotación de logs `json-file` (`max-size: 10m`, `max-file: 3`) en ambos servicios;
  el driver por defecto no rota y compite con la grabación por el disco del router.
