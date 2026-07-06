"""
Genera (una sola vez) todas las imagenes PNG usadas por la interfaz grafica:
las 40 cartas del mazo de Truco, el dorso, los fondos y las pantallas de
victoria/derrota. Requiere Pillow instalado ('pip install pillow').

Ejecutar desde la carpeta del proyecto:  python assets/generar_assets.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

CARPETA_ASSETS = os.path.dirname(os.path.abspath(__file__))
CARPETA_CARTAS = os.path.join(CARPETA_ASSETS, "cartas")

ANCHO_CARTA, ALTO_CARTA = 120, 172
ANCHO_PANTALLA, ALTO_PANTALLA = 900, 800

PALOS = {
    "oro": {"claro": (255, 215, 0), "oscuro": (139, 101, 8)},
    "copa": {"claro": (231, 76, 60), "oscuro": (120, 30, 20)},
    "espada": {"claro": (93, 156, 236), "oscuro": (25, 55, 120)},
    "basto": {"claro": (102, 187, 106), "oscuro": (20, 80, 30)},
}
VALORES = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)


def _fuente(tamano, negrita=True):
    nombres = ["arialbd.ttf", "Arial Bold.ttf"] if negrita else ["arial.ttf", "Arial.ttf"]
    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def _dibujar_icono_palo(draw, palo_nombre, cx, cy, escala, color):
    """Dibuja un icono geometrico simple representando el palo, centrado en (cx, cy)."""
    s = escala
    if palo_nombre == "oro":
        draw.ellipse([cx - s, cy - s, cx + s, cy + s], fill=color, outline=(0, 0, 0, 80), width=2)
        draw.ellipse([cx - s * 0.55, cy - s * 0.55, cx + s * 0.55, cy + s * 0.55],
                     outline=(0, 0, 0, 90), width=2)
    elif palo_nombre == "copa":
        draw.polygon([
            (cx - s, cy - s), (cx + s, cy - s),
            (cx + s * 0.55, cy + s * 0.35), (cx - s * 0.55, cy + s * 0.35),
        ], fill=color)
        draw.rectangle([cx - s * 0.18, cy + s * 0.3, cx + s * 0.18, cy + s * 0.85], fill=color)
        draw.rectangle([cx - s * 0.55, cy + s * 0.75, cx + s * 0.55, cy + s * 0.95], fill=color)
    elif palo_nombre == "espada":
        draw.rectangle([cx - s * 0.14, cy - s, cx + s * 0.14, cy + s * 0.7], fill=color)
        draw.polygon([(cx - s * 0.14, cy - s), (cx + s * 0.14, cy - s), (cx, cy - s * 1.3)], fill=color)
        draw.rectangle([cx - s * 0.5, cy + s * 0.35, cx + s * 0.5, cy + s * 0.5], fill=color)
        draw.ellipse([cx - s * 0.22, cy + s * 0.68, cx + s * 0.22, cy + s * 0.95], fill=color)
    elif palo_nombre == "basto":
        draw.rounded_rectangle([cx - s * 0.28, cy - s, cx + s * 0.28, cy + s], radius=int(s * 0.28), fill=color)
        draw.ellipse([cx - s * 0.42, cy - s * 1.15, cx + s * 0.42, cy - s * 0.4], fill=color)


def _dibujar_carta(valor, palo_nombre):
    colores = PALOS[palo_nombre]
    color_claro = colores["claro"]
    color_oscuro = colores["oscuro"]

    img = Image.new("RGBA", (ANCHO_CARTA, ALTO_CARTA), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, ANCHO_CARTA - 3, ALTO_CARTA - 3], radius=16,
                           fill=(255, 255, 255, 255), outline=color_oscuro, width=5)

    texto_valor = str(valor)
    fuente_grande = _fuente(30)
    fuente_chica = _fuente(16)

    draw.text((12, 8), texto_valor, font=fuente_grande, fill=color_oscuro)
    _dibujar_icono_palo(draw, palo_nombre, ANCHO_CARTA // 2, ALTO_CARTA // 2 + 6, 30, color_claro)

    texto_girado = Image.new("RGBA", (60, 40), (0, 0, 0, 0))
    draw_girado = ImageDraw.Draw(texto_girado)
    draw_girado.text((0, 0), texto_valor, font=fuente_grande, fill=color_oscuro)
    texto_girado = texto_girado.rotate(180, expand=True)
    img.paste(texto_girado, (ANCHO_CARTA - 60 - 4, ALTO_CARTA - 40 - 4), texto_girado)

    nombre_archivo = os.path.join(CARPETA_CARTAS, f"{valor}_{palo_nombre}.png")
    img.save(nombre_archivo)


def _dibujar_dorso():
    img = Image.new("RGBA", (ANCHO_CARTA, ALTO_CARTA), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color_fondo = (26, 60, 46)
    color_linea = (212, 175, 55)
    draw.rounded_rectangle([2, 2, ANCHO_CARTA - 3, ALTO_CARTA - 3], radius=16,
                           fill=color_fondo, outline=color_linea, width=5)
    paso = 14
    for offset in range(-ALTO_CARTA, ANCHO_CARTA, paso):
        draw.line([(offset, ALTO_CARTA), (offset + ALTO_CARTA, 0)], fill=(255, 255, 255, 25), width=3)
    draw.ellipse([ANCHO_CARTA // 2 - 22, ALTO_CARTA // 2 - 22, ANCHO_CARTA // 2 + 22, ALTO_CARTA // 2 + 22],
                outline=color_linea, width=3)
    fuente = _fuente(14)
    draw.text((ANCHO_CARTA // 2 - 16, ALTO_CARTA // 2 - 10), "T", font=fuente, fill=color_linea)
    img.save(os.path.join(CARPETA_CARTAS, "dorso.png"))


def _fondo_liso_con_vineta(color_base, color_borde):
    img = Image.new("RGB", (ANCHO_PANTALLA, ALTO_PANTALLA), color_base)
    draw = ImageDraw.Draw(img)
    pasos = 40
    for i in range(pasos):
        t = i / pasos
        color = tuple(int(color_base[c] * (1 - t) + color_borde[c] * t) for c in range(3))
        draw.rectangle([i * 4, i * 3, ANCHO_PANTALLA - i * 4, ALTO_PANTALLA - i * 3], outline=color)
    return img


def _dibujar_fondo_inicio():
    img = _fondo_liso_con_vineta((21, 87, 57), (8, 35, 22))
    draw = ImageDraw.Draw(img)
    fuente = _fuente(52)
    texto = "TRUCO"
    bbox = draw.textbbox((0, 0), texto, font=fuente)
    ancho_texto = bbox[2] - bbox[0]
    draw.text(((ANCHO_PANTALLA - ancho_texto) // 2, 70), texto, font=fuente, fill=(212, 175, 55))
    fuente_chica = _fuente(20, negrita=False)
    subtitulo = "Argentino"
    bbox2 = draw.textbbox((0, 0), subtitulo, font=fuente_chica)
    ancho_sub = bbox2[2] - bbox2[0]
    draw.text(((ANCHO_PANTALLA - ancho_sub) // 2, 135), subtitulo, font=fuente_chica, fill=(230, 230, 230))
    img.save(os.path.join(CARPETA_ASSETS, "fondo_inicio.png"))


def _dibujar_fondo_mesa():
    img = _fondo_liso_con_vineta((13, 71, 48), (5, 26, 17))
    img.save(os.path.join(CARPETA_ASSETS, "fondo_mesa.png"))


def _dibujar_banner(nombre_archivo, texto_grande, texto_chico, color_fondo, color_acento, forma):
    ancho, alto = 520, 300
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, ancho - 5, alto - 5], radius=24, fill=color_fondo, outline=color_acento, width=6)

    cx, cy = ancho // 2, 95
    if forma == "trofeo":
        draw.polygon([(cx - 55, cy - 45), (cx + 55, cy - 45), (cx + 32, cy + 30), (cx - 32, cy + 30)],
                     fill=color_acento)
        draw.ellipse([cx - 80, cy - 45, cx - 40, cy + 5], outline=color_acento, width=8)
        draw.ellipse([cx + 40, cy - 45, cx + 80, cy + 5], outline=color_acento, width=8)
        draw.rectangle([cx - 12, cy + 28, cx + 12, cy + 55], fill=color_acento)
        draw.rectangle([cx - 40, cy + 55, cx + 40, cy + 70], fill=color_acento)
    else:
        draw.line([cx - 45, cy - 45, cx + 45, cy + 45], fill=color_acento, width=14)
        draw.line([cx - 45, cy + 45, cx + 45, cy - 45], fill=color_acento, width=14)

    fuente_grande = _fuente(34)
    bbox = draw.textbbox((0, 0), texto_grande, font=fuente_grande)
    ancho_texto = bbox[2] - bbox[0]
    draw.text(((ancho - ancho_texto) // 2, 175), texto_grande, font=fuente_grande, fill=color_acento)

    fuente_chica = _fuente(16, negrita=False)
    bbox2 = draw.textbbox((0, 0), texto_chico, font=fuente_chica)
    ancho_chico = bbox2[2] - bbox2[0]
    draw.text(((ancho - ancho_chico) // 2, 225), texto_chico, font=fuente_chica, fill=(230, 230, 230))

    img.save(os.path.join(CARPETA_ASSETS, nombre_archivo))


def generar_todo():
    os.makedirs(CARPETA_CARTAS, exist_ok=True)
    for palo_nombre in PALOS:
        for valor in VALORES:
            _dibujar_carta(valor, palo_nombre)
    _dibujar_dorso()
    _dibujar_fondo_inicio()
    _dibujar_fondo_mesa()
    _dibujar_banner("ganaste.png", "GANASTE LA PARTIDA", "Volve a jugar cuando quieras",
                     (20, 70, 35, 235), (212, 175, 55), "trofeo")
    _dibujar_banner("perdiste.png", "PERDISTE LA PARTIDA", "La proxima va a salir mejor",
                     (60, 20, 20, 235), (231, 76, 60), "equis")
    print("Assets generados en:", CARPETA_ASSETS)


if __name__ == "__main__":
    generar_todo()
