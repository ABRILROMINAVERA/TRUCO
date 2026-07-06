"""Clase Nodo: unidad basica de una lista enlazada."""


class Nodo:
    """
    Representa un nodo de una lista enlazada simple.

    Invariante de representacion:
        - 'siguiente' es None o una referencia a otro objeto Nodo.
    """

    def __init__(self, dato, siguiente=None):
        """
        PRE: 'dato' es el valor a almacenar; 'siguiente' es None o un Nodo existente.
        POST: se crea un nodo con el dato dado y la referencia 'siguiente' indicada.
        """
        self.dato = dato
        self.siguiente = siguiente

    def __str__(self):
        return str(self.dato)
