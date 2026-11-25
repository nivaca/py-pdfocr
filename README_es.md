py-pdfocr
=========

*(English: [README.md](README.md))*

py-pdfocr lee con [tesseract](https://github.com/tesseract-ocr/tesseract)
el texto de las páginas escaneadas de un PDF y lo escribe en el PDF,
invisible, bajo las imágenes de las páginas, para que se pueda buscar,
copiar y marcar. Funciona en la línea de órdenes: lee las páginas de los
PDF, hace un PDF de imágenes y lo lee, dice qué páginas son escaneos y
administra los idiomas de tesseract, con la descarga de sus modelos más
precisos.

Su código se adaptó después y se incluyó en
[py-pdftools](https://github.com/nivaca/py-pdftools), mi editor de
documentos PDF, donde tiene una ventana propia (véase «py-pdfocr y
py-pdftools»).

La línea de órdenes está en inglés y en español. Funciona en Linux, macOS y
Windows. Esta es la versión 1.0.5.

Soy Nicolas Vaughan (<nicolasvaughan@proton.me>) y lo escribí en 2026. Es
software libre, bajo la Licencia Pública General de GNU, versión 3 o
posterior (véase «Licencia»).

Instalación
-----------

py-pdfocr necesita el programa tesseract, con los idiomas de los
documentos:

* Fedora: `sudo dnf install tesseract tesseract-langpack-spa …`
* Debian y Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-spa …`
* macOS: `brew install tesseract tesseract-lang`
* Windows: `winget install UB-Mannheim.TesseractOCR` (su instalador
  pregunta los idiomas; py-pdfocr lo encuentra en `Program Files` aunque
  no esté en el PATH)

**La AppImage** (Linux) trae todo lo demás, Python incluido. Descargue
`py-pdfocr-1.0.5-x86_64.AppImage` de las
[versiones publicadas](https://github.com/nivaca/py-pdfocr/releases),
hágala ejecutable y úsela como la orden:

    $ chmod +x py-pdfocr-1.0.5-x86_64.AppImage
    $ ./py-pdfocr-1.0.5-x86_64.AppImage scan.pdf

**Los instaladores** necesitan Python 3.14 o posterior. Desde el código
(clonado, o el ZIP de una versión descomprimido):

    $ install/install.sh                Linux y macOS: instalar, o actualizar
    $ install/install.sh --uninstall
    > install\install.bat               Windows: instalar, o actualizar
    > install\install.bat -Uninstall

Cada uno hace un entorno de Python propio para py-pdfocr y lo instala allí
con PyMuPDF (descargado de PyPI, así que la primera vez necesita internet).
En Linux y macOS la orden `py-pdfocr` se enlaza en `~/bin` o
`~/.local/bin`; en Windows va a `%LOCALAPPDATA%\py-pdfocr\bin`, que se
agrega al PATH del usuario. Nada necesita permisos de administrador, y al
desinstalar se conservan los ajustes y los modelos descargados. Los
instaladores se prueban en los tres sistemas con cada cambio
(`.github/workflows/installers.yml`).

**Con [uv](https://docs.astral.sh/uv/)**, desde el código:

    $ git clone https://github.com/nivaca/py-pdfocr.git
    $ cd py-pdfocr
    $ uv run py-pdfocr --help
    $ uv tool install .                 o como una orden propia

Leer páginas escaneadas
-----------------------

    $ py-pdfocr scan.pdf                     escribe scan-ocr.pdf a su lado
    $ py-pdfocr scan.pdf -l lat+spa          en latín y español, el latín primero
    $ py-pdfocr scan.pdf -i                  sobre el mismo archivo
    $ py-pdfocr *.pdf --output-dir leidos/   varios, en una carpeta
    $ py-pdfocr scan.pdf --pages 3-10,LAST -o salida.pdf

`read` es la orden cuando no se da ninguna (`py-pdfocr read scan.pdf` es lo
mismo). Solo se leen las páginas que son escaneos: las que tienen imágenes y
ningún texto. Una página que ya tiene texto se deja como está, para que su
texto no quede dos veces, y un archivo puede leerse de nuevo sin daño.

Las palabras se escriben donde la imagen las muestra, tan anchas como son
allí, en texto invisible (modo de dibujo 3). Se leen varias páginas a la
vez, cada una en un proceso propio (`-j` dice cuántas; por omisión, la mitad
de los procesadores). Cada página se dibuja a 300 ppp (`--dpi`) para
tesseract.

`--rotate` gira primero las páginas escaneadas de lado o al revés, y las
páginas del PDF giran con ellas. Necesita el modelo `osd` de tesseract, que
averigua cómo está puesta una página: `py-pdfocr download osd`.

Tesseract dice qué tan seguro está de cada palabra, de 0 a 100. Las que
quedan por debajo de 60 (`--doubtful`) son dudosas; `--report` las lista,
una por línea, como página, confianza y palabra, separadas por tabuladores
(con varios PDF, primero el archivo), para revisarlas luego en el PDF.

Un PDF con contraseña se abre con `--password`; si no, la contraseña se pide
en la terminal. La copia conserva la protección del original.

Un PDF hecho de imágenes
------------------------

    $ py-pdfocr images p1.jpg p2.jpg p3.tif -o libro.pdf -l spa
    $ py-pdfocr images *.png -o libro.pdf --paper A4 --margin 10 --no-ocr

Cada imagen es una página (cada cuadro, en un TIFF de varios); la página es
del tamaño de la imagen, o del papel de `--paper` (A3, A4, A5, Letter,
Legal), vertical u horizontal según la imagen (o `--portrait`,
`--landscape`). Luego se lee su texto, como arriba, salvo con `--no-ocr`.

Qué páginas son escaneos
------------------------

    $ py-pdfocr --interface es scanned *.pdf
    scan.pdf: 12 páginas son escaneos sin texto (de 14): 1-10, 13-14

Idiomas
-------

    $ py-pdfocr languages              los que tesseract puede leer aquí
    $ py-pdfocr languages --all grc    también los que se pueden descargar
    $ py-pdfocr download lat osd       sus modelos más precisos
    $ py-pdfocr remove lat             se vuelve a usar el instalado

Los idiomas que vienen con tesseract salen de los paquetes del sistema.
Tesseract tiene además modelos más precisos de cada idioma
([tessdata_best](https://github.com/tesseract-ocr/tessdata_best)), más
lentos pero mejores en páginas difíciles: `download` los pone en la carpeta
propia de py-pdfocr (`~/.local/share/py-pdfocr/tessdata`; `%LOCALAPPDATA%`
en Windows), y se usan en lugar de los instalados, marcados con ★ en la
lista. Descargarlos de nuevo los actualiza. Es lo único que py-pdfocr hace
en internet, y la petición no lleva nada sobre el usuario.

Ajustes
-------

    $ py-pdfocr settings --languages lat+spa    leer en estos por omisión
    $ py-pdfocr settings --interface es         la línea de órdenes en español
    $ py-pdfocr --interface en languages        en inglés, solo esta vez

Se guardan en `~/.config/py-pdfocr/config.toml` (en macOS, en
`~/Library/Application Support/py-pdfocr`; en Windows, en
`%APPDATA%\py-pdfocr`; `PY_PDFOCR_CONFIG` nombra otra carpeta).

py-pdfocr y py-pdftools
-----------------------

py-pdfocr vino primero. Su código (la lectura de las páginas, los idiomas y
los modelos, el PDF hecho de imágenes) se adaptó después y se incluyó en
py-pdftools, que edita documentos PDF en una ventana. Allí tiene un modo
propio y algo que py-pdfocr deja fuera a propósito: las palabras dudosas se
muestran junto a sus imágenes, para corregirlas antes de escribir el texto.
Aquí solo se listan (`--report`).

py-pdftools guarda los modelos que descarga en su propia carpeta
(`~/.local/share/py-pdftools/tessdata`). py-pdfocr también los usa, para no
descargar dos veces el mismo modelo; `languages` muestra dónde está cada
uno, y solo py-pdftools quita los suyos.

Pruebas
-------

Hay 27 pruebas (`uv run pytest`): la lectura de las páginas, con el lugar y
la confianza de las palabras; las palabras dudosas; las páginas giradas;
los idiomas y modelos, y su descarga; cada orden de la línea de órdenes;
los PDF con contraseña; la interfaz en español, con todos sus textos
traducidos; y la versión, la misma en todas partes. Las pruebas que leen
necesitan tesseract con inglés, y las que giran páginas, el modelo `osd`
(sin él se omiten).

Licencia
--------

py-pdfocr es software libre: puede redistribuirlo o modificarlo bajo los
términos de la Licencia Pública General de GNU publicada por la Free
Software Foundation, versión 3 o (a su elección) cualquier versión
posterior (véase [LICENSE](LICENSE)). Usa PyMuPDF (GNU AGPL 3) y ejecuta
tesseract (Licencia Apache 2.0), cuyos modelos tienen la misma licencia. La
AppImage incluye un Python del proyecto python-appimage (licencia de la
Python Software Foundation). El software libre que usa py-pdfocr, con la
licencia de cada uno, está en [docs/TERCEROS_es.md](docs/TERCEROS_es.md).
