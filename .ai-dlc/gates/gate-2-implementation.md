# Gate 2 — Implementation

> Adaptación: este proyecto no tiene código propio (COTS configurado). El equivalente a
> "SAST limpio + deps verificadas + 80 % cobertura" es **configuración validada + cadena de
> suministro verificada + historial versionado**. Artefacto: `docs/03-implementation/`.

- [ ] Repositorio git inicializado, `main` como rama principal, primer commit con Gates 0–1
- [ ] `docs/03-implementation/repo-history.md` generado con `scripts/gitgraph_from_log.py`
- [ ] Validación de config (equivale a SAST):
  - [ ] `docker compose config` sin errores
  - [ ] `config.yml` parsea y Frigate arranca sin `config validation error` en el log
  - [ ] `version:` del config coincide con `CURRENT_CONFIG_VERSION` del tag desplegado
- [ ] Cadena de suministro (A03, equivale a deps verificadas):
  - [ ] Digest SHA256 de `frigate:0.17.2` y `eclipse-mosquitto:2` anotado en el repo
  - [ ] Escaneo de imagen (`trivy image` o `docker scout cves`) revisado; CVEs críticos triados
  - [ ] Release notes de 0.17.2 leídas (cambios de schema respecto al config)
- [ ] Secretos (A02): escaneo del repo (`gitleaks detect`) limpio; `.env` y `passwd` ignorados
- [ ] **HITL**: Jeremi acepta los CVEs residuales de las imágenes base

Al aprobar: cortar → `0.3.0`.
