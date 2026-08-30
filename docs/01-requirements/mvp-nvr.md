# PRD — MVP NVR: despliegue Frigate + cámaras ONVIF

* **Estado:** approved (Gate 0, 2026-08-30)
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 01-requirements
* **Versión:** 0.1.0
* **Gate:** 0
* **Feature/Épica ID:** NVR-MVP-001
* **Nivel ASVS objetivo:** L1

## Problema y contexto
Las cámaras del hogar están fragmentadas: 2× Tapo C310 (RTSP/ONVIF, visibles solo en la
app Tapo) y 2× Blink Mini (cloud Amazon, sin acceso local). No hay grabación continua
propia, ni retención controlada, ni eventos integrables con el stack IoT (MQTT/Node-RED)
que corre en el appliance de red. Se necesita un concentrador local tipo DVR con
monitoreo casi en tiempo real y capacidad de ampliar cámaras.

## Objetivos / No-objetivos
- **Objetivos:** NVR local con Frigate; ingesta de las 2 C310; DVR continuo con retención;
  vista en vivo ≤2 s; detección de persona/vehículo; eventos por MQTT; cero exposición WAN.
- **No-objetivos:** integrar Blink Mini (técnicamente inviable: sin RTSP ni workaround
  mantenido); Coral/GPU; búsqueda semántica (sin AVX2); Home Assistant; audio (legal FL).

## Contexto del sistema (C4 Context)

```mermaid
C4Context
    title Contexto — NVR Doméstico Frigate

    Person(jeremi, "Jeremi", "Administra el NVR y revisa grabaciones")
    Person(hogar, "Miembro del hogar", "Consulta vista en vivo y clips")

    Enterprise_Boundary(lan, "LAN doméstica (trust boundary nftables)") {
        System(nvr, "NVR Doméstico Frigate", "Ingiere RTSP, graba, detecta objetos y publica eventos")
        System_Ext(camaras, "2x Tapo C310", "Cámaras IP RTSP/ONVIF con cuenta local")
        System_Ext(nodered, "Node-RED + stack IoT", "Consume eventos MQTT para automatizaciones")
    }

    System_Ext(wg, "Cliente WireGuard remoto", "Acceso remoto cifrado del propio Jeremi")
    System_Ext(tapocloud, "Nube TP-Link Tapo", "Solo gestión por app; bloqueable por egress", $tags="external")

    Rel(jeremi, nvr, "Administra y revisa", "HTTPS 8971 LAN")
    Rel(hogar, nvr, "Ve en vivo", "WebRTC 8555 LAN")
    Rel(nvr, camaras, "Ingiere video de", "RTSP 554 en claro")
    Rel(nvr, nodered, "Publica eventos a", "MQTT 1883")
    Rel(wg, nvr, "Accede vía túnel a", "WireGuard UDP")
    Rel(camaras, tapocloud, "Telemetría opcional a", "TLS saliente")

    UpdateElementStyle(nvr, $bgColor="#1168bd", $fontColor="#ffffff")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Usuarios y escenarios

### Journey del usuario

```mermaid
journey
    title Revisar un evento de movimiento en una camara
    section Notificación
      Frigate detecta persona: 4: Sistema
      Node-RED notifica por MQTT: 4: Sistema
    section Revisión
      Abre UI Frigate (LAN o WireGuard): 5: Jeremi
      Ve clip y snapshot del evento: 5: Jeremi
    section Seguimiento
      Exporta clip si es relevante: 4: Jeremi
      Segmento expira según retención: 5: Sistema
```

### Escenarios positivos
1. Grabación 24/7 de ambas C310 con purga automática por retención.
2. Persona entra al encuadre → evento con clip/snapshot → mensaje en `frigate/events`.
3. Vista en vivo desde el móvil por WireGuard con latencia ≤2 s.
4. Alta de una tercera cámara ONVIF editando solo `config.yml` (ampliable).

### Escenarios negativos / abuso (requerido por Gate 0)
- **A1 — Acceso no autorizado a la UI:** un invitado de la LAN intenta abrir la UI del
  NVR → la autenticación de Frigate (puerto 8971) lo bloquea; el puerto 5000 interno no
  se publica.
- **A2 — Exposición WAN accidental:** un error de compose publica puertos en las
  interfaces WAN → nftables (default drop en WAN input) actúa como segunda barrera.
- **A3 — Cámara comprometida como pivote:** una C310 vulnerada intenta escanear la LAN o
  exfiltrar a internet → regla de egress que aísla a las cámaras (solo puede hablarle el
  NVR; salida a internet bloqueada).
- **A4 — DoS por disco lleno:** la grabación llena el HDD y tumba servicios del router →
  media en ruta dedicada + retención con purga + alerta de watermark.
- **A5 — Robo de credenciales RTSP:** las credenciales viajan en claro por RTSP → cuentas
  de cámara dedicadas (no la cuenta TP-Link), alcance limitado a la LAN, rotación.
- **A6 — Captura de audio ilegal:** grabar audio sin consentimiento infringe FL §934.03 →
  audio deshabilitado en cámara y en Frigate.

## Requisitos funcionales
| ID | Requisito |
|---|---|
| RF01 | Ingerir RTSP de las 2 C310 (stream1 grabación, stream2 detección) |
| RF02 | Grabación continua con retención de 3 días y 14 días para alertas |
| RF03 | Detectar persona y vehículo con CPU sobre el sub-stream a 5 fps |
| RF04 | Vista en vivo ≤2 s vía go2rtc (WebRTC) |
| RF05 | Publicar eventos en MQTT (`frigate/events`) consumibles por Node-RED |
| RNF01 | CPU sostenida del NVR <50 % para no degradar el enrutamiento |
| RNF02 | Decodificación por hardware VAAPI (i965) |

## Trazabilidad de requisitos

```mermaid
requirementDiagram
    requirement RF01 {
      id: RF01
      text: Ingesta RTSP de ambas C310
      risk: medium
      verifymethod: test
    }
    requirement RF02 {
      id: RF02
      text: DVR continuo con retencion y purga
      risk: high
      verifymethod: test
    }
    requirement RF05 {
      id: RF05
      text: Eventos publicados en MQTT
      risk: medium
      verifymethod: test
    }
    requirement SR01 {
      id: SR01
      text: UI solo autenticada y sin exposicion WAN
      risk: high
      verifymethod: inspection
    }
    element Frigate {
      type: "servicio"
    }
    element Mosquitto {
      type: "servicio"
    }
    element Nftables {
      type: "control de red"
    }
    element VerifDespliegue {
      type: "prueba"
    }
    Frigate - satisfies -> RF01
    Frigate - satisfies -> RF02
    Mosquitto - satisfies -> RF05
    Nftables - satisfies -> SR01
    VerifDespliegue - verifies -> RF01
    VerifDespliegue - verifies -> RF02
    VerifDespliegue - verifies -> SR01
```

## Requisitos de seguridad (mapeados a OWASP ASVS)
| Req | ASVS | Nivel | OWASP Top 10 |
|---|---|---|---|
| SR01: UI autenticada (8971), puerto 5000 no publicado | V2.1 Autenticación | L1 | A01, A07 |
| SR02: cero puertos NVR alcanzables desde WAN (nftables) | V13 Config de red | L1 | A05 |
| SR03: credenciales en `.env` (600), nunca en git | V6 Secretos | L1 | A02 |
| SR04: cámaras aisladas (egress deny a internet) | V13 | L1 | A05 |
| SR05: imagen pineada `0.17.2` (sin `latest`/`stable`) | V14 Integridad | L1 | A08 |
| SR06: audio deshabilitado (FL §934.03) | — legal | — | — |

## Threat assessment inicial

```mermaid
flowchart LR
    WG([Cliente WireGuard]) -->|"UDP cifrado"| FW
    subgraph LAN [Trust boundary: LAN nftables]
      FW[Appliance router] --> NVR[Frigate NVR]
      CAM1[C310 num 1] -->|"RTSP en claro"| NVR
      CAM2[C310 num 2] -->|"RTSP en claro"| NVR
      NVR -->|"eventos"| MQTT[(Mosquitto)]
      MQTT --> NR[Node-RED]
      NVR --> HDD[(Media HDD)]
    end
    CAM1 -.->|"TLS saliente, bloqueable"| CLOUD([Nube Tapo])
```

```mermaid
quadrantChart
    title DREAD inicial — MVP NVR
    x-axis Baja probabilidad --> Alta probabilidad
    y-axis Bajo impacto --> Alto impacto
    quadrant-1 Atender ya
    quadrant-2 Monitorear
    quadrant-3 Aceptar
    quadrant-4 Planear
    Exposicion WAN accidental: [0.3, 0.9]
    Disco lleno DoS: [0.7, 0.7]
    Camara comprometida pivote: [0.4, 0.7]
    Acceso UI no autorizado LAN: [0.35, 0.6]
    RTSP en claro sniffing LAN: [0.25, 0.45]
    Saturacion CPU router: [0.6, 0.6]
```

## Métricas de éxito
Las del charter, más: evento visible en `frigate/events` <3 s tras la detección;
purga verificada al alcanzar la retención.

## Dependencias y riesgos
- Depende de: reservas DHCP en dnsmasq para las cámaras; Docker instalado; HDD con
  ≥200 GB libres para media.
- Riesgo abierto: rendimiento real del detector CPU en Ivy Bridge — medir en despliegue
  y, si excede presupuesto, bajar fps de detección o planificar acelerador (ciclo 2).
