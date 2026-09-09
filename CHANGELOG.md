# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

El cierre de cada gate AI-DLC corta versión. **No es la única razón para cortar**: un cambio
entre gates que añada requisitos o controles también corta su MINOR, como manda SemVer. Por
eso los gates reservan *el siguiente* MINOR y no un número fijo — ver `.ai-dlc/gates/`.

## [Unreleased]

### Cambiado

- **Retención continua de 3 a 5 días** (ADR-0004 v1.1). La v1.0 fijó 3 días condicionada a
  ≥200 GB libres, sin conocer la capacidad real; medida el 2026-09-08: **422 GB**, holgura
  ×2,1. Con 5 días la ocupación queda en el 66 % del watermark del 90 %, que es el techo
  operativo de T1. No se sube a 7 días (89 %) porque el crecimiento real aún no está medido
  y porque retener menos video Confidencial sin cifrar sigue siendo un control, no una
  limitación que haya que superar porque ahora cabe.
- El riesgo del charter *"fallo del HDD único"* pasa de asumido a **mitigado parcialmente**.

### Añadido

- **ADR-0006 — respaldo al NAS iniciado por el NAS (pull), no por el appliance.** La
  propuesta original era rotar grabaciones antiguas al NAS por NFS; **no es implementable**:
  Frigate no tiene almacenamiento por niveles, su retención purga en vez de migrar, y las
  grabaciones están indexadas en `frigate.db` con sus rutas, así que mover archivos deja el
  índice apuntando a rutas muertas. Lo que sí cabe es un respaldo, que es otra cosa y no
  amplía la retención.
- La dirección se invierte respecto a lo propuesto: el NAS tira por `rsync` sobre SSH y el
  appliance **no monta nada**. Así una caída del NAS es invisible para el NVR, y el video
  viaja cifrado en vez de por una export NFS con `AUTH_SYS`, que no autentica de verdad.
  El NFS-push queda documentado como plan B si el NAS no puede iniciar tareas.
- Se respaldan `config/` (con `frigate.db`), alertas, snapshots y exportados. **No el
  continuo**: 43 GB/día replicados reintroducen el I/O de red que la ADR descarta.
- **T8** en el threat model: el NAS es una segunda ubicación de video Confidencial y hereda
  su clasificación. DREAD 4,8.
- Paso 8bis del runbook (cuenta `nvrbackup` restringida por `command=`), casos T-19
  (restauración real), T-20 (el NVR sobrevive al NAS apagado) y S-10 (la cuenta de respaldo
  no puede escribir), SLI de frescura del respaldo y runbook de incidente I-7.

## [0.3.0] - 2026-09-08

**Documentación de las seis fases completa y presupuesto de recursos cerrado.** No cierra
ningún gate: los Gates 2 a 5 siguen abiertos porque su evidencia exige el sistema desplegado.
Lo que sí queda cerrado es el papel — y el presupuesto, que hasta ahora solo cubría CPU.

### Añadido

- **RNF03 — presupuesto de memoria** (enmienda al PRD posterior al Gate 0). El presupuesto de
  recursos solo cubría CPU: en un host compartido con el router, agotar la memoria hace tanto
  daño como agotar la CPU, y no había requisito, ni SLO, ni prueba. Techos: contenedor
  `frigate` 3 GB, `mosquitto` 128 MB, `MemAvailable` del host ≥4 GB, swap del NVR en 0.
- **T7 en el threat model**: agotamiento de memoria del host. Sin límite por contenedor, el
  OOM killer del kernel elige víctima por heurística y puede matar `dnsmasq` — DNS y DHCP de
  toda la casa — en vez de Frigate. DREAD 5.4.
- Observabilidad de memoria: SLIs (`frigate_mem_usage_percent`, `MemAvailable`, swap), dos
  alertas nuevas y el runbook de incidente **I-6 · Presión de memoria**.
- Casos **T-17** (memoria durante los 15 min de T-11) y **T-18** (el `tmpfs` se drena tras un
  export); S-06 pasa a vigilar también la memoria mientras simula el disco lleno.

- Checklists de Gates 2–5 adaptados a un proyecto COTS-configuración (sin código propio).
- `docs/03-implementation/config-baseline.md` (Gate 2): inventario de artefactos, gitGraph de
  ramas y releases, validación de config (equivalente SAST) y cadena de suministro con
  digests (A03).
- `docs/04-testing/test-plan.md` (Gate 3): 16 casos de aceptación + 9 de seguridad,
  C4Container con el alcance de prueba, requirementDiagram con `verifies` y matriz de
  transiciones del segmento (incluidas las que NO deben ocurrir).
- `docs/06-monitoring/observability.md` (Gate 5): SLIs/SLOs trazados a charter y threat
  model, sequence señal→alerta→on-call, stateDiagram del incidente, 5 runbooks y timeline
  al ciclo 2.
- ADR-0005 (observabilidad sobre Node-RED en vez de Prometheus/Grafana, por
  proporcionalidad). En `proposed`: se aprueba al cerrar el Gate 4.

### Cambiado

- `deploy/docker-compose.yml`: `mem_limit` de 3 GB en `frigate` y 128 MB en `mosquitto`.
  El límite se dimensiona a 3 GB y no a 2 porque en cgroup v2 el `tmpfs` (techo 954 MiB) y
  el `shm` (128 MiB) se cargan al cgroup del contenedor: con 2 GB quedarían 966 MiB para
  procesos, sin margen sobre el RSS estimado.
- T1 gana una dimensión que no tenía: **escala a memoria**. El `tmpfs` es donde aterrizan los
  segmentos antes de moverse al HDD, así que un disco lleno impide drenar la caché y esta
  crece en RAM. El acoplamiento T1→T7 es lo que motivó el requisito.

### Spike cerrado — resultado negativo (NVR-SPIKE-002)

- `docs/01-requirements/spike-blinkpy.md`: spike para validar `blinkpy` como vía de recuperar
  los eventos de las Blink Mini y revisarlos a destiempo.
- `spikes/blinkpy/`: script de validación con listado en seco por defecto, descarga
  incremental y despojado de audio en la ingesta. **Aparcado**: no corre en ningún sitio.
- Verificado contra `blinkpy` 0.25.9 instalado: soporta tanto los clips en nube
  (`download_videos`, exige plan de suscripción) como el almacenamiento local del Sync
  Module 2 (`poll_local_storage_manifest`), que **no** lo exige y mantiene el video en casa.
- **Cerrado sin ejecutar**: no hay plan de suscripción ni Sync Module 2, de modo que las
  Blink Mini no generan clips recuperables por ninguna de las dos vías.
- Riesgos identificados para el día que se retome: R1 el audio de las Blink reintroduce lo
  que SR06 excluyó (FL §934.03); R2 la credencial pasa a ser la cuenta Amazon; R3 cliente no
  oficial; R4 dependencia de nube que el charter excluía.

## [0.2.0] - 2026-08-30

**Gate 1 (Design) aprobado.** Arquitectura C4 validada, threat model STRIDE+DREAD con
controles trazables, ADRs y contratos de interfaz.

### Añadido

- `architecture.md` con C4 Container, sequence del flujo detección→evento, stateDiagram
  del segmento de grabación y erDiagram del dominio.
- `threat-model.md` STRIDE + DREAD con controles trazados a ADRs y nftables.
- ADR-0001 (Frigate como NVR), ADR-0002 (placement on-prem en el appliance, PxD por
  proporcionalidad), ADR-0003 (Docker Compose con imagen pineada 0.17.2),
  ADR-0004 (política de retención 3 d continuo / 14 d alertas / 7 d detecciones).
- Contratos de interfaz: tabla de endpoints RTSP / HTTPS / WebRTC / MQTT.
- Artefactos ejecutables: `deploy/docker-compose.yml`, `deploy/frigate/config.yml`,
  `deploy/mosquitto/mosquitto.conf`, `deploy/.env.example`.
- Runbook de despliegue paso a paso (fase 05, hacia Gate 4): cámaras Tapo, Docker, Frigate,
  Mosquitto, verificación VAAPI y endurecimiento de red.

### Cambiado

- **ADR-0002 pasa a `accepted (condicional)`, resolviendo un bloqueo circular.** Estaba
  redactada para aprobarse *"tras medir la CPU real"*, mientras el runbook exigía el Gate 1
  aprobado para ejecutarse: cada uno esperaba al otro y el proyecto no podía avanzar sin
  romper su propia regla. Se separan las dos preguntas que estaban mezcladas — *¿es el sitio
  correcto?* es diseño y se contesta en el Gate 1 (candidato único viable); *¿aguanta la
  carga?* es verificación y se contesta en T-11/T-12 del Gate 3. La ADR lleva ahora su
  condición de revocación escrita.
- **Anonimización para repositorio público**: ninguna IP, MAC ni ubicación real vive en el
  repo. Las IPs de cámara salen del `config.yml` a variables `FRIGATE_CAM1_IP` /
  `FRIGATE_CAM2_IP` en el `.env` gitignorado — el mismo patrón que ya usaban las credenciales
  (SR03), así que no hay tabla de traducción que recordar. Las cámaras pasan a llamarse
  `cam_01` / `cam_02` y los ejemplos usan `192.0.2.0/24` (RFC 5737, reservado para
  documentación). Convención documentada en el README.
- El runbook pasa de `draft` a `ready`: con los Gates 0 y 1 aprobados, es ejecutable.

### Corregido

- `config.yml`: `version` pasa de `0.17-1` (inexistente) a `0.17-0`, que es el
  `CURRENT_CONFIG_VERSION` del tag 0.17.2; un valor futuro se salta las migraciones.
- `go2rtc`: añadido `webrtc.candidates` — sin ellos WebRTC no negocia y la vista en vivo
  degrada a MSE, incumpliendo RF04 (≤2 s) tanto en LAN como por WireGuard.
- `go2rtc`: `#backchannel=0` en los streams de las Tapo para no negociar audio bidireccional.

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

## [0.1.0] - 2026-08-30

**Gate 0 (Requirements) aprobado.** Requisitos de seguridad mapeados a ASVS L1, escenarios
de abuso, threat assessment inicial y datos clasificados.

### Añadido

- Charter con mindmap de alcance y glosario de lenguaje ubicuo (DDD).
- Clasificación de datos con regulación aplicable, cifrado y retención por tipo de dato.
- PRD del MVP (`NVR-MVP-001`) con objetivos y no-objetivos, C4 Context, journey del usuario,
  escenarios de abuso A1–A6, requirementDiagram (ASVS L1) y threat assessment inicial
  (DFD + quadrant DREAD).

### Seguridad

- Requisitos SR01–SR06 mapeados a OWASP ASVS L1 y al Top 10.
- Audio deshabilitado por defecto: Florida §934.03 exige consentimiento de todas las partes.
- Blink Mini fuera de alcance: protocolo cloud propietario, sin RTSP/ONVIF.

[Unreleased]: https://github.com/higerotech/nvr-frigate/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/higerotech/nvr-frigate/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/higerotech/nvr-frigate/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/higerotech/nvr-frigate/releases/tag/v0.1.0
