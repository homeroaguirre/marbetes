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
la carpeta de dudas).

```python
#!/usr/bin/env python3
import sys, json, os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def apply_changes(path):
    with open(path, encoding='utf-8') as f:
        changes = json.load(f)
    service = get_service()
    for c in changes:
        file_id = c['fileId']
        try:
            if c['action'] == 'rename':
                service.files().update(fileId=file_id, body={'name': c['newTitle']}).execute()
                print(f"Renombrado {file_id} -> {c['newTitle']}")
            elif c['action'] == 'trash':
                service.files().update(fileId=file_id, body={'trashed': True}).execute()
                print(f"Eliminado (papelera) {file_id}")
            elif c['action'] == 'move':
                meta = service.files().get(fileId=file_id, fields='parents').execute()
                old_parents = ",".join(meta.get('parents', []))
                service.files().update(
                    fileId=file_id,
                    addParents=c['targetFolderId'],
                    removeParents=old_parents,
                    fields='id, parents'
                ).execute()
                print(f"Movido {file_id} -> carpeta {c['targetFolderId']}")
            else:
                print(f"Accion desconocida para {file_id}: {c['action']}")
        except Exception as e:
            print(f"ERROR con {file_id} ({c['action']}): {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 marbetes.py cambios.json")
        sys.exit(1)
    apply_changes(sys.argv[1])
```

Es idempotente: volver a aplicar un cambio ya aplicado (mismo rename, mismo trash)
no rompe nada, así que no hace falta que el usuario recuerde exactamente qué ya
corrió — puede simplemente volver a pasarle el `cambios.json` más reciente.

## Cómo lo corre el usuario

Una vez que Claude pusheó cambios nuevos al repo:

```bash
cd <carpeta donde el usuario clonó el repo marbetes> && git pull
cd ~/marbetes-script
./venv/bin/python marbetes.py <ruta al cambios.json del repo>
```

Se le puede sugerir dejar esto en un cron o un loop simple para que se aplique solo
cada cierto tiempo, sin que el usuario tenga que acordarse.
