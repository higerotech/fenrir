# ADR-0005: Observabilidad sobre Node-RED en vez de un stack Prometheus/Grafana

* **Estado:** **superseded por ADR-0008** (2026-09-09). Nunca llegó a aceptarse.
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 06-monitoring
* **Versión:** 1.0.0
* **ID:** ADR-0005
* **Supersede / Superseded-by:** superseded-by ADR-0008
* **Controles OWASP afectados:** A09 (logging y monitorización), A02 (superficie añadida)

> **Por qué cayó.** Su argumento era de proporcionalidad: que Prometheus y Grafana costarían
> *"~300–500 MB de RAM y CPU constante en el host que hay que proteger"*. La inspección del
> host del 2026-09-09 mostró que **ya estaban desplegados y corriendo**, junto con
> Alertmanager. La premisa era falsa, así que la decisión no se sostiene. Se conserva el
> documento porque el razonamiento sigue siendo válido *para un host donde no existieran*, y
> porque la deuda que aceptaba —no tener historial— resultó ser justo lo que hacía falta.

## Contexto
El Gate 5 exige SLOs monitorizados y alertas que lleguen a una persona. Frigate 0.17 expone
métricas Prometheus en `/api/metrics` (`frigate_cpu_usage_percent`, `frigate_storage_*`,
`frigate_camera_fps`, `frigate_skipped_fps`, `frigate_detector_inference_speed_seconds`),
así que la telemetría ya existe; lo que falta es quién la evalúa y quién avisa.

La restricción que manda es la misma que en ADR-0002: el host es el router del hogar y el
presupuesto de CPU es <50 %. Añadir observabilidad no puede costar lo que se está intentando
proteger. Y ya hay un Node-RED planificado en el appliance, suscrito a MQTT por RF05.

## Decisión
Node-RED es el evaluador y el notificador. Sondea `/api/metrics` cada 60 s, se suscribe a
`frigate/#`, confirma cada umbral en tres muestras seguidas antes de avisar y envía por el
canal que ese stack ya use.

Para leer `/api/metrics` sin reabrir T6, Node-RED se conecta a la red interna de Docker
(`docker network connect nvr_default node-red`, o se mueve al mismo proyecto compose). El
puerto 5000 **no** se publica: no tiene autenticación.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| Node-RED (elegida) | Coste marginal ~0; ya está desplegado y ya habla MQTT; sin componentes nuevos | Sin series históricas ni gráficas; la lógica de alerta se mantiene a mano | Bajo: no añade puertos ni servicios |
| Prometheus + Grafana | Historial, dashboards, alerting maduro | Dos servicios más, ~300–500 MB de RAM y CPU constante en el host que hay que proteger; un puerto más que endurecer | Amplía la superficie (A02) |
| Prometheus + Grafana Cloud | Sin carga local de almacenamiento | Saca métricas del hogar hacia un tercero; contradice la premisa de privacidad del charter | Residencia de datos |
| `frigate-exporter` de terceros | Ya hecho | Dependencia extra de la comunidad para algo que Frigate ya expone nativo | A03 supply chain |
| Nada, revisión manual | Coste cero | El Gate 5 exige alertas que lleguen a alguien; una revisión manual no se hace | Incumple A09 |

## Consecuencias
- Positivas: cero componentes nuevos, cero puertos nuevos, cero coste de CPU relevante; la
  observabilidad vive donde ya viven las automatizaciones del hogar.
- Negativas / deuda: **sin historial**, así que las tendencias lentas (una fuga de memoria,
  un coste de inferencia que sube mes a mes) no se ven. La mitigación pobre es anotar el
  baseline a mano en el CHANGELOG en cada gate.
- Deuda asumida a conciencia: si el ciclo 2 trae el mini-PC dedicado de ADR-0002, el
  argumento de proporcionalidad decae y Prometheus/Grafana vuelve a la mesa — el endpoint
  Prometheus ya está ahí, así que migrar cuesta poco.
- Impacto en threat model: no introduce amenazas nuevas; refuerza la detección de T1 y T2,
  que hoy dependen de que alguien mire.
