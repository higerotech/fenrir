#!/bin/sh
# Respaldo del NVR — se ejecuta EN EL NAS, por cron (ADR-0006).
#
# El NAS tira; el appliance no monta nada. Así una caída del NAS es invisible para el NVR
# y el tránsito va cifrado, en vez de por una export NFS con AUTH_SYS.
#
# Configuración por entorno: este repositorio es público y no lleva ni un dato real.
# Ponerlos en /etc/nvr-backup.env con permisos 600.
#
#   NVR_HOST=<ip-o-nombre-del-appliance>
#   NVR_USER=nvrbackup
#   NVR_KEY=/ruta/a/la/clave/privada
#   NVR_DEST=/volumen/backups/nvr
set -eu

# shellcheck disable=SC1091
[ -f /etc/nvr-backup.env ] && . /etc/nvr-backup.env

NVR_HOST="${NVR_HOST:?falta NVR_HOST}"
NVR_USER="${NVR_USER:-nvrbackup}"
NVR_KEY="${NVR_KEY:?falta NVR_KEY}"
NVR_DEST="${NVR_DEST:?falta NVR_DEST}"
LOCK="${NVR_LOCK:-/tmp/nvr-backup.lock}"
STAMP="$NVR_DEST/.last-success"

log() { echo "$(date -Is) [nvr-backup] $*"; }
die() { echo "$(date -Is) [nvr-backup] ERROR: $*" >&2; exit 1; }

# Sin lock, una ejecución lenta se solapa con la siguiente y acaban compitiendo por el
# mismo destino. mkdir es atómico en cualquier sistema de ficheros POSIX.
if ! mkdir "$LOCK" 2>/dev/null; then
    die "ya hay un respaldo en curso ($LOCK). Si es un resto de una ejecución muerta, borrarlo."
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM

SSH="ssh -i $NVR_KEY -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new"

# Sin --delete a propósito: el NAS conserva lo que Frigate ya purgó, que es justamente
# el motivo de tener respaldo. La contrapartida es que el destino crece sin límite y el
# NAS necesita su propia política de retención (ver README).
RSYNC_OPTS="-a --partial --human-readable --stats"

# Las rutas son relativas al root de rrsync (`command="rrsync -ro /srv/frigate"`).
# Si sale "access denied", probar con barra inicial: rrsync acepta ambas formas según versión.
copiar() {
    origen="$1"; destino="$2"
    log "tirando de $origen"
    mkdir -p "$NVR_DEST/$destino"
    # shellcheck disable=SC2086
    rsync $RSYNC_OPTS -e "$SSH" \
        "$NVR_USER@$NVR_HOST:$origen" "$NVR_DEST/$destino/" \
        || die "rsync fallo sobre $origen"
}

log "inicio"

# 1. Config + el snapshot consistente de la base (lo genera snapshot-db.sh en el appliance).
copiar "config/" "config"

if [ ! -f "$NVR_DEST/config/frigate.db.backup" ]; then
    log "AVISO: no hay frigate.db.backup en el origen. ¿Corre snapshot-db.sh en el appliance?"
    log "  Sin él, la base solo se respalda como copia potencialmente rota, que no sirve."
fi

# 2. Alertas y snapshots: el material con valor probatorio.
copiar "media/frigate/clips/" "clips"

# 3. Exportados: alguien ya los marcó como relevantes.
copiar "media/frigate/exports/" "exports"

# El continuo NO se copia: 43 GB/día replicados reintroducen el I/O de red que ADR-0006
# descarta. Si muere el disco se pierde el metraje de contexto, no los eventos.

# Marca de frescura: es la fuente del SLI de la fase 06 (alerta si supera 36 h).
date -Is > "$STAMP"
log "fin correcto. Marca en $STAMP"
