# ADR-0008: El NVR se integra en la plataforma del host en vez de traer sus propias piezas

* **Estado:** accepted
* **Fecha:** 2026-09-09
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0008
* **Supersede / Superseded-by:** **supersede a ADR-0005**
* **Controles OWASP afectados:** A02 (superficie y configuración), A05 (segmentación), A09 (monitorización)

## Contexto

ADR-0005 decidió montar la observabilidad del NVR sobre Node-RED en lugar de
Prometheus/Grafana, con un argumento explícito de proporcionalidad: *"dos servicios más,
~300–500 MB de RAM y CPU constante en el host que hay que proteger; un puerto más que
endurecer"*. Y el diseño preveía desplegar un Mosquitto propio dentro del proyecto compose
del NVR.

**La inspección del host del 2026-09-09 desmiente las dos premisas.** El appliance ya ejecuta
una plataforma de servicios madura: un broker MQTT con autenticación y ACLs, Node-RED,
Prometheus, Grafana, Alertmanager y un blackbox exporter que ya vigila la salud de ambas WAN.
Todo ello en una red Docker compartida y con ~415 MB de consumo real, sobre un host que
estaba a 0,1 de carga.

Dos consecuencias inmediatas, una de ellas un fallo que habría aparecido en el despliegue:

1. El broker existente ya escucha en el puerto y la dirección que nuestro compose pretendía
   publicar. `docker compose up -d` **habría fallado** con *address already in use*. Y el
   escenario peor no era ese: era que no fallara y acabáramos con dos brokers, con Node-RED
   suscrito al que no toca.
2. El coste que ADR-0005 usaba como argumento **ya está pagado**. Añadir observabilidad del
   NVR cuesta un `job_name` en el `prometheus.yml` existente.

## Decisión

El NVR se integra en la plataforma que ya existe, en vez de duplicarla. Es una sola postura
con dos consecuencias:

**Broker.** Se elimina el servicio Mosquitto del compose del NVR. Frigate publica en el
broker existente, alcanzándolo por nombre a través de la red Docker compartida. Hace falta
crear en ese broker un usuario `frigate` y sus entradas de ACL para `frigate/#`.

**Observabilidad.** Prometheus raspa `/api/metrics` de Frigate; las alertas se enrutan por el
Alertmanager existente y los paneles van a Grafana. La especificación —job de scrape y reglas
de alerta— se versiona en este repositorio (`deploy/prometheus/`) aunque se **instale** en el
proyecto que gobierna Prometheus.

**Red.** Frigate se une a la red Docker de esa plataforma. Efecto colateral que conviene
subrayar: **ni el 1883 ni el 5000 se publican en ninguna interfaz**. Prometheus alcanza el
5000 por la red interna, así que T6 pasa de "mitigado no publicando el puerto" a "no existe
superficie que mitigar", y el 1883 deja de estar expuesto en la LAN.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| **Integrar (elegida)** | Sin duplicar broker ni stack de métricas; menos puertos publicados que el diseño original; historial de métricas gratis | Acopla el NVR a la disponibilidad del broker compartido; el job de scrape vive en otro repositorio | Bajo: reduce superficie |
| Broker propio en otro puerto | El NVR sigue registrando eventos si el broker doméstico cae | Dos brokers que mantener y dos juegos de credenciales, para un beneficio que solo aplica a un fallo poco probable | Un puerto más |
| Mantener ADR-0005 (Node-RED como evaluador) | Sin tocar el proyecto de Prometheus | Reinventa lo que ya está desplegado, **y sin historial**: la deuda que la propia ADR-0005 aceptaba es justo lo que hace falta para ver la deriva del coste de inferencia (T2) y una fuga de memoria (T7) | Ninguno nuevo, pero deja A09 peor cubierto |

## Consecuencias

- Positivas: menos piezas, menos puertos publicados y menos credenciales que rotar. Las
  tendencias lentas —deriva del coste de inferencia, fuga de memoria— pasan a ser visibles,
  que era la deuda explícita de ADR-0005. Alertmanager ya sabe enrutar a una persona, así que
  el Gate 5 deja de depender de construir un notificador.
- Negativas / deuda: **acoplamiento**. Si el broker compartido cae, Frigate deja de publicar
  eventos (seguirá grabando y sirviendo vivo). Y la observabilidad del NVR deja de ser
  autocontenida: el job vive en otro repositorio, así que un cambio aquí exige acordarse de
  allí. `deploy/prometheus/` existe precisamente para que la especificación no se pierda.
- **Hueco detectado y cerrado en la misma decisión:** el host no tenía `node_exporter` ni
  `cadvisor`, así que no había métricas de host — y las preguntas que de verdad importan
  (RNF01/ADR-0002 y RNF03) son de host, no de proceso. Se despliega `node_exporter` con la
  especificación en `deploy/prometheus/`, siguiendo el patrón del blackbox exporter que ya
  corría ahí. Queda pendiente una sola fuente: la frescura del respaldo al NAS (ADR-0006).
- Intercambio consciente de `node_exporter`: monta la raíz del host en solo lectura, así que
  un escape de ese contenedor tendría lectura del sistema de ficheros. Mitigado con solo
  lectura, sin `privileged`, imagen pineada y límite de memoria.
- Impacto en threat model: reduce T6 a superficie nula y elimina el 1883 de la LAN. No
  introduce amenazas nuevas: el broker y sus ACLs ya existían.
