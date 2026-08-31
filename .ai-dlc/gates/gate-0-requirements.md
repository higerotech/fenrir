# Gate 0 — Requirements

- [x] PRD con objetivos / no-objetivos (`docs/01-requirements/mvp-nvr.md`)
- [x] Escenarios negativos / de abuso documentados
- [x] Requisitos de seguridad mapeados a OWASP ASVS (L1)
- [x] Threat assessment inicial (DFD + quadrant DREAD)
- [x] Clasificación de datos (`docs/00-project/data-classification.md`)
- [x] Charter + glosario (lenguaje ubicuo)
- [x] **HITL**: alcance, no-scope y nota legal validados 2026-08-30.
      El no-scope de las Blink Mini queda reforzado por NVR-SPIKE-002 con una segunda
      razón verificada: sin plan ni Sync Module 2 **hoy no graban nada en ningún sitio**,
      así que no hay material que recuperar aunque el transporte se resolviera.
      Audio: deshabilitado por FL §934.03, con doble control (micrófono off en cámara +
      `preset-record-generic` en Frigate) y verificación en T-13.
- [x] ~~confirmar IPs/reservas DHCP definitivas~~ — **migrado, no cumplido aquí**.
      Este ítem dejó de pertenecer al Gate 0 cuando la anonimización sacó las IPs del
      `config.yml` hacia variables del `.env`: el diseño ya no depende de conocerlas.
      Vive ahora donde toca, en el Paso 0 del runbook, como prerrequisito de despliegue.
      Marcarlo satisfecho habría sido mentir; dejarlo abierto habría bloqueado un gate de
      requisitos por un dato de operación.

Evidencia: journey + requirementDiagram + DFD/quadrant en el PRD.
**Aprobado 2026-08-30.** Cortado `[Unreleased]` → `0.1.0`; PRD en `approved`.
