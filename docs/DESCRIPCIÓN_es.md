# py-pdfocr 1.0.5: descripción

## Análisis

py-pdfocr lee con el programa tesseract el texto de las páginas escaneadas de un PDF y lo escribe en el mismo PDF, invisible, bajo las imágenes de las páginas, para que pueda buscarse, copiarse y marcarse. Fue desarrollado en noviembre de 2026 por Nicolas Vaughan, para los escaneos de libros y manuscritos que un visor de PDF muestra pero no deja buscar. Su código se adaptó después y se incluyó en py-pdftools, el editor de documentos PDF del mismo autor.

Tesseract lee imágenes, no PDF, y devuelve texto, no un PDF; lo que hacía falta era todo lo que lo rodea. Los requisitos fueron estos: leer solo las páginas escaneadas y dejar intactas las que ya tienen texto; escribir cada palabra donde la imagen la muestra; girar las páginas escaneadas de lado; elegir los idiomas y descargar los modelos más precisos de tesseract; listar las palabras dudosas para revisarlas; hacer un PDF de imágenes y leerlo. Debía funcionar en la línea de órdenes, en inglés y en español, en Linux, macOS y Windows, con Python 3.14 o posterior, bajo la licencia GPL 3 o posterior, y sin salir a internet salvo cuando el usuario lo pida.

Corregir las palabras dudosas antes de escribirlas quedó fuera: es editar el texto, y eso pide una ventana. py-pdftools lo hace en la suya.

## Diseño

El paquete `py_pdfocr` tiene ocho módulos. `ocr.py` es el motor: dibuja cada página en gris a 300 ppp, la hace leer por tesseract en un proceso propio, varias a la vez, y escribe las palabras donde la imagen las muestra. `cli.py` es la línea de órdenes; `images.py` hace un PDF de imágenes; `document.py` abre y guarda los PDF, con su contraseña y su protección; `pagesel.py` lee listas de páginas (`1-5, 9, LAST`); `interface.py` y `locale/es.xml` traducen la interfaz; `config.py` lee y escribe los ajustes.

Las órdenes son siete. `read` lee las páginas escaneadas y es también la orden por omisión, de modo que `py-pdfocr scan.pdf` lee un PDF. `images` hace un PDF de imágenes y lo lee, salvo con `--no-ocr`. `scanned` dice qué páginas son escaneos sin texto. `languages` imprime una tabla de los idiomas, con un filtro y, con `--all`, también los que pueden descargarse; `download` los descarga o actualiza y `remove` los quita. `settings` guarda los idiomas que se leen por omisión y el de la interfaz.

Tesseract entrega una tabla de palabras (`tessedit_create_tsv`), cada una con su rectángulo y su confianza de 0 a 100. El rectángulo se lleva a puntos de la página y la palabra se escribe en texto invisible (modo de dibujo 3), con la altura de la caja y estirada a su anchura. Por debajo de 60, una palabra es dudosa. Para cada lectura, una carpeta temporal de enlaces le da a tesseract los modelos pedidos, de manera que un modelo mejor descargado sustituye al instalado sin tocar el sistema.

### py-pdftools

py-pdftools tomó después este código y lo adaptó a un modo de su ventana. Guarda los modelos que descarga en su propia carpeta; py-pdfocr también los usa, para no bajar dos veces el mismo modelo, pero solo py-pdftools quita los suyos.

## Implementación

Está escrito en Python 3.14, con PyMuPDF como única biblioteca; tesseract se ejecuta como programa aparte. Son 22 archivos de Python, unas 4100 líneas entre programa, pruebas y herramientas, con 281 textos de la interfaz en español, 31 de ellos propios de argparse.

### La terminal

Una línea en la salida de errores se reescribe con cada página; solo aparece en una terminal y no con `-q`, así un guion encuentra en la salida solo el resultado y el informe. Ctrl+C detiene la lectura: las páginas no empezadas se cancelan, nada se escribe y el programa sale con 130. Los procesos que leen se arrancan con `spawn`, y cada uno recibe al arrancar el idioma de la interfaz, porque un proceso así empieza en inglés y sus errores salían en inglés en medio de una interfaz en español.

### Una clave estropeada

Con un PDF protegido con AES-256, la copia se escribía, se abría con su contraseña y no tenía texto. La función de guardar preguntaba `needs_pass` para saber si debía conservar la protección; preguntado después de dar la contraseña, MuPDF prueba otra vez la vacía y deja una clave equivocada, con la que se cifra todo lo que se escribe después. Ahora se pregunta a los metadatos (`encryption`), que dicen lo mismo sin tocar la clave.

### Instaladores y AppImage

Los instaladores (`install/install.sh` para Linux y macOS, `install/install.bat` para Windows) hacen un entorno propio y enlazan la orden; en Windows, un `py-pdfocr.cmd` en una carpeta propia que se agrega al PATH del usuario. El programa busca tesseract también donde lo dejan sus instaladores de Windows y macOS, fuera del PATH. PyMuPDF 2.1 arrastra onnxruntime, numpy y otras bibliotecas que py-pdfocr no usa; los instaladores y la AppImage lo instalan solo (`--no-deps`), y la AppImage, con su propio Python, bajó de 135 a 85 MB.

### Versiones firmadas y Zenodo

Desde la 1.0.5 cada versión va firmada con la clave del autor: la etiqueta, cada archivo publicado (con su `ARCHIVO.asc`) y un `SHA256SUMS`, firmado también. `tools/release.py` comprueba cada firma con solo la clave pública, en un `GNUPGHOME` propio, antes de subir nada, y se detiene si una falla. `tools/zenodo.py` reúne el árbol de la etiqueta, firmado, y lo sube a Zenodo como borrador, nueva versión del depósito si ya lo hay; nunca lo publica. La descripción es el README entero. Los campos que la API de depósitos no admite (idiomas, copyright, repositorio, lenguaje) se ponen después por la API de registros, y la subida se detiene si Zenodo no los guardó.

## Validación

Hay 47 pruebas, con pytest, cada archivo en un proceso propio (`tools/test.py`). Once son del motor: las palabras leídas en otros procesos, con su lugar y su confianza, y escritas donde la imagen las muestra; las dudosas con su imagen; la lectura detenida; el error de tesseract en el idioma de la interfaz; páginas giradas 90, 180 y 270 grados; los idiomas instalados y descargados, también los de py-pdftools; y la descarga, con sus fallos, sin red. Trece son de la línea de órdenes: cada orden, las salidas, el informe con uno y con varios PDF, el PDF protegido y su clave, y los errores. Dos son de la interfaz: todo texto del código está en el archivo español, y no sobra ninguno. Una comprueba que la versión sea la misma en todas partes. Tres son de la firma: cada archivo firmado y comprobado con la clave pública sola, la firma de otra clave rechazada y los archivos que faltan. Diecisiete son del depósito de Zenodo, contra un Zenodo imitado en la máquina: la recolección firmada, el paquete cambiado o la etiqueta de otra clave que la detienen, los metadatos, el README en HTML, el token, el borrador nuevo o la nueva versión y lo que los impide. Las pruebas firman con una clave desechable.

Las pruebas trabajan en carpetas propias y no tocan los ajustes ni los modelos del usuario; las que giran páginas necesitan el modelo `osd`. Además, el programa se probó a mano con escaneos hechos para eso, con `osd` descargado y quitado, y con Ctrl+C enviado a todo el grupo de procesos a mitad de una lectura. El instalador de Linux se probó en una carpeta personal hecha para eso, y la AppImage, con un entorno vacío. Un flujo de GitHub corre los instaladores en Linux, macOS y Windows, con tesseract, pasa las pruebas contra el programa instalado y lo desinstala.

## Plataforma

Funciona en Linux, macOS y Windows, con Python 3.14 o posterior y tesseract; la AppImage, en Linux con glibc 2.28 o posterior, solo necesita tesseract. Se desarrolló en Fedora 45 con tesseract 5.5.4, y los otros sistemas se prueban en GitHub. Los idiomas de tesseract vienen con los paquetes del sistema (`tesseract-langpack-…` en Fedora, `tesseract-ocr-…` en Debian y Ubuntu) o con su instalador. No necesita internet salvo para instalarse y para `download`, que pide los modelos al repositorio tessdata_best de tesseract sin enviar nada sobre el usuario.

## Ambiente

Fue desarrollado en Fedora 45 con uv y Python 3.14. El código está en GitHub (`github.com/nivaca/py-pdfocr`) y en Codeberg (`codeberg.org/nivaca/py-pdfocr`), donde también están las versiones publicadas, con la wheel, el paquete fuente, el ZIP y la AppImage, firmados, y la clave pública; cada versión se deposita también en Zenodo. Se instala con los instaladores de `install/`, con la AppImage o con `uv tool install .`; las pruebas se corren con `uv run python tools/test.py`. El software libre que usa, con la licencia de cada uno, está en `docs/TERCEROS_es.md` (en inglés, `docs/THIRD-PARTY.md`).

Los ajustes están en `~/.config/py-pdfocr/config.toml` (en macOS, `~/Library/Application Support/py-pdfocr`; en Windows, `%APPDATA%\py-pdfocr`; la variable `PY_PDFOCR_CONFIG` nombra otra carpeta), y los modelos descargados, en `~/.local/share/py-pdfocr/tessdata` (en Windows, `%LOCALAPPDATA%\py-pdfocr\tessdata`). El contacto del autor es nicolasvaughan@proton.me.
