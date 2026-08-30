# Spike — `blinkpy` para recuperar eventos de las Blink Mini

* **Estado:** draft (spike en curso, sin decisión tomada)
* **Fecha:** 2026-08-30
* **Decisores:** Jeremi
* **Fase AI-DLC:** 01-requirements
* **Versión:** 0.1.0
* **Gate:** 0 (del ciclo 2 — **no** modifica el Gate 0 del MVP)
* **Feature/Épica ID:** NVR-SPIKE-002
* **Time box:** 1 sesión de trabajo

## Por qué esto es un spike y no una funcionalidad

Las Blink Mini están en **no-scope explícito** del charter: *"sin RTSP/ONVIF ni workaround
mantenido (protocolo cloud propietario de Amazon); permanecen en la app Blink"*. Ese no-scope
sigue vigente hasta que este spike lo desmienta con evidencia.

Un spike no entrega funcionalidad: entrega una **respuesta**. Al terminar, o se abre una ADR
que cambia el no-scope del charter, o se anota el resultado negativo y las Blink siguen fuera.
Lo que no puede pasar es que el código del spike se quede en producción sin esa decisión.

## Pregunta a responder

¿Se pueden descargar de forma fiable y desatendida los clips de evento que las Blink Mini
generan, para revisarlos a destiempo junto al resto del material del NVR, sin romper ninguna
de las premisas del proyecto (privacidad, legalidad del audio, no degradar el router)?

## Alcance del spike

- **Incluye:** autenticación con la cuenta Blink/Amazon, listado de eventos disponibles,
  descarga a disco, y medir cuánto cuesta en tiempo, espacio y llamadas a la API.
- **No incluye:** vista en vivo de las Blink, integración con la UI de Frigate (Frigate ingiere
  RTSP, no archivos: no hay forma de meter estos clips en su línea de tiempo), ni automatizar
  nada en Node-RED. Eso serían decisiones posteriores a la respuesta.

## Prerrequisito que decide si el spike es siquiera posible

Blink **exige plan de suscripción para almacenar clips en la nube**. Sin plan y sin
almacenamiento local, la grabación en nube se detiene y no hay nada que descargar: los clips
que ya estén guardados siguen visibles en la app, pero deja de generarse material nuevo.

Eso deja dos caminos, y `blinkpy` 0.25.9 soporta los dos:

| Camino | Requisito | Qué implica |
|---|---|---|
| **A — Clips en la nube** | Plan de suscripción Blink activo | `download_videos()`. El video vive en Amazon y se trae a casa |
| **B — Almacenamiento local** | Sync Module 2 + USB (o XR/XR+ con microSD) | `poll_local_storage_manifest()` + `LocalStorageMediaItem.download_video()`. **El video nunca sale de casa** |

**El camino B es estratégicamente mejor** y encaja con la visión del charter (*"sin dependencia
de nubes de terceros"*): el clip se genera y se guarda en el Sync Module, y el appliance lo
recoge por LAN. El camino A contradice esa visión aunque funcione.

**Primera pregunta a contestar, antes de escribir una línea más:** ¿hay plan de suscripción
activo, hay Sync Module 2 con USB, ninguno de los dos, o ambos? Si la respuesta es "ninguno",
el spike termina aquí con un resultado negativo y las Blink se quedan en no-scope hasta que se
reemplacen.

## Riesgos que este spike introduce y que hay que evaluar, no ignorar

### R1 — El audio vuelve por la puerta de atrás (crítico)

Es el hallazgo más importante y el más fácil de pasar por alto. Todo el MVP se diseñó sin
audio de forma deliberada: micrófono apagado en las Tapo, `preset-record-generic` en Frigate,
SR06 trazado a FL §934.03 (Florida exige consentimiento de todas las partes).

**Las Blink Mini graban audio en sus clips.** Descargarlos y guardarlos en el appliance mete
en casa exactamente el material que el diseño excluyó a conciencia. Un clip de la nube no es
menos audio que uno grabado en local.

Mitigación obligatoria en el spike: **quitar la pista de audio en la ingesta**, antes de que
el archivo se considere almacenado. El script lo hace por defecto y exige `--keep-audio`
explícito para no hacerlo. Si se opta por conservar audio, es una decisión legal consciente
que necesita su propia ADR y señalización visible, no un flag por descuido.

### R2 — Credenciales de la cuenta Amazon en el appliance

Las cuentas de cámara Tapo son locales y de alcance mínimo: si se filtran, se ve video.
La cuenta Blink **es la cuenta Amazon**, con métodos de pago, historial de pedidos y el resto
del ecosistema detrás. Es una credencial de valor mucho más alto que cualquiera del MVP, y el
token de sesión que `blinkpy` persiste vale tanto como ella.

Clasificación: **Restringido**, por encima de las credenciales RTSP. Fichero en modo 600,
fuera del repo, y si el spike prospera, lo suyo es una cuenta Amazon secundaria con las Blink
compartidas, no la cuenta principal.

### R3 — Cliente no oficial

`blinkpy` es un cliente de ingeniería inversa; no hay API pública de Blink. Amazon puede
cambiar el protocolo sin aviso, y un patrón de acceso automatizado puede disparar sus
controles antifraude. Consecuencias a asumir: la integración puede romperse en cualquier
momento y hay riesgo no nulo de fricción con la cuenta. De ahí el `delay` entre llamadas.

### R4 — Dependencia de nube en un proyecto que la excluyó

El charter dice *"sin dependencia de nubes de terceros"*. El camino A la reintroduce. No es
descalificante —las Blink ya son cloud hoy, así que no se pierde nada que no estuviera
perdido— pero si se adopta, la visión del charter necesita un matiz honesto: *"sin dependencia
de nube para las cámaras propias; las Blink siguen siendo cloud hasta su reemplazo"*.

## Criterios de éxito

El spike se considera **exitoso** si, dentro del time box:

1. La autenticación funciona y sobrevive a un reinicio sin volver a pedir el 2FA.
2. Se listan los eventos disponibles con su marca de tiempo y cámara.
3. Se descargan al menos 5 clips reales, íntegros y reproducibles.
4. Una segunda ejecución es **incremental**: no vuelve a bajar lo que ya tiene.
5. Los clips almacenados **no tienen pista de audio** (verificable con `ffprobe`).
6. El coste es despreciable para el appliance: sin carga sostenida de CPU y con espacio acotado.

Se considera **fallido, y las Blink siguen en no-scope**, si: no hay plan ni Sync Module; la
autenticación exige intervención manual en cada ejecución; o la API resulta demasiado
inestable para confiar en ella sin vigilancia.

## Qué cambiaría si sale bien

Nada se toca hasta que la respuesta esté. Si el spike es exitoso, lo que se abre es:

- ADR-0006 con la decisión (camino A o B), sus alternativas y sus consecuencias.
- Charter: sacar las Blink Mini del no-scope y matizar la visión (R4).
- `data-classification.md`: dos entradas nuevas — credenciales de cuenta Amazon (Restringido)
  y clips de Blink (Confidencial, con su retención propia).
- `threat-model.md`: R2 y R3 como amenazas con su puntuación DREAD.
- PRD del ciclo 2: el requisito funcional de la recuperación de eventos.

Y una pregunta que quedará abierta y que conviene tener presente desde ya: **dónde se miran
estos clips**. Frigate no los puede mostrar —ingiere RTSP, no archivos—, así que acaban en un
directorio, y revisarlos "a destiempo" significa abrir una carpeta, no la UI del NVR. Si eso
resulta incómodo en la práctica, el valor real del spike es menor de lo que parece sobre el
papel, y quizá el dinero esté mejor puesto en reemplazar las Blink por cámaras ONVIF, que es
justo lo que el charter ya anticipaba.
