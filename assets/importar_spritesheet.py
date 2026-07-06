"""
Importa las cartas reales de la baraja espanola desde un archivo JSON tipo
"hoja de sprites" (con las 50 imagenes embebidas en base64, una por sprite)
y las guarda como los 48 PNG individuales que usa la interfaz grafica
('assets/cartas/{valor}_{palo}.png'), mas el dorso ('assets/cartas/dorso.png').

El orden de los 50 sprites en el archivo original es:
  1-12:  Oro   (valores 1 a 12, en orden)
  13-24: Copa  (valores 1 a 12, en orden)
  25-36: Espada (valores 1 a 12, en orden)
  37-48: Basto (valores 1 a 12, en orden)
  49:    carta en blanco sin usar (se descarta)
  50:    dorso de la carta

Uso: python assets/importar_spritesheet.py "C:\\ruta\\al\\spritesheet.json"
"""

import base64
import json
import os
import sys

CARPETA_ASSETS = os.path.dirname(os.path.abspath(__file__))
CARPETA_CARTAS = os.path.join(CARPETA_ASSETS, "cartas")

PALOS_EN_ORDEN = ("oro", "copa", "espada", "basto")
VALORES_EN_ORDEN = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)


def _nombres_de_sprites():
    """POST: retorna una tupla con el nombre de archivo destino para cada uno de los 50 sprites, en orden."""
    nombres = []
    for palo in PALOS_EN_ORDEN:
        for valor in VALORES_EN_ORDEN:
            nombres.append(f"{valor}_{palo}.png")
    nombres.append(None)  # sprite 49: carta en blanco, se descarta
    nombres.append("dorso.png")  # sprite 50
    return tuple(nombres)


def importar(ruta_json):
    """
    PRE: 'ruta_json' apunta al archivo JSON con los 50 sprites embebidos en base64.
    POST: se sobrescriben los archivos correspondientes en 'assets/cartas/'
          con las imagenes reales extraidas del archivo.
    """
    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    sprites = datos["layers"][0]["sprites"]
    if len(sprites) != 50:
        raise ValueError(f"Se esperaban 50 sprites, se encontraron {len(sprites)}")

    nombres_destino = _nombres_de_sprites()
    os.makedirs(CARPETA_CARTAS, exist_ok=True)

    guardados = 0
    for sprite, nombre_destino in zip(sprites, nombres_destino):
        if nombre_destino is None:
            continue
        base64_datos = sprite["base64"].split(",", 1)[1]
        contenido = base64.b64decode(base64_datos)
        ruta_destino = os.path.join(CARPETA_CARTAS, nombre_destino)
        with open(ruta_destino, "wb") as salida:
            salida.write(contenido)
        guardados += 1

    print(f"Listo: se guardaron {guardados} imagenes reales en {CARPETA_CARTAS}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python assets/importar_spritesheet.py \"C:\\ruta\\al\\spritesheet.json\"")
        sys.exit(1)
    importar(sys.argv[1])
