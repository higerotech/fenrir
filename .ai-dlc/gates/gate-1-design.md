# Gate 1 — Design

- [x] C4 Context + Container validables (`architecture.md`)
- [x] Flujo crítico en sequenceDiagram; entidad núcleo en stateDiagram-v2
- [x] Threat model STRIDE + DREAD con controles trazables
- [x] ADR-0001..0005 (una decisión = una ADR; incluye placement PxD y retención)
- [x] Contratos de interfaz (tabla de endpoints RTSP/HTTP/MQTT)
- [ ] **HITL**: aprobar ADR-0002 (convivencia NVR + router en el mismo host) tras medir CPU real
- [x] **HITL**: política de retención aprobada 2026-08-30 → ADR-0004 (3 d continuo /
      14 d alertas / 7 d detecciones). Condicionada a ≥200 GB libres: verificar en el
      Paso 0 del runbook y contra el crecimiento real a 24 h (T-14 / T-15)

Al aprobar: cortar → `0.2.0`.
