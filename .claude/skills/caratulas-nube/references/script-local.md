# Script local para aplicar cambios en Google Drive

Este script corre en la máquina del usuario (no en la sesión de Claude Code) y
aplica contra la API de Google Drive los cambios que Claude decide y sube al repo
en `.claude/skills/caratulas-nube/state/cambios.json`. Corriendo fuera de Claude
Code, no dispara ningún diálogo de permiso.

## Configuración ya hecha con el usuario (no repetir si ya existe)

1. Proyecto de Google Cloud (`gmail-mcp-carmona` en este caso) con la API de Drive
   habilitada.
2. Un ID de cliente OAuth de tipo "Aplicación de escritorio", descargado como
   `credentials.json`.
3. La cuenta dueña de la carpeta (`informescarmonamotos@gmail.com`) agregada como
   usuario de prueba en la pantalla de consentimiento OAuth.
4. Carpeta `~/marbetes-script/` con:
   - `credentials.json` (las credenciales OAuth descargadas)
   - `venv/` (entorno virtual de Python con `google-api-python-client`,
     `google-auth-httplib2`, `google-auth-oauthlib` instalados)
   - `marbetes.py` (el script, contenido abajo)
   - `token.json` (se genera solo la primera vez que se corre el script y se loguea)

Si alguno de estos pasos no está hecho todavía, seguirlos en orden antes de usar el
script (fueron dados paso a paso al usuario en la conversación original; si hace
falta repetirlos, ir de a un paso por vez y esperar confirmación de cada uno, tal
como pidió el usuario).

## Contenido de `marbetes.py`

Soporta tres acciones: `rename`, `trash`, `move` (mover a otra carpeta, usado para
la carpeta de dudas). **Usa rutas absolutas basadas en la ubicación del propio
script** (no en el directorio desde el que se lo invoca), para que funcione sin
importar desde qué carpeta lo corra el usuario — esto evitó un
`FileNotFoundError` que apareció la primera vez que se corrió desde otra carpeta
(`~/marbetes-repo` en vez de `~/marbetes-script`).

El código fuente vive en `assets/marbetes.py` junto a este archivo. Copiarlo tal
cual a `~/marbetes-script/marbetes.py` en la máquina del usuario.

## Cómo lo corre el usuario

Una vez que Claude pusheó cambios nuevos al repo:

```bash
cd <carpeta donde el usuario clonó el repo marbetes> && git pull
~/marbetes-script/venv/bin/python ~/marbetes-script/marbetes.py <ruta al cambios.json del repo>
```

Con las rutas absolutas del script, esto funciona sin importar desde qué
directorio se ejecute — no hace falta `cd` a `~/marbetes-script` primero.

Es idempotente: volver a aplicar un cambio ya aplicado (mismo rename, mismo trash)
no rompe nada, así que no hace falta que el usuario recuerde exactamente qué ya
corrió — puede simplemente volver a pasarle el `cambios.json` más reciente.

Se le puede sugerir dejar esto en un cron o un loop simple para que se aplique solo
cada cierto tiempo, sin que el usuario tenga que acordarse.
