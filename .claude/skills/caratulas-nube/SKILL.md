---
name: caratulas-nube
description: Renombra fotos de etiquetas de discos de pasta (78 rpm) guardadas en una carpeta de Google Drive, leyendo el texto de cada etiqueta (sello, número de disco, cara, título, autores, intérprete, estilo) y generando un nombre de archivo estandarizado. Funciona en modo AUTÓNOMO — no pide confirmación por tanda, lo dudoso va a una carpeta aparte para revisión posterior. Usar esta skill siempre que el usuario pida "renombrar marbetes", "caratulas-nube", "etiquetas de discos", "fotos de discos de pasta/78 rpm en Drive", o pegue un link de una carpeta de Google Drive con fotos de etiquetas para catalogar/renombrar, incluso si no menciona el nombre exacto de la skill.
---

# Carátulas Nube — renombrado de etiquetas de discos de pasta (modo autónomo)

Este flujo cataloga fotos de etiquetas de discos de pasta (78 rpm) guardadas en Google
Drive, renombrando cada archivo con los datos que figuran en la etiqueta del disco.
**Corre sin supervisión**: no interrumpe al usuario tanda por tanda. Lo que no se puede
leer con confianza se aparta en una carpeta de dudas para que el usuario la revise
cuando quiera, no en el momento.

## Por qué es así

El usuario dejó claro (después de mucha fricción) que para un volumen de miles de
archivos NO quiere que se le pida confirmación por cada tanda ni por cada acción de
escritura en Drive. Dos decisiones de diseño responden a eso:

1. **Nada de confirmación en el chat por tanda.** Los pasos de este flujo deciden solos
   nombre y duplicados; lo dudoso se separa (ver más abajo) en vez de preguntar.
2. **Las escrituras reales en Drive (renombrar, borrar, mover) NO las hace Claude
   directamente**, porque eso dispara un diálogo de permiso por cada llamada que en
   este entorno no se puede desactivar. En cambio, Claude acumula los cambios
   decididos en un archivo `cambios.json` dentro del repo (`.claude/skills/caratulas-nube/state/`),
   lo commitea y pushea, y un script Python que corre en la máquina del usuario
   (`marbetes-script/marbetes.py`, fuera de Claude Code) aplica esos cambios contra la
   API de Google Drive sin ningún diálogo de por medio. Ver `references/script-local.md`
   para el script y las instrucciones de configuración que ya se le dieron al usuario.

## Cuándo usar esta skill

Activarla cuando el usuario pida renombrar/catalogar fotos de etiquetas de discos de
pasta en una carpeta de Google Drive, con un formato de nombre tipo:
`Sello, Nº Cara, Título (Autor - Autor), Intérprete, Estilo.jpg`

Si el usuario no da la URL de la carpeta, pedirla antes de empezar. Si es la primera
vez que se usa en un proyecto, confirmar que existe `marbetes-script/marbetes.py`
en la máquina del usuario (el script local); si no existe, guiarlo para crearlo
siguiendo `references/script-local.md` **antes** de arrancar el modo autónomo.

## Carpeta de dudas

Antes de procesar, asegurarse de que exista en Drive una carpeta llamada
`DUDAS_REVISAR` dentro de la misma carpeta madre de los marbetes (crearla una única
vez con `mcp__Google_Drive__create_file` si no existe — es una sola escritura, no una
por archivo, así que el único permiso que puede pedir es ese, una vez).

Cualquier foto que caiga en alguno de estos casos se **mueve** a `DUDAS_REVISAR` (no
se renombra, no se borra) para que el usuario la revise cuando quiera:
- No se puede leer con confianza el sello, número de disco, cara, título o
  intérprete (los campos imprescindibles para armar el nombre).
- Hay dos o más fotos del mismo disco y no está claro cuál es la de mejor calidad
  (ambigüedad real, no solo una ligera diferencia de nitidez).
- La imagen no parece ser una etiqueta de disco (mala foto, archivo corrupto, etc.)

No es necesario preguntarle al usuario por cada caso dudoso: se agrega la acción
`move` a `cambios.json` (ver más abajo) y listo — no hace falta llevar ningún
registro aparte de "cuáles son dudas".

## Sin lista de "ya procesados"

Esta skill **no guarda en el repo un historial de qué fotos ya se catalogaron**.
No hace falta y no se quiere: el propio estado de Drive ya dice qué falta.

- Las fotos **sin catalogar todavía** conservan el nombre crudo que les puso la
  cámara/app de escaneo (patrón `NNNNNNNNNNNNNN-N.label.omar-a.DSCNxxxx.jpg` o
  similar — contienen literalmente `.label.omar-a.` en el título).
- Las fotos **ya catalogadas** tienen el nombre nuevo (`Sello, Nº Cara, Título...`)
  y por lo tanto ya no matchean ese patrón.
- Las fotos **apartadas por dudosas** están físicamente movidas a la carpeta
  `DUDAS_REVISAR`, así que tampoco aparecen más al listar la carpeta principal.

Por eso "pendiente" se determina en el momento, contra Drive, y no contra un
archivo de estado en el repo. No crear ni mantener un `processed.json` / `dudas.json`
con IDs de fotos ya vistas — si alguno existe de una versión vieja de la skill,
se puede borrar sin miedo.

## Flujo de trabajo (autónomo)

1. **Listar los archivos de imagen pendientes** de la carpeta de Drive con
   `mcp__Google_Drive__search_files`, filtrando por
   `parentId = '<carpetaMarbetesId>' and mimeType contains 'image/' and title contains '.label.omar-a.'`
   (ajustar el patrón del título al que realmente use el usuario si es distinto).
   Esto ya excluye solo, sin necesidad de estado adicional, tanto lo ya renombrado
   como lo movido a `DUDAS_REVISAR`.

2. **Trabajar en tandas internas de 10 fotos.** Nunca leer/descargar más de 10 a la
   vez, pero **no parar a pedir confirmación entre tandas**: procesar una tanda,
   aplicar la decisión (ver paso 6), y seguir directo con la siguiente, hasta
   agotar lo pendiente o hasta que se termine la sesión de trabajo (en cuyo caso,
   al retomar, simplemente volver a listar pendientes con la misma query — como el
   script local ya habrá renombrado lo anterior, esos archivos no van a volver a
   aparecer).

3. **Leer y analizar cada foto** de la tanda con `download_file_content` /
   `read_file_content`, extrayendo: sello, número de disco, cara, título, autor(es),
   intérprete, cantor de estribillo si lo hay, y estilo.

4. **Construir el nombre nuevo**, mismo formato y reglas que siempre:

   ```
   Sello, Nº Cara, Título (Autor - Autor), Intérprete, Estilo.jpg
   ```
   - Sello corto (RCA Victor → Victor, Odeón, Columbia, Brunswick, Disco Nacional...).
   - Nº Cara: número + espacio + A/B.
   - Título en capitalización tipo oración, tal como figura en la etiqueta.
   - Autores entre paréntesis, separados por " - ".
   - Intérprete tal como figura; cantor de estribillo como campo aparte `Canta Fulano`.
   - Estilo tal como figura.
   - **Si algún campo imprescindible no se puede leer con confianza: no inventar, no
     usar "SIN DATO" tampoco — directamente mandar el archivo a `DUDAS_REVISAR`**
     (esto reemplaza la regla anterior de escribir "SIN DATO" en el nombre; ahora
     el archivo dudoso ni se renombra, se aparta entero).

5. **Si hay dos o más fotos del mismo disco (mismo sello, número y cara), se
   numeran y punto** — no hay que comparar calidad, no hay que decidir cuál
   descartar, no hay que mandar nada a `DUDAS_REVISAR` por esto. Se conservan
   todas, agregando `2`, `3`, `4`... antes de la extensión al nombre que le
   tocaría por sí solo (ej.: `Victor, 38999 A, ....jpg` y
   `Victor, 38999 A, ... 2.jpg`).

   Como no se guarda un historial de nombres ya asignados (ver más arriba), para
   saber si un disco ya tiene nombre asignado hay que preguntarle a Drive en el
   momento: antes de fijar el nombre final de un archivo, buscar en la misma
   carpeta (excluyendo `DUDAS_REVISAR`) títulos que empiecen con
   `"Sello, Nº Cara, "` (`mcp__Google_Drive__search_files` con
   `title contains 'Sello, Nº Cara,'`). Si no aparece ninguno, va sin sufijo. Si
   ya hay uno o más, el nuevo lleva el siguiente número disponible.

6. **Registrar la decisión, no aplicarla directamente.** Por cada archivo de la
   tanda, agregar una entrada a `.claude/skills/caratulas-nube/state/cambios.json`
   (formato abajo). Commitear y pushear ese archivo al repo después de cada tanda
   (o cada pocas tandas) para que el script local del usuario lo vaya recogiendo.
   **No llamar `update_file` ni `trash_file` directamente** salvo para el
   movimiento único de creación de la carpeta `DUDAS_REVISAR` — eso es lo que le
   genera al usuario los diálogos de permiso que quiere evitar. No hace falta
   registrar el fileId en ningún otro lado: una vez que el script local aplique el
   cambio, ese archivo deja de matchear la query de "pendientes" del paso 1.

   Formato de cada entrada en `cambios.json`:
   ```json
   {"fileId": "<id>", "action": "rename", "newTitle": "Victor, 38999 A, ....jpg"}
   {"fileId": "<id>", "action": "move", "targetFolderId": "<id de DUDAS_REVISAR>"}
   ```

7. **Avanzar solo, tanda tras tanda**, sin pausas de confirmación, hasta cubrir
   todo lo pendiente. Si la sesión se corta (se acaba el turno, se cierra la
   conversación), lo hecho hasta ese punto ya quedó en `cambios.json` en el repo —
   al retomar (manualmente o por un disparador programado), simplemente volver a
   listar pendientes (paso 1); no hay ningún archivo de estado que consultar.

8. **Nunca reportar avance pidiendo aprobación.** Está bien dejar un mensaje corto
   de progreso si el usuario está mirando, pero no hace falta esperar respuesta para
   seguir. El usuario revisa el resultado cuando quiera, en Drive directamente (los
   ya renombrados) y en `DUDAS_REVISAR` (los que necesitan su ojo).

## Aplicación de los cambios (lado del usuario)

El usuario tiene un script en `~/marbetes-script/marbetes.py` (Python, con su propio
entorno virtual y credenciales OAuth de Google) que lee un archivo de cambios y los
aplica contra la API de Google Drive, sin pasar por el sistema de permisos de Claude
Code. Para que aplique lo que Claude vaya subiendo al repo, su comando es:

```bash
cd ~/marbetes-script && git -C ~/marbetes (o donde tenga clonado el repo) pull && \
  ./venv/bin/python marbetes.py <ruta al cambios.json actualizado>
```

Se le puede sugerir que lo deje corriendo en un cron/loop local (por ejemplo cada 30
minutos) para que la aplicación sea automática y no tenga que acordarse de hacerlo
él. Ver `references/script-local.md` para el detalle del script (incluye soporte
para las tres acciones: `rename`, `trash`, `move`) y las instrucciones que ya se le
dieron paso a paso para configurar Google Cloud, las credenciales OAuth, el entorno
virtual, etc.

## Nota sobre permisos

Las llamadas de **solo lectura** a Google Drive (`search_files`, `list_recent_files`,
`download_file_content`, `read_file_content`, `get_file_metadata`) están
allowlisteadas en `.claude/settings.json` y no deberían interrumpir. **No se debe
allowlistear `update_file`/`trash_file`**: en este entorno esa auto-concesión de
permiso está bloqueada por diseño (protección contra auto-modificación), y de
cualquier forma ya no se usan directamente en el flujo autónomo — el script local
del usuario es quien escribe en Drive.
