# ADR-0003: Docker Compose con imagen pineada

* **Estado:** accepted
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0003
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A02 (secretos), A08 (integridad de software)

## Contexto
Frigate no se distribuye como paquete nativo de Ubuntu; el método soportado es Docker.
El host es crítico (router): las actualizaciones no pueden ser sorpresivas y los secretos
no pueden vivir en el repo.

## Decisión
`docker compose` con:
1. Imagen pineada `ghcr.io/blakeblackshear/frigate:0.17.2` — nunca `stable`/`latest`: el
   schema de config cambia entre minors y un pull desatendido puede dejar el contenedor
   sin arrancar contra el YAML existente.
2. Secretos vía `.env` (modo 600, en `.gitignore`) y sustitución `FRIGATE_*` en config.
3. Contenedores sin `privileged`; solo `/dev/dri/renderD128` para VAAPI; `restart:
   unless-stopped`.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| Compose + tag pineado | Reproducible, actualización deliberada | Update manual | Bajo |
| Tag stable con auto-pull | Siempre al día | Rotura silenciosa en cambios de schema | Integridad A08 |
| Instalación bare-metal | Sin capa Docker | No soportada upstream, dependencias frágiles | Parcheo manual |

## Consecuencias
- Positivas: rollback trivial (`docker compose down` + tag anterior + backup de config).
- Negativas / deuda: Docker Engine pasa a ser dependencia del appliance; revisar release
  notes en cada upgrade (procedimiento en runbook §9).
- Impacto en threat model: mitiga T6 (mapeo mínimo de puertos) y supply chain.
