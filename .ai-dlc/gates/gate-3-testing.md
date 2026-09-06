# Gate 3 — Testing

> Adaptación: sin código no hay pirámide unit→e2e. La verificación es **funcional sobre el
> sistema real** (aceptación) + **seguridad** (DAST equivalente = escaneo externo e interno)
> + **rendimiento contra los SLOs del charter**. Artefacto: `docs/04-testing/test-plan.md`.

- [ ] Cada RF01–RF05 y RNF01–RNF02 tiene un caso de aceptación ejecutado y con evidencia
- [ ] `requirementDiagram` con relaciones `verifies` (cierra el círculo abierto en Gate 0)
- [ ] Matriz OWASP: A01 (login 8971), A02 (puertos/bind), A03 (imagen pineada), A07 (fuerza bruta)
- [ ] Escenarios de abuso A1–A6 del PRD probados uno a uno, no solo documentados
- [ ] Transiciones del `stateDiagram` del Segmento verificadas, incluida **purga por retención**
      (requiere esperar al día 3 / día 14, o forzar con relojes de prueba)
- [ ] Equivalente DAST: `nmap -Pn <IP-WAN> -p 8971,8554,8555,1883` desde fuera → todo filtrado
- [ ] Rendimiento dentro de SLO: CPU sostenida <50 %, latencia de vivo ≤2 s (LAN y WireGuard),
      evento en `frigate/events` <3 s tras la detección
- [ ] Memoria dentro de RNF03 (T-17/T-18): Frigate <80 % de su límite, host con ≥4 GB
      disponibles, swap del NVR en 0, y el `tmpfs` se drena tras un export
- [ ] **HITL**: Jeremi acepta el resultado de la medición de carga (entrada de ADR-0002)

Al aprobar: cortar → `0.4.0`.
