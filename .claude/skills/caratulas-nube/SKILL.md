---
name: caratulas-nube
description: Renombra fotos de etiquetas de discos de pasta (78 rpm) en una carpeta de Google Drive, leyendo el texto de cada etiqueta y aplicando un formato estándar. Usar cuando el usuario pida "renombrar etiquetas de discos", "carátulas de discos de pasta", o pase un link de Drive con fotos de etiquetas de 78 rpm.
---

# Carátulas nube

Renombra fotos de etiquetas de discos de pasta (78 rpm) alojadas en una carpeta de Google Drive, usando el texto legible en cada etiqueta.

## Formato de nombre final

```
Sello, Nº Cara, Título (Autor - Autor), Intérprete, Canta Fulano, Estilo.jpg
```

(El campo "Canta Fulano" solo se agrega si hay un cantor de estribillo; si el tema es instrumental se omite.)

## Reglas de cada campo

- **Sello**: nombre corto (ej. "RCA Victor" → "Victor", "Columbia", "Odeón", "Brunswick", "Disco Nacional").
- **Nº Cara**: número de disco + espacio + cara (A o B), ej. "38682 A".
- **Título**: tal como figura en la etiqueta, con mayúscula solo en la inicial (no todo en mayúsculas). Corregir tildes obvias (ej. "MAS ALLA" → "Más allá").
- **Autor(es)**: entre paréntesis después del título, separados por " - " si hay más de uno.
- **Intérprete**: nombre completo de la orquesta/cantor tal como figura en la etiqueta.
- **Canta Fulano**: campo aparte si hay estribillo cantado por alguien (ej. "Canta Ricardo Ruiz").
- **Estilo**: Tango, Vals, Milonga, Fox-trot, Tango canción, etc., tal como figura en la etiqueta.
- Si un dato no se puede leer con confianza, dejarlo tal cual aparece en la etiqueta (no inventar). Marcar como "SIN DATO" solo si es totalmente ilegible.

## Duplicados

Es frecuente que la carpeta tenga varios archivos para un mismo disco/tema (distintas resoluciones, formatos, exportaciones "-scaled", etc.). Antes de nombrar hay que distinguir dos casos:

- **Mismo tema, misma foto** (solo cambia formato/resolución/tamaño de archivo, el contenido visual es el mismo): quedarse con la copia de mejor calidad (mayor resolución/tamaño de archivo) y **eliminar** las demás copias de ese archivo con `mcp__Google_Drive__trash_file` (a la papelera, no borrado permanente).
- **Mismo tema, distinta foto** (dos fotos diferentes del mismo disco, por ejemplo dos ángulos o dos ejemplares físicos distintos): conservar ambas y numerarlas agregando " (2)", " (3)", etc. al final del nombre (antes de la extensión) para que no se pisen.

Para decidir si dos archivos son "la misma foto" comparar el texto OCR extraído (debe ser prácticamente idéntico) y el nombre de archivo original (mismo número de tema, mismo slug, solo difiere extensión o sufijo "-scaled"/tamaño). Si el texto OCR difiere sensiblemente o encuadre/calidad de la imagen es visiblemente otra toma, tratarlas como fotos distintas.

## Procedimiento

1. Listar todos los archivos de la carpeta de Drive indicada con `mcp__Google_Drive__search_files` usando `parentId = '<ID_DE_CARPETA>'` (paginar con `pageToken` si hace falta) y armar la lista completa de `fileId`/nombre actual antes de tocar nada.
2. **Pre-limpieza de duplicados obvios por nombre de archivo** (sin gastar OCR): agrupar por número de tema + slug del nombre original (ignorando extensión y sufijos de tamaño como "-scaled"). Dentro de cada grupo cuyo nombre base sea idéntico salvo extensión/sufijo de tamaño, quedarse con el archivo de mayor `fileSize` y mandar los demás a la papelera con `mcp__Google_Drive__trash_file`. El resultado es la lista deduplicada a procesar.
3. **Procesar la lista deduplicada en tandas de 10 fotos**, en el orden en que aparecen:
   1. Tomar los siguientes 10 archivos pendientes (los últimos 10 pueden ser menos de 10).
   2. Leer el contenido de cada imagen de la tanda con `mcp__Google_Drive__read_file_content` (funciona como OCR/descripción para `image/jpeg`), todas en paralelo en la misma tanda de tool calls.
   3. Extraer de cada resultado: sello, número de disco, cara, título, autor(es), intérprete, cantor de estribillo (si hay), estilo.
   4. Si dentro de la tanda (o contra un tema ya renombrado en una tanda anterior) aparece el mismo tema con texto OCR prácticamente idéntico al de un archivo ya procesado → es la misma foto que se coló en la pre-limpieza: mandarla a la papelera en vez de renombrarla. Si el OCR es del mismo tema pero claramente otra foto (otro encuadre/calidad, contenido igual pero imagen distinta) → nombrarla igual que la ya asignada pero agregando " (2)", " (3)", etc. antes de la extensión.
   5. Armar el nombre propuesto para cada archivo restante de la tanda según el formato de arriba.
   6. Mostrar al usuario la tabla "nombre actual → nombre propuesto" (o "→ eliminado (duplicado)") de esa tanda de 10, señalando explícitamente los campos de baja confianza u OCR dudoso.
   7. Aplicar los renombres con `mcp__Google_Drive__update_file` (parámetro `title`) y las eliminaciones de duplicados detectados por OCR con `mcp__Google_Drive__trash_file`, todos en paralelo en la misma tanda de tool calls.
   8. Confirmar brevemente que esa tanda quedó procesada y pasar de inmediato a la siguiente tanda de 10, sin esperar respuesta.
4. Repetir el paso 3 hasta agotar todos los archivos de la lista deduplicada.
5. Al terminar la última tanda, confirmar al usuario el total de fotos renombradas y el total de duplicados eliminados, listando cualquier dato incierto que haya quedado documentado en el propio nombre de archivo.

## Notas

- **No pedir confirmación ni aprobar una por una, ni entre tandas.** El usuario ya autorizó de forma permanente esta skill: se muestra la tabla de cada tanda y se aplica de inmediato, tanda tras tanda, sin pausas ni preguntas intermedias.
- Dentro de cada tanda, todas las llamadas a `read_file_content` pueden hacerse en paralelo en un solo mensaje (misma tanda de tool calls) para ahorrar tiempo, y lo mismo con los `update_file`/`trash_file` al aplicar los cambios de esa tanda.
- Eliminar duplicados siempre con `trash_file` (papelera, reversible), nunca con un borrado permanente.
- Este flujo es específico de discos argentinos de tango/vals/milonga de sellos como Victor, Odeón, Columbia — pero el formato es genérico y sirve para cualquier etiqueta con estos campos.
