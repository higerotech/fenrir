# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

El cierre de cada gate AI-DLC corta versión. **No es la única razón para cortar**: un cambio
entre gates que añada requisitos o controles también corta su MINOR, como manda SemVer. Por
eso los gates reservan *el siguiente* MINOR y no un número fijo — ver `.ai-dlc/gates/`.

## [Unreleased]

### Ejecutado en el host (2026-09-09 13:29)

Migración de nombres y **salida del SAFE MODE** en un solo despliegue, siguiendo el anexo
del runbook. `/opt/nvr` → `/opt/fenrir`, `/srv/frigate` → `/srv/fenrir`, contenedor
`frigate` → `fenrir-frigate`.

- **La configuración está en vigor por primera vez.** No «no hay errores», sino
  comprobado contra `/api/config`: continuo 5 días, alertas 14, detecciones 7,
  `preset-record-generic` (sin audio) y `detect.enabled` a `True` en ambas cámaras a 5 fps.
  Las tareas de mantenimiento y limpieza ya no aparecen como *skipped*: **la retención de
  ADR-0004, y con ella el control de T1, existe desde ahora.**
- **El movimiento de datos fue transparente**, como predecía la comprobación previa: 5,0 GB
  y 5.711 segmentos intactos, 86 eventos, y las 5.711 filas de `recordings.path` siguen con
  el único prefijo `/media/frigate/recordings` — ruta interna del contenedor, que el
  renombrado del origen en el host no toca.
- MQTT reconectado: `frigate/available online` y `detect/state ON` en ambas cámaras.
- **La CPU sigue fuera de presupuesto**: 207 % de 4 hilos ≈ 52 %, contra el `<50 %` de
  RNF01. Ahora sí es una medida válida — con el mantenimiento activo y la configuración
  real—, así que deja de ser un dato sospechoso y pasa a ser una entrada para ADR-0002.
  Falta la medición sostenida de 15 min para T-11/T-12.

**Sin desplegar todavía**: el job de scrape y las reglas de alerta. Se confirmó que el
`prometheus.yml` del host **nunca llegó a incluirlos**, así que no hay observabilidad del
NVR: ninguna de las 6 alertas puede dispararse hoy.


### Corregido

Los tres primeros errores del arranque real, en el orden en que Frigate 0.17.2 los fue
sacando. Ninguno se ve en `docker compose config` ni validando el YAML: los tres necesitan
el contenedor levantado contra el host.

- **`FRIGATE_MQTT_HOST` y `FRIGATE_MQTT_USER` no llegaban al contenedor.** `config.yml` las
  interpola, pero solo estaban en el `.env`; Frigate sustituye únicamente las variables que
  ve en **su** entorno, así que abortaba con `KeyError` antes de arrancar. Se añaden al
  bloque `environment:` del compose, con la comprobación que lo detecta sin desplegar:
  `grep -oE '\{FRIGATE_[A-Z0-9_]+\}' frigate/config.yml | sort -u` — toda variable que salga
  ahí tiene que estar en el compose.
- **`record.retain` ya no existe en 0.17; el continuo es `record.continuous.days`.** El fallo
  no es ruidoso: Frigate no rechaza el arranque, entra en **SAFE MODE** e **ignora la
  configuración entera** — cámaras, detección, retención y endurecimiento incluidos. Es el
  peor modo de fallo de los tres, porque el contenedor queda «arriba». Verificado contra el
  modelo del propio contenedor, no contra la documentación:
  `docker exec fenrir-frigate python3 -c "from frigate.config.config import RecordConfig; print(RecordConfig.model_json_schema()['properties'].keys())"`.
- **`detect.enabled` viene en `False` por defecto en 0.17** y hay que activarlo por cámara.
  Sin esto el sistema graba pero no detecta: RF03 no se cumple y el silencio es idéntico al
  de una escena sin movimiento.

Y un cuarto que no es de Frigate sino del propio runbook:

- **Cuatro comandos del runbook llevaban un `\n` literal en medio**, restos de una edición
  anterior: las dos verificaciones RTSP de las cámaras (Paso 1), la comprobación de que el
  segmento grabado no tiene pista de audio (Paso 7, SR06 / FL §934.03) y la línea de
  `authorized_keys` del respaldo (Paso 8bis). Copiadas y pegadas fallaban. En un documento cuyo
  único modo de uso es copiar y pegar durante el arranque, eso no es cosmético. Las tres
  primeras pasan a continuación de línea real; la de `authorized_keys` se parte sin barra,
  con el aviso de que ahí va todo en una sola línea.

- **El test de audio del runbook pasaba en falso.** `ffprobe` no está en el `PATH` del
  contenedor —vive en `/usr/lib/ffmpeg/7.0/bin/`— y la ruta del `find` sobraba un nivel:
  la media del host cuelga de `/srv/fenrir/media/`, y el `frigate/` interno lo pone el
  montaje. Con cualquiera de las dos cosas mal, el comando aborta, `grep -c codec_type`
  devuelve `0` y **eso es exactamente lo que el runbook lee como «sin audio»**. Un control
  de cumplimiento (SR06 / FL §934.03) que se aprueba solo no es un control. Corregidos el
  binario y la ruta, y el test comprueba primero que existe un segmento reciente antes de
  medir nada. **Ejecutado bien da `0` en ambas cámaras**: el requisito se cumple de verdad.

### Añadido

- **Comprobación de SAFE MODE en el Paso 6 del runbook.** Con un config inválido, Frigate
  no se para: arranca en modo seguro, graba, detecta y publica en MQTT, y `docker ps` lo da
  por `healthy` — pero desactiva el mantenimiento de almacenamiento y la limpieza de
  grabaciones y eventos. La retención de ADR-0004, que es **el** control de T1, deja de
  aplicarse sin que nada lo diga. Se añade el `grep` que lo detecta y el corolario que
  costó siete horas el 2026-09-09: **arreglar el fichero no basta**, porque el config se lee
  al arrancar; un contenedor levantado a las 05:29 con el fichero corregido a las 05:34
  sigue en modo seguro indefinidamente.

### Medido en el arranque real (2026-09-09)

Primeras cifras del sistema corriendo. Ninguna cierra Gate 3 — se tomaron con Frigate en
safe mode, o sea sin las tareas de mantenimiento — pero dos contradicen al diseño:

- **CPU al 216 % de 4 hilos = 54 % sostenido, por encima del `<50 %` de RNF01.** El muestreo
  de 15 min (`muestreo.csv`, 05:40–05:56) da 145–207 %, o sea 36–52 %: ya entonces rozaba
  el techo. Es la entrada de la condición de revocación de ADR-0002 y hay que repetirla
  fuera de safe mode antes de decidir nada.
- **El crecimiento real es ~14 GB/día** (4,2 GB en 7 h 09 min, dos cámaras en continuo),
  frente a los ~216 GB por 5 días que estimaba ADR-0004: **un tercio**. La holgura para
  subir la retención es mucho mayor de lo que decía el ADR, pero el argumento para no
  hacerlo nunca fue el espacio, así que el dato no cambia la decisión por sí solo.
- **Los segmentos son 2304x1296, no 1920x1080.** El Paso 1 del runbook daba por hecha una
  resolución que estas C310 no entregan.
- Sin pista de audio en ninguna cámara (SR06 / §934.03), MQTT conectado y publicando, y
  VAAPI autodetectado. **Pendiente**: confirmar que la decodificación cae de verdad en la
  iGPU — `intel_gpu_top` falla dentro del contenedor con *Failed to initialize PMU
  (Operation not permitted)*, así que T-24 sigue sin evidencia directa.

### Cambiado

- **El proyecto pasa a llamarse Fenrir**, siguiendo la nomenclatura nórdica de la
  plataforma doméstica (`yggdrasil` la plataforma, `mimir` las métricas, `odin` los
  paneles, `ratatosk` el broker). El lobo encadenado: vigila, y el diseño entero consiste
  en tenerlo atado — sin salida a internet, sin pista de audio, con la API sin autenticar
  fuera de toda interfaz.

  La convención se leyó del host, no se inventó: ahí el **proyecto compose** es la
  plataforma, el **servicio** lleva el nombre mítico y el **contenedor** es
  `<proyecto>-<software>` (`yggdrasil-prometheus` corre el servicio `mimir`). Aplicado:

  | | Antes | Ahora |
  |---|---|---|
  | Repositorio | `higerotech/nvr-frigate` | `higerotech/fenrir` |
  | Proyecto compose | `nvr` | `fenrir` |
  | Servicio | `frigate` | `fenrir` |
  | Contenedor | `frigate` | `fenrir-frigate` |
  | Job de Prometheus | `frigate` | `fenrir` |
  | Raíz de despliegue | `/opt/nvr` | `/opt/fenrir` |
  | Datos y config | `/srv/frigate` | `/srv/fenrir` |

  **Lo que deliberadamente no cambia**, porque nombra al producto y no al proyecto: la
  imagen y el software Frigate, sus métricas `frigate_*`, sus rutas internas
  (`/media/frigate`, `/config`), `frigate.db`, y el directorio `deploy/frigate/` — los
  subdirectorios de `deploy/` llevan el nombre del software cuya configuración contienen,
  igual que `deploy/prometheus/`.

  **Tampoco cambian el usuario ni los tópicos MQTT `frigate/#`**, y no por descuido: viven
  en el broker de `yggdrasil`, con su ACL, y los consume Node-RED. Renombrarlos es un
  cambio en la plataforma con clientes que romper, no parte de este rename. Queda anotado
  como la única costura donde el nombre viejo sigue a la vista.

- **El error de un nivel en la ruta de la media estaba en seis sitios, no en uno.** En el
  host la media cuelga de `<raiz>/media/`; el `frigate/` intermedio lo añade el montaje del
  contenedor, no el disco. Escrito como `<raiz>/media/frigate/...` apuntaba a un directorio
  inexistente en: el `find` de grabaciones del runbook (Paso 7), el `setfacl` del respaldo
  (Paso 8bis y `deploy/backup/README.md`), el caso T-03 del plan de pruebas, la
  comprobación de purga de `observability.md` — y las dos rutas de `rsync` de
  `pull-from-appliance.sh`, que **habrían fallado en la primera ejecución real**, todavía
  pendiente. Es el mismo error que hacía pasar en falso el test de audio: un `find` sin
  resultados no distingue «no hay» de «miraste donde no era». De paso, el comentario del
  continuo decía 43 GB/día; el dato medido es ~14.
- **El diagrama de despliegue seguía mostrando un Mosquitto dentro del compose del NVR**,
  que ADR-0008 eliminó hace dos versiones. Ahora muestra el broker de la plataforma como
  lo que es: un contenedor de otro proyecto. También corrige la retención (5/14, no 3/14)
  y la resolución de las cámaras.
- **El corte de versión va directo a `main`, sin ronda de revisión** (`config-baseline.md`,
  «Cómo se corta una versión»). El corte es mecánico —mover `[Unreleased]`, ajustar enlaces
  de comparación y los MINOR previstos de los gates— y no contiene ninguna decisión que
  revisar. El ruleset `Protect-MAIN` **no se desactiva**: como no exige aprobaciones
  (`required_approving_review_count: 0`), la PR se crea y se mergea en el mismo paso y la
  protección se conserva. Si algún día pasa a exigirlas, el procedimiento deja de funcionar
  solo. Los cambios de diseño siguen yendo por PR.
- Queda escrito por qué el tag apunta al commit del corte y no a `main` sin más: un tag
  publicado no se mueve, así que no se clava sobre un commit cuyo CHANGELOG todavía dice
  `[Unreleased]`.

## [0.4.0] - 2026-09-09

**Contacto con el host real.** La inspección de `midgard` desmintió supuestos del diseño y
evitó al menos tres fallos que habrían aparecido durante el despliegue. Tampoco cierra ningún
gate: los Gates 2 a 5 siguen abiertos porque su evidencia exige el sistema corriendo.

### Cambiado

- **Retención continua de 3 a 5 días** (ADR-0004 v1.1). La v1.0 fijó 3 días condicionada a
  ≥200 GB libres, sin conocer la capacidad real; medida el 2026-09-08: **422 GB**, holgura
  ×2,1. Con 5 días la ocupación queda en el 66 % del watermark del 90 %, que es el techo
  operativo de T1. No se sube a 7 días (89 %) porque el crecimiento real aún no está medido
  y porque retener menos video Confidencial sin cifrar sigue siendo un control, no una
  limitación que haya que superar porque ahora cabe.
- El riesgo del charter *"fallo del HDD único"* pasa de asumido a **mitigado parcialmente**.

### Añadido

- **ADR-0008 — el NVR se integra en la plataforma del host en vez de traer sus propias
  piezas. Supersede a ADR-0005.** La inspección del host (2026-09-09) desmintió las dos
  premisas del diseño: ya corren un broker MQTT con `password_file` y `acl_file`, Node-RED,
  Prometheus, Grafana, Alertmanager y un blackbox exporter que vigila ambas WAN.
  - **Bug evitado**: el compose publicaba su propio Mosquitto en la misma IP y puerto que el
    broker existente. `docker compose up -d` habría fallado con *address already in use* —
    y el escenario peor era que no fallara y quedaran dos brokers.
  - Se elimina el servicio Mosquitto del compose. Frigate usa el broker existente, con
    usuario y ACL propios para `frigate/#`.
  - Frigate se une a la red Docker de esa plataforma. **Ni el 1883 ni el 5000 se publican en
    ninguna interfaz**: Prometheus raspa `frigate:5000` por la red interna, así que T6 pasa
    de "mitigado no publicando el puerto" a "no hay superficie que mitigar".
  - `deploy/prometheus/`: job de scrape y seis reglas de alerta. Es la especificación; se
    instala en el proyecto que gobierna Prometheus, pero se versiona junto al NVR.
- **`group_add` para VAAPI.** `/dev/dri/renderD128` es `root:render` y mapear el dispositivo
  no da pertenencia al grupo dentro del contenedor: sin esto ffmpeg falla con *permission
  denied* y Frigate decodifica por CPU sin decirlo claramente. Verificado en T-24.
- Casos T-23 (los clientes MQTT existentes no pierden acceso), T-24 (VAAPI de verdad),
  T-25 (Prometheus raspa sin puerto publicado) y S-12 (el usuario del NVR no ve el resto del
  tráfico MQTT del hogar).

### Cambiado (por la inspección del host)

- **ADR-0005 pasa a `superseded`.** Su argumento era que Prometheus y Grafana costarían
  "~300–500 MB de RAM y CPU constante"; ya estaban desplegados. La premisa era falsa. Y la
  deuda que aceptaba —no tener historial— resultó ser justo lo que hace falta para ver la
  deriva del coste de inferencia (T2) y una fuga de memoria (T7).
- **T1 sube de impacto: no hay volumen dedicado y no se puede tallar uno** (el grupo de
  volúmenes no tiene espacio sin asignar). `/srv` comparte LV con la raíz del host, así que
  llenarlo afecta a todo lo que corre en la máquina. El control *"media en ruta dedicada"*
  del diseño no está disponible; la alerta de disco baja al **85 %** y pasa de segunda
  barrera a primera.
- Runbook: Paso 5 deja de crear un broker y da de alta un usuario en el existente, con un
  aviso destacado de que `mosquitto_passwd -c` **borra el fichero entero** y dejaría sin
  acceso a los clientes que ya había.

- **`node_exporter` para métricas de host.** Sin él, las dos preguntas que deciden si el
  proyecto se sostiene —¿la CPU sostenida degrada el enrutamiento (RNF01, condición de
  revocación de ADR-0002)? ¿queda `MemAvailable` sobre 4 GB (RNF03)?— no se podían responder:
  Frigate solo expone su propio proceso. Se añaden el servicio, su job y `host-rules.yml` con
  7 alertas (memoria, swap, CPU, carga y raíz del host). Sigue el patrón del blackbox exporter
  que ya corría en el host: red de host, sin puertos publicados, alcanzado por
  `host.docker.internal`.
  - **Las 13 reglas están validadas con `promtool` contra el propio Prometheus del host**, no
    solo comprobadas como YAML.
  - Redundancia deliberada en el disco: `DiscoNvrAlto` (desde Frigate) y `RaizHostAlta` (desde
    node_exporter) miran el mismo sistema de ficheros desde dos vantajes, porque no hay volumen
    dedicado. **Si discrepan, algo está montado distinto de lo que la documentación asume** —
    T-27 lo comprueba.
  - El runbook I-3 gana un primer paso que antes no era posible: **atribuir**. Si la CPU del
    host sube y la de Frigate no, el NVR es la víctima y no la causa, y tocar `detect.fps` no
    arregla nada.

### Hueco conocido, sin cerrar

- **Frescura del respaldo al NAS** (ADR-0006): el `.last-success` vive en el NAS y no hay
  fuente de métrica todavía. Se resolvería con el mismo patrón de textfile servido por HTTP
  que el host ya usa para el job de throughput. No se escriben alertas que no puedan
  dispararse.

- **ADR-0007 — cámaras temporalmente fuera del trust boundary LAN.** Ambas C310 están en el
  Wi-Fi del lado WAN mientras se adquiere el equipamiento Wi-Fi definitivo. Se documenta como
  **desviación temporal con condición de salida**, no reescribiendo el diseño objetivo: el
  destino no ha cambiado y rehacer charter, C4 y threat model para un estado transitorio
  habría que deshacerlo después.
  - **SR02 se mantiene**: el NVR es cliente RTSP saliente, así que no se abre ningún puerto de
    entrada WAN y el `default drop` sigue intacto.
  - **T3 sube temporalmente de 4,2 a 6,0**: la justificación original —"LAN física propia"—
    no aplica a un segmento que el appliance no gobierna. Acotado a quien tenga la contraseña
    de ese Wi-Fi, no expuesto a internet.
  - **T4 queda más contenida, no menos**: las cámaras están al otro lado del `default drop` y
    no alcanzan la LAN en absoluto. Al migrarlas, el egress deny pasa de deseable a obligatorio.
  - Controles compensatorios: IP fija en la propia cámara (no reserva DHCP en router ajeno),
    ruta fijada para que el failover dual-WAN no la mueva, credenciales únicas y **rotación al
    migrar**, y WPA2/WPA3 fuerte en ese Wi-Fi.
  - Casos T-21 (la ruta no cambia con el failover), T-22 (contar reconexiones RTSP en 24 h) y
    S-11 (desde el segmento de las cámaras no se alcanza la LAN ni la UI).

- **ADR-0006 — respaldo al NAS iniciado por el NAS (pull), no por el appliance.** La
  propuesta original era rotar grabaciones antiguas al NAS por NFS; **no es implementable**:
  Frigate no tiene almacenamiento por niveles, su retención purga en vez de migrar, y las
  grabaciones están indexadas en `frigate.db` con sus rutas, así que mover archivos deja el
  índice apuntando a rutas muertas. Lo que sí cabe es un respaldo, que es otra cosa y no
  amplía la retención.
- La dirección se invierte respecto a lo propuesto: el NAS tira por `rsync` sobre SSH y el
  appliance **no monta nada**. Así una caída del NAS es invisible para el NVR, y el video
  viaja cifrado en vez de por una export NFS con `AUTH_SYS`, que no autentica de verdad.
  El NFS-push queda documentado como plan B si el NAS no puede iniciar tareas.
- Se respaldan `config/` (con `frigate.db`), alertas, snapshots y exportados. **No el
  continuo**: 43 GB/día replicados reintroducen el I/O de red que la ADR descarta.
- **T8** en el threat model: el NAS es una segunda ubicación de video Confidencial y hereda
  su clasificación. DREAD 4,8.
- `deploy/backup/`: `snapshot-db.sh` (appliance) y `pull-from-appliance.sh` (NAS), ambos por
  cron, con su README. La base **no se copia con rsync directamente**: sobre una SQLite viva
  eso puede dar un fichero roto, así que un cron previo genera un snapshot consistente con
  `sqlite3 .backup`, validado con `integrity_check` y publicado con un `mv` atómico.
- Paso 8bis del runbook (cuenta `nvrbackup` restringida por `command=`), casos T-19
  (restauración real), T-20 (el NVR sobrevive al NAS apagado) y S-10 (la cuenta de respaldo
  no puede escribir), SLI de frescura del respaldo y runbook de incidente I-7.

## [0.3.0] - 2026-09-08

**Documentación de las seis fases completa y presupuesto de recursos cerrado.** No cierra
ningún gate: los Gates 2 a 5 siguen abiertos porque su evidencia exige el sistema desplegado.
Lo que sí queda cerrado es el papel — y el presupuesto, que hasta ahora solo cubría CPU.

### Añadido

- **RNF03 — presupuesto de memoria** (enmienda al PRD posterior al Gate 0). El presupuesto de
  recursos solo cubría CPU: en un host compartido con el router, agotar la memoria hace tanto
  daño como agotar la CPU, y no había requisito, ni SLO, ni prueba. Techos: contenedor
  `frigate` 3 GB, `mosquitto` 128 MB, `MemAvailable` del host ≥4 GB, swap del NVR en 0.
- **T7 en el threat model**: agotamiento de memoria del host. Sin límite por contenedor, el
  OOM killer del kernel elige víctima por heurística y puede matar `dnsmasq` — DNS y DHCP de
  toda la casa — en vez de Frigate. DREAD 5.4.
- Observabilidad de memoria: SLIs (`frigate_mem_usage_percent`, `MemAvailable`, swap), dos
  alertas nuevas y el runbook de incidente **I-6 · Presión de memoria**.
- Casos **T-17** (memoria durante los 15 min de T-11) y **T-18** (el `tmpfs` se drena tras un
  export); S-06 pasa a vigilar también la memoria mientras simula el disco lleno.

- Checklists de Gates 2–5 adaptados a un proyecto COTS-configuración (sin código propio).
- `docs/03-implementation/config-baseline.md` (Gate 2): inventario de artefactos, gitGraph de
  ramas y releases, validación de config (equivalente SAST) y cadena de suministro con
  digests (A03).
- `docs/04-testing/test-plan.md` (Gate 3): 16 casos de aceptación + 9 de seguridad,
  C4Container con el alcance de prueba, requirementDiagram con `verifies` y matriz de
  transiciones del segmento (incluidas las que NO deben ocurrir).
- `docs/06-monitoring/observability.md` (Gate 5): SLIs/SLOs trazados a charter y threat
  model, sequence señal→alerta→on-call, stateDiagram del incidente, 5 runbooks y timeline
  al ciclo 2.
- ADR-0005 (observabilidad sobre Node-RED en vez de Prometheus/Grafana, por
  proporcionalidad). En `proposed`: se aprueba al cerrar el Gate 4.

### Cambiado

- `deploy/docker-compose.yml`: `mem_limit` de 3 GB en `frigate` y 128 MB en `mosquitto`.
  El límite se dimensiona a 3 GB y no a 2 porque en cgroup v2 el `tmpfs` (techo 954 MiB) y
  el `shm` (128 MiB) se cargan al cgroup del contenedor: con 2 GB quedarían 966 MiB para
  procesos, sin margen sobre el RSS estimado.
- T1 gana una dimensión que no tenía: **escala a memoria**. El `tmpfs` es donde aterrizan los
  segmentos antes de moverse al HDD, así que un disco lleno impide drenar la caché y esta
  crece en RAM. El acoplamiento T1→T7 es lo que motivó el requisito.

### Spike cerrado — resultado negativo (NVR-SPIKE-002)

- `docs/01-requirements/spike-blinkpy.md`: spike para validar `blinkpy` como vía de recuperar
  los eventos de las Blink Mini y revisarlos a destiempo.
- `spikes/blinkpy/`: script de validación con listado en seco por defecto, descarga
  incremental y despojado de audio en la ingesta. **Aparcado**: no corre en ningún sitio.
- Verificado contra `blinkpy` 0.25.9 instalado: soporta tanto los clips en nube
  (`download_videos`, exige plan de suscripción) como el almacenamiento local del Sync
  Module 2 (`poll_local_storage_manifest`), que **no** lo exige y mantiene el video en casa.
- **Cerrado sin ejecutar**: no hay plan de suscripción ni Sync Module 2, de modo que las
  Blink Mini no generan clips recuperables por ninguna de las dos vías.
- Riesgos identificados para el día que se retome: R1 el audio de las Blink reintroduce lo
  que SR06 excluyó (FL §934.03); R2 la credencial pasa a ser la cuenta Amazon; R3 cliente no
  oficial; R4 dependencia de nube que el charter excluía.

## [0.2.0] - 2026-08-30

**Gate 1 (Design) aprobado.** Arquitectura C4 validada, threat model STRIDE+DREAD con
controles trazables, ADRs y contratos de interfaz.

### Añadido

- `architecture.md` con C4 Container, sequence del flujo detección→evento, stateDiagram
  del segmento de grabación y erDiagram del dominio.
- `threat-model.md` STRIDE + DREAD con controles trazados a ADRs y nftables.
- ADR-0001 (Frigate como NVR), ADR-0002 (placement on-prem en el appliance, PxD por
  proporcionalidad), ADR-0003 (Docker Compose con imagen pineada 0.17.2),
  ADR-0004 (política de retención 3 d continuo / 14 d alertas / 7 d detecciones).
- Contratos de interfaz: tabla de endpoints RTSP / HTTPS / WebRTC / MQTT.
- Artefactos ejecutables: `deploy/docker-compose.yml`, `deploy/frigate/config.yml`,
  `deploy/mosquitto/mosquitto.conf`, `deploy/.env.example`.
- Runbook de despliegue paso a paso (fase 05, hacia Gate 4): cámaras Tapo, Docker, Frigate,
  Mosquitto, verificación VAAPI y endurecimiento de red.

### Cambiado

- **ADR-0002 pasa a `accepted (condicional)`, resolviendo un bloqueo circular.** Estaba
  redactada para aprobarse *"tras medir la CPU real"*, mientras el runbook exigía el Gate 1
  aprobado para ejecutarse: cada uno esperaba al otro y el proyecto no podía avanzar sin
  romper su propia regla. Se separan las dos preguntas que estaban mezcladas — *¿es el sitio
  correcto?* es diseño y se contesta en el Gate 1 (candidato único viable); *¿aguanta la
  carga?* es verificación y se contesta en T-11/T-12 del Gate 3. La ADR lleva ahora su
  condición de revocación escrita.
- **Anonimización para repositorio público**: ninguna IP, MAC ni ubicación real vive en el
  repo. Las IPs de cámara salen del `config.yml` a variables `FRIGATE_CAM1_IP` /
  `FRIGATE_CAM2_IP` en el `.env` gitignorado — el mismo patrón que ya usaban las credenciales
  (SR03), así que no hay tabla de traducción que recordar. Las cámaras pasan a llamarse
  `cam_01` / `cam_02` y los ejemplos usan `192.0.2.0/24` (RFC 5737, reservado para
  documentación). Convención documentada en el README.
- El runbook pasa de `draft` a `ready`: con los Gates 0 y 1 aprobados, es ejecutable.

### Corregido

- `config.yml`: `version` pasa de `0.17-1` (inexistente) a `0.17-0`, que es el
  `CURRENT_CONFIG_VERSION` del tag 0.17.2; un valor futuro se salta las migraciones.
- `go2rtc`: añadido `webrtc.candidates` — sin ellos WebRTC no negocia y la vista en vivo
  degrada a MSE, incumpliendo RF04 (≤2 s) tanto en LAN como por WireGuard.
- `go2rtc`: `#backchannel=0` en los streams de las Tapo para no negociar audio bidireccional.

### Seguridad

- Exclusión explícita de exposición WAN; acceso remoto solo vía WireGuard existente.
- Credenciales RTSP fuera del repo vía variables `FRIGATE_*` en `.env`.
- **SR06 / FL §934.03**: `ffmpeg.output_args.record: preset-record-generic`. El default de
  Frigate es `preset-record-generic-audio-aac`, que graba audio si el stream lo trae; el
  micrófono apagado en la cámara era un control de un único punto de fallo.
- **T5**: los puertos publicados se bindean a `${FRIGATE_LAN_IP}` en vez de `0.0.0.0`.
  Docker publica vía DNAT en `PREROUTING`, así que el `policy drop` de la cadena `input`
  del router no protegía un puerto publicado; las reglas `DOCKER-USER` quedan como segunda
  barrera y no como única.
- **T1**: rotación de logs `json-file` (`max-size: 10m`, `max-file: 3`) en ambos servicios;
  el driver por defecto no rota y compite con la grabación por el disco del router.

## [0.1.0] - 2026-08-30

**Gate 0 (Requirements) aprobado.** Requisitos de seguridad mapeados a ASVS L1, escenarios
de abuso, threat assessment inicial y datos clasificados.

### Añadido

- Charter con mindmap de alcance y glosario de lenguaje ubicuo (DDD).
- Clasificación de datos con regulación aplicable, cifrado y retención por tipo de dato.
- PRD del MVP (`NVR-MVP-001`) con objetivos y no-objetivos, C4 Context, journey del usuario,
  escenarios de abuso A1–A6, requirementDiagram (ASVS L1) y threat assessment inicial
  (DFD + quadrant DREAD).

### Seguridad

- Requisitos SR01–SR06 mapeados a OWASP ASVS L1 y al Top 10.
- Audio deshabilitado por defecto: Florida §934.03 exige consentimiento de todas las partes.
- Blink Mini fuera de alcance: protocolo cloud propietario, sin RTSP/ONVIF.

[Unreleased]: https://github.com/higerotech/fenrir/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/higerotech/fenrir/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/higerotech/fenrir/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/higerotech/fenrir/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/higerotech/fenrir/releases/tag/v0.1.0
