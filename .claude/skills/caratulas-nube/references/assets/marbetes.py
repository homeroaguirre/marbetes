#!/usr/bin/env python3
import sys
import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")


def get_service():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def apply_changes(path):
    with open(path, encoding="utf-8") as f:
        changes = json.load(f)
    service = get_service()
    ok = 0
    failed = []
    for c in changes:
        file_id = c["fileId"]
        action = c["action"]
        try:
            if action == "rename":
                service.files().update(
                    fileId=file_id, body={"name": c["newTitle"]}
                ).execute()
                print("Renombrado " + file_id + " -> " + c["newTitle"])
            elif action == "trash":
                service.files().update(
                    fileId=file_id, body={"trashed": True}
                ).execute()
                print("Eliminado (papelera) " + file_id)
            elif action == "move":
                meta = service.files().get(fileId=file_id, fields="parents").execute()
                old_parents = ",".join(meta.get("parents", []))
                service.files().update(
                    fileId=file_id,
                    addParents=c["targetFolderId"],
                    removeParents=old_parents,
                    fields="id, parents",
                ).execute()
                print("Movido " + file_id + " -> carpeta " + c["targetFolderId"])
            else:
                print("Accion desconocida para " + file_id + ": " + action)
                failed.append(c)
                continue
            ok += 1
        except Exception as e:
            print("ERROR con " + file_id + " (" + action + "): " + str(e))
            failed.append(c)

    print("")
    print(str(ok) + " cambios aplicados, " + str(len(failed)) + " con error, de " + str(len(changes)) + " en total.")

    # Solo se quitan de la cola los cambios que se aplicaron con éxito.
    # Los que fallaron quedan en el archivo para poder revisarlos o reintentarlos,
    # en vez de perderse en silencio.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2, ensure_ascii=False)
    if failed:
        print(str(len(failed)) + " cambios quedaron en " + path + " por revisar/reintentar.")
    else:
        print("cambios.json vaciado (todo se aplico en Drive).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 marbetes.py cambios.json")
        sys.exit(1)
    apply_changes(sys.argv[1])
