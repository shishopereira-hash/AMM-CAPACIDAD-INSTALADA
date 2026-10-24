"""
Revisa si la AMM publicó una versión nueva del archivo de Capacidad Instalada y avisa en Slack.

- Revisa el archivo del año actual y, desde diciembre, también el del año siguiente
  (https://www.amm.org.gt/pdfs2/AAAA/Capacidad_Instalada_AAAA.xls), así no hay que
  cambiar nada cuando la AMM empiece a publicar el del año nuevo.
- Compara el hash SHA-256 contra el guardado en data/last_hash_AAAA.txt.
- Si cambió: guarda el archivo en data/Capacidad_Instalada_AAAA.xls, actualiza el hash
  y publica el aviso (con el archivo adjunto) en el canal de Slack.

Variables de entorno: SLACK_BOT_TOKEN, SLACK_CHANNEL_ID.
Uso: python scripts/check_capacidad.py            (revisión normal)
     python scripts/check_capacidad.py --prueba   (manda un mensaje de prueba al canal)
"""
import datetime as dt
import hashlib
import json
import os
import sys

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GT = dt.timezone(dt.timedelta(hours=-6))
UA = {"User-Agent": "Mozilla/5.0"}


def url_de(anio):
    return f"https://www.amm.org.gt/pdfs2/{anio}/Capacidad_Instalada_{anio}.xls"


def archivo_hash(anio):
    nuevo = os.path.join(DATA_DIR, f"last_hash_{anio}.txt")
    viejo = os.path.join(DATA_DIR, "last_hash.txt")      # nombre usado antes para 2026
    if not os.path.exists(nuevo) and anio == 2026 and os.path.exists(viejo):
        return viejo
    return nuevo


def slack(texto, adjunto=None):
    token, canal = os.environ.get("SLACK_BOT_TOKEN"), os.environ.get("SLACK_CHANNEL_ID")
    if not token or not canal:
        print("(sin SLACK_BOT_TOKEN / SLACK_CHANNEL_ID: no se avisa en Slack)")
        return
    h = {"Authorization": f"Bearer {token}"}
    if adjunto:
        data = open(adjunto, "rb").read()
        nombre = os.path.basename(adjunto)
        r = requests.post("https://slack.com/api/files.getUploadURLExternal", headers=h,
                          data={"filename": nombre, "length": len(data)}, timeout=60).json()
        if not r.get("ok"):
            raise SystemExit(f"Slack: {r}")
        requests.post(r["upload_url"], files={"file": (nombre, data)}, timeout=120).raise_for_status()
        c = requests.post("https://slack.com/api/files.completeUploadExternal",
                          headers={**h, "Content-Type": "application/json; charset=utf-8"},
                          data=json.dumps({"files": [{"id": r["file_id"], "title": nombre}],
                                           "channel_id": canal, "initial_comment": texto}), timeout=60).json()
    else:
        c = requests.post("https://slack.com/api/chat.postMessage",
                          headers={**h, "Content-Type": "application/json; charset=utf-8"},
                          data=json.dumps({"channel": canal, "text": texto}), timeout=60).json()
    if not c.get("ok"):
        raise SystemExit(f"Slack: {c}")
    print("Aviso publicado en Slack")


def revisar(anio):
    try:
        resp = requests.get(url_de(anio), timeout=30, headers=UA)
    except requests.RequestException as e:
        print(f"{anio}: no se pudo descargar ({e})")
        return False
    es_excel = resp.content[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04")   # .xls (OLE) o .xlsx (zip)
    if resp.status_code != 200 or len(resp.content) < 1000 or not es_excel:
        print(f"{anio}: todavía no hay archivo publicado (HTTP {resp.status_code}, {len(resp.content)} bytes)")
        return False
    nuevo_hash = hashlib.sha256(resp.content).hexdigest()
    hf = archivo_hash(anio)
    viejo_hash = open(hf, encoding="utf-8").read().strip() if os.path.exists(hf) else None
    print(f"{anio}: hash anterior {viejo_hash} · actual {nuevo_hash}")
    if nuevo_hash == viejo_hash:
        return False

    destino = os.path.join(DATA_DIR, f"Capacidad_Instalada_{anio}.xls")
    with open(destino, "wb") as f:
        f.write(resp.content)
    with open(os.path.join(DATA_DIR, f"last_hash_{anio}.txt"), "w", encoding="utf-8") as f:
        f.write(nuevo_hash)
    if hf.endswith("last_hash.txt") and os.path.exists(hf):
        os.remove(hf)

    ahora = dt.datetime.now(GT)
    primero = viejo_hash is None
    texto = (f"📁 *{'Primer archivo' if primero else 'Nueva versión'} de Capacidad Instalada {anio}* publicado por la AMM\n"
             f"Detectado el {ahora:%d/%m/%Y} a las {ahora:%H:%M}.\n"
             f"Descarga: {url_de(anio)}\n"
             f"_Súbelo a Claude para actualizar el Excel y el Word de capacidad instalada._")
    slack(texto, destino)
    return True


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    if "--prueba" in sys.argv:
        slack("✅ Prueba: el aviso de *Capacidad Instalada AMM* está conectado a este canal. "
              "Aquí llegará un mensaje cada vez que la AMM publique una versión nueva del archivo.")
        return
    hoy = dt.datetime.now(GT).date()
    anios = [hoy.year] + ([hoy.year + 1] if hoy.month == 12 else [])
    if hoy.month == 1:
        anios = [hoy.year - 1, hoy.year]         # en enero sigue revisando el del año que terminó
    changed = any([revisar(a) for a in anios])
    print("Cambio detectado:", changed)
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
