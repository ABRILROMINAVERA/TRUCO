"""Mazo generico de cartas y su especializacion como mazo espanol."""

import random

from cartas.carta import Carta, Palo
from estructuras.pila import Pila


class Mazo:
    """
    Representa un conjunto de cartas, almacenadas como una pila.

    Invariante de representacion:
        - Todos los elementos contenidos en '_cartas' son instancias de Carta.
    """

    def __init__(self):
        """POST: se crea un mazo vacio."""
        self._cartas = Pila()

    def agregar_carta(self, carta):
        """
        PRE: 'carta' es una instancia de Carta.
        POST: 'carta' queda en el tope del mazo.
        """
        self._cartas.push(carta)

    def barajar(self):
        """
        PRE: el mazo puede tener 0 o mas cartas.
        POST: el orden de las cartas del mazo queda permutado de forma aleatoria
              (algoritmo de Fisher-Yates adaptado a la lista enlazada interna).
        """
        cantidad = len(self._cartas)
        if cantidad <= 1:
            return
        lista_interna = self._cartas._lista
        for i in range(cantidad - 1, 0, -1):
            j = random.randint(0, i)
            self._intercambiar(lista_interna, i, j)

    def _intercambiar(self, lista_interna, i, j):
        nodo_i = self._nodo_en_posicion(lista_interna, i)
        nodo_j = self._nodo_en_posicion(lista_interna, j)
        nodo_i.dato, nodo_j.dato = nodo_j.dato, nodo_i.dato

    def _nodo_en_posicion(self, lista_interna, indice):
        actual = lista_interna._cabeza
        posicion = 0
        while posicion < indice:
            actual = actual.siguiente
            posicion += 1
        return actual

    def robar_carta(self):
        """
        PRE: el mazo no debe estar vacio.
        POST: se elimina y retorna la carta que estaba en el tope del mazo.
        """
        if self.esta_vacio():
            raise IndexError("No hay mas cartas para robar")
        return self._cartas.pop()

    def cartas_restantes(self):
        """POST: retorna la cantidad de cartas que quedan en el mazo."""
        return len(self._cartas)

    def esta_vacio(self):
        """POST: retorna True si no quedan cartas en el mazo."""
        return self._cartas.is_empty()

    def __str__(self):
        return f"Mazo con {self.cartas_restantes()} cartas"


class MazoEspanol(Mazo):
    """
    Mazo espanol tradicional: 4 palos (oro, copa, espada, basto), valores
    del 1 al 12, y opcionalmente 2 comodines.

    Invariante adicional:
        - Recien creado (sin robar cartas), contiene 48 cartas (o 50 con comodines).
    """

    PALOS = (Palo.ORO, Palo.COPA, Palo.ESPADA, Palo.BASTO)
    VALORES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

    def __init__(self, con_comodines=True):
        """
        PRE: 'con_comodines' indica si se deben incluir los 2 comodines.
        POST: se crea un mazo espanol completo sin barajar.
        """
        super().__init__()
        for palo in self.PALOS:
            for valor in self.VALORES:
                self.agregar_carta(Carta(valor, palo))
        if con_comodines:
            self.agregar_carta(Carta(0, Palo.COMODIN, es_comodin=True))
            self.agregar_carta(Carta(0, Palo.COMODIN, es_comodin=True))

    def __str__(self):
        return f"Mazo Espanol ({self.cartas_restantes()} cartas restantes)"


class MazoTruco(Mazo):
    """
    Mazo de 40 cartas usado para jugar al Truco: mazo espanol sin comodines
    y sin los ochos ni los nueves (que no participan del juego).

    Invariante adicional:
        - Recien creado (sin robar cartas), contiene exactamente 40 cartas.
    """

    PALOS = (Palo.ORO, Palo.COPA, Palo.ESPADA, Palo.BASTO)
    VALORES = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)

    def __init__(self):
        """POST: se crea un mazo de 40 cartas de Truco sin barajar."""
        super().__init__()
        for palo in self.PALOS:
            for valor in self.VALORES:
                self.agregar_carta(Carta(valor, palo))

    def __str__(self):
        return f"Mazo de Truco ({self.cartas_restantes()} cartas restantes)"
