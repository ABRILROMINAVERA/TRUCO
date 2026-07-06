"""GameManager: coordina el inicio y el flujo general de una partida."""

from juegos.truco import Truco


class GameManager:
    """
    Responsable de iniciar el programa, crear el juego elegido y coordinar
    el flujo general de la partida, sin acoplarse a un juego en particular.

    Invariante de representacion:
        - 'juego_actual' es None hasta que se invoca 'iniciar_juego'.
        - 'jugador_cpu' y 'estrategia_cpu' son ambos None, o ninguno lo es
          (la CPU siempre tiene un jugador asignado y una estrategia para
          decidir sus jugadas).
    """

    def __init__(self):
        """POST: se crea un GameManager sin ningun juego iniciado y sin CPU configurada."""
        self.juego_actual = None
        self.jugador_cpu = None
        self.estrategia_cpu = None

    def iniciar_juego(self, juego):
        """
        PRE: 'juego' es una instancia ya construida de una subclase de JuegoDeCartas.
        POST: 'juego_actual' referencia a 'juego', listo para ser jugado.
        """
        self.juego_actual = juego

    def configurar_cpu(self, jugador_cpu, estrategia):
        """
        PRE: 'jugador_cpu' es uno de los jugadores de 'juego_actual'; 'estrategia'
             es una instancia de EstrategiaCPU.
        POST: las decisiones de 'jugador_cpu' (que carta jugar, si cantar o
              responder Envido/Truco, si irse al mazo) quedan delegadas a 'estrategia'.
        """
        self.jugador_cpu = jugador_cpu
        self.estrategia_cpu = estrategia

    def _es_cpu(self, jugador):
        """POST: retorna True si 'jugador' es el jugador manejado por la CPU."""
        return self.jugador_cpu is not None and jugador is self.jugador_cpu

    def jugar_truco_por_consola(self):
        """
        PRE: 'juego_actual' debe ser una instancia de Truco.
        POST: se ejecuta la partida de Truco por consola, mano tras mano,
              hasta que alguno de los jugadores alcance PUNTOS_PARTIDA (30,
              divididos en "Malas" las primeras 15 y "Buenas" las ultimas 15).
              Si hay una CPU configurada, sus cartas no se muestran y sus
              decisiones las toma la estrategia asignada en 'configurar_cpu'.
        """
        juego = self.juego_actual
        if not isinstance(juego, Truco):
            raise TypeError("Esta operacion requiere una partida de Truco activa")

        jugador_1, jugador_2 = juego.jugador_en_posicion(0), juego.jugador_en_posicion(1)
        print(f"Comienza el Truco: {jugador_1.nombre} vs {jugador_2.nombre} (a {juego.PUNTOS_PARTIDA} puntos)")
        repartidor = juego.sortear_mano_inicial()
        print(f"{repartidor.nombre} reparte primero.")

        while juego.verificar_ganador() is None:
            juego.iniciar_mano()
            jugador_mano = juego.jugador_en_posicion(juego.indice_mano)
            print(f"\n--- Nueva mano ({juego.fase_actual()}) --- "
                  f"(quedan {juego.mazo.cartas_restantes()} cartas en el mazo)")
            print(f"{jugador_mano.nombre} es mano en esta mano.")
            for jugador in (jugador_1, jugador_2):
                if self._es_cpu(jugador):
                    print(f"Cartas de {jugador.nombre}: oculta")
                else:
                    print(f"Cartas de {jugador.nombre}: {jugador.mano}")

            for _ in range(3):
                if not juego.en_curso:
                    break
                lider = juego.jugador_en_posicion(juego.lider_baza_index)
                oponente = juego.jugador_en_posicion(1 - juego.lider_baza_index)
                self._jugar_baza_consola(juego, lider, oponente)
                if juego.jugador_gana_mano() is not None:
                    break

            if juego.en_curso:
                ganador_mano = juego.jugador_gana_mano()
                if ganador_mano is not None:
                    juego.sumar_puntos(ganador_mano, juego.puntos_en_juego)
                    print(f"{ganador_mano.nombre} se lleva la mano "
                          f"(+{juego.puntos_en_juego} pto/s).")

            for jugador in (jugador_1, jugador_2):
                print(f"Puntaje {jugador.nombre}: {jugador.puntos}")

        ganador = juego.verificar_ganador()
        print(f"\n¡{ganador.nombre} gano la partida!")
        return ganador

    def _jugar_baza_consola(self, juego, lider, oponente):
        """
        PRE: 'lider' y 'oponente' tienen al menos 1 carta en mano.
        POST: se juega la baza actual (lider primero, luego oponente),
              salvo que la mano termine antes (un "no quiero" o alguien se
              va al mazo); se actualiza el lider de la proxima baza segun
              quien gano esta.
        """
        for jugador, rival in ((lider, oponente), (oponente, lider)):
            if self._es_cpu(jugador):
                self._turno_cpu_consola(juego, jugador, rival)
            else:
                self._turno_jugador_consola(juego, jugador, rival)
            if not juego.en_curso:
                return

        ganador = juego.resolver_baza()
        if ganador is not None:
            print(f"Baza para {ganador.nombre}")
            juego.lider_baza_index = juego.indice_de_jugador(ganador)
        else:
            print("Baza empatada (parda)")

    def _turno_cpu_consola(self, juego, jugador, rival):
        """
        PRE: es el turno de 'jugador' (la CPU) dentro de la baza actual.
        POST: la CPU juega una carta (eventualmente, tras cantar Envido y/o
              Truco segun decida su estrategia), se va al mazo, o la mano
              termina si algun canto es respondido con "no quiero".
        """
        while True:
            if juego.puede_cantar_envido(jugador):
                nivel = self.estrategia_cpu.quiere_cantar_envido(juego, jugador, rival)
                if nivel is not None:
                    self._resolver_envido_consola(juego, jugador, rival, nivel)
                    if not juego.en_curso:
                        return
                    continue
            if juego.puede_cantar_truco(jugador):
                if self.estrategia_cpu.quiere_cantar_truco(juego, jugador, rival):
                    self._resolver_truco_consola(juego, jugador, rival)
                    if not juego.en_curso:
                        return
                    continue
            if self.estrategia_cpu.quiere_irse_al_mazo(juego, jugador, rival):
                ganador, puntos = juego.irse_al_mazo(jugador)
                print(f"{jugador.nombre} se va al mazo. {ganador.nombre} suma {puntos} pto/s.")
                return
            carta = self.estrategia_cpu.elegir_carta(juego, jugador, rival)
            juego.jugar_turno(jugador, carta)
            print(f"{jugador.nombre} juega {carta}")
            return

    def _turno_jugador_consola(self, juego, jugador, rival):
        """
        PRE: es el turno de 'jugador' (humano) dentro de la baza actual.
        POST: 'jugador' juega una carta (eventualmente, tras cantar Envido
              y/o Truco las veces que la situacion lo permita), se va al
              mazo, o la mano termina si algun canto es respondido con
              "no quiero".
        """
        while True:
            etiquetas = ("Jugar una carta",)
            acciones = (("jugar", None),)
            if juego.puede_cantar_envido(jugador):
                for nivel in juego.niveles_disponibles_envido():
                    etiquetas += (f"Cantar {self._nombre_legible(nivel)}",)
                    acciones += (("envido", nivel),)
            if juego.puede_cantar_truco(jugador):
                etiquetas += (f"Cantar {self._nombre_legible(juego.nombre_proximo_canto())}",)
                acciones += (("truco", None),)
            etiquetas += ("Irse al mazo",)
            acciones += (("mazo", None),)

            print(f"\nTurno de {jugador.nombre}. Cartas: {jugador.mano}")
            for numero, etiqueta in enumerate(etiquetas, start=1):
                print(f"  {numero}) {etiqueta}")
            tipo, valor = acciones[self._pedir_opcion(len(etiquetas)) - 1]

            if tipo == "jugar":
                indice = self._pedir_indice_carta(jugador)
                carta = jugador.mano.obtener(indice)
                juego.jugar_turno(jugador, carta)
                print(f"{jugador.nombre} juega {carta}")
                return
            if tipo == "envido":
                self._resolver_envido_consola(juego, jugador, rival, valor)
                if not juego.en_curso:
                    return
            elif tipo == "truco":
                self._resolver_truco_consola(juego, jugador, rival)
                if not juego.en_curso:
                    return
            else:
                ganador, puntos = juego.irse_al_mazo(jugador)
                print(f"{jugador.nombre} se fue al mazo. {ganador.nombre} suma {puntos} pto/s.")
                return

    def _resolver_envido_consola(self, juego, jugador_que_canta, rival, nivel_inicial):
        """
        PRE: 'jugador_que_canta' acaba de elegir cantar 'nivel_inicial' de Envido.
        POST: se resuelve la cadena completa de Envido (permitiendo que quien
              responde suba la apuesta en lugar de aceptar o rechazar,
              respondiendo humano por menu o CPU por su estrategia),
              otorgando los puntos correspondientes segun corresponda.
        """
        cantor, respondiente = jugador_que_canta, rival
        print(f"{cantor.nombre} canta {self._nombre_legible(nivel_inicial)}.")
        juego.cantar_envido(nivel_inicial, cantor)

        while True:
            if self._es_cpu(respondiente):
                decision = self.estrategia_cpu.responder_envido(juego, respondiente, cantor)
            else:
                decision = self._preguntar_respuesta_envido_humano(juego, respondiente)

            if decision == "quiero":
                ganador, valor1, valor2, puntos = juego.resolver_envido_quiero()
                jugador1, jugador2 = juego.jugador_en_posicion(0), juego.jugador_en_posicion(1)
                print(f"Envido de {jugador1.nombre}: {valor1} - Envido de {jugador2.nombre}: {valor2}")
                print(f"{ganador.nombre} gana el Envido (+{puntos} pts).")
                return
            if decision == "no_quiero":
                puntos = juego.resolver_envido_no_quiero(respondiente)
                print(f"{respondiente.nombre} no quiso. {cantor.nombre} suma {puntos} pto/s por Envido.")
                return

            print(f"{respondiente.nombre} canta {self._nombre_legible(decision)}.")
            juego.cantar_envido(decision, respondiente)
            cantor, respondiente = respondiente, cantor

    def _preguntar_respuesta_envido_humano(self, juego, respondiente):
        """POST: pregunta por consola y retorna 'quiero', 'no_quiero', o un nivel de Envido superior."""
        etiquetas = ("Quiero", "No quiero")
        niveles_superiores = juego.niveles_disponibles_envido()
        for nivel in niveles_superiores:
            etiquetas += (f"Cantar {self._nombre_legible(nivel)}",)

        print(f"\n{respondiente.nombre}, ¿que decis?")
        for numero, etiqueta in enumerate(etiquetas, start=1):
            print(f"  {numero}) {etiqueta}")
        eleccion = self._pedir_opcion(len(etiquetas))

        if eleccion == 1:
            return "quiero"
        if eleccion == 2:
            return "no_quiero"
        return niveles_superiores[eleccion - 3]

    def _resolver_truco_consola(self, juego, jugador_que_canta, rival):
        """
        PRE: 'jugador_que_canta' puede cantar el proximo nivel de Truco.
        POST: se resuelve la cadena completa de Truco (permitiendo que quien
              responde suba la apuesta a Retruco/Vale Cuatro en lugar de
              aceptar o rechazar, respondiendo humano por menu o CPU por su
              estrategia), respetando que solo quien recibe un canto sin
              responder puede subir la apuesta.
        """
        cantor, respondiente = jugador_que_canta, rival
        print(f"{cantor.nombre} canta {self._nombre_legible(juego.nombre_proximo_canto())}.")
        juego.cantar(juego.proximo_valor_truco(), cantor)

        while True:
            if self._es_cpu(respondiente):
                decision = self.estrategia_cpu.responder_truco(juego, respondiente, cantor)
                if decision == "subir" and not juego.puede_cantar_truco(respondiente):
                    decision = "quiero"
            else:
                decision = self._preguntar_respuesta_truco_humano(juego, respondiente)

            if decision == "quiero":
                juego.resolver_canto(True)
                print(f"{respondiente.nombre} quiso. Ahora se juega por {juego.puntos_en_juego} pto/s.")
                return
            if decision == "no_quiero":
                puntos = juego.resolver_canto(False, jugador_que_no_quiere=respondiente)
                print(f"{respondiente.nombre} no quiso. {cantor.nombre} suma {puntos} pto/s.")
                return

            print(f"{respondiente.nombre} canta {self._nombre_legible(juego.nombre_proximo_canto())}.")
            juego.cantar(juego.proximo_valor_truco(), respondiente)
            cantor, respondiente = respondiente, cantor

    def _preguntar_respuesta_truco_humano(self, juego, respondiente):
        """POST: pregunta por consola y retorna 'quiero', 'no_quiero' o 'subir'."""
        etiquetas = ("Quiero", "No quiero")
        if juego.puede_cantar_truco(respondiente):
            etiquetas += (f"Cantar {self._nombre_legible(juego.nombre_proximo_canto())}",)

        print(f"\n{respondiente.nombre}, ¿que decis?")
        for numero, etiqueta in enumerate(etiquetas, start=1):
            print(f"  {numero}) {etiqueta}")
        eleccion = self._pedir_opcion(len(etiquetas))

        if eleccion == 1:
            return "quiero"
        if eleccion == 2:
            return "no_quiero"
        return "subir"

    def _nombre_legible(self, nombre_interno):
        """POST: retorna 'nombre_interno' (p.ej. 'real_envido') formateado para mostrar (Real Envido)."""
        return nombre_interno.replace("_", " ").title()

    def _pedir_opcion(self, cantidad):
        """PRE: cantidad > 0. POST: retorna un entero entre 1 y 'cantidad' elegido por el usuario."""
        while True:
            entrada = input(f"Elegi una opcion (1-{cantidad}): ").strip()
            if entrada.isdigit() and 1 <= int(entrada) <= cantidad:
                return int(entrada)
            print("Opcion invalida, intenta de nuevo.")

    def _pedir_indice_carta(self, jugador):
        """
        PRE: jugador.mano no esta vacia.
        POST: retorna el indice (base 0) de la carta elegida por el usuario,
              mostrando previamente todas las cartas disponibles numeradas desde 1.
        """
        cantidad = len(jugador.mano)
        for numero, carta in enumerate(jugador.mano, start=1):
            print(f"  {numero}) {carta}")
        while True:
            entrada = input(f"Elegi una carta (1-{cantidad}): ").strip()
            if entrada.isdigit() and 1 <= int(entrada) <= cantidad:
                return int(entrada) - 1
            print("Opcion invalida, intenta de nuevo.")

    def __str__(self):
        estado = str(self.juego_actual) if self.juego_actual is not None else "sin juego iniciado"
        return f"GameManager - {estado}"
