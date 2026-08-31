# Clasificación de Datos

* **Estado:** approved (Gate 0, 2026-08-30)
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 00-project
* **Versión:** 0.1.0
* **Owner de datos (DPO):** Jeremi (uso doméstico personal)
* **Regulación aplicable:** Uso personal en EE. UU. (Florida). Video en propiedad privada: lícito.
  **Audio: FL Stat. §934.03 exige consentimiento de todas las partes → audio deshabilitado por defecto.**
  Sin GDPR/CCPA aplicables (no actividad comercial).

| Dato | Clasificación | Regulación | Cifrado en reposo | Cifrado en tránsito | Retención |
|---|---|---|---|---|---|
| Video grabado (segmentos, clips) | Confidencial | Privacidad doméstica | No (HDD local, acceso físico controlado) | Parcial: RTSP en claro (LAN); WireGuard al acceder remoto | 3 días continuo / 14 días alertas |
| Snapshots de eventos | Confidencial | — | No | HTTPS-LAN / WireGuard | 14 días |
| Audio | Restringido | FL §934.03 (dos partes) | — | — | **No se captura (deshabilitado)** |
| Credenciales RTSP de cámaras | Restringido | — | En `.env` con permisos 600, fuera de git | Solo LAN | Hasta rotación |
| Credenciales UI Frigate / MQTT | Restringido | — | Hash interno Frigate / passwd Mosquitto | LAN / WireGuard | Hasta rotación |
| Metadatos de eventos (MQTT, SQLite) | Interno | — | No | LAN | Igual que eventos |
| Logs de servicios | Interno | — | No | — | Rotación journald/docker |

Niveles: Público < Interno < Confidencial < Restringido.

Notas:
- Las C310 no soportan RTSPS: el video en claro queda aceptado **solo** dentro del trust
  boundary LAN (ver threat model, amenaza T3).
- Si en el futuro se habilita audio, colocar señalización visible y revisar §934.03.
