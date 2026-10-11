#!/usr/bin/env python3
"""Deduplica cambios.json antes de aplicarlo con marbetes.py.

Como puede haber más de una sesión de Claude trabajando en paralelo sobre el
mismo cambios.json, puede terminar con el mismo fileId repetido (por ejemplo,
una entrada vieja que apuntaba a DUDAS_REVISAR y otra más nueva que lo
renombra). Este script se queda con la última decisión para cada fileId
(la que aparece más abajo en el archivo) y descarta las anteriores.
"""
import sys
import json


def limpiar(path):
    with open(path, encoding="utf-8") as f:
        changes = json.load(f)

    por_file_id = {}
    for c in changes:
        por_file_id[c["fileId"]] = c  # la última pisa a la anterior

    limpio = list(por_file_id.values())

    descartados = len(changes) - len(limpio)
    print(f"{len(changes)} entradas originales, {len(limpio)} después de deduplicar ({descartados} descartadas).")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(limpio, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 limpiar_cambios.py cambios.json")
        sys.exit(1)
    limpiar(sys.argv[1])
