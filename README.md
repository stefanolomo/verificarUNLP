# 🧾 Verificación de Certificados de Alumnos Regulares — UNLP

Este proyecto contiene una serie de **scripts en Python** diseñados para **automatizar la verificación de certificados de alumnos regulares** emitidos por la **Universidad Nacional de La Plata (UNLP)**.
El proceso combina **extracción de datos de PDFs** (texto, imágenes, códigos QR) con **validación estructurada** mediante un archivo de configuración.



## 📂 Estructura del Proyecto

```
.
├── authenticator/
│   ├── auther.py          # Script de validación de documentos según reglas definidas
│   └── config.json        # Reglas de validación (textos e imágenes esperadas)
│
├── jsonCreator/
│   └── main.py            # Script para extraer datos estructurados de un PDF
│
├── .gitignore
├── LICENSE
└── README.md
```



## ⚙️ Descripción General

### 🧠 1. `jsonCreator/main.py`

Script encargado de **procesar un PDF** (por ejemplo, un certificado) y generar:

* Un archivo `.json` con:

  * Texto extraído por página
  * Imágenes embebidas (metadatos, dimensiones, posición, hash SHA-256)
  * Metadatos del documento
* Una carpeta con las **imágenes extraídas** del PDF (incluyendo el QR, si existe)

> Este módulo utiliza `PyMuPDF`, `Pillow` y `pyzbar` para la extracción de texto e imágenes, y detección de códigos QR.

#### Uso:

```bash
python3 jsonCreator/main.py certificado.pdf
```

Opcionalmente se puede especificar un nombre base para los archivos de salida:

```bash
python3 jsonCreator/main.py certificado.pdf -o salida_certificado
```

Esto generará:

```
salida_certificado.json
salida_certificado_imagenes/
```



### 🔍 2. `authenticator/auther.py`

Script que **valida** el archivo JSON generado por el módulo anterior contra las **reglas definidas en `config.json`**.

Valida:

* Que las **imágenes esperadas** (identificadas por su hash SHA-256) estén presentes.
* Que los **textos obligatorios** estén contenidos en el documento (con normalización de espacios y minúsculas).

#### Uso:

```bash
python3 authenticator/auther.py salida_certificado.json
```

#### Ejemplo de salida:

```
Validando 'certificado_alumno.pdf'...
Verificando hashes de imágenes requeridas...
Verificando textos obligatorios en la página 1...

 RESULTADO DE LA VALIDACIÓN 
El documento cumple con todas las reglas de validación.

ESTADO: APROBADO
```

O bien:

```
 RESULTADO DE LA VALIDACIÓN 
El documento NO cumple con las siguientes reglas:
  - Error de texto: La cadena obligatoria 'constancia de alumno regular observaciones' no se encontró en la página 1.

ESTADO: RECHAZADO
```



## 🧩 Archivo de Configuración (`config.json`)

Define las **reglas de validación** para cada documento:

```json
{
  "imagenes_a_validar": [
    {
      "hash_sha256": "ac6842fa67bf136c291f497859e19f5fc55c84b239b3738e9ccdb9009f04ebc9",
      "posicion_esperada": { "x0": 62.0, "y0": 25.0, "x1": 154.0, "y1": 52.1 }
    }
  ],
  "textos_a_validar": [
    "este certificado podrá ser validado ingresando a https://autogestion.guarani.unlp.edu.ar/validador_certificados...",
    "constancia de alumno regular observaciones"
  ]
}
```

Esto permite ajustar fácilmente las reglas según la estructura de los certificados generados por el sistema Guaraní.



## 🧱 Dependencias

Instalá las dependencias necesarias con:

```bash
pip install PyMuPDF Pillow pyzbar
```

> En Fedora u otras distribuciones Linux, puede ser necesario instalar `zbar` previamente:

```bash
sudo dnf install zbar
```



## 🧪 Ejemplo de Flujo Completo

1. **Extraer datos del certificado PDF:**

   ```bash
   python3 jsonCreator/main.py certificado_alumno.pdf
   ```

   → genera `certificado_alumno.json` y carpeta `certificado_alumno_imagenes/`

2. **Validar los datos extraídos:**

   ```bash
   python3 authenticator/auther.py certificado_alumno.json
   ```

3. **Interpretar el resultado:**

   * `APROBADO` → certificado válido
   * `RECHAZADO` → faltan textos o imágenes requeridas



## 📜 Licencia

Este proyecto está bajo la licencia [MIT](./LICENSE).
