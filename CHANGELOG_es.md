# Cambios

Los cambios de py-pdfocr que importan. Las versiones, con sus wheels, ZIP y
AppImages, están en
[Codeberg](https://codeberg.org/nivaca/py-pdfocr/releases) y
[GitHub](https://github.com/nivaca/py-pdfocr/releases).

## Sin publicar

- Ya no se guarda aquí nada de una versión: `tools/release.py` hace y firma
  la rueda, el paquete de fuentes, el ZIP, la AppImage y `SHA256SUMS` en
  `build/release/` (no en `dist/`), y el depósito para Zenodo en
  `build/zenodo/`, los publica desde allí y al final borra las dos
  carpetas. `tools/bundle-appimage.py` escribe por omisión en
  `build/release/`.
- `tools/zenodo.py`: la descripción del depósito deja fuera la línea que
  lleva a los README en otras lenguas y la sección Screenshots, cuyas
  imágenes Zenodo no muestra.
- `tools/release.py` publica ahora cada versión en Zenodo
  (`tools/zenodo.py upload --publish`), en vez de dejar un borrador;
  `--zenodo-draft` todavía lo deja. `tools/zenodo.py publish` publica un
  borrador que ya está allí (por omisión, el que espera con el título del
  proyecto).

## 1.0.5 — 2026-11-25

- `tools/zenodo.py`: la descripción del depósito es ahora el README entero
  de la etiqueta, en HTML. El borrador recibe además el colaborador (el
  director del proyecto), los idiomas, el copyright, el repositorio en
  GitHub, el lenguaje de programación y el estado del desarrollo; estos
  últimos, por la API de registros de Zenodo, porque la de depósitos no los
  admite. El token puede guardarse en el llavero del escritorio
  (`secret-tool store --label="Zenodo token" service zenodo`) en vez de en
  `$ZENODO_TOKEN`; `tools/zenodo.py check-token` dice si hay uno.

- **Versiones firmadas.** La etiqueta de cada versión va firmada, y cada
  archivo publicado lleva su firma (`ARCHIVO.asc`), con `SHA256SUMS`,
  firmado también, y la clave pública `packaging/RPM-GPG-KEY-py-pdfocr`,
  todo adjunto a la versión. `tools/release.py` los firma
  (`tools/sign_release.py`) y comprueba cada firma con solo esa clave antes
  de publicar nada; una etiqueta sin firma que ya esté en el commit se firma
  y se sube de nuevo.
- `tools/zenodo.py` prepara el depósito de una versión en Zenodo. `collect`
  deja en `dist/zenodo/` el árbol de la etiqueta como
  `py-pdfocr-VERSIÓN-source.tar.gz`, con su firma, un `SHA256SUMS` del
  depósito, firmado, y la clave pública, y comprueba cada firma con solo esa
  clave (`--packages` añade los archivos de la versión). `upload` lo sube a
  Zenodo como borrador, versión nueva del depósito si ya lo hay, y nunca lo
  publica. `tools/release.py` reúne ahora el depósito después de la etiqueta
  y lo sube como borrador, salvo con `--no-zenodo`. Los metadatos están en
  `.zenodo.json`.
- Las pruebas corren en paralelo, cada archivo en su proceso
  (`tools/test.py`), también en la publicación.

## 1.0.4 — 2026-11-21

- El software libre que usa py-pdfocr, con la licencia de cada uno, está en
  `docs/TERCEROS_es.md` (en inglés, `docs/THIRD-PARTY.md`), y los README
  enlazan a esa lista.

## 1.0.3 — 2026-11-21

La primera versión publicada.

- `py-pdfocr read` (o solo `py-pdfocr ARCHIVO.pdf`): el texto de las páginas
  escaneadas, leído por tesseract y escrito bajo sus imágenes, invisible; en
  una copia, en el mismo archivo (`-i`) o en una carpeta (`--output-dir`);
  las páginas elegidas (`--pages`), giradas antes si están de lado
  (`--rotate`), leídas a una resolución (`--dpi`), varias a la vez (`-j`), y
  las palabras dudosas listadas (`--report`, `--doubtful`). Muestra en la
  terminal cuánto ha leído y pide la contraseña de un PDF protegido si no
  se da.
- `py-pdfocr images`: un PDF hecho de imágenes, y luego leído.
- `py-pdfocr scanned`: qué páginas son escaneos sin texto.
- `py-pdfocr languages`, `download`, `remove`: los idiomas de tesseract y
  sus modelos más precisos (tessdata_best), descargados, actualizados o
  quitados.
- `py-pdfocr settings`: los idiomas que se leen por omisión y el idioma de
  la interfaz (inglés, español).
- Un PDF protegido (AES-256) conserva su texto y sus imágenes al guardarse
  de nuevo: la clave ya no se estropea al preguntar, después de abrirlo con
  ella, si el archivo necesita contraseña.
- Tesseract se encuentra donde lo ponen sus instaladores para Windows y
  macOS, aunque no esté en el PATH.
- Instaladores para Linux, macOS y Windows (`install/`), probados en los
  tres sistemas, y una AppImage para Linux; ambos con PyMuPDF solo, sin las
  bibliotecas que trae para analizar la disposición de las páginas, que
  py-pdfocr no usa.
