# ADR-0006: Respaldo al NAS iniciado por el NAS (pull), no por el appliance

* **Estado:** proposed (HITL: aprobar al cerrar el Gate 4, con el respaldo ya funcionando)
* **Fecha:** 2026-09-08
* **Decisores:** Jeremi
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0006
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A01 (acceso a la copia), A04 (cifrado en tránsito), A05 (superficie de red)

## Contexto

El charter tiene un riesgo asumido y sin mitigar: *"Fallo del HDD único → pérdida de
grabaciones (sin RAID; asumido en MVP)"*. Hay un NAS disponible en la LAN con espacio.

La propuesta inicial era **rotar** las grabaciones antiguas al NAS por NFS. No es
implementable: **Frigate no tiene almacenamiento por niveles**. Su retención purga, no migra,
y las grabaciones están indexadas en `frigate.db` con sus rutas. Un script externo que mueva
archivos al NAS deja el índice apuntando a rutas muertas: los clips dejan de reproducirse en
la UI y la purga se desincroniza de lo que hay en disco.

Lo que sí cabe es un **respaldo**: copias que Frigate no conoce ni indexa, cuyo propósito no
es ampliar la ventana de retención sino sobrevivir a la muerte del disco. Es importante no
confundir los dos conceptos ni en la documentación ni al hablar de ello: la retención la fija
ADR-0004 y no cambia por esto.

## Decisión

**El NAS tira; el appliance no monta nada.** Una tarea programada en el NAS hace `rsync`
sobre SSH contra el appliance, con una cuenta dedicada de solo lectura restringida por
`command=` en `authorized_keys`.

Qué se copia, y por qué solo eso:

| Origen | Por qué | Tamaño aprox. |
|---|---|---|
| `/srv/frigate/config/` (incluye `frigate.db`) | Es lo que hace reconstruible el sistema; hoy el runbook lo respalda a mano solo antes de upgrades | MB |
| Alertas y snapshots (`media/frigate/clips/`) | Es el material con valor probatorio: lo que querrías tener tras un incidente | ~35 GB |
| Exportados | Ya han sido señalados como relevantes por una persona | Variable |

**El continuo no se copia.** Son 43 GB/día: replicarlo reintroduce por la puerta de atrás el
mismo I/O de red sostenido que descartamos, solo que diferido. Lo que se pierde si muere el
disco es el metraje de contexto, no los eventos.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| **NAS tira por rsync/SSH (elegida)** | El appliance no monta nada: una caída del NAS es invisible para el NVR. Tránsito cifrado. Las credenciales viven en el NAS, no en el router | El NAS necesita poder ejecutar tareas rsync; la clave SSH hay que restringirla bien | Bajo |
| Appliance empuja por NFS | Trivial de montar; es lo que se propuso al principio | Mete un cliente NFS en la máquina que enruta: con montaje *hard*, un stall del NAS bloquea procesos indefinidamente. NFSv3 con `AUTH_SYS` no autentica de verdad y va en claro, así que el video Confidencial cruzaría la LAN sin cifrar | Video en claro + punto de bloqueo en el router |
| Todo el media store en NFS | Capacidad grande, el HDD local descansa | Todo el I/O de grabación pasa a la red. Frigate documenta el aviso *"Unable to keep up with recording segments in cache"* cuando el almacenamiento no da abasto — y si el `tmpfs` no drena, crece hacia sus 954 MiB en RAM: el acoplamiento T1→T7 | Agrava T1, T7 y añade el video en claro |
| RAID en el appliance | Mitiga el disco único sin red | Requiere hardware y reinstalar; el appliance es el router y no se toca a la ligera | Bajo |
| No hacer nada | Cero trabajo | El riesgo del charter sigue asumido y sin mitigar | — |

La opción del NFS-push queda como **plan B explícito** si el NAS no puede iniciar tareas: en
ese caso el montaje debe ser `soft` con `timeo`/`retrans` acotados y usarse **solo** desde el
script de respaldo, nunca desde ninguna ruta que Frigate toque.

## Consecuencias

- Positivas: mitiga el riesgo del HDD único, que era el único riesgo del charter sin control.
  El appliance no gana ninguna dependencia nueva: si el NAS desaparece, el NVR ni se entera.
  El respaldo del `config/` deja de depender de que alguien se acuerde antes de un upgrade.
- Negativas / deuda: **las copias no se ven en la UI de Frigate**. Recuperar algo del NAS es
  abrir una carpeta y reproducir un archivo, no navegar la línea de tiempo. Es el precio de
  que Frigate no tenga niveles, y conviene tenerlo claro antes de confiar en ello.
- Deuda operativa: un respaldo que deja de correr en silencio es peor que no tenerlo, porque
  da una falsa sensación de red de seguridad. De ahí la alerta de frescura en la fase 06.
- Impacto en threat model: introduce **T8** — el NAS pasa a ser una segunda ubicación de video
  Confidencial y hereda su clasificación. Su control de acceso y su cifrado en reposo son
  ahora parte de la postura del NVR, no un asunto aparte.
- Verificación: T-19 (el respaldo corre y un archivo restaurado se reproduce). Sin esa prueba,
  esto es una intención, no un control.
