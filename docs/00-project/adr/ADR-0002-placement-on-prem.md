# ADR-0002: Placement — on-prem en el appliance existente

* **Estado:** proposed (HITL: aprobar tras medir CPU real en despliegue)
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0002
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A05 (segmentación de red)

## Contexto
Procedimiento de deployment placement AI-DLC, componente desplegable: NVR (Frigate +
Mosquitto). Clasificación: **tipo E (especial)** — requiere adyacencia física a las
cámaras (ingesta RTSP continua ~4–8 Mbps), acceso a iGPU local y residencia de datos
privados de video en el hogar. Nube descartada de raíz: subir 2 streams 1080p 24/7
consumiría el uplink, añadiría costo mensual y sacaría video Confidencial del hogar.

## Decisión
Desplegar en el appliance i3-3240 existente (mismo host que el router). Por
**proporcionalidad** (candidato único viable, costo marginal $0/mes — solo ~10–15 W de
consumo incremental), se documenta sin matriz PxD completa, como prevé la guía.

| Candidato | Costo mensual | Latencia | Carga operativa | Veredicto |
|---|---|---|---|---|
| Appliance existente (on-prem) | ~$1–2 (electricidad) | LAN, mínima | Media (host compartido) | **Elegido** |
| Mini-PC dedicado nuevo | ~$150–250 CAPEX | LAN, mínima | Baja | Diferido: revisar si T2 se materializa |
| VPS / nube | ≥$20 + egress | Alta; video sale del hogar | Media | Descartado (privacidad + uplink) |

**CD:** no aplica pipeline cloud. Despliegue por `docker compose` manual documentado en
runbook; opcional GitHub Actions solo para validar YAML/Mermaid del repo (gratis).

## Consecuencias
- Positivas: $0 CAPEX, datos en casa, integración directa con dnsmasq/nftables/WireGuard.
- Negativas / deuda: acoplamiento de fallos (si cae el host, caen router y NVR); recursos
  compartidos (T2).
- Impacto en threat model: habilita T2; condición de revisión — si CPU sostenida >50 % o
  al pasar de 4 cámaras, reabrir con la opción mini-PC dedicado.
