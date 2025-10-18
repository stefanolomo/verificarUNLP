import fitz  # PyMuPDF
import os
import json
import hashlib
import io
import sys
import argparse
from PIL import Image
from pyzbar.pyzbar import decode

def process_pdf(pdf_path, json_output_path, images_output_dir):
    """
    Procesa un archivo PDF para extraer texto, imágenes y metadatos,
    y guarda el resultado en un archivo JSON.
    """
    print(f"--- Iniciando procesamiento de: {pdf_path} ---")

    # 1. Asegurarse de que el directorio de salida para imágenes exista
    if not os.path.exists(images_output_dir):
        os.makedirs(images_output_dir)

    # Estructura principal para los datos
    final_data = {
        "nombre_archivo": os.path.basename(pdf_path),
        "ruta_completa": pdf_path,
        "metadata_pdf": {},
        "texto_por_pagina": {},
        "cantidad_imagenes": 0,
        "imagenes": []
    }

    try:
        # 2. Abrir el archivo PDF
        with fitz.open(pdf_path) as doc:
            final_data["metadata_pdf"] = doc.metadata
            print(f"Procesando {doc.page_count} páginas...")

            # 3. Iterar a través de cada página
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_label = f"pagina_{page_num + 1}"

                final_data["texto_por_pagina"][page_label] = page.get_text("text")
                image_list = page.get_images(full=True)

                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_hash = hashlib.sha256(image_bytes).hexdigest()

                    # Lógica de detección de QR
                    is_qr, qr_data = False, None
                    try:
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        width, height = pil_image.size
                        decoded_objects = decode(pil_image)
                        if decoded_objects:
                            for obj in decoded_objects:
                                if obj.type == 'QRCODE':
                                    is_qr = True
                                    qr_data = obj.data.decode('utf-8')
                                    print(f"  -> ¡QR encontrado en la página {page_num + 1}!")
                                    break
                    except Exception:
                        width, height = 0, 0

                    # Guardar la imagen
                    image_filename = f"{page_label}_img_{img_index + 1}_{image_hash[:8]}.{image_ext}"
                    image_path = os.path.join(images_output_dir, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

                    # Obtener posición
                    try:
                        bbox = page.get_image_bbox(img)
                        position_dict = {"x0": bbox.x0, "y0": bbox.y0, "x1": bbox.x1, "y1": bbox.y1}
                    except ValueError:
                        position_dict = "No disponible"

                    # Ensamblar información de la imagen
                    image_info = {
                        "nombre_imagen": image_filename,
                        "pagina": page_num + 1,
                        "hash_sha256": image_hash,
                        "es_qr": is_qr,
                        "datos_qr": qr_data,
                        "posicion": position_dict,
                        "tamano_bytes": len(image_bytes),
                        "dimensiones": {"ancho": width, "alto": height},
                        "metadata_interna": {k: v for k, v in base_image.items() if k != 'image'},
                    }
                    final_data["imagenes"].append(image_info)

        # 4. Actualizar conteo y guardar JSON
        final_data["cantidad_imagenes"] = len(final_data["imagenes"])
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)

        print("\n--- ¡Proceso Completado! ---")
        print(f"✓ Se extrajeron {final_data['cantidad_imagenes']} imágenes en la carpeta '{images_output_dir}'.")
        print(f"✓ Se ha creado el archivo de datos '{json_output_path}'.")
        return True

    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo '{pdf_path}': {e}", file=sys.stderr)
        return False

def main():
    # Configuración del parser de argumentos
    parser = argparse.ArgumentParser(
        description="Extrae texto, imágenes y metadatos de un archivo PDF y los guarda en un JSON.",
        formatter_class=argparse.RawTextHelpFormatter # Para un mejor formato de la ayuda
    )

    # Argumento posicional obligatorio: el archivo PDF
    parser.add_argument("pdf_file", help="Ruta al archivo PDF que se va a procesar.")

    # Argumento opcional: nombre base para los archivos de salida
    parser.add_argument(
        "-o", "--output",
        help="Nombre base para los archivos de salida (sin extensión).\n"
             "Por defecto, se usa el nombre del archivo PDF de entrada."
    )

    args = parser.parse_args()

    # Verificar si el archivo de entrada existe
    if not os.path.exists(args.pdf_file):
        print(f"Error: El archivo '{args.pdf_file}' no fue encontrado.", file=sys.stderr)
        sys.exit(1)

    # Determinar los nombres de los archivos de salida
    if args.output:
        output_base_name = args.output
    else:
        # Usa el nombre del PDF sin la extensión .pdf
        base = os.path.basename(args.pdf_file)
        output_base_name = os.path.splitext(base)[0]

    # Construir las rutas completas para los archivos de salida
    json_path = f"{output_base_name}.json"
    images_dir = f"{output_base_name}_imagenes"

    # Llamar a la función principal de procesamiento
    process_pdf(args.pdf_file, json_path, images_dir)

if __name__ == "__main__":
    main()
