# Observabilidad del NVR (ADR-0008)

Estos ficheros son la **especificación** de la observabilidad del NVR. Se instalan en el
proyecto que gobierna Prometheus, no en este repositorio.

Viven aquí a propósito: si la observabilidad del NVR solo existiera en el otro proyecto, un
cambio en las alertas quedaría fuera del alcance de este, y los umbrales dejarían de estar
trazados a los requisitos que los justifican.

| Fichero | Qué es | Dónde se instala |
|---|---|---|
| `fenrir-job.yml` | Scrape de `fenrir:5000` por la red Docker compartida | Bloque `scrape_configs` del `prometheus.yml` |
| `fenrir-rules.yml` | 6 alertas del NVR | Directorio de reglas que Prometheus carga |
| `node-exporter.compose.yml` | Servicio `node_exporter` | Compose de la plataforma |
| `node-exporter-job.yml` | Scrape de `host.docker.internal:9100` | Bloque `scrape_configs` |
| `host-rules.yml` | 7 alertas de host | Directorio de reglas |

## Por qué hace falta node_exporter

Frigate expone métricas de **su propio proceso**. Las dos preguntas que deciden si el
proyecto se sostiene son de **host**:

- ¿La CPU sostenida degrada el enrutamiento? Es la condición de revocación de ADR-0002.
- ¿Queda `MemAvailable` por encima de 4 GB? Es RNF03.

Sin métricas de host, ambas se responden a mano con `htop` y `free`, que es otra forma de
decir que no se responden. node_exporter las convierte en series con historial, y el
historial es justo lo que hace visible una fuga de memoria o una deriva del coste de
inferencia — la deuda que ADR-0005 aceptaba y ADR-0008 no tiene por qué heredar.

## Instalación

```bash
# 1. Añadir el servicio al compose de la plataforma y levantarlo
docker compose up -d node-exporter
curl -s localhost:9100/metrics | head -5      # debe responder

# 2. Añadir los dos jobs a scrape_configs y copiar las reglas al directorio de reglas
# 3. Validar ANTES de recargar
docker exec <prometheus> promtool check config /etc/prometheus/prometheus.yml

# 4. Recarga en caliente, sin reiniciar
docker exec <prometheus> kill -HUP 1
```

Comprobar en la UI de Prometheus que los targets `fenrir` y `jord` aparecen *up*, y que
`node_memory_MemAvailable_bytes` y `frigate_camera_fps` devuelven datos.

## Dos decisiones de montaje que conviene entender

**Red del host, y por qué eso no repite el error de T5.** node_exporter usa
`network_mode: host` —igual que el blackbox exporter que ya corre ahí— para que las métricas
de interfaces sean las reales y no las del namespace del contenedor. Eso **no** reabre T5: un
contenedor en red de host bindea directamente sobre el host, así que su tráfico atraviesa la
cadena `input` de nftables y el default-drop de las WAN lo protege. Lo que se saltaba esa
cadena eran los puertos **publicados** por Docker, que entran por DNAT. Son mecanismos
distintos y conviene no confundirlos al revisar la configuración.

**Monta la raíz en solo lectura.** Es el patrón estándar y necesario para reportar el uso de
sistemas de ficheros, pero significa que un escape de ese contenedor tendría lectura del
sistema de ficheros del host. Mitigado por: solo lectura, sin `privileged`, imagen pineada y
límite de memoria. Es un intercambio consciente, no un descuido.

## Los filtros de sistemas de ficheros no son cosmética

Con ~15 contenedores, cada capa de overlay2 y cada bind aparece como un sistema de ficheros
propio. Sin los `mount-points-exclude` / `fs-types-exclude`, las series se multiplican y la
alerta de la raíz —lo único que de verdad importa aquí, porque no hay volumen dedicado— queda
enterrada entre decenas de montajes irrelevantes.

## Redundancia deliberada en el disco

`DiscoNvrAlto` (desde Frigate) y `RaizHostAlta` (desde node_exporter) miran el **mismo**
sistema de ficheros desde dos sitios distintos, porque `/srv` comparte volumen con la raíz.
No es duplicación por descuido:

- La de host ve **a todos los consumidores**, incluida la base de series temporales del host,
  que crece por su cuenta.
- **Si las dos discrepan, algo está montado distinto de lo que la documentación asume.** Esa
  discrepancia es en sí misma una señal útil.

## Nombres

Los jobs del host siguen nomenclatura nórdica (`mimir`, `gjallarhorn`, `huginn_muninn`,
`sleipnir`). Propuesta para node_exporter: **`jord`** —Jörð, la tierra sobre la que todo se
sostiene—, que encaja con las constantes vitales del propio host. El NVR es **`fenrir`**,
el lobo encadenado: vigila, y el diseño entero consiste en tenerlo atado — sin salida a
internet, sin audio, con la API sin autenticar fuera de toda interfaz. Renombrar cualquiera
de los dos exige ajustar las reglas que los referencian.
