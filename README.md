# NVR Doméstico Frigate

Concentrador de videovigilancia local (DVR + monitoreo casi en tiempo real) sobre Frigate,
desplegado en el appliance de red doméstico (Ubuntu Server 24.04, i3-3240).
Documentación bajo metodología AI-DLC.

## Mapa del repo

- `docs/00-project/` — charter, glosario, clasificación de datos, ADRs
- `docs/01-requirements/` — PRD del MVP (Gate 0)
- `docs/02-design/` — arquitectura C4 y threat model STRIDE+DREAD (Gate 1)
- `docs/03-implementation/` — baseline de configuracion y cadena de suministro (Gate 2)
- `docs/04-testing/` — plan de verificacion: aceptacion, seguridad y carga (Gate 3)
- `docs/05-deployment/` — runbook paso a paso del despliegue (borrador hacia Gate 4)
- `docs/06-monitoring/` — SLIs/SLOs, alertas y respuesta a incidentes (Gate 5)
- `deploy/` — docker-compose, config de Frigate y Mosquitto (artefactos ejecutables)
- `.ai-dlc/gates/` — checklists de los Gates 0 a 5
- `CHANGELOG.md` — Keep a Changelog 1.1.0 + SemVer 2.0.0

## Anonimización

Este repositorio es público y documenta la postura de seguridad de una casa concreta, así
que **ningún dato real del despliegue vive en él**:

| Dato real | Dónde vive | Cómo aparece en el repo |
|---|---|---|
| IP LAN del appliance | `.env` (600, gitignored) | `${FRIGATE_LAN_IP}` |
| IPs de las cámaras | `.env` | `{FRIGATE_CAM1_IP}`, `{FRIGATE_CAM2_IP}` |
| MACs de las cámaras | dnsmasq del appliance | `<MAC-CAM-1>` |
| Credenciales RTSP y MQTT | `.env` y `passwd` (ambos gitignored) | `CAMBIAR` |
| Ubicación de cada cámara | Solo en la UI del NVR | `cam_01`, `cam_02` |

Los valores de ejemplo del `.env.example` usan `192.0.2.0/24`, el rango que RFC 5737
reserva para documentación: si ves esa IP en algún sitio, es un marcador, no un despliegue.
No es una medida de seguridad —el threat model no depende de ella— sino de higiene: evita
regalar el mapa. Al añadir documentación, mantener la convención.
