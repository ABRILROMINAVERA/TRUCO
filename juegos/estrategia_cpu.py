"""Estrategias de decision para un jugador de Truco manejado por la computadora."""

import random
from abc import ABC, abstractmethod


def _carta_rival_en_mesa(juego, jugador):
    """POST: retorna la carta que el rival ya jugo en la baza actual, o None si no jugo ninguna."""
    for jugador_en_mesa, carta_en_mesa in juego.cartas_jugadas:
        if jugador_en_mesa is not jugador:
            return carta_en_mesa
    return None


class EstrategiaCPU(ABC):
    """
    Interfaz que debe implementar cada nivel de dificultad de la CPU para
    tomar todas las decisiones de una mano de Truco: que carta jugar, si
    cantar o responder a un Envido/Truco, y si irse al mazo.
    """

    def _elegir_carta_basica(self, juego, jugador):
        """
        POST: retorna una carta de la mano de 'jugador' tratando de ganar la
              baza actual con la carta mas baja que alcance para hacerlo, o
              la carta mas baja de la mano si no puede ganarla (para
              reservar las cartas fuertes para las bazas siguientes).
        """
        cartas = tuple(jugador.mano)
        carta_rival = _carta_rival_en_mesa(juego, jugador)
        if carta_rival is None:
            return min(cartas, key=juego.valor_truco)
        valor_rival = juego.valor_truco(carta_rival)
        ganadoras = tuple(carta for carta in cartas if juego.valor_truco(carta) > valor_rival)
        if ganadoras:
            return min(ganadoras, key=juego.valor_truco)
        return min(cartas, key=juego.valor_truco)

    @abstractmethod
    def elegir_carta(self, juego, jugador, rival):
        """POST: retorna la Carta de la mano de 'jugador' que decide jugar."""
        raise NotImplementedError

    @abstractmethod
    def quiere_cantar_envido(self, juego, jugador, rival):
        """POST: retorna el nivel de Envido a cantar (de niveles_disponibles_envido), o None."""
        raise NotImplementedError

    @abstractmethod
    def responder_envido(self, juego, jugador, rival):
        """POST: retorna 'quiero', 'no_quiero', o un nivel de Envido al que subir la apuesta."""
        raise NotImplementedError

    @abstractmethod
    def quiere_cantar_truco(self, juego, jugador, rival):
        """POST: retorna True si 'jugador' quiere cantar el proximo nivel de Truco disponible."""
        raise NotImplementedError

    @abstractmethod
    def responder_truco(self, juego, jugador, rival):
        """POST: retorna 'quiero', 'no_quiero' o 'subir'."""
        raise NotImplementedError

    @abstractmethod
    def quiere_irse_al_mazo(self, juego, jugador, rival):
        """POST: retorna True si 'jugador' decide abandonar la mano actual."""
        raise NotImplementedError


class EstrategiaFacil(EstrategiaCPU):
    """
    Nivel Facil: juega cartas al azar, nunca canta Envido ni Truco por
    iniciativa propia, siempre acepta lo que le cantan y nunca se va al mazo.
    """

    def elegir_carta(self, juego, jugador, rival):
        cartas = tuple(jugador.mano)
        return cartas[random.randint(0, len(cartas) - 1)]

    def quiere_cantar_envido(self, juego, jugador, rival):
        return None

    def responder_envido(self, juego, jugador, rival):
        return "quiero"

    def quiere_cantar_truco(self, juego, jugador, rival):
        return False

    def responder_truco(self, juego, jugador, rival):
        return "quiero"

    def quiere_irse_al_mazo(self, juego, jugador, rival):
        return False


class EstrategiaMedia(EstrategiaCPU):
    """
    Nivel Media: juega tratando de ganar cada baza con la carta mas baja
    posible, y canta o responde Envido/Truco comparando el valor de su mano
    contra umbrales fijos.
    """

    UMBRAL_ENVIDO_CANTA = 27
    UMBRAL_ENVIDO_ACEPTA = 20
    JERARQUIA_TRUCO_CANTA = 11  # 2 o mejor
    JERARQUIA_TRUCO_ACEPTA = 8  # anchos falsos o mejor

    def elegir_carta(self, juego, jugador, rival):
        return self._elegir_carta_basica(juego, jugador)

    def quiere_cantar_envido(self, juego, jugador, rival):
        if juego.calcular_envido(jugador) >= self.UMBRAL_ENVIDO_CANTA:
            niveles = juego.niveles_disponibles_envido()
            return niveles[0] if niveles else None
        return None

    def responder_envido(self, juego, jugador, rival):
        if juego.calcular_envido(jugador) >= self.UMBRAL_ENVIDO_ACEPTA:
            return "quiero"
        return "no_quiero"

    def quiere_cantar_truco(self, juego, jugador, rival):
        mejor = max((juego.valor_truco(carta) for carta in jugador.mano), default=0)
        return mejor >= self.JERARQUIA_TRUCO_CANTA

    def responder_truco(self, juego, jugador, rival):
        mejor = max((juego.valor_truco(carta) for carta in jugador.mano), default=0)
        return "quiero" if mejor >= self.JERARQUIA_TRUCO_ACEPTA else "no_quiero"

    def quiere_irse_al_mazo(self, juego, jugador, rival):
        if len(jugador.mano) == 0:
            return False
        mejor = max((juego.valor_truco(carta) for carta in jugador.mano), default=0)
        return juego.puntos_en_juego >= 3 and mejor < 3


class EstrategiaDificil(EstrategiaCPU):
    """
    Nivel Dificil: ademas de la heuristica de Media, sube la apuesta de
    Envido y de Truco con manos muy fuertes, juega mas agresivo si ya perdio
    la primera baza, se va al mazo con manos muy flojas cuando la apuesta es
    alta, y de vez en cuando "blofea" cantando con una mano floja.
    """

    UMBRAL_ENVIDO_CANTA = 24
    UMBRAL_ENVIDO_SUBE = 30
    UMBRAL_ENVIDO_ACEPTA = 22
    JERARQUIA_TRUCO_CANTA = 9
    JERARQUIA_TRUCO_SUBE = 12
    JERARQUIA_TRUCO_ACEPTA = 6
    PROBABILIDAD_BLOF = 0.15

    def elegir_carta(self, juego, jugador, rival):
        if juego.ronda_actual == 1 and len(juego.resultados_bazas) == 1:
            primer_ganador = juego.resultados_bazas.obtener(0)
            if primer_ganador is not None and primer_ganador is not jugador:
                return self._elegir_carta_agresiva(juego, jugador)
        return self._elegir_carta_basica(juego, jugador)

    def _elegir_carta_agresiva(self, juego, jugador):
        """POST: juega para ganar esta baza como sea, ya que perder tambien esta pierde la mano."""
        cartas = tuple(jugador.mano)
        carta_rival = _carta_rival_en_mesa(juego, jugador)
        if carta_rival is None:
            return max(cartas, key=juego.valor_truco)
        valor_rival = juego.valor_truco(carta_rival)
        ganadoras = tuple(carta for carta in cartas if juego.valor_truco(carta) > valor_rival)
        if ganadoras:
            return min(ganadoras, key=juego.valor_truco)
        return max(cartas, key=juego.valor_truco)

    def quiere_cantar_envido(self, juego, jugador, rival):
        valor = juego.calcular_envido(jugador)
        niveles = juego.niveles_disponibles_envido()
        if not niveles:
            return None
        if valor >= self.UMBRAL_ENVIDO_CANTA:
            if valor >= self.UMBRAL_ENVIDO_SUBE and "falta_envido" in niveles:
                return "falta_envido"
            return niveles[0]
        if random.random() < self.PROBABILIDAD_BLOF:
            return niveles[0]
        return None

    def responder_envido(self, juego, jugador, rival):
        valor = juego.calcular_envido(jugador)
        niveles = juego.niveles_disponibles_envido()
        if valor >= self.UMBRAL_ENVIDO_SUBE and niveles:
            return niveles[0]
        if valor >= self.UMBRAL_ENVIDO_ACEPTA:
            return "quiero"
        return "no_quiero"

    def quiere_cantar_truco(self, juego, jugador, rival):
        mejor = max((juego.valor_truco(carta) for carta in jugador.mano), default=0)
        if mejor >= self.JERARQUIA_TRUCO_CANTA:
            return True
        return random.random() < self.PROBABILIDAD_BLOF

    def responder_truco(self, juego, jugador, rival):
        mejor = max((juego.valor_truco(carta) for carta in jugador.mano), default=0)
        if mejor >= self.JERARQUIA_TRUCO_SUBE and juego.puede_cantar_truco(jugador):
            return "subir"
        if mejor >= self.JERARQUIA_TRUCO_ACEPTA:
            return "quiero"
        return "no_quiero"

    def quiere_irse_al_mazo(self, juego, jugador, rival):
        if len(jugador.mano) == 0:
            return False
        mejor = max((juego.valor_truco(carta) for carta in jugador.mano), default=0)
        return juego.puntos_en_juego >= 3 and mejor <= 2 and random.random() > 0.3


def crear_estrategia(dificultad):
    """
    PRE: 'dificultad' es una de "facil", "media" o "dificil".
    POST: retorna una instancia de la EstrategiaCPU correspondiente.
    """
    estrategias = {
        "facil": EstrategiaFacil,
        "media": EstrategiaMedia,
        "dificil": EstrategiaDificil,
    }
    if dificultad not in estrategias:
        raise ValueError("Dificultad invalida")
    return estrategias[dificultad]()
