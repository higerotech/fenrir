#!/bin/sh
# Snapshot consistente de frigate.db — se ejecuta EN EL APPLIANCE, por cron, poco antes
# de que el NAS tire (ADR-0006).
#
# Por qué existe este script en vez de dejar que rsync copie frigate.db directamente:
# rsync sobre una SQLite viva puede producir un fichero roto. Frigate escribe en la base
# mientras se copia, así que el resultado puede ser una copia a medias — y una copia rota
# es el peor tipo de respaldo, porque parece que lo tienes hasta el día que lo necesitas.
# `.backup` usa la API de backup en línea de SQLite, que sí es consistente con un escritor
# activo.
set -eu

CONFIG_DIR="${FRIGATE_CONFIG_DIR:-/srv/frigate/config}"
DB="$CONFIG_DIR/frigate.db"
SNAP="$CONFIG_DIR/frigate.db.backup"

log() { echo "[snapshot-db] $*"; }
die() { echo "[snapshot-db] ERROR: $*" >&2; exit 1; }

[ -f "$DB" ] || die "no existe $DB"
command -v sqlite3 >/dev/null 2>&1 || die "falta sqlite3 (apt-get install -y sqlite3)"

# A un fichero temporal y luego mv: el rename es atómico dentro del mismo sistema de
# ficheros, así que el NAS nunca puede tirar de un snapshot a medio escribir.
tmp="$SNAP.tmp.$$"
trap 'rm -f "$tmp"' EXIT INT TERM

sqlite3 "$DB" ".backup '$tmp'" || die "sqlite3 .backup fallo"

# Comprobar antes de publicarlo: un snapshot corrupto no debe reemplazar al anterior,
# que quizas si estaba bien.
if [ "$(sqlite3 "$tmp" 'PRAGMA integrity_check;' 2>/dev/null)" != "ok" ]; then
    die "el snapshot no pasa integrity_check; se conserva el anterior"
fi

mv "$tmp" "$SNAP"
trap - EXIT INT TERM
chmod 640 "$SNAP"

log "ok: $SNAP ($(du -h "$SNAP" | cut -f1))"
