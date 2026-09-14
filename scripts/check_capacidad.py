"""
Revisa si el archivo de Capacidad Instalada de la AMM cambió desde la última vez.

- Descarga el .xls directamente (sin navegador, es una URL estatica).
- Compara su hash SHA-256 contra el guardado en data/last_hash.txt.
- Si cambio: sobrescribe data/Capacidad_Instalada_2026.xls, actualiza el hash,
  y avisa al workflow (via GITHUB_OUTPUT) para que haga commit + cree un issue.

Cuando la AMM publique el archivo de 2027, solo hay que cambiar la variable URL
(y de paso el nombre del archivo en data/) para apuntar al año nuevo.
"""

import hashlib
import os

import requests

URL = "https://www.amm.org.gt/pdfs2/2026/Capacidad_Instalada_2026.xls"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
HASH_FILE = os.path.join(DATA_DIR, "last_hash.txt")
FILE_PATH = os.path.join(DATA_DIR, "Capacidad_Instalada_2026.xls")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    content = resp.content

    if len(content) < 1000:
        # Respuesta sospechosamente pequena (ej. pagina de error en vez del xls)
        raise SystemExit(f"Respuesta demasiado pequena ({len(content)} bytes), revisar URL/formato.")

    new_hash = hashlib.sha256(content).hexdigest()

    old_hash = None
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()

    changed = new_hash != old_hash

    print(f"Hash anterior: {old_hash}")
    print(f"Hash actual:   {new_hash}")
    print(f"Cambio detectado: {changed}")

    if changed:
        with open(FILE_PATH, "wb") as f:
            f.write(content)
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(new_hash)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
