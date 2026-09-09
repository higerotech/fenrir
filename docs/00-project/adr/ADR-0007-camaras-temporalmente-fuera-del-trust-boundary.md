# ADR-0007: Cámaras temporalmente fuera del trust boundary LAN

* **Estado:** accepted (temporal, con fecha de caducidad) — 2026-09-09
* **Fecha:** 2026-09-09
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0007
* **Supersede / Superseded-by:** — (se retira al cumplirse la condición de salida)
* **Controles OWASP afectados:** A04 (cifrado en tránsito), A05 (segmentación), A07 (credenciales)

## Contexto

El diseño sitúa las cámaras dentro del trust boundary LAN, con reserva DHCP en el `dnsmasq`
del appliance y egress deny aplicado por él. La realidad del despliegue es otra, y de forma
declaradamente transitoria: **ambas C310 están en el Wi-Fi del lado WAN**, en un segmento que
el appliance no gobierna, alcanzables por su interfaz WAN2. Es un apaño mientras se adquiere
el equipamiento Wi-Fi definitivo de la casa.

No se reescribe el diseño objetivo, porque no ha cambiado. Lo que se documenta es una
**desviación temporal con condición de salida explícita**. Rehacer el charter, el C4 y el
threat model para un estado que va a durar semanas sería peor que inútil: dejaría el diseño
objetivo sin registrar y habría que deshacerlo entero después.

## Lo que realmente cambia, y lo que no

| Control del diseño | Estado en el apaño |
|---|---|
| SR02 — cero puertos del NVR alcanzables desde WAN | **Se mantiene.** El NVR es cliente RTSP: abre la conexión hacia la cámara. No hace falta abrir nada en la entrada WAN, y el `default drop` sigue intacto |
| T3 — RTSP en claro, aceptado por ser "LAN física propia" | **Roto.** La justificación era el control físico del segmento, y ese segmento ya no es nuestro. Usuario, contraseña y video pasan por un Wi-Fi compartido |
| SR04 / A3 — egress deny de las cámaras | **No aplicable.** El appliance no es su puerta de enlace y no puede impedirles salir a internet |
| Reserva DHCP en `dnsmasq` | **No aplicable.** Las direcciona otro router |

### La parte contraintuitiva: A3 mejora

Estar fuera del boundary no es solo pérdida. La amenaza T4/A3 era *"una C310 comprometida
pivota hacia la LAN"*. En el apaño, las cámaras están al otro lado del cortafuegos del
appliance, cuya entrada WAN es `default drop`: **no pueden alcanzar la LAN de la casa en
absoluto**. Han caído sin querer en una DMZ.

Así que esto es un intercambio, no una degradación pura: se pierde confidencialidad del
stream (T3) y se gana aislamiento contra el pivote (T4). Conviene decirlo porque el instinto
—"las cámaras fuera de la LAN es peor"— es engañoso aquí, y porque cuando lleguen a la LAN
definitiva **T4 vuelve a ser real** y el egress deny pasa a ser obligatorio, no opcional.

### Calibrar T3 sin alarmismo

Quien puede esnifar el RTSP es quien esté en ese Wi-Fi: la familia, un invitado, o un
dispositivo IoT comprometido del mismo segmento. **No** es un atacante cualquiera de
internet: el segmento no está expuesto a la WAN. El riesgo sube, pero de "aceptado por
control físico" a "acotado a quien tenga la contraseña del Wi-Fi", no a "expuesto".

## Decisión

Se acepta el despliegue en esta topología, de forma temporal, con cuatro controles
compensatorios que cuestan poco y son reales:

1. **IP fija configurada en la propia cámara**, no reserva DHCP en un router ajeno. Es más
   robusto para un estado transitorio: no depende de la configuración del router del ISP.
2. ~~Ruta a la red de las cámaras fijada con regla de política~~ — **innecesario, verificado
   en el host 2026-09-09**. La interfaz WAN2 del appliance tiene dirección en la propia red
   de las cámaras, así que existe una **ruta conectada** (`proto kernel scope link`) que
   siempre gana sobre la ruta por defecto: el balanceo dual-WAN no puede moverla. Lo escribí
   asumiendo que las cámaras estaban detrás de un salto, y no lo están.
   Lo que sí queda: si esa interfaz cae, las cámaras son inalcanzables y ninguna ruta lo
   arregla. Eso es disponibilidad de enlace, y lo cubre el watchdog de `frigate/available`.
3. **Credenciales de cámara únicas y fuertes, una por cámara**, y **rotarlas al migrar** a la
   LAN definitiva: hay que asumir que las actuales han viajado por un medio compartido.
4. **Wi-Fi del segmento con WPA2/WPA3 y contraseña fuerte.** Es lo único que separa el stream
   de un tercero, así que deja de ser un detalle de comodidad.

## Condición de salida

Esta ADR **se retira** cuando llegue el equipamiento Wi-Fi definitivo y las cámaras pasen a
la LAN del appliance. En ese momento, y en este orden:

1. Mover las cámaras a la LAN; IP por reserva DHCP en `dnsmasq` (Paso 1 del runbook, tal como
   está escrito).
2. **Rotar las credenciales de ambas cámaras.**
3. Aplicar el egress deny del Paso 8, que hasta entonces no era aplicable — y que a partir de
   entonces es obligatorio, porque T4 vuelve a estar viva.
4. Devolver T3 a su puntuación original y marcar esta ADR como retirada.

Mientras tanto, el diseño objetivo (charter, C4, threat model) queda **como está**: describe
el destino, no el apaño.

## Consecuencias

- Positivas: el despliegue no se bloquea esperando hardware. El aislamiento accidental contra
  el pivote es real mientras dure.
- Negativas / deuda: T3 elevada durante el periodo transitorio, con credenciales que habrá que
  rotar. Y una deuda de vigilancia: es fácil que "temporal" se convierta en permanente por
  inercia, y esta ADR es justo el recordatorio de que no lo es.
- Riesgo operativo añadido: las cámaras van por Wi-Fi y a través de una interfaz WAN. Las
  desconexiones son más probables que en la LAN cableada del diseño, así que el watchdog de
  `frigate/available` y la alerta de cámara caída importan más de lo previsto, no menos.
