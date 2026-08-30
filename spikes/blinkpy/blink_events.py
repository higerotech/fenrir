#!/usr/bin/env python3
"""Spike NVR-SPIKE-002 — recupera los eventos de las Blink Mini para revisarlos a destiempo.

Responde la pregunta del spike (docs/01-requirements/spike-blinkpy.md), no entrega
funcionalidad. Por defecto NO descarga nada: lista lo que hay y para.

Decisiones de diseño, todas trazadas al doc del spike:
  - Dry-run por defecto (R3): la primera ejecución contra un cliente no oficial no debe
    escribir en disco ni martillear la API.
  - Audio fuera en la ingesta (R1): las Blink Mini graban audio y todo el MVP se diseñó sin
    él por FL 934.03. Hay que pedir --keep-audio a proposito para conservarlo.
  - Credenciales por entorno y token en fichero 600 (R2): es la cuenta Amazon, no una
    cuenta de camara local.
  - Descarga incremental por marca de agua en disco (criterio de exito 4).

Uso:
    python blink_events.py --list                 # que hay ahi fuera (no baja nada)
    python blink_events.py --download --since "2026/08/25 00:00"
    python blink_events.py --download             # incremental desde la ultima vez
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from aiohttp import ClientSession
from blinkpy.auth import Auth
from blinkpy.blinkpy import Blink, BlinkTwoFARequiredError
from blinkpy.helpers.util import json_load

# Verificado contra blinkpy 0.25.9 instalado, no contra el README del proyecto.
TOKEN_FILE = Path(os.environ.get("BLINK_TOKEN_FILE", "~/.blink/token.json")).expanduser()
STATE_FILE = Path(os.environ.get("BLINK_STATE_FILE", "~/.blink/state.json")).expanduser()
MEDIA_DIR = Path(os.environ.get("BLINK_MEDIA_DIR", "/srv/blink/events")).expanduser()

# Un clip de Blink Mini son segundos, no minutos: paginar poco es suficiente y es mas
# amable con una API no oficial (R3).
DEFAULT_PAGES = 3
DEFAULT_DELAY_S = 2


def log(msg: str) -> None:
    print(f"[blink-spike] {msg}", flush=True)


def die(msg: str, code: int = 1) -> None:
    print(f"[blink-spike] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


# --------------------------------------------------------------------------- estado

def read_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def write_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def default_since(state: dict, fallback_days: int) -> str:
    """Reanuda donde lo dejo la ejecucion anterior (criterio de exito 4)."""
    if last := state.get("last_run"):
        # Un solapamiento pequeno evita perder un clip que aterrizo justo en el corte.
        return (datetime.fromisoformat(last) - timedelta(minutes=10)).strftime("%Y/%m/%d %H:%M:%S")
    return (datetime.now() - timedelta(days=fallback_days)).strftime("%Y/%m/%d %H:%M:%S")


# ------------------------------------------------------------------------ auth (R2)

async def connect(session: ClientSession) -> Blink:
    blink = Blink(session=session)

    if TOKEN_FILE.exists():
        log(f"reutilizando sesion de {TOKEN_FILE}")
        blink.auth = Auth(await json_load(str(TOKEN_FILE)), session=session)
    else:
        user = os.environ.get("BLINK_USERNAME")
        password = os.environ.get("BLINK_PASSWORD")
        if not user or not password:
            die(
                "faltan BLINK_USERNAME / BLINK_PASSWORD.\n"
                "  Son las credenciales de la cuenta Amazon: exportalas en la shell "
                "(no las escribas en un fichero del repo) y considera una cuenta "
                "secundaria con las camaras compartidas. Ver R2 del spike."
            )
        log("primer arranque: autenticando con usuario y contrasena")
        blink.auth = Auth({"username": user, "password": password}, no_prompt=True, session=session)

    try:
        await blink.start()
    except BlinkTwoFARequiredError:
        code = input("[blink-spike] codigo 2FA recibido por SMS/email: ").strip()
        await blink.auth.send_auth_key(blink, code)
        await blink.setup_post_verify()

    await blink.save(str(TOKEN_FILE))
    try:
        TOKEN_FILE.chmod(0o600)  # no-op efectivo en Windows; imprescindible en el appliance
    except OSError:
        pass
    log(f"sesion persistida en {TOKEN_FILE} (modo 600)")
    return blink


# ------------------------------------------------------------- inventario y contexto

def report_cameras(blink: Blink) -> None:
    if not blink.cameras:
        log("no se ha detectado ninguna camara en la cuenta")
        return
    log(f"camaras en la cuenta: {len(blink.cameras)}")
    for name, cam in blink.cameras.items():
        log(f"  - {name}  ({cam.product_type or 'tipo desconocido'})")


def report_storage_path(blink: Blink) -> None:
    """Camino A (nube) contra camino B (Sync Module local). Ver el spike."""
    local = [n for n, s in blink.sync.items() if getattr(s, "local_storage", False)]
    if local:
        log(f"CAMINO B disponible: almacenamiento local en {', '.join(local)}")
        log("  El video puede no salir de casa. Es el camino que encaja con el charter.")
    else:
        log("CAMINO A: sin almacenamiento local detectado; los clips vienen de la nube.")
        log("  Si no hay plan de suscripcion activo, no habra clips nuevos que descargar.")


# ------------------------------------------------------------------- audio fuera (R1)

def strip_audio(path: Path) -> bool:
    """Reescribe el clip sin pista de audio. Devuelve True si quedo sin audio."""
    if not shutil.which("ffmpeg"):
        log(f"  AVISO: sin ffmpeg, {path.name} conserva su audio (ver R1)")
        return False
    tmp = path.with_suffix(".noaudio.mp4")
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(path), "-c", "copy", "-an", str(tmp)],
        capture_output=True,
    )
    if proc.returncode != 0 or not tmp.exists():
        log(f"  AVISO: ffmpeg fallo sobre {path.name}: {proc.stderr.decode(errors='replace')[:200]}")
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


def has_audio(path: Path) -> bool | None:
    if not shutil.which("ffprobe"):
        return None
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True,
    )
    return bool(proc.stdout.strip())


# ------------------------------------------------------------------------ operaciones

async def cmd_list(blink: Blink, since: str, pages: int) -> int:
    videos = await blink.get_videos_metadata(since=since, stop=pages)
    if not videos:
        log("no hay eventos en la ventana consultada.")
        log("  Si esperabas que los hubiera, revisa el prerrequisito del spike: los clips")
        log("  en nube exigen plan de suscripcion Blink activo.")
        return 0
    log(f"{len(videos)} eventos desde {since}:")
    for v in videos:
        log(f"  {v.get('created_at', '?')}  {v.get('device_name', '?'):<20} id={v.get('id', '?')}")
    return len(videos)


async def cmd_download(blink: Blink, since: str, pages: int, delay: int, keep_audio: bool) -> int:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in MEDIA_DIR.glob("*.mp4")}

    # blinkpy no vuelve a escribir un fichero que ya existe: la marca de agua es el disco.
    await blink.download_videos(str(MEDIA_DIR), since=since, stop=pages, delay=delay)

    nuevos = sorted(p for p in MEDIA_DIR.glob("*.mp4") if p.name not in before)
    log(f"clips nuevos: {len(nuevos)}")

    for p in nuevos:
        if keep_audio:
            log(f"  {p.name}  (audio CONSERVADO por --keep-audio; decision legal consciente)")
            continue
        ok = strip_audio(p)
        estado = "sin audio" if ok else "AUDIO PRESENTE"
        log(f"  {p.name}  {p.stat().st_size // 1024} KB  [{estado}]")

    # Criterio de exito 5: verificar, no asumir. Y distinguir "no tiene audio" de
    # "no he podido comprobarlo": tratar lo segundo como lo primero seria afirmar que
    # el control legal esta cubierto sin haberlo mirado.
    if nuevos and not keep_audio:
        veredictos = {p.name: has_audio(p) for p in nuevos}
        con_audio = [n for n, v in veredictos.items() if v is True]
        sin_verificar = [n for n, v in veredictos.items() if v is None]
        if con_audio:
            log(f"AVISO R1: {len(con_audio)} clips conservan audio. Revisar antes de darlos por buenos.")
        if sin_verificar:
            log(f"R1 SIN VERIFICAR: {len(sin_verificar)} clips, falta ffprobe en este host.")
            log("  No se puede afirmar que cumplan SR06. Instalar ffmpeg y reejecutar la comprobacion.")
        if not con_audio and not sin_verificar:
            log("verificado: ningun clip almacenado tiene pista de audio (R1 cubierto).")
    return len(nuevos)


# ------------------------------------------------------------------------------ main

async def main() -> int:
    ap = argparse.ArgumentParser(description="Spike: eventos de Blink Mini a disco local.")
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--list", action="store_true", help="solo listar (por defecto)")
    modo.add_argument("--download", action="store_true", help="descargar a BLINK_MEDIA_DIR")
    ap.add_argument("--since", help='ventana, ej "2026/08/25 00:00". Por defecto, incremental')
    ap.add_argument("--days", type=int, default=2, help="dias hacia atras en la primera ejecucion")
    ap.add_argument("--pages", type=int, default=DEFAULT_PAGES, help="paginas de la API (~25 items)")
    ap.add_argument("--delay", type=int, default=DEFAULT_DELAY_S, help="segundos entre descargas")
    ap.add_argument("--keep-audio", action="store_true",
                    help="NO quitar el audio. Ver R1 del spike y FL 934.03 antes de usarlo")
    args = ap.parse_args()

    state = read_state()
    since = args.since or default_since(state, args.days)

    async with ClientSession() as session:
        blink = await connect(session)
        await blink.refresh(force=True)
        report_cameras(blink)
        report_storage_path(blink)

        if args.download:
            n = await cmd_download(blink, since, args.pages, args.delay, args.keep_audio)
            state["last_run"] = datetime.now().isoformat(timespec="seconds")
            state["last_count"] = n
            write_state(state)
        else:
            await cmd_list(blink, since, args.pages)
            log("modo listado: no se ha escrito nada. Anade --download para bajar los clips.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(130)
