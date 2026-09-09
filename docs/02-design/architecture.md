# Diseño del Sistema — NVR Doméstico Frigate

* **Estado:** approved (Gate 1, 2026-08-30)
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 0.1.0
* **Gate:** 1
* **Estilo arquitectónico:** Servicios COTS contenedorizados sobre host compartido (sin código propio)
* **ADRs relacionadas:** ADR-0001, ADR-0002, ADR-0003

## Contextos acotados (DDD)
| Bounded Context | Responsabilidad | Entidades núcleo |
|---|---|---|
| Vigilancia | Ingesta, grabación, detección, eventos | Cámara, Segmento, Evento |
| Red doméstica | Transporte, aislamiento, acceso remoto | Reserva DHCP, reglas nftables, peer WireGuard |

## Vista C4 — Container

```mermaid
C4Container
    title Contenedores — NVR sobre el appliance compartido

    Person(jeremi, "Jeremi", "Admin y usuario")
    System_Ext(cam1, "Tapo C310 num 1", "RTSP 554 / ONVIF 2020")
    System_Ext(cam2, "Tapo C310 num 2", "RTSP 554 / ONVIF 2020")
    System_Ext(nodered, "Node-RED", "Automatizaciones IoT")

    System_Boundary(host, "Appliance i3-3240 (Ubuntu 24.04, tambien router)") {
        Container(frigate, "Frigate 0.17.2", "Docker, Python/ffmpeg, VAAPI i965", "NVR: go2rtc + detector CPU + grabador", $tags="owasp-a01")
        Container(mosquitto, "Mosquitto 2", "Docker, MQTT", "Broker de eventos con auth por password")
        ContainerDb(media, "Media store", "HDD SATA /srv/fenrir/media", "Segmentos, clips y snapshots (Confidencial)")
        ContainerDb(cfgdb, "Config + SQLite", "/srv/fenrir/config", "config.yml, frigate.db, credenciales UI")
    }

    Rel(cam1, frigate, "Envia stream1 y stream2 a", "RTSP en claro")
    Rel(cam2, frigate, "Envia stream1 y stream2 a", "RTSP en claro")
    Rel(frigate, media, "Escribe segmentos en", "ext4 local")
    Rel(frigate, cfgdb, "Lee config y persiste metadatos en", "ext4 local")
    Rel(frigate, mosquitto, "Publica eventos en", "MQTT 1883 auth")
    Rel(nodered, mosquitto, "Se suscribe a frigate/# en", "MQTT 1883 auth")
    Rel(jeremi, frigate, "Usa UI autenticada de", "HTTPS 8971 / WebRTC 8555")

    UpdateElementStyle(frigate, $bgColor="#1168bd", $fontColor="#ffffff")
    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

Nota C4 Component: los internos de Frigate (go2rtc, detector, recorder) son COTS y su
descomposición no aporta decisiones propias; se omite por la regla anti-ruido. El
`classDiagram` (Code) no aplica: el MVP es configuración, no desarrollo.

## Flujos críticos (comportamiento)

```mermaid
sequenceDiagram
    autonumber
    participant C as C310 (stream2 640x360)
    participant G as go2rtc/ffmpeg (VAAPI)
    participant D as Detector CPU
    participant R as Grabador
    participant M as Mosquitto
    participant N as Node-RED
    C->>G: RTSP sub-stream 5 fps
    G->>D: frames con movimiento
    D->>D: inferencia persona/vehiculo
    alt objeto confirmado
        D->>R: marca evento (clip + snapshot)
        D->>M: publish frigate/events (JSON)
        M->>N: notifica suscriptores
    else sin objeto
        D-->>G: descarta frames
    end
    Note over R: stream1 1080p se graba 24/7 en paralelo
```

## Ciclo de vida de la entidad núcleo (Segmento de grabación)

```mermaid
stateDiagram-v2
    [*] --> Grabando
    Grabando --> Continuo: cierre de segmento sin evento
    Grabando --> Evento: solapa una deteccion
    Continuo --> Purgado: retencion 5 dias
    Evento --> Purgado: retencion 14 dias (alertas)
    Evento --> Exportado: Jeremi exporta clip
    Exportado --> [*]
    Purgado --> [*]
```

## Modelo de datos y dominio

```mermaid
erDiagram
    CAMARA ||--o{ SEGMENTO : produce
    CAMARA ||--o{ EVENTO : origina
    EVENTO ||--o{ SEGMENTO : "se solapa con"
    CAMARA { string nombre  string ip  string rol_streams }
    SEGMENTO { datetime inicio  int duracion_s  string ruta  string modo_retencion }
    EVENTO { string id  string etiqueta  float score  datetime inicio  datetime fin }
```

## Contratos de API (interfaces del sistema)
| Interfaz | Endpoint | Protocolo | AuthN/Z | Consumidor |
|---|---|---|---|---|
| Ingesta principal | `rtsp://<user>:<pass>@<ip-cam>:554/stream1` | RTSP | Cuenta local de cámara | Frigate (rol record vía go2rtc) |
| Ingesta detección | `rtsp://<user>:<pass>@<ip-cam>:554/stream2` | RTSP | Cuenta local de cámara | Frigate (rol detect) |
| UI + API | `https://<ip-lan>:8971/` | HTTPS | Login Frigate (admin generado al primer arranque) | Jeremi / hogar |
| Restream | `rtsp://<ip-lan>:8554/<camara>` | RTSP | go2rtc | Consumidores LAN (VLC) |
| Vivo baja latencia | `:8555` TCP/UDP | WebRTC | Sesión UI | Navegador/móvil (requiere `go2rtc.webrtc.candidates`; sin ellos degrada a MSE y RF04 no se cumple) |
| Eventos | topic `frigate/events` | MQTT | usuario/clave Mosquitto | Node-RED |
| Disponibilidad | topic `frigate/available` | MQTT | ídem | Node-RED (watchdog) |

Puerto 5000 (API interna sin auth): **no publicado** fuera del contenedor.

## Patrones de seguridad seleccionados (por amenaza DREAD priorizada)
| Amenaza | Patrón / Control | OWASP |
|---|---|---|
| Exposición WAN accidental | Defensa en profundidad: bind de los puertos publicados a la IP LAN (primario) + `DOCKER-USER`/default-drop nftables (secundario) | A05 |
| Disco lleno (DoS) | Cuota implícita por retención + purga automática + watermark monitorizado | A05 |
| Cámara comprometida | Segmentación: egress deny de cámaras a internet y a la LAN salvo NVR | A05 |
| Acceso UI no autorizado | AuthN nativa Frigate en 8971; 5000 solo loopback del contenedor | A01/A07 |
| Secretos en repo | `.env` fuera de git + sustitución `FRIGATE_*` en config | A02 |
| Captura de audio ilegal (SR06) | Doble control: micrófono off en cámara + `preset-record-generic` (graba sin pista de audio) | — legal |
| Supply chain imagen | Tag pineado `0.17.2` + revisión de release notes antes de subir | A08 |
