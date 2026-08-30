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
