# Gate 5 — Monitoring

> Artefacto: `docs/06-monitoring/observability.md`.

- [ ] SLIs/SLOs definidos con su fuente de medida (CPU del host, % de disco, uptime por cámara,
      latencia de vivo, retraso evento→MQTT) y error budget
- [ ] Watchdog de disponibilidad: Node-RED suscrito a `frigate/available`; alerta si `offline`
- [ ] Alerta de disco al 90 % en `/srv/frigate` (T1) con destino real (no solo un log)
- [ ] Alerta de CPU sostenida >50 % (T2), que es la condición de reapertura de ADR-0002
- [ ] Logging de seguridad (A09): logins fallidos de la UI de Frigate revisables
- [ ] `sequenceDiagram` señal→alerta→on-call y `stateDiagram-v2` del ciclo de incidente
- [ ] Proceso de incidentes escrito: cámara caída, disco lleno, contenedor en crash-loop,
      host router degradado
- [ ] `timeline` de hitos del ciclo y hallazgos que abren el ciclo 2 (bucle 06 → 01)
- [ ] **HITL**: Jeremi valida los umbrales de alerta tras 2 semanas de datos reales

Al aprobar: cortar → `1.1.0` y abrir ciclo 2 (acelerador, VLAN de cámaras, reemplazo de Blink).
