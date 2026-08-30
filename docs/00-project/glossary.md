# Glosario / Lenguaje Ubicuo (DDD)

* **Estado:** draft
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 00-project
* **Versión:** 0.1.0
* **Contextos acotados:** Vigilancia (captura/grabación/eventos), Red doméstica (transporte/aislamiento)

| Término | Definición | Contexto acotado (Bounded Context) |
|---|---|---|
| NVR | Network Video Recorder: sistema que ingiere, graba y analiza streams IP | Vigilancia |
| Cámara | Fuente RTSP registrada en Frigate (Tapo C310) | Vigilancia |
| stream1 / stream2 | Streams RTSP de la C310: principal 1080p (grabación) y sub-stream 640×360 (detección) | Vigilancia |
| Cuenta de cámara | Credencial local creada en la app Tapo que habilita RTSP/ONVIF sin nube | Vigilancia |
| go2rtc | Restreamer embebido en Frigate: multiplexa 1 conexión a cámara hacia N consumidores (WebRTC/RTSP) | Vigilancia |
| Detector | Proceso que ejecuta el modelo de detección de objetos (CPU en este MVP) | Vigilancia |
| Detección | Objeto identificado en un frame (persona, coche…) con score | Vigilancia |
| Evento / Alerta | Objeto seguido en el tiempo que Frigate clasifica para revisión (review: alerts/detections) | Vigilancia |
| Segmento | Trozo de video grabado en disco sujeto a retención | Vigilancia |
| Retención | Días que se conservan segmentos continuos vs eventos antes de purgarse | Vigilancia |
| VAAPI | API de aceleración de video de Intel; en Ivy Bridge vía driver i965 | Vigilancia |
| Broker MQTT | Mosquitto: bus de eventos entre Frigate y Node-RED | Vigilancia |
| Appliance | El equipo i3-3240 que actúa como router dual-WAN y ahora hospeda el NVR | Red doméstica |
| Reserva DHCP | Asignación fija de IP por MAC en dnsmasq para cada cámara | Red doméstica |
| Trust boundary LAN | Perímetro nftables: nada del NVR ni de las cámaras es alcanzable desde las WAN | Red doméstica |
