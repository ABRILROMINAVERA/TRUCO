"""Modelado generico de una carta de baraja (Naipe)."""

from enum import Enum


class Palo(Enum):
    """Palos posibles de una carta. COMODIN se usa para los comodines del mazo."""

    ORO = "Oro"
    COPA = "Copa"
    ESPADA = "Espada"
    BASTO = "Basto"
    COMODIN = "Comodin"


class Carta:
    """
    Representa una carta generica de un juego (valor + palo).

    Invariante de representacion:
        - 'valor' y 'palo' no cambian una vez creada la carta (uso inmutable).
        - Si 'es_comodin' es True, 'palo' es Palo.COMODIN.

    Orden generico (usado por __lt__/__gt__): se compara primero por 'valor' y,
    en caso de empate, por el palo segun _ORDEN_PALOS. Este orden generico es
    independiente de la jerarquia especial que puede definir un juego concreto
    (por ejemplo, el Truco define su propia jerarquia en la clase Truco).
    """

    _ORDEN_PALOS = {
        Palo.ESPADA: 0,
        Palo.BASTO: 1,
        Palo.ORO: 2,
        Palo.COPA: 3,
        Palo.COMODIN: 4,
    }

    def __init__(self, valor, palo, es_comodin=False):
        """
        PRE: 'valor' es un entero valido para el mazo utilizado; 'palo' es un Palo.
        POST: se crea la carta con el valor y palo indicados.
        """
        self.valor = valor
        self.palo = palo
        self.es_comodin = es_comodin

    def _clave(self):
        return (self.valor, self._ORDEN_PALOS.get(self.palo, 99))

    def __str__(self):
        if self.es_comodin:
            return "Comodin"
        return f"{self.valor} de {self.palo.value}"

    def __eq__(self, other):
        if not isinstance(other, Carta):
            return NotImplemented
        return self.valor == other.valor and self.palo == other.palo

    def __lt__(self, other):
        if not isinstance(other, Carta):
            return NotImplemented
        return self._clave() < other._clave()

    def __gt__(self, other):
        if not isinstance(other, Carta):
            return NotImplemented
        return self._clave() > other._clave()

    def __hash__(self):
        return hash((self.valor, self.palo))
