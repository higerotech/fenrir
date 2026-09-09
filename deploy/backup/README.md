# Respaldo del NVR al NAS (ADR-0006)

Dos scripts y dos crons, en dos máquinas distintas. **El appliance no monta nada del NAS**:
si el NAS desaparece, el NVR ni se entera (probado en T-20).

```
appliance                                   NAS
  snapshot-db.sh  (cron 03:40)               pull-from-appliance.sh (cron 04:00)
  frigate.db  ->  frigate.db.backup   <---   rsync sobre SSH, solo lectura
                                              config/ clips/ exports/
```

## Por qué el snapshot de la base va aparte

`rsync` sobre una SQLite viva puede producir un fichero roto: Frigate escribe mientras se
copia. Una copia rota es el peor tipo de respaldo, porque parece que lo tienes hasta el día
que lo necesitas. `snapshot-db.sh` usa `sqlite3 .backup`, que sí es consistente con un
escritor activo, valida el resultado con `integrity_check` antes de publicarlo, y solo
entonces lo pone en su sitio con un `mv` atómico.

Por eso el cron del appliance corre **antes** que el del NAS, con margen suficiente.

## Instalación — appliance

```bash
sudo apt-get install -y sqlite3
sudo install -m 755 snapshot-db.sh /usr/local/bin/snapshot-db.sh
sudo crontab -e
#   40 3 * * *  /usr/local/bin/snapshot-db.sh >> /var/log/nvr-snapshot.log 2>&1
```

Cuenta de solo lectura para el NAS (es el Paso 8bis del runbook):

```bash
sudo useradd -r -m -s /bin/bash nvrbackup
sudo install -d -m 700 -o nvrbackup -g nvrbackup /home/nvrbackup/.ssh
sudo -u nvrbackup nano /home/nvrbackup/.ssh/authorized_keys
sudo chmod 600 /home/nvrbackup/.ssh/authorized_keys
sudo setfacl -R -m u:nvrbackup:rX /srv/fenrir/config /srv/fenrir/media
```

La línea de `authorized_keys`, en una sola línea y con la clave **pública** del NAS:

```
command="rrsync -ro /srv/fenrir",no-agent-forwarding,no-port-forwarding,no-pty,no-X11-forwarding ssh-ed25519 AAAA...
```

`rrsync` viene con `rsync` (suele estar en `/usr/share/doc/rsync/scripts/rrsync`; en Ubuntu
24.04 basta `sudo apt-get install rsync` y `rrsync` está en el `PATH`). El `-ro` es lo que
convierte esa clave en solo lectura: aunque se filtre, no puede escribir ni borrar nada.
S-10 lo comprueba intentándolo.

## Instalación — NAS

```bash
sudo install -m 755 pull-from-appliance.sh /usr/local/bin/fenrir-backup.sh
sudo tee /etc/fenrir-backup.env >/dev/null <<'EOF'
NVR_HOST=<ip-del-appliance>
NVR_USER=nvrbackup
NVR_KEY=/root/.ssh/id_ed25519_nvrbackup
NVR_DEST=/volumen/backups/fenrir
EOF
sudo chmod 600 /etc/fenrir-backup.env
sudo crontab -e
#   0 4 * * *  /usr/local/bin/fenrir-backup.sh >> /var/log/fenrir-backup.log 2>&1
```

Ninguna IP ni nombre real vive en el repositorio: van a `/etc/fenrir-backup.env` con permisos
600, igual que las credenciales del NVR van al `.env`. Es la misma convención del README raíz.

## Retención en el NAS

El script **no usa `--delete`** a propósito: el NAS conserva lo que Frigate ya purgó, que es
el motivo de tener respaldo. La contrapartida es que el destino crece sin límite, así que el
NAS necesita su propia política. Con la retención de 14 días de alertas en el NVR, algo del
estilo:

```bash
find /volumen/backups/fenrir/clips -type f -mtime +180 -delete
find /volumen/backups/fenrir/clips -type d -empty -delete
```

Esa decisión es del NAS, no del NVR, y conviene tomarla a conciencia: la clasificación de
datos dice que el respaldo hereda la clasificación **Confidencial** del original, así que
guardarlo eternamente amplía la ventana de exposición de T8.

## Verificación

No basta con que el cron no dé error. Los casos del plan de pruebas:

| Caso | Qué comprueba |
|---|---|
| **T-19** | Restaurar un archivo cualquiera desde el NAS y reproducirlo. Un respaldo nunca restaurado no es un respaldo |
| **T-20** | Apagar el NAS 30 min: grabación, vivo y eventos siguen sin inmutarse |
| **S-10** | Desde `nvrbackup`, intentar escribir o salir del árbol: todo rechazado |

Y la alerta de frescura de la fase 06 (`<36 h` desde el último `.last-success`) existe porque
un respaldo que dejó de correr en silencio es peor que no tenerlo: da una red de seguridad
que no existe. El runbook I-7 dice qué hacer cuando salta.
