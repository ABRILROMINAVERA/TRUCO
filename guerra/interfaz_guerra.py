"""Interfaz grafica (Tkinter) para La Guerra, independiente de la del Truco.

Reutiliza las mismas imagenes de cartas de 'assets/cartas/' (por
importacion de rutas, no de codigo) para mantener el mismo estilo visual
que el resto del proyecto, pero no importa nada de interfaz_grafica.py ni
de los modulos del Truco.
"""

import os
import tkinter as tk

from PIL import Image, ImageTk

from guerra.guerra import JuegoGuerra

_CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CARPETA_CARTAS = os.path.join(_CARPETA_PROYECTO, "assets", "cartas")
_ANCHO_CARTA, _ALTO_CARTA = 120, 172
_COLOR_FONDO = "#0D4730"
_COLOR_DORADO = "#D4AF37"
_RETRASO_AUTO_MS = 450
_LIMITE_RONDAS_AUTO = 5000  # tope de seguridad para el modo "Auto-jugar" (ver _paso_auto)


class GuerraGUI:
    """
    Ventana de La Guerra. A diferencia del Truco, ac no hay decisiones que
    tomar durante la partida (siempre se juega la carta de arriba del
    mazo): la interfaz solo dispara rondas -una por una, o en modo
    automatico- y muestra el resultado de cada una en la mesa y el historial.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("La Guerra")
        self.root.geometry("900x800")
        self.root.resizable(False, False)

        self.juego = JuegoGuerra("Jugador 1", "Jugador 2")
        self._auto_jugando = False
        self._rondas_auto_jugadas = 0

        self._cargar_imagenes()
        self._construir_pantalla()
        self._refrescar()

    def iniciar(self):
        """POST: arranca el bucle principal de la interfaz grafica."""
        self.root.mainloop()

    # ---------- Carga de imagenes (reutiliza assets/cartas/) ----------

    def _cargar_imagenes(self):
        self._imagenes_cartas = {}
        for archivo in os.listdir(_CARPETA_CARTAS):
            if archivo == "dorso.png":
                continue
            nombre, _ext = os.path.splitext(archivo)
            valor_str, palo_str = nombre.split("_", 1)
            imagen = Image.open(os.path.join(_CARPETA_CARTAS, archivo)).convert("RGBA").resize(
                (_ANCHO_CARTA, _ALTO_CARTA), Image.LANCZOS)
            self._imagenes_cartas[(int(valor_str), palo_str)] = ImageTk.PhotoImage(imagen)
        dorso = Image.open(os.path.join(_CARPETA_CARTAS, "dorso.png")).convert("RGBA").resize(
            (_ANCHO_CARTA, _ALTO_CARTA), Image.LANCZOS)
        self._imagen_dorso = ImageTk.PhotoImage(dorso)

    def _imagen_de_carta(self, carta):
        return self._imagenes_cartas[(carta.valor, carta.palo.value.lower())]

    # ---------- Construccion de la pantalla ----------

    def _construir_pantalla(self):
        self.frame = tk.Frame(self.root, bg=_COLOR_FONDO, padx=15, pady=15)
        self.frame.pack(expand=True, fill="both")

        tk.Label(self.frame, text="La Guerra", font=("Georgia", 22, "bold"),
                 bg=_COLOR_FONDO, fg=_COLOR_DORADO).pack(pady=(0, 10))

        self.label_estado = tk.Label(self.frame, font=("Arial", 13, "bold"),
                                      bg=_COLOR_FONDO, fg="white")
        self.label_estado.pack()

        tk.Label(self.frame, text="Mesa", font=("Arial", 10, "italic"),
                 bg=_COLOR_FONDO, fg="white").pack(pady=(15, 0))
        self.frame_mesa = tk.Frame(self.frame, bg=_COLOR_FONDO, height=200)
        self.frame_mesa.pack(pady=10)

        self.frame_botones = tk.Frame(self.frame, bg=_COLOR_FONDO)
        self.frame_botones.pack(pady=10)
        self.boton_ronda = tk.Button(self.frame_botones, text="Jugar ronda", font=("Arial", 11, "bold"),
                                      command=self._jugar_una_ronda)
        self.boton_ronda.pack(side="left", padx=5)
        self.boton_auto = tk.Button(self.frame_botones, text="Auto-jugar", font=("Arial", 11, "bold"),
                                     command=self._alternar_auto_jugar)
        self.boton_auto.pack(side="left", padx=5)
        tk.Button(self.frame_botones, text="Volver al menu", font=("Arial", 11),
                  command=self._volver_al_menu).pack(side="left", padx=5)

        tk.Label(self.frame, text="Historial", font=("Arial", 10, "italic"),
                 bg=_COLOR_FONDO, fg="white").pack(pady=(10, 0))
        frame_log = tk.Frame(self.frame, bg=_COLOR_FONDO)
        frame_log.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(frame_log)
        scrollbar.pack(side="right", fill="y")
        self.text_log = tk.Text(frame_log, height=10, state="disabled", bg="#08301F", fg="#E8E8E8",
                                 insertbackground="white", yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.text_log.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_log.yview)

    def _log(self, mensaje):
        self.text_log.configure(state="normal")
        self.text_log.insert("end", mensaje + "\n")
        self.text_log.configure(state="disabled")
        self.text_log.see("end")

    # ---------- Flujo del juego ----------

    def _refrescar(self, resultado=None):
        jugador1, jugador2 = self.juego.jugador1, self.juego.jugador2
        self.label_estado.config(
            text=f"{jugador1.nombre}: {jugador1.cartas_restantes()} cartas    |    "
                 f"{jugador2.nombre}: {jugador2.cartas_restantes()} cartas")

        for widget in self.frame_mesa.winfo_children():
            widget.destroy()
        if resultado and resultado.get("carta1") is not None:
            for nombre, carta in ((jugador1.nombre, resultado["carta1"]),
                                   (jugador2.nombre, resultado["carta2"])):
                sub = tk.Frame(self.frame_mesa, bg=_COLOR_FONDO)
                tk.Label(sub, text=nombre, font=("Arial", 9), bg=_COLOR_FONDO, fg="white").pack()
                tk.Label(sub, image=self._imagen_de_carta(carta), bg=_COLOR_FONDO).pack()
                sub.pack(side="left", padx=20)

        if self.juego.terminado():
            self.boton_ronda.config(state="disabled")
            self.boton_auto.config(state="disabled")
            self._auto_jugando = False
            ganador = self.juego.ganador()
            texto = f"¡Gano {ganador.nombre}!" if ganador is not None else "Empate: nadie se quedo con cartas."
            self._log(f"\n=== FIN DEL JUEGO: {texto} ===")

    def _jugar_una_ronda(self):
        resultado = self.juego.jugar_ronda()
        self._describir_resultado(resultado)
        self._refrescar(resultado)

    def _describir_resultado(self, resultado):
        tipo = resultado["tipo"]
        if tipo == "terminado":
            return
        if tipo == "guerra_sin_definicion":
            self._log("Guerra sin definicion: ambos se quedaron sin cartas al mismo tiempo.")
            return
        carta1, carta2, ganador = resultado["carta1"], resultado["carta2"], resultado["ganador"]
        if tipo == "guerra":
            self._log(f"¡Empate! Hubo guerra ({resultado['rondas_de_guerra']} vuelta/s). "
                      f"Cartas decisivas: {carta1} vs {carta2}.")
        else:
            self._log(f"{self.juego.jugador1.nombre} tira {carta1} - {self.juego.jugador2.nombre} tira {carta2}.")
        self._log(f"{ganador.nombre} se lleva {resultado['cartas_ganadas']} carta(s).")

    def _alternar_auto_jugar(self):
        self._auto_jugando = not self._auto_jugando
        self.boton_auto.config(text="Detener" if self._auto_jugando else "Auto-jugar")
        if self._auto_jugando:
            self._rondas_auto_jugadas = 0
            self._paso_auto()

    def _paso_auto(self):
        """
        POST: juega rondas en bucle (con una pequena demora entre cada una,
              para poder seguirlas visualmente) hasta que el juego termine,
              se detenga manualmente, o se alcance '_LIMITE_RONDAS_AUTO'.
              Este ultimo tope existe porque La Guerra, jugada con cartas
              reales, a veces entra en un ciclo que se repite para siempre
              sin que nadie gane (una propiedad conocida del juego, no un
              error de esta implementacion): sin el tope, "Auto-jugar"
              podria quedar corriendo indefinidamente.
        """
        if not self._auto_jugando or self.juego.terminado():
            self._auto_jugando = False
            self.boton_auto.config(text="Auto-jugar")
            return
        if self._rondas_auto_jugadas >= _LIMITE_RONDAS_AUTO:
            self._auto_jugando = False
            self.boton_auto.config(text="Auto-jugar")
            self._log(f"\nSe alcanzaron {_LIMITE_RONDAS_AUTO} rondas sin que nadie gane: "
                      f"esta partida probablemente entro en un ciclo infinito (le puede pasar "
                      f"a La Guerra real). Se detuvo el auto-juego; podes seguir con 'Jugar ronda' "
                      f"o volver al menu para empezar una partida nueva.")
            return
        self._jugar_una_ronda()
        self._rondas_auto_jugadas += 1
        self.root.after(_RETRASO_AUTO_MS, self._paso_auto)

    def _volver_al_menu(self):
        """POST: cierra la ventana de La Guerra (el selector de juegos vuelve a mostrarse)."""
        self.root.destroy()


if __name__ == "__main__":
    GuerraGUI().iniciar()
