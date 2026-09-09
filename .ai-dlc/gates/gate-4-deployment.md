# Gate 4 — Deployment

- [x] `C4Deployment` + flowchart de pipeline/rollback + gantt de cutover (`deployment.md`)
- [ ] Runbook ejecutado de principio a fin, con las desviaciones anotadas en el propio doc
- [ ] Estado del runbook `draft` → `accepted` y ADR-0002 `proposed` → `accepted`
- [ ] Rollback probado de verdad, no solo escrito: bajar a la config anterior y volver a subir
- [ ] Backup de `/srv/frigate/config` (incluye `frigate.db`) verificado y restaurable
- [ ] Respaldo al NAS operativo (ADR-0006) y ADR-0006 promovida de `proposed` a `accepted`
- [ ] Endurecimiento de red aplicado y verificado (runbook §8: bind + `DOCKER-USER` + egress cámaras)
- [ ] CI mínima (opcional, ADR-0002): acción que valide Mermaid y `docker compose config` en push
- [ ] **HITL**: Jeremi confirma que el enrutamiento dual-WAN no se degradó tras 72 h

Al aprobar: cortar → `1.0.0` (MVP en producción doméstica). Este sí es un número fijo: el
1.0.0 marca el hito, no la secuencia.
