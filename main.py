"""Punto de entrada del programa: deja elegir entre Truco y La Guerra, y
lanza la interfaz grafica del juego elegido.

Para jugar al Truco por consola en su lugar, ejecutar main_consola.py.
"""

import tkinter as tk


def _elegir_juego():
    """
    POST: muestra una pequena ventana para elegir entre "Truco" y "La
          Guerra", y retorna "truco", "guerra", o None si se cerro la
          ventana sin elegir nada.
    """
    seleccion = {"juego": None}

    ventana = tk.Tk()
    ventana.title("Elegir juego")
    ventana.geometry("320x220")
    ventana.resizable(False, False)

    def elegir(juego):
        seleccion["juego"] = juego
        ventana.destroy()

    tk.Label(ventana, text="¿Que queres jugar?", font=("Arial", 14, "bold")).pack(pady=(25, 15))
    tk.Button(ventana, text="Truco Argentino", font=("Arial", 12), width=22,
              command=lambda: elegir("truco")).pack(pady=6)
    tk.Button(ventana, text="La Guerra", font=("Arial", 12), width=22,
              command=lambda: elegir("guerra")).pack(pady=6)

    ventana.mainloop()
    return seleccion["juego"]


def main():
    while True:
        juego = _elegir_juego()
        if juego == "truco":
            from interfaz_grafica import TrucoGUI
            TrucoGUI().iniciar()
        elif juego == "guerra":
            from guerra.interfaz_guerra import GuerraGUI
            GuerraGUI().iniciar()
        else:
            break


if __name__ == "__main__":
    main()
