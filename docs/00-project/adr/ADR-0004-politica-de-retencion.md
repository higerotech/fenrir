# ADR-0004: Política de retención 5 días continuo / 14 días alertas

* **Estado:** accepted
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.1.0 (enmienda 2026-09-08 con la capacidad real medida)
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
| Continuo (`record.retain`, `mode: all`) | 5 | ~216 GB |
| Alertas — person, car (`record.alerts.retain`) | 14 | Solo los segmentos con evento |
| Detecciones — cat, dog (`record.detections.retain`) | 7 | Marginal |
| Snapshots (`snapshots.retain.default`) | 14 | Marginal |

### Enmienda 2026-09-08 — de 3 a 5 días

La versión 1.0.0 fijó 3 días y se aceptó **condicionada a ≥200 GB libres**, sin conocer la
capacidad real. Medida: **422 GB disponibles**, holgura ×2,1 sobre la condición. El techo
operativo es el watermark del 90 % de T1, o sea **380 GB**:

| Continuo | GB | + alertas 14 d (~35) | % del techo |
|---|---|---|---|
| 3 d | 130 | 165 | 43 % |
| **5 d (elegido)** | **216** | **251** | **66 %** |
| 7 d | 302 | 337 | 89 % |
| 9 d | 389 | 424 | no cabe |

Se elige 5 días y no 7 por dos razones. La primera es margen: el crecimiento real todavía no
está medido —el dimensionado de 43,2 GB/día es una estimación— y apurar al 89 % del techo
antes de tener el dato de 24 h deja sin colchón para la desviación. La segunda es que **la
capacidad no es el único criterio**: el video es Confidencial y no está cifrado en reposo,
así que retener menos sigue siendo un control de minimización, no una limitación que haya
que superar porque ahora cabe. 5 días cubren un fin de semana largo, que era el caso de uso
que motivaba subir.

Si el crecimiento medido a 24 h se confirma por debajo de lo estimado, subir a 7 días es un
cambio de una línea y esta ADR se vuelve a enmendar.

La clasificación en alertas y detecciones se declara de forma explícita en `review:` aunque
coincida con el default de Frigate, para que la retención sea trazable desde el config sin
tener que conocer los defaults del producto.

## Alternativas consideradas
| Opción | Pros | Contras | Riesgo |
|---|---|---|---|
| 5 d continuo / 14 d alertas | Cubre un fin de semana largo con margen; el incidente que importa sobrevive dos semanas | Un hecho descubierto pasada la semana pierde su contexto continuo | **Elegido (v1.1)** |
| 3 d continuo / 14 d alertas | Mínimo de datos retenidos | Un fin de semana largo se sale del continuo por poco | Aceptado en v1.0, superado por la capacidad real |
| 7 d continuo / 30 d alertas | Más margen para descubrir algo tarde | 89 % del techo sin tener medido el crecimiento real; y más video Confidencial retenido | Diferido hasta el dato de 24 h |
| 1 d continuo / 30 d alertas | Mínimo consumo de disco | Sin contexto continuo alrededor del evento: se ve el qué, no el antes | Pierde valor probatorio |
| Solo eventos, sin continuo | Consumo mínimo | Lo que el detector no marca no existió nunca; ningún DVR real funciona así | Incumple RF02 |

## Consecuencias
- Positivas: T1 acotado por diseño y no por vigilancia; menos video Confidencial retenido, lo
  que reduce el impacto de un robo del disco (riesgo aceptado en la clasificación de datos).
- Negativas / deuda: un incidente descubierto pasado el día 3 conserva el clip pero pierde el
  metraje continuo de alrededor. Es el precio explícito de no llenar el disco del router.
- Condición de revisión: si el crecimiento real medido a 24 h se desvía más de un 25 % del
  estimado, o si el disco pasa del 90 %, esta ADR se revisa antes de añadir la tercera cámara.
- El respaldo al NAS (ADR-0006) **no** amplía esta retención: son cosas distintas. Frigate no
  tiene almacenamiento por niveles —su retención purga, no migra— así que lo que sale de esta
  ventana se borra del NVR, y lo que el NAS conserve vive fuera de su índice.
- Verificación: T-14 y T-15 del plan de pruebas — la purga no se da por hecha, se observa el
  día 4 y el día 15.
