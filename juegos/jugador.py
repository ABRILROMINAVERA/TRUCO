"""Representa a un jugador dentro de un juego de cartas."""

from estructuras.lista_enlazada import ListaEnlazada


class Jugador:
    """
    Representa a un jugador con su mano de cartas y su puntaje.

    Invariante de representacion:
        - 'mano' solo contiene cartas que el jugador todavia no jugo en la mano actual.
        - 'puntos' es siempre mayor o igual a 0.
    """

    def __init__(self, nombre):
        """
        PRE: 'nombre' es una cadena no vacia que identifica al jugador.
        POST: se crea un jugador sin cartas en mano y con 0 puntos.
        """
        self.nombre = nombre
        self.mano = ListaEnlazada()
        self.puntos = 0

    def recibir_carta(self, carta):
        """
        PRE: 'carta' es la carta a agregar a la mano.
        POST: 'carta' queda incorporada a la mano del jugador.
        """
        self.mano.insertar_al_final(carta)

    def jugar_carta(self, carta):
        """
        PRE: 'carta' debe encontrarse actualmente en la mano del jugador.
        POST: 'carta' se retira de la mano del jugador y se retorna.
        """
        if not self.mano.buscar(carta):
            raise ValueError(f"{self.nombre} no tiene la carta {carta} en su mano")
        self.mano.eliminar(carta)
        return carta

    def __str__(self):
        return f"{self.nombre} ({self.puntos} pts) - Mano: {self.mano}"
