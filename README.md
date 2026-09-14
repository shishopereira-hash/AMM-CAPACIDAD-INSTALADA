# Vigilancia de Capacidad Instalada — AMM Guatemala

Revisa automáticamente, una vez por semana, si la AMM publicó una versión nueva
del archivo de Capacidad Instalada (https://www.amm.org.gt/pdfs2/2026/Capacidad_Instalada_2026.xls).

Si detecta un cambio:
1. Guarda el archivo nuevo en `data/Capacidad_Instalada_2026.xls` (commit automático).
2. Abre un **Issue** en este repositorio para avisarte.

## Configuración (una sola vez)

1. Crea un repositorio nuevo en GitHub (puede ser privado) y sube estos archivos
   manteniendo la misma estructura de carpetas:
   ```
   .github/workflows/check_amm.yml
   scripts/check_capacidad.py
   data/.gitkeep
   README.md
   ```
2. No necesitas crear ningún secreto ni token: el workflow usa el
   `GITHUB_TOKEN` que GitHub genera automáticamente en cada ejecución.
3. Entra a la pestaña **Actions** del repositorio y confirma que el workflow
   "Revisar Capacidad Instalada AMM" aparece habilitado.
4. Para recibir avisos por correo cuando se abra un Issue: arriba a la derecha
   del repositorio, clic en **Watch → All Activity** (es gratis, no requiere
   configurar nada más).
5. (Opcional pero recomendado) Ejecuta el workflow una vez a mano para probar
   que todo funciona: pestaña **Actions** → "Revisar Capacidad Instalada AMM"
   → **Run workflow**. La primera corrida siempre va a detectar "cambio"
   (porque no hay hash previo guardado) y va a crear el primer commit + issue;
   es normal, es solo la línea base.

## Cuándo tengas que tocar algo

- **Cuando la AMM publique el archivo de 2027**: cambia la URL dentro de
  `scripts/check_capacidad.py` (variable `URL`) y el nombre de archivo en
  `FILE_PATH`, apuntando al año nuevo.
- **Si quieres cambiar la frecuencia**: edita la línea `cron` en
  `.github/workflows/check_amm.yml` (usa https://crontab.guru para armar el
  horario que quieras).

## Qué hacer cuando llegue el aviso

Descarga `data/Capacidad_Instalada_2026.xls` desde el repositorio y súbelo a
Claude (junto con el Excel de gráficas que ya tienes) para que compare los
cambios y actualice el Dashboard.
