---
name: caratulas-nube
description: Renombra fotos de etiquetas de discos de pasta (78 rpm) guardadas en una carpeta de Google Drive, leyendo el texto de cada etiqueta (sello, número de disco, cara, título, autores, intérprete, estilo) y generando un nombre de archivo estandarizado. Usar esta skill siempre que el usuario pida "renombrar marbetes", "caratulas-nube", "etiquetas de discos", "fotos de discos de pasta/78 rpm en Drive", o pegue un link de una carpeta de Google Drive con fotos de etiquetas para catalogar/renombrar, incluso si no menciona el nombre exacto de la skill.
---

# Carátulas Nube — renombrado de etiquetas de discos de pasta

Este flujo cataloga fotos de etiquetas de discos de pasta (78 rpm) guardadas en Google
Drive, renombrando cada archivo con los datos que figuran en la etiqueta del disco.

## Cuándo usar esta skill

Activarla cuando el usuario pida renombrar/catalogar fotos de etiquetas de discos de
pasta en una carpeta de Google Drive, con un formato de nombre tipo:
`Sello, Nº Cara, Título (Autor - Autor), Intérprete, Estilo.jpg`

Si el usuario no da la URL de la carpeta, pedirla antes de empezar.

## Flujo de trabajo

1. **Listar los archivos de imagen** de la carpeta de Drive indicada, con
   `mcp__Google_Drive__search_files` o el listado que corresponda a esa carpeta.
   Confirmar la cantidad total de fotos antes de seguir (si son muchas, cientos o
   miles, avisar al usuario que se va a procesar en lotes).

2. **Leer y analizar cada foto** con `mcp__Google_Drive__download_file_content` /
   `read_file_content`, mirando el texto impreso en la etiqueta del disco. Extraer:
   - Sello discográfico
   - Número de disco
   - Cara (A o B)
   - Título de la obra
   - Autor(es)
   - Intérprete (orquesta/cantor)
   - Cantor de estribillo, si lo hay
   - Estilo (Tango, Vals, Milonga, Fox-trot, Tango canción, etc.)

3. **Construir el nombre nuevo** con este formato EXACTO, campos separados por ", ":

   ```
   Sello, Nº Cara, Título (Autor - Autor), Intérprete, Estilo.jpg
   ```

   Reglas de formato:
   - **Sello**: nombre corto (ej. "RCA Victor" → "Victor", "Columbia", "Odeón",
     "Brunswick", "Disco Nacional").
   - **Nº Cara**: número de disco + espacio + cara, ej. `38682 A`.
   - **Título**: capitalización tipo oración (solo la inicial en mayúscula), tal
     como figura en la etiqueta — no todo en mayúsculas aunque la etiqueta lo esté.
   - **Autores**: entre paréntesis después del título, separados por " - " si hay
     más de uno.
   - **Intérprete**: nombre completo de la orquesta/cantor tal como figura en la
     etiqueta. Si hay un cantor de estribillo, agregarlo como campo aparte:
     `Canta Fulano`.
   - **Estilo**: tal como figura en la etiqueta.
   - Si algún dato no se puede leer con confianza, **no inventarlo**: dejar el
     campo tal cual aparece en la etiqueta, o escribir `SIN DATO`. Nunca
     completar con una suposición.

4. **Detectar duplicados del mismo disco.** Antes de armar la lista de renombres,
   agrupar las fotos que corresponden al MISMO tema/etiqueta (mismo número de
   disco y cara, mismo contenido de etiqueta) aunque estén en distintos archivos
   o formatos (ej. la misma foto subida en `.jpg` y en `.png`, o dos tomas
   prácticamente idénticas de la misma cara).
   - Si son la misma imagen (o recortes/versiones de la misma toma): comparar
     la calidad (nitidez, resolución, que no falte texto por recorte o brillo)
     y quedarse con la mejor. Avisar en la lista de confirmación cuál se
     conserva y cuál se va a **eliminar** (no solo renombrar), y aplicar esa
     eliminación en Drive recién después de la confirmación del usuario, igual
     que los renombres.
   - Si son fotos **distintas** del mismo disco/cara (ángulos, tomas o estados
     de conservación diferentes, no la misma imagen), no se elimina ninguna:
     conservar todas y numerarlas agregando ` 2`, ` 3`, ` 4`... antes de la
     extensión, en el mismo orden en que aparecen en la carpeta, ej.
     `Victor, 39246 A, Yo soy el tango (H. Expósito - D. S. Federico), Aníbal
     Troilo (Pichuco) y su Orquesta Típica, Canta Fiorentino, Tango.jpg` y
     `Victor, 39246 A, Yo soy el tango (H. Expósito - D. S. Federico), Aníbal
     Troilo (Pichuco) y su Orquesta Típica, Canta Fiorentino, Tango 2.jpg`.

5. **Confirmación obligatoria antes de renombrar (o eliminar).** Nunca renombrar archivos sin
   aprobación explícita del usuario. Mostrar la lista completa
   "nombre actual → nombre propuesto" (marcando también los que se van a
   **eliminar** por ser duplicados) para TODOS los archivos del lote (o de la
   carpeta entera si es manejable) y esperar a que el usuario la revise y
   confirme. Recién después de la confirmación, aplicar los renombres en Drive
   uno por uno con la tool de renombrado/actualización de metadata
   (`mcp__Google_Drive__update_file`) y las eliminaciones de duplicados
   correspondientes.

6. **Procesar en lotes** si hay muchos archivos, mostrando avance (ej. "lote 1 de
   6, archivos 1–500") para que el usuario pueda cortar o revisar sin perder el
   trabajo ya hecho.

## Nota sobre permisos

Este flujo hace muchas llamadas de **solo lectura** a Google Drive
(`search_files`, `list_recent_files`, `download_file_content`,
`read_file_content`, `get_file_metadata`) que no deberían interrumpir con un
prompt de confirmación cada vez. Si las confirmaciones de permisos se vuelven
repetitivas, sugerirle al usuario correr la skill `fewer-permission-prompts`
(o agregar un allowlist en `.claude/settings.json`) para esas tools de lectura.

La tool de escritura (`mcp__Google_Drive__update_file`, que renombra el
archivo) sí debe seguir pidiendo confirmación normal, porque modifica archivos
reales del usuario — el paso 4 de este flujo ya cubre esa confirmación a nivel
de contenido (la lista completa de renombres), pero el permiso de la tool en sí
no se debe saltear.
