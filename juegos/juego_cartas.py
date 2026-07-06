"""Arquitectura general para modelar cualquier juego de cartas."""

from abc import ABC, abstractmethod

from estructuras.lista_enlazada import ListaEnlazada
from juegos.jugador import Jugador


class JuegoDeCartas(ABC):
    """
    Clase base abstracta que representa un juego de cartas generico.

    Esta clase concentra lo que cualquier juego de cartas necesita (mazo,
    jugadores, cartas por mano y estado de la partida), de forma que agregar
    un juego nuevo en el futuro solo requiera heredar de ella e implementar
    'jugar_turno' y 'verificar_ganador'.

    Invariante de representacion:
        - 'jugadores' contiene al menos 2 elementos una vez construido el juego.
        - 'cartas_por_mano' es mayor a 0.
        - 'en_curso' es True unicamente mientras la partida esta activa.
    """

    def __init__(self, mazo, nombres_jugadores, cartas_por_mano):
        """
        PRE: 'mazo' es una instancia de Mazo; 'nombres_jugadores' es un iterable
             con al menos 2 nombres; 'cartas_por_mano' es un entero mayor a 0.
        POST: se crea el juego con un Jugador por cada nombre recibido, sin
              cartas repartidas todavia y con 'en_curso' en False.
        """
        self.mazo = mazo
        self.jugadores = ListaEnlazada()
        for nombre in nombres_jugadores:
            self.jugadores.insertar_al_final(Jugador(nombre))
        if len(self.jugadores) < 2:
            raise ValueError("Un juego de cartas requiere al menos 2 jugadores")
        self.cartas_por_mano = cartas_por_mano
        self.en_curso = False

    def repartir(self):
        """
        PRE: el mazo debe tener al menos 'cartas_por_mano' * cantidad_jugadores cartas.
        POST: cada jugador recibe 'cartas_por_mano' cartas nuevas en su mano.
        """
        for _ in range(self.cartas_por_mano):
            for jugador in self.jugadores:
                jugador.recibir_carta(self.mazo.robar_carta())

    @abstractmethod
    def jugar_turno(self, *args, **kwargs):
        """Debe implementar la logica de un turno especifica del juego concreto."""
        raise NotImplementedError

    @abstractmethod
    def verificar_ganador(self):
        """Debe retornar el Jugador ganador de la partida, o None si aun no lo hay."""
        raise NotImplementedError

    def __str__(self):
        estado = "en curso" if self.en_curso else "sin iniciar"
        jugadores_str = ", ".join(str(jugador) for jugador in self.jugadores)
        return f"{self.__class__.__name__} ({estado}) - Jugadores: {jugadores_str}"
