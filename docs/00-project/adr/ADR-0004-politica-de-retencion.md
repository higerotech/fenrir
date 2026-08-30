# ADR-0004: Política de retención 3 días continuo / 14 días alertas

* **Estado:** accepted
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0004
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A02 (disponibilidad por agotamiento de disco), A04 (minimización de datos)

## Contexto
La retención es la decisión que gobierna a la vez el requisito RF02, la amenaza mejor
puntuada del threat model (T1, score 7.6: la grabación llena el HDD y degrada el router) y
la minimización de datos de la clasificación (el video es Confidencial y no cifrado en
reposo: guardar menos es guardar mejor). Era el HITL abierto del Gate 1.

Dimensionado: 2 cámaras × ~2 Mbps de stream1 ≈ 0,5 MB/s ≈ **43 GB/día** en continuo.

## Decisión
Retención escalonada por valor de la grabación, no uniforme:

| Clase | Días | Coste estimado |
|---|---|---|
| Continuo (`record.retain`, `mode: all`) | 3 | ~130 GB |
| Alertas — person, car (`record.alerts.retain`) | 14 | Solo los segmentos con evento |
| Detecciones — cat, dog (`record.detections.retain`) | 7 | Marginal |
| Snapshots (`snapshots.retain.default`) | 14 | Marginal |

Requiere **≥200 GB libres** en `/srv/frigate/media`: los 130 GB del continuo más el margen
de los eventos y el colchón que mantiene la ocupación por debajo del watermark del 90 %.

La clasificación en alertas y detecciones se declara de forma explícita en `review:` aunque
coincida con el default de Frigate, para que la retención sea trazable desde el config sin
tener que conocer los defaults del producto.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo |
|---|---|---|---|
| 3 d continuo / 14 d alertas | Cubre un fin de semana largo; el incidente que importa sobrevive dos semanas | Un hecho descubierto tarde puede haber perdido su contexto continuo | Aceptado |
| 7 d continuo / 30 d alertas | Más margen para descubrir algo tarde | ~300 GB: no cabe con holgura y acerca el disco al watermark, que es justo T1 | Agrava T1 |
| 1 d continuo / 30 d alertas | Mínimo consumo de disco | Sin contexto continuo alrededor del evento: se ve el qué, no el antes | Pierde valor probatorio |
| Solo eventos, sin continuo | Consumo mínimo | Lo que el detector no marca no existió nunca; ningún DVR real funciona así | Incumple RF02 |

## Consecuencias
- Positivas: T1 acotado por diseño y no por vigilancia; menos video Confidencial retenido, lo
  que reduce el impacto de un robo del disco (riesgo aceptado en la clasificación de datos).
- Negativas / deuda: un incidente descubierto pasado el día 3 conserva el clip pero pierde el
  metraje continuo de alrededor. Es el precio explícito de no llenar el disco del router.
- Condición de revisión: si el crecimiento real medido a 24 h se desvía más de un 25 % del
  estimado, o si el disco pasa del 90 %, esta ADR se revisa antes de añadir la tercera cámara.
- Verificación: T-14 y T-15 del plan de pruebas — la purga no se da por hecha, se observa el
  día 4 y el día 15.
