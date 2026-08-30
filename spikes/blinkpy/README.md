# Spike NVR-SPIKE-002 — eventos de Blink Mini con `blinkpy`

> **APARCADO — 2026-08-30.** El spike se cerró con **resultado negativo**: no hay plan de
> suscripción Blink ni Sync Module 2, así que las Blink Mini no generan clips recuperables
> por ninguna vía. Este código **no corre en ningún sitio** y no es dependencia de nada.
> Solo vuelve a la mesa si se compra un Sync Module 2 (camino B). Ver el
> [resultado del spike](../../docs/01-requirements/spike-blinkpy.md#resultado).

Código de **spike**, no de producción. Responde la pregunta de
[`docs/01-requirements/spike-blinkpy.md`](../../docs/01-requirements/spike-blinkpy.md) y se
borra o se promueve según el resultado. Las Blink Mini siguen en el no-scope del charter
hasta que este spike lo cambie con evidencia.

## Antes de ejecutar

**Comprueba el prerrequisito.** Blink exige plan de suscripción para guardar clips en la
nube. Sin plan y sin Sync Module 2 con USB, no hay nada que descargar y el spike termina
con un resultado negativo. El script te lo dirá en el primer arranque (`CAMINO A` / `CAMINO B`).

Instala en un entorno aislado, nunca en el Python del sistema del appliance:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

`ffmpeg` es obligatorio: sin él no se puede quitar el audio ni verificar que no está.

## Credenciales

Son las de tu cuenta **Amazon**, no una cuenta de cámara local. Valen mucho más que
cualquier credencial del MVP (R2 del spike). No las escribas en ningún archivo del repo:

```bash
read -s -p "usuario: " BLINK_USERNAME; export BLINK_USERNAME
read -s -p "clave: "   BLINK_PASSWORD; export BLINK_PASSWORD
```

Tras el primer login con 2FA, la sesión queda en `~/.blink/token.json` en modo 600 y las
variables ya no hacen falta. **Ese fichero vale lo mismo que la contraseña**: trátalo como
Restringido y no lo respaldes en sitios donde no pondrías tu clave de Amazon.

Si el spike prospera, lo correcto es una cuenta Amazon secundaria con las cámaras
compartidas, no la principal.

## Uso

```bash
# 1. Qué hay ahí fuera. No escribe nada en disco. Empieza siempre por aquí.
python blink_events.py --list --days 7

# 2. Descargar. El audio se quita en la ingesta salvo que pidas lo contrario.
export BLINK_MEDIA_DIR=/srv/blink/events
python blink_events.py --download --since "2026/08/25 00:00"

# 3. Ejecuciones siguientes: incremental, reanuda donde lo dejó.
python blink_events.py --download
```

| Variable | Por defecto | Para qué |
|---|---|---|
| `BLINK_USERNAME` / `BLINK_PASSWORD` | — | Solo en el primer login |
| `BLINK_TOKEN_FILE` | `~/.blink/token.json` | Sesión persistida (600) |
| `BLINK_STATE_FILE` | `~/.blink/state.json` | Marca de agua de la descarga incremental |
| `BLINK_MEDIA_DIR` | `/srv/blink/events` | Destino de los clips |

## El audio no es un detalle

Las Blink Mini graban audio. Todo el MVP se diseñó sin él a propósito —micrófonos apagados,
`preset-record-generic` en Frigate, SR06 trazado a FL §934.03— y bajarse clips de la nube
mete en casa exactamente ese material.

Por eso el script quita la pista de audio antes de dar el clip por almacenado, y luego
**verifica con `ffprobe` que efectivamente no está**. Si no puede verificarlo lo dice en voz
alta en vez de callarse: un "no lo he comprobado" no es un "está limpio".

`--keep-audio` existe, pero usarlo es una decisión legal consciente que necesita su propia
ADR y señalización visible. No es un flag de conveniencia.

## Qué anotar durante la ejecución

Los criterios de éxito están en el doc del spike. Lo que hay que medir:

1. ¿Sobrevive la sesión a un reinicio sin volver a pedir el 2FA?
2. ¿Cuántos clips hay por día y cuánto ocupan? (dimensiona la retención si se adopta)
3. ¿La segunda ejecución baja solo lo nuevo?
4. ¿Quedan todos sin audio?
5. ¿Cuánto tarda y cuánta CPU consume en el appliance? Compite con el enrutamiento (T2).

Y la pregunta cualitativa, que es la que de verdad decide: **revisar estos clips abriendo
una carpeta, en vez de la línea de tiempo del NVR, ¿resulta útil o incómodo?** Frigate no
puede mostrarlos: ingiere RTSP, no archivos. Si la respuesta es "incómodo", el spike ha
salido técnicamente bien y la conclusión sigue siendo reemplazar las Blink por cámaras
ONVIF, que es lo que el charter ya anticipaba.
