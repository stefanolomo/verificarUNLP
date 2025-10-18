import json
import sys
import os
import argparse
import re

def normalize_text(text):
    """
    Limpia y normaliza una cadena de texto para una comparación robusta.
    - Convierte a minúsculas.
    - Reemplaza saltos de línea y otros espacios en blanco por un solo espacio.
    - Elimina espacios al principio y al final.
    """
    if not isinstance(text, str):
        return ""
    # Reemplaza cualquier secuencia de uno o más caracteres de espacio en blanco (\s+) con un solo espacio
    normalized = re.sub(r'\s+', ' ', text)
    # Convierte a minúsculas y elimina espacios sobrantes en los extremos
    return normalized.lower().strip()

def validate_document(data, config):
    """
    Valida los datos de un documento extraído contra un conjunto de reglas de configuración.
    """
    errors = []

    # --- 1. Validación de Imágenes ---
    print("Verificando hashes de imágenes requeridas...")
    required_hashes = {img['hash_sha256'] for img in config.get('imagenes_a_validar', [])}
    found_hashes = {img['hash_sha256'] for img in data.get('imagenes', [])}
    missing_hashes = required_hashes - found_hashes

    if missing_hashes:
        for missing_hash in missing_hashes:
            errors.append(f"Error de imagen: El hash requerido '{missing_hash}' no fue encontrado.")

    # --- 2. Validación de Textos (con normalización) ---
    print("Verificando textos obligatorios en la página 1...")
    required_texts = config.get('textos_a_validar', [])
    page_one_text = data.get('texto_por_pagina', {}).get('pagina_1', '')

    # Normalizamos el texto completo de la página 1 UNA SOLA VEZ para eficiencia
    normalized_page_text = normalize_text(page_one_text)

    if not normalized_page_text and required_texts:
        errors.append("Error de texto: No se encontró texto en la 'pagina_1' del documento.")
    else:
        for text_to_find in required_texts:
            # Normalizamos también la cadena que estamos buscando
            normalized_text_to_find = normalize_text(text_to_find)

            if normalized_text_to_find not in normalized_page_text:
                errors.append(f"Error de texto: La cadena obligatoria '{text_to_find}' no se encontró en la página 1.")

    # --- Resultado Final ---
    return not errors, errors

def main():
    parser = argparse.ArgumentParser(
        description="Valida un archivo JSON de datos de PDF contra un 'config.json'."
    )
    parser.add_argument("data_file", help="Ruta al archivo JSON generado por el script de extracción.")
    args = parser.parse_args()

    data_json_path = args.data_file
    # __file__ es la ruta del script actual. os.path.dirname obtiene su directorio.
    config_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

    if not os.path.exists(data_json_path):
        print(f"Error: El archivo de datos '{data_json_path}' no fue encontrado.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(config_json_path):
        print(f"Error: El archivo de configuración '{config_json_path}' no fue encontrado.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(data_json_path, 'r', encoding='utf-8') as f:
            pdf_data = json.load(f)

        with open(config_json_path, 'r', encoding='utf-8') as f:
            config_rules = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: No se pudo decodificar uno de los archivos JSON. {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Validando '{pdf_data.get('nombre_archivo', 'archivo desconocido')}'...")

    is_valid, validation_errors = validate_document(pdf_data, config_rules)

    print("\n--- RESULTADO DE LA VALIDACIÓN ---")
    if is_valid:
        print("El documento cumple con todas las reglas de validación.")
        print("\nESTADO: APROBADO")
        sys.exit(0)
    else:
        print("El documento NO cumple con las siguientes reglas:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\nESTADO: RECHAZADO")
        sys.exit(1)

if __name__ == "__main__":
    main()