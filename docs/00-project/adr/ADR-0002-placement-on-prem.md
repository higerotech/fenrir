# ADR-0002: Placement — on-prem en el appliance existente

* **Estado:** accepted (condicional) — aprobada 2026-08-30 por mérito de diseño;
  verificación diferida a T-11/T-12 del Gate 3. Ver §Verificación diferida.
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

## Verificación diferida y condición de revocación

Esta ADR se escribió con la condición de aprobarse *"tras medir la CPU real"*, y eso creaba
un bloqueo circular: el Gate 1 esperaba una medida que solo el despliegue podía dar, y el
runbook esperaba que el Gate 1 estuviera aprobado. Tal como estaba redactado, el proyecto no
podía avanzar sin romper su propia regla.

La salida es separar dos preguntas que estaban mezcladas:

| Pregunta | Naturaleza | Dónde se contesta |
|---|---|---|
| ¿Es este el sitio correcto para desplegar? | **Diseño** | Gate 1 — contestada: sí |
| ¿Aguanta el host compartido la carga? | **Verificación** | Gate 3 — T-11 y T-12 |

La primera no depende de ninguna medida. El componente es de tipo E (especial): exige
adyacencia física a las cámaras, iGPU local y residencia del video en casa. El appliance es
el **único candidato viable**, y las alternativas están descartadas por razones que ninguna
medición va a cambiar — la nube saca video Confidencial del hogar y consume el uplink; el
mini-PC dedicado es la misma decisión con hardware nuevo, y solo tiene sentido plantearlo
*si* el host compartido falla. Aprobarla no es optimismo: es reconocer que no hay otra opción
sobre la mesa.

La segunda es un riesgo de ejecución, y los riesgos de ejecución se verifican, no se
predicen. Es el mismo tratamiento que ya recibió ADR-0004: decisión aceptada en diseño,
purga verificada en T-14/T-15.

**Se revoca esta ADR** — y el mini-PC dedicado pasa de diferido a necesario — si, tras
agotar las palancas del runbook I-3 (bajar `detect.fps` a 4, luego `cpuset`, luego reducir
objetos rastreados), se cumple cualquiera de estas:

- CPU sostenida >50 % durante 15 min con solo 2 cámaras (T-11).
- `frigate_skipped_fps` > 0 de forma persistente: el detector no da abasto (T-12).
- El enrutamiento se degrada de forma medible contra el baseline previo al NVR, o parar el
  NVR lo arregla (runbook I-5). Esta invalida la ADR **de facto y de inmediato**: el router
  manda sobre el NVR, siempre.

Hasta entonces, la ADR está vigente y el despliegue puede ejecutarse.

## Consecuencias
- Positivas: $0 CAPEX, datos en casa, integración directa con dnsmasq/nftables/WireGuard.
- Negativas / deuda: acoplamiento de fallos (si cae el host, caen router y NVR); recursos
  compartidos (T2).
- Impacto en threat model: habilita T2. Condición de revisión formalizada arriba; además
  se reabre al pasar de 4 cámaras, aunque la CPU aguante.
