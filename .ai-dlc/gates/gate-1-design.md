# Gate 1 — Design

- [x] C4 Context + Container validables (`architecture.md`)
- [x] Flujo crítico en sequenceDiagram; entidad núcleo en stateDiagram-v2
- [x] Threat model STRIDE + DREAD con controles trazables
- [x] ADR-0001..0005 (una decisión = una ADR; incluye placement PxD y retención)
- [x] Contratos de interfaz (tabla de endpoints RTSP/HTTP/MQTT)
- [x] **HITL**: ADR-0002 aprobada 2026-08-30 como **accepted (condicional)**.
      El deadlock estaba en la propia redacción: el gate exigía una medida que solo el
      despliegue podía dar, y el runbook exigía el gate aprobado. Se separan las dos
      preguntas que estaban mezcladas — *¿es el sitio correcto?* es diseño y se contesta
      aquí (candidato único viable); *¿aguanta la carga?* es verificación y se contesta en
      T-11/T-12 del Gate 3, con condición de revocación escrita en la ADR.
- [x] **HITL**: política de retención aprobada 2026-08-30 → ADR-0004 (3 d continuo /
      14 d alertas / 7 d detecciones). Condicionada a ≥200 GB libres: verificar en el
      Paso 0 del runbook y contra el crecimiento real a 24 h (T-14 / T-15)

**Aprobado 2026-08-30.** Cortado → `0.2.0`.
