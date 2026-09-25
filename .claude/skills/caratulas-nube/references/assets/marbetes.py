#!/usr/bin/env python3
import sys
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")


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
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def apply_changes(path):
    with open(path, encoding="utf-8") as f:
        changes = json.load(f)
    service = get_service()
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
        except Exception as e:
            print("ERROR con " + file_id + " (" + action + "): " + str(e))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 marbetes.py cambios.json")
        sys.exit(1)
    apply_changes(sys.argv[1])
