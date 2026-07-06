"""Interfaz grafica (Tkinter) para jugar al Truco contra la CPU.

Reutiliza integramente el modelo de juego ya implementado (Truco,
EstrategiaCPU) sin modificarlo: esta clase solo coordina la presentacion y
el flujo de turnos mediante callbacks encadenados, ya que el bucle de
eventos de Tkinter no admite bloquear la ejecucion con 'input()' como hacia
la version de consola (game_manager.GameManager).
"""

import os
import traceback
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from juegos.estrategia_cpu import crear_estrategia
from juegos.truco import Truco

_RETRASO_CPU_MS = 700
_CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_CARPETA_CARTAS = os.path.join(_CARPETA_ASSETS, "cartas")
_COLOR_FONDO_MESA = "#0D4730"
_COLOR_DORADO = "#D4AF37"
_ANCHO_CARTA, _ALTO_CARTA = 120, 172


class TrucoGUI:
    """
    Ventana principal del Truco. Cada mano se juega como una cadena de
    callbacks: 'iniciar_turno' decide si el turno lo resuelve la CPU (sola,
    con un pequeno retraso simulando que "piensa") o si le muestra al
    humano sus cartas y acciones disponibles; al terminar cada turno se
    invoca el callback 'luego' recibido, que continua con la baza o la mano.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Truco Argentino")
        self.root.geometry("900x800")
        self.root.resizable(False, False)

        self.truco = None
        self.jugador_cpu = None
        self.estrategia = None
        self._turno_actual = None  # (jugador, rival, luego) mientras el humano decide
        self._mesa_visual = ()  # cartas mostradas en la mesa; solo cambia cuando se juega una carta
        self._nombre_jugador = None
        self._dificultad_nombre = None
        self._puntos_partida = 30
        self._sesion_id = 0  # se incrementa al reiniciar/salir, para invalidar callbacks pendientes de la CPU
        self._dialogo_actual = None  # dialogo modal abierto (respuesta a un canto), si hay uno

        self.root.report_callback_exception = self._reportar_excepcion

        self._cargar_imagenes()
        self._construir_pantalla_inicio()

    def iniciar(self):
        """POST: arranca el bucle principal de la interfaz grafica."""
        self.root.mainloop()

    def _reportar_excepcion(self, tipo_exc, valor_exc, tb):
        """
        POST: cualquier excepcion no esperada que ocurra dentro de un callback
              de Tkinter (por ejemplo, al apretar un boton) se muestra en el
              historial de la partida en vez de perderse silenciosamente
              (esto importa especialmente al ejecutar main.pyw, que no tiene
              consola donde se pudiera haber visto el error).
        """
        mensaje = "".join(traceback.format_exception(tipo_exc, valor_exc, tb))
        print(mensaje)
        if hasattr(self, "text_log") and self.text_log.winfo_exists():
            self._log(f"\n[Error interno, esto no deberia pasar] {valor_exc}")

    def _programar(self, demora_ms, funcion):
        """
        PRE: 'funcion' es una accion diferida relacionada con la partida actual
             (por ejemplo, una decision de la CPU).
        POST: 'funcion' se ejecuta luego de 'demora_ms', pero solo si la
              partida no se reinicio ni se abandono mientras tanto (evita
              que una decision de la CPU programada antes de apretar
              "Reiniciar" o "Menu principal" se ejecute sobre el estado nuevo).
        """
        sesion = self._sesion_id

        def envoltorio():
            if sesion == self._sesion_id:
                funcion()

        self.root.after(demora_ms, envoltorio)

    # ---------- Carga de imagenes (assets/) ----------

    def _cargar_imagen_carta(self, ruta):
        """
        PRE: 'ruta' apunta a una imagen de carta (cualquier formato que
             soporte Pillow: PNG, JPG, etc.) de cualquier resolucion.
        POST: retorna la imagen redimensionada a (_ANCHO_CARTA, _ALTO_CARTA),
              para que reemplazar las cartas generadas por fotos o escaneos
              reales no descuadre el resto de la pantalla.
        """
        return Image.open(ruta).convert("RGBA").resize((_ANCHO_CARTA, _ALTO_CARTA), Image.LANCZOS)

    def _cargar_imagenes(self):
        """
        PRE: la carpeta 'assets' (generada con assets/generar_assets.py, o
             reemplazada a mano con fotos/escaneos reales del mismo nombre)
             existe junto a este archivo, con las 40 cartas, el dorso, los
             fondos y los carteles de victoria/derrota.
        POST: quedan cargadas en memoria (como atributos de la instancia,
              para que Tkinter no las descarte) todas las imagenes usadas
              por la interfaz, todas las cartas normalizadas al mismo tamano.
        """
        self._imagenes_cartas = {}
        for archivo in os.listdir(_CARPETA_CARTAS):
            if archivo == "dorso.png":
                continue
            nombre, _ext = os.path.splitext(archivo)
            valor_str, palo_str = nombre.split("_", 1)
            imagen = self._cargar_imagen_carta(os.path.join(_CARPETA_CARTAS, archivo))
            self._imagenes_cartas[(int(valor_str), palo_str)] = ImageTk.PhotoImage(imagen)
        imagen_dorso = self._cargar_imagen_carta(os.path.join(_CARPETA_CARTAS, "dorso.png"))
        self._imagen_dorso = ImageTk.PhotoImage(imagen_dorso)
        self._imagen_dorso_chico = ImageTk.PhotoImage(imagen_dorso.resize((60, 86), Image.LANCZOS))
        self._imagen_fondo_inicio = ImageTk.PhotoImage(Image.open(os.path.join(_CARPETA_ASSETS, "fondo_inicio.png")))
        self._imagen_fondo_mesa = ImageTk.PhotoImage(Image.open(os.path.join(_CARPETA_ASSETS, "fondo_mesa.png")))
        self._imagen_ganaste = ImageTk.PhotoImage(Image.open(os.path.join(_CARPETA_ASSETS, "ganaste.png")))
        self._imagen_perdiste = ImageTk.PhotoImage(Image.open(os.path.join(_CARPETA_ASSETS, "perdiste.png")))

        # Indicadores de los radiobutton de la pantalla de inicio: cada uno usa
        # un recorte del propio fondo en su posicion exacta (en vez de un color
        # solido) para que el "vacio" sea perfectamente invisible sobre la
        # textura del pergamino, y el "lleno" sea ese mismo recorte con un
        # punto agregado.
        self._imagenes_radio = {}
        for nombre in ("facil", "media", "dificil", "15", "30"):
            vacio = Image.open(os.path.join(_CARPETA_ASSETS, f"radio_vacio_{nombre}.png")).convert("RGB")
            lleno = Image.open(os.path.join(_CARPETA_ASSETS, f"radio_lleno_{nombre}.png"))
            color_borde = self._color_promedio_del_borde(vacio)
            self._imagenes_radio[nombre] = (ImageTk.PhotoImage(vacio), ImageTk.PhotoImage(lleno), color_borde)

    def _color_promedio_del_borde(self, imagen):
        """
        POST: retorna (en formato '#rrggbb') el color promedio de los pixeles
              del borde de 'imagen'. Tkinter deja siempre 1px de margen propio
              alrededor de la imagen de un Radiobutton con indicatoron=0 (sin
              importar padx/pady/highlightthickness); usar este color como
              'bg' del widget hace que ese margen se mezcle con el fondo real
              en vez de mostrarse con el gris por defecto del sistema.
        """
        ancho, alto = imagen.size
        pixeles = [imagen.getpixel((x, 0)) for x in range(ancho)]
        pixeles += [imagen.getpixel((x, alto - 1)) for x in range(ancho)]
        pixeles += [imagen.getpixel((0, y)) for y in range(alto)]
        pixeles += [imagen.getpixel((ancho - 1, y)) for y in range(alto)]
        r = sum(p[0] for p in pixeles) // len(pixeles)
        g = sum(p[1] for p in pixeles) // len(pixeles)
        b = sum(p[2] for p in pixeles) // len(pixeles)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _imagen_de_carta(self, carta):
        """PRE: carta no es comodin. POST: retorna la PhotoImage correspondiente a 'carta'."""
        return self._imagenes_cartas[(carta.valor, carta.palo.value.lower())]

    def _crear_selector(self, valor, relx, rely, variable, mapa_labels):
        """
        POST: crea un Label clickeable en (relx, rely) que funciona como una
              opcion de un grupo tipo "radio": al hacer click, fija 'variable'
              a 'valor' y actualiza la imagen de todos los labels de
              'mapa_labels' para reflejar cual quedo seleccionada.

              Se usa Label en lugar de Radiobutton porque Radiobutton (con
              indicatoron=0) siempre deja un margen de 1px alrededor de la
              imagen -sin importar padx/pady/highlightthickness/borderwidth-
              que se veia como un borde desalineado sobre el pergamino de
              fondo; un Label comun se ajusta exacto al tamano de la imagen.
        """
        vacio, lleno, color_borde = self._imagenes_radio[valor]
        esta_seleccionado = variable.get() == valor
        label = tk.Label(self.frame_inicio, image=lleno if esta_seleccionado else vacio,
                          bg=color_borde, bd=0, highlightthickness=0, cursor="hand2")
        label.place(relx=relx, rely=rely, anchor="center")
        label.bind("<Button-1>", lambda evento: self._seleccionar_opcion(valor, variable, mapa_labels))
        return label

    def _seleccionar_opcion(self, valor, variable, mapa_labels):
        """POST: 'variable' pasa a valer 'valor' y se actualiza la imagen de cada label del grupo."""
        variable.set(valor)
        for valor_label, label in mapa_labels.items():
            vacio, lleno, _ = self._imagenes_radio[valor_label]
            label.config(image=lleno if valor_label == valor else vacio)

    # ---------- Pantalla de inicio ----------

    def _construir_pantalla_inicio(self):
        """
        Ubica los controles reales (entry, radiobuttons, boton) exactamente
        sobre el pergamino ya dibujado en 'assets/fondo_inicio.png' (que ya
        trae impresos los textos "Tu nombre", "Dificultad de la CPU",
        "Puntos para ganar" y "Comenzar partida"). Las posiciones estan
        calculadas como fracciones (relx/rely) de la imagen original, para
        que sigan alineadas sin importar el tamano final de la ventana.
        """
        self.frame_inicio = tk.Frame(self.root)
        self.frame_inicio.pack(expand=True, fill="both")

        tk.Label(self.frame_inicio, image=self._imagen_fondo_inicio, bd=0).place(
            x=0, y=0, relwidth=1, relheight=1)

        color_texto = "#4A2C17"
        color_campo = "#DDBC91"  # tono exacto muestreado del pergamino en el campo de nombre
        color_boton = "#0A2E1D"  # tono exacto muestreado del boton ya dibujado en la imagen

        self.entrada_nombre = tk.Entry(self.frame_inicio, font=("Georgia", 11), bg=color_campo,
                                        fg=color_texto, relief="flat", borderwidth=0,
                                        highlightthickness=0, justify="center")
        self.entrada_nombre.insert(0, "Jugador")
        self.entrada_nombre.place(relx=0.4089, rely=0.4938, relwidth=0.1800, relheight=0.0238)

        # Las posiciones de estos circulos ya incluyen un corrimiento leve
        # hacia la izquierda respecto del circulo dibujado en la imagen (el
        # recorte de fondo usado en cada imagen vacio/lleno se genero desde
        # ese mismo punto corrido, por lo que el anillo dibujado se sigue
        # viendo en su lugar real; solo el punto de seleccion queda un poco
        # mas a la izquierda, como se pidio).
        self.dificultad_var = tk.StringVar(value="media")
        posiciones_dificultad = (("facil", 0.4100, 0.5963), ("media", 0.4100, 0.6325), ("dificil", 0.4111, 0.6688))
        self._labels_dificultad = {}
        for valor, relx, rely in posiciones_dificultad:
            self._labels_dificultad[valor] = self._crear_selector(
                valor, relx, rely, self.dificultad_var, self._labels_dificultad)

        self.puntos_partida_var = tk.StringVar(value="30")
        posiciones_puntos = (("15", 0.4100, 0.7563), ("30", 0.4811, 0.7563))
        self._labels_puntos = {}
        for valor, relx, rely in posiciones_puntos:
            self._labels_puntos[valor] = self._crear_selector(
                valor, relx, rely, self.puntos_partida_var, self._labels_puntos)

        tk.Button(self.frame_inicio, text="Comenzar partida", command=self._comenzar_partida,
                  font=("Georgia", 12, "bold"), fg="#D4AF37", bg=color_boton,
                  activebackground=color_boton, activeforeground="#D4AF37", relief="flat",
                  borderwidth=0, highlightthickness=0, cursor="hand2").place(
            relx=0.3956, rely=0.8038, relwidth=0.2100, relheight=0.0500)

    def _comenzar_partida(self):
        nombre = self.entrada_nombre.get().strip() or "Jugador"
        dificultad = self.dificultad_var.get()
        puntos_partida = int(self.puntos_partida_var.get())

        self._sesion_id += 1
        self._nombre_jugador = nombre
        self._dificultad_nombre = dificultad
        self._puntos_partida = puntos_partida

        self.truco = Truco(nombre, "CPU", puntos_partida=puntos_partida)
        self.jugador_cpu = self.truco.jugador_en_posicion(1)
        self.estrategia = crear_estrategia(dificultad)
        self._mesa_visual = ()

        self.frame_inicio.destroy()
        self._construir_pantalla_juego()

        repartidor = self.truco.sortear_mano_inicial()
        self._log(f"Comienza el Truco: {nombre} vs CPU (a {self.truco.PUNTOS_PARTIDA} puntos)")
        self._log(f"{repartidor.nombre} reparte primero.")
        self._iniciar_mano()

    # ---------- Construccion de la pantalla de juego ----------

    def _construir_pantalla_juego(self):
        self.frame_juego = tk.Frame(self.root)
        self.frame_juego.pack(expand=True, fill="both")

        tk.Label(self.frame_juego, image=self._imagen_fondo_mesa, bd=0).place(
            x=0, y=0, relwidth=1, relheight=1)

        contenido = tk.Frame(self.frame_juego, bg=_COLOR_FONDO_MESA, padx=10, pady=10)
        contenido.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.97, relheight=0.97)

        frame_encabezado = tk.Frame(contenido, bg=_COLOR_FONDO_MESA)
        frame_encabezado.pack(fill="x")
        self.label_puntajes = tk.Label(frame_encabezado, font=("Arial", 14, "bold"),
                                        bg=_COLOR_FONDO_MESA, fg=_COLOR_DORADO)
        self.label_puntajes.pack(side="left")

        frame_botones_partida = tk.Frame(frame_encabezado, bg=_COLOR_FONDO_MESA)
        frame_botones_partida.pack(side="right")
        tk.Button(frame_botones_partida, text="Menu principal", font=("Arial", 9),
                  command=self._confirmar_volver_al_menu).pack(side="left", padx=(0, 6))
        tk.Button(frame_botones_partida, text="Reiniciar partida", font=("Arial", 9),
                  command=self._confirmar_reiniciar_partida).pack(side="left")

        frame_estado = tk.Frame(contenido, bg=_COLOR_FONDO_MESA)
        frame_estado.pack(fill="x")
        self.label_estado = tk.Label(frame_estado, font=("Arial", 10),
                                      bg=_COLOR_FONDO_MESA, fg="white")
        self.label_estado.pack(side="right")

        self.frame_mano_cpu = tk.Frame(contenido, bg=_COLOR_FONDO_MESA)
        self.frame_mano_cpu.pack(pady=(10, 0))

        tk.Label(contenido, text="Mesa", font=("Arial", 10, "italic"),
                 bg=_COLOR_FONDO_MESA, fg="white").pack(pady=(10, 0))
        self.frame_mesa_cartas = tk.Frame(contenido, bg=_COLOR_FONDO_MESA, height=100)
        self.frame_mesa_cartas.pack(pady=5)

        self.frame_acciones = tk.Frame(contenido, bg=_COLOR_FONDO_MESA)
        self.frame_acciones.pack(pady=10)

        tk.Label(contenido, text="Tu mano", font=("Arial", 10, "italic"),
                 bg=_COLOR_FONDO_MESA, fg="white").pack()
        self.frame_mano_humano = tk.Frame(contenido, bg=_COLOR_FONDO_MESA)
        self.frame_mano_humano.pack(pady=5)

        tk.Label(contenido, text="Historial", font=("Arial", 10, "italic"),
                 bg=_COLOR_FONDO_MESA, fg="white").pack(pady=(10, 0))
        frame_log = tk.Frame(contenido, bg=_COLOR_FONDO_MESA)
        frame_log.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(frame_log)
        scrollbar.pack(side="right", fill="y")
        self.text_log = tk.Text(frame_log, height=7, state="disabled", bg="#08301F", fg="#E8E8E8",
                                 insertbackground="white", yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.text_log.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_log.yview)

    # ---------- Utilidades de presentacion ----------

    def _es_cpu(self, jugador):
        return jugador is self.jugador_cpu

    def _humano(self):
        jugador_1 = self.truco.jugador_en_posicion(0)
        return jugador_1 if not self._es_cpu(jugador_1) else self.truco.jugador_en_posicion(1)

    def _nombre_legible(self, nombre_interno):
        return nombre_interno.replace("_", " ").title()

    def _crear_boton_carta(self, parent, carta, habilitado, comando):
        return tk.Button(parent, image=self._imagen_de_carta(carta), bd=3,
                          relief="raised" if habilitado else "flat",
                          bg=_COLOR_FONDO_MESA, activebackground=_COLOR_FONDO_MESA,
                          state="normal" if habilitado else "disabled",
                          command=comando if habilitado else None)

    def _crear_label_carta(self, parent, carta, nombre_dueno):
        frame = tk.Frame(parent, bg=_COLOR_FONDO_MESA)
        tk.Label(frame, text=nombre_dueno, font=("Arial", 9), bg=_COLOR_FONDO_MESA, fg="white").pack()
        tk.Label(frame, image=self._imagen_de_carta(carta), bg=_COLOR_FONDO_MESA).pack()
        return frame

    def _log(self, mensaje):
        self.text_log.configure(state="normal")
        self.text_log.insert("end", mensaje + "\n")
        self.text_log.configure(state="disabled")
        self.text_log.see("end")

    def _mostrar_dialogo_opciones(self, titulo, opciones):
        """POST: muestra un dialogo modal con un boton por cada (etiqueta, callback) en 'opciones'."""
        sesion = self._sesion_id
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Tu decision")
        dialogo.resizable(False, False)
        dialogo.grab_set()
        self._dialogo_actual = dialogo
        tk.Label(dialogo, text=titulo, font=("Arial", 12, "bold"), wraplength=280,
                 padx=20, pady=15).pack()
        for etiqueta, callback in opciones:
            def accion(cb=callback):
                dialogo.destroy()
                self._dialogo_actual = None
                if sesion == self._sesion_id:
                    cb()
            tk.Button(dialogo, text=etiqueta, font=("Arial", 11), command=accion).pack(
                fill="x", padx=20, pady=4)
        tk.Frame(dialogo, height=10).pack()

    def _refrescar_pantalla(self):
        humano = self._humano()
        self.label_puntajes.config(text=f"{humano.nombre}: {humano.puntos}    |    CPU: {self.jugador_cpu.puntos}")
        self.label_estado.config(
            text=f"Fase: {self.truco.fase_actual()}   Mazo: {self.truco.mazo.cartas_restantes()} cartas   "
                 f"En juego: {self.truco.puntos_en_juego} pto/s")
        for widget in self.frame_mano_cpu.winfo_children():
            widget.destroy()
        tk.Label(self.frame_mano_cpu, text=f"{self.jugador_cpu.nombre} ({len(self.jugador_cpu.mano)} cartas)",
                 font=("Arial", 10), bg=_COLOR_FONDO_MESA, fg="white").pack()
        frame_dorsos = tk.Frame(self.frame_mano_cpu, bg=_COLOR_FONDO_MESA)
        frame_dorsos.pack()
        for _ in range(len(self.jugador_cpu.mano)):
            tk.Label(frame_dorsos, image=self._imagen_dorso_chico, bg=_COLOR_FONDO_MESA).pack(side="left", padx=4)

        for widget in self.frame_mesa_cartas.winfo_children():
            widget.destroy()
        for jugador_en_mesa, carta_en_mesa in self._mesa_visual:
            self._crear_label_carta(self.frame_mesa_cartas, carta_en_mesa,
                                     jugador_en_mesa.nombre).pack(side="left", padx=15)

        for widget in self.frame_mano_humano.winfo_children():
            widget.destroy()
        puede_jugar = self._turno_actual is not None and self._turno_actual[0] is humano
        for carta in humano.mano:
            self._crear_boton_carta(
                self.frame_mano_humano, carta, puede_jugar,
                lambda c=carta: self._humano_juega_carta(c)
            ).pack(side="left", padx=6)

        for widget in self.frame_acciones.winfo_children():
            widget.destroy()
        if self._turno_actual is not None and self._turno_actual[0] is humano:
            jugador, rival, _ = self._turno_actual
            if self.truco.puede_cantar_envido(jugador):
                for nivel in self.truco.niveles_disponibles_envido():
                    tk.Button(self.frame_acciones, text=f"Cantar {self._nombre_legible(nivel)}",
                              command=lambda n=nivel: self._humano_canta_envido(n)).pack(side="left", padx=4)
            if self.truco.puede_cantar_truco(jugador):
                tk.Button(self.frame_acciones,
                          text=f"Cantar {self._nombre_legible(self.truco.nombre_proximo_canto())}",
                          command=self._humano_canta_truco).pack(side="left", padx=4)
            tk.Button(self.frame_acciones, text="Irse al mazo", fg="white", bg="#8B0000",
                      command=self._humano_se_va_al_mazo).pack(side="left", padx=4)

    # ---------- Flujo de una mano ----------

    def _iniciar_mano(self):
        for widget in self.frame_acciones.winfo_children():
            widget.destroy()
        self.truco.iniciar_mano()
        self._log(f"\n--- Nueva mano ({self.truco.fase_actual()}) --- "
                  f"(quedan {self.truco.mazo.cartas_restantes()} cartas en el mazo)")
        jugador_mano = self.truco.jugador_en_posicion(self.truco.indice_mano)
        self._log(f"{jugador_mano.nombre} es mano en esta mano.")
        self._refrescar_pantalla()

        lider = self.truco.jugador_en_posicion(self.truco.lider_baza_index)
        oponente = self.truco.jugador_en_posicion(1 - self.truco.lider_baza_index)
        self._jugar_baza(lider, oponente)

    def _jugar_baza(self, lider, oponente):
        self._iniciar_turno(lider, oponente, luego=lambda: self._despues_de_primer_turno(lider, oponente))

    def _despues_de_primer_turno(self, lider, oponente):
        if not self.truco.en_curso:
            self._finalizar_mano()
            return
        self._iniciar_turno(oponente, lider, luego=lambda: self._despues_de_baza(lider, oponente))

    def _despues_de_baza(self, lider, oponente):
        if not self.truco.en_curso:
            self._finalizar_mano()
            return
        ganador = self.truco.resolver_baza()
        if ganador is not None:
            self._log(f"Baza para {ganador.nombre}")
            self.truco.lider_baza_index = self.truco.indice_de_jugador(ganador)
        else:
            self._log("Baza empatada (parda)")

        mano_decidida = self.truco.jugador_gana_mano() is not None or self.truco.ronda_actual >= 3
        if not mano_decidida:
            # Cambia la ronda (baza) pero seguimos en la misma mano: la mesa se limpia.
            self._mesa_visual = ()
        self._refrescar_pantalla()

        if mano_decidida:
            self._finalizar_mano()
        else:
            nuevo_lider = self.truco.jugador_en_posicion(self.truco.lider_baza_index)
            nuevo_oponente = self.truco.jugador_en_posicion(1 - self.truco.lider_baza_index)
            self._jugar_baza(nuevo_lider, nuevo_oponente)

    def _finalizar_mano(self):
        self._turno_actual = None
        if self.truco.en_curso:
            ganador_mano = self.truco.jugador_gana_mano()
            if ganador_mano is not None:
                self.truco.sumar_puntos(ganador_mano, self.truco.puntos_en_juego)
                self._log(f"{ganador_mano.nombre} se lleva la mano (+{self.truco.puntos_en_juego} pto/s).")
        self._refrescar_pantalla()

        for jugador in (self.truco.jugador_en_posicion(0), self.truco.jugador_en_posicion(1)):
            self._log(f"Puntaje {jugador.nombre}: {jugador.puntos}")

        for widget in self.frame_acciones.winfo_children():
            widget.destroy()
        for widget in self.frame_mano_humano.winfo_children():
            widget.destroy()

        ganador_partida = self.truco.verificar_ganador()
        if ganador_partida is not None:
            self._log(f"\n¡{ganador_partida.nombre} gano la partida!")
            humano_gano = ganador_partida is self._humano()
            imagen = self._imagen_ganaste if humano_gano else self._imagen_perdiste
            tk.Label(self.frame_acciones, image=imagen, bg=_COLOR_FONDO_MESA).pack(pady=10)
            tk.Button(self.frame_acciones, text="Volver al inicio", font=("Arial", 12, "bold"),
                      bg="#1565C0", fg="white", command=self._volver_al_menu).pack(pady=(0, 10))
        else:
            tk.Button(self.frame_acciones, text="Siguiente mano", font=("Arial", 12, "bold"),
                      bg="#1565C0", fg="white", command=self._iniciar_mano).pack(pady=10)

    def _confirmar_volver_al_menu(self):
        """POST: si la partida ya termino, o el usuario confirma, vuelve al menu principal."""
        if self.truco.verificar_ganador() is None:
            if not messagebox.askyesno(
                    "Volver al menu principal",
                    "Se va a abandonar la partida en curso. ¿Queres volver al menu principal?"):
                return
        self._volver_al_menu()

    def _confirmar_reiniciar_partida(self):
        """POST: si la partida ya termino, o el usuario confirma, reinicia la partida actual desde 0."""
        if self.truco.verificar_ganador() is None:
            if not messagebox.askyesno(
                    "Reiniciar partida",
                    "Se va a reiniciar la partida en curso desde 0. ¿Estas seguro?"):
                return
        self._reiniciar_partida()

    def _cancelar_estado_en_curso(self):
        """
        POST: invalida cualquier decision de la CPU programada con 'root.after'
              (ver '_programar') y cierra el dialogo modal de respuesta a un
              canto si estuviera abierto, dejando la partida lista para
              reiniciarse o para volver al menu principal sin interferencias.
        """
        self._sesion_id += 1
        if self._dialogo_actual is not None:
            self._dialogo_actual.destroy()
            self._dialogo_actual = None
        self._turno_actual = None

    def _volver_al_menu(self):
        """
        POST: se descarta la partida en curso (si la habia) y se vuelve a
              mostrar la pantalla de inicio, permitiendo elegir nombre,
              dificultad y puntos de nuevo para arrancar una partida nueva.
        """
        self._cancelar_estado_en_curso()
        self.frame_juego.destroy()
        self.truco = None
        self.jugador_cpu = None
        self.estrategia = None
        self._mesa_visual = ()
        self._construir_pantalla_inicio()

    def _reiniciar_partida(self):
        """
        PRE: hay una partida en curso (creada por '_comenzar_partida').
        POST: se descarta el estado de la partida actual y se arranca una
              partida nueva con el mismo nombre, dificultad y puntos elegidos
              al principio, sin volver al menu.
        """
        self._cancelar_estado_en_curso()
        self.truco = Truco(self._nombre_jugador, "CPU", puntos_partida=self._puntos_partida)
        self.jugador_cpu = self.truco.jugador_en_posicion(1)
        self.estrategia = crear_estrategia(self._dificultad_nombre)
        self._mesa_visual = ()

        for widget in self.frame_acciones.winfo_children():
            widget.destroy()

        repartidor = self.truco.sortear_mano_inicial()
        self._log(f"\n=== Partida reiniciada: {self._nombre_jugador} vs CPU "
                  f"(a {self.truco.PUNTOS_PARTIDA} puntos) ===")
        self._log(f"{repartidor.nombre} reparte primero.")
        self._iniciar_mano()

    # ---------- Turno de un jugador (humano o CPU) ----------

    def _iniciar_turno(self, jugador, rival, luego):
        if self._es_cpu(jugador):
            self._programar(_RETRASO_CPU_MS, lambda: self._decidir_turno_cpu(jugador, rival, luego))
        else:
            self._turno_actual = (jugador, rival, luego)
            self._refrescar_pantalla()

    def _decidir_turno_cpu(self, jugador, rival, luego):
        if self.truco.puede_cantar_envido(jugador):
            nivel = self.estrategia.quiere_cantar_envido(self.truco, jugador, rival)
            if nivel is not None:
                self._iniciar_negociacion_envido(
                    jugador, rival, nivel,
                    luego=lambda: self._programar(
                        _RETRASO_CPU_MS, lambda: self._decidir_turno_cpu(jugador, rival, luego)))
                return
        if self.truco.puede_cantar_truco(jugador):
            if self.estrategia.quiere_cantar_truco(self.truco, jugador, rival):
                self._iniciar_negociacion_truco(
                    jugador, rival,
                    luego=lambda: self._programar(
                        _RETRASO_CPU_MS, lambda: self._decidir_turno_cpu(jugador, rival, luego)))
                return
        if self.estrategia.quiere_irse_al_mazo(self.truco, jugador, rival):
            ganador, puntos = self.truco.irse_al_mazo(jugador)
            self._log(f"{jugador.nombre} se va al mazo. {ganador.nombre} suma {puntos} pto/s.")
            self._finalizar_mano()
            return
        carta = self.estrategia.elegir_carta(self.truco, jugador, rival)
        self.truco.jugar_turno(jugador, carta)
        self._mesa_visual = tuple(self.truco.cartas_jugadas)
        self._log(f"{jugador.nombre} juega {carta}")
        self._refrescar_pantalla()
        luego()

    def _humano_juega_carta(self, carta):
        if self._turno_actual is None:
            return  # click repetido/doble click sobre un boton que ya se proceso
        jugador, rival, luego = self._turno_actual
        self._turno_actual = None
        self.truco.jugar_turno(jugador, carta)
        self._mesa_visual = tuple(self.truco.cartas_jugadas)
        self._log(f"{jugador.nombre} juega {carta}")
        self._refrescar_pantalla()
        luego()

    def _humano_canta_envido(self, nivel):
        if self._turno_actual is None:
            return  # click repetido/doble click sobre un boton que ya se proceso
        jugador, rival, luego = self._turno_actual
        self._turno_actual = None
        self._iniciar_negociacion_envido(
            jugador, rival, nivel,
            luego=lambda: self._reanudar_turno_humano(jugador, rival, luego))

    def _humano_canta_truco(self):
        if self._turno_actual is None:
            return  # click repetido/doble click sobre un boton que ya se proceso
        jugador, rival, luego = self._turno_actual
        self._turno_actual = None
        self._iniciar_negociacion_truco(
            jugador, rival,
            luego=lambda: self._reanudar_turno_humano(jugador, rival, luego))

    def _reanudar_turno_humano(self, jugador, rival, luego):
        self._turno_actual = (jugador, rival, luego)
        self._refrescar_pantalla()

    def _humano_se_va_al_mazo(self):
        if self._turno_actual is None:
            return  # click repetido/doble click sobre un boton que ya se proceso
        jugador, rival, luego = self._turno_actual
        self._turno_actual = None
        ganador, puntos = self.truco.irse_al_mazo(jugador)
        self._log(f"{jugador.nombre} se va al mazo. {ganador.nombre} suma {puntos} pto/s.")
        self._finalizar_mano()

    # ---------- Negociacion de Envido (con posible escalada) ----------

    def _iniciar_negociacion_envido(self, cantor, respondiente, nivel, luego):
        self._log(f"{cantor.nombre} canta {self._nombre_legible(nivel)}.")
        self.truco.cantar_envido(nivel, cantor)
        self._refrescar_pantalla()
        self._resolver_respuesta_envido(cantor, respondiente, luego)

    def _resolver_respuesta_envido(self, cantor, respondiente, luego):
        if self._es_cpu(respondiente):
            decision = self.estrategia.responder_envido(self.truco, respondiente, cantor)
            self._programar(_RETRASO_CPU_MS,
                             lambda: self._aplicar_respuesta_envido(cantor, respondiente, decision, luego))
        else:
            opciones = [
                ("Quiero", lambda: self._aplicar_respuesta_envido(cantor, respondiente, "quiero", luego)),
                ("No quiero", lambda: self._aplicar_respuesta_envido(cantor, respondiente, "no_quiero", luego)),
            ]
            for nivel in self.truco.niveles_disponibles_envido():
                opciones.append((f"Cantar {self._nombre_legible(nivel)}",
                                  lambda n=nivel: self._aplicar_respuesta_envido(cantor, respondiente, n, luego)))
            titulo = f"{cantor.nombre} canto {self._nombre_legible(self.truco.envido_nivel_actual)}.\n{respondiente.nombre}, ¿que decis?"
            self._mostrar_dialogo_opciones(titulo, opciones)

    def _aplicar_respuesta_envido(self, cantor, respondiente, decision, luego):
        if decision == "quiero":
            ganador, valor1, valor2, puntos = self.truco.resolver_envido_quiero()
            jugador1, jugador2 = self.truco.jugador_en_posicion(0), self.truco.jugador_en_posicion(1)
            self._log(f"Envido de {jugador1.nombre}: {valor1} - Envido de {jugador2.nombre}: {valor2}")
            self._log(f"{ganador.nombre} gana el Envido (+{puntos} pts).")
            self._refrescar_pantalla()
            luego()
        elif decision == "no_quiero":
            puntos = self.truco.resolver_envido_no_quiero(respondiente)
            self._log(f"{respondiente.nombre} no quiso. {cantor.nombre} suma {puntos} pto/s por Envido.")
            self._refrescar_pantalla()
            luego()
        else:
            self._log(f"{respondiente.nombre} canta {self._nombre_legible(decision)}.")
            self.truco.cantar_envido(decision, respondiente)
            self._refrescar_pantalla()
            self._resolver_respuesta_envido(respondiente, cantor, luego)

    # ---------- Negociacion de Truco (con posible escalada) ----------

    def _iniciar_negociacion_truco(self, cantor, respondiente, luego):
        nombre_canto = self._nombre_legible(self.truco.nombre_proximo_canto())
        self._log(f"{cantor.nombre} canta {nombre_canto}.")
        self.truco.cantar(self.truco.proximo_valor_truco(), cantor)
        self._refrescar_pantalla()
        self._resolver_respuesta_truco(cantor, respondiente, luego)

    def _resolver_respuesta_truco(self, cantor, respondiente, luego):
        if self._es_cpu(respondiente):
            decision = self.estrategia.responder_truco(self.truco, respondiente, cantor)
            if decision == "subir" and not self.truco.puede_cantar_truco(respondiente):
                decision = "quiero"
            self._programar(_RETRASO_CPU_MS,
                             lambda: self._aplicar_respuesta_truco(cantor, respondiente, decision, luego))
        else:
            opciones = [
                ("Quiero", lambda: self._aplicar_respuesta_truco(cantor, respondiente, "quiero", luego)),
                ("No quiero", lambda: self._aplicar_respuesta_truco(cantor, respondiente, "no_quiero", luego)),
            ]
            if self.truco.puede_cantar_truco(respondiente):
                opciones.append((f"Cantar {self._nombre_legible(self.truco.nombre_proximo_canto())}",
                                  lambda: self._aplicar_respuesta_truco(cantor, respondiente, "subir", luego)))
            titulo = f"{cantor.nombre} te canto Truco.\n{respondiente.nombre}, ¿que decis?"
            self._mostrar_dialogo_opciones(titulo, opciones)

    def _aplicar_respuesta_truco(self, cantor, respondiente, decision, luego):
        if decision == "quiero":
            self.truco.resolver_canto(True)
            self._log(f"{respondiente.nombre} quiso. Ahora se juega por {self.truco.puntos_en_juego} pto/s.")
            self._refrescar_pantalla()
            luego()
        elif decision == "no_quiero":
            puntos = self.truco.resolver_canto(False, jugador_que_no_quiere=respondiente)
            self._log(f"{respondiente.nombre} no quiso. {cantor.nombre} suma {puntos} pto/s.")
            self._refrescar_pantalla()
            self._finalizar_mano()
        else:
            self._log(f"{respondiente.nombre} canta {self._nombre_legible(self.truco.nombre_proximo_canto())}.")
            self.truco.cantar(self.truco.proximo_valor_truco(), respondiente)
            self._refrescar_pantalla()
            self._resolver_respuesta_truco(respondiente, cantor, luego)
