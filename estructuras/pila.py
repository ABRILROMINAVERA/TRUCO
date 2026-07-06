"""TAD Pila (LIFO) implementado sobre ListaEnlazada."""

from estructuras.lista_enlazada import ListaEnlazada


class Pila:
    """
    TAD Pila (Last In, First Out) implementado utilizando ListaEnlazada.

    Invariante de representacion:
        - El tope de la pila coincide siempre con el primer elemento de la
          lista enlazada interna (_lista), de modo que push/pop operan en O(1).
    """

    def __init__(self):
        """POST: se crea una pila vacia."""
        self._lista = ListaEnlazada()

    def push(self, dato):
        """
        PRE: 'dato' es el elemento a apilar.
        POST: 'dato' queda en el tope de la pila.
        """
        self._lista.insertar_al_inicio(dato)

    def pop(self):
        """
        PRE: la pila no debe estar vacia.
        POST: se elimina y retorna el elemento que estaba en el tope.
        """
        if self.is_empty():
            raise IndexError("No se puede desapilar: la pila esta vacia")
        cabeza = self._lista._cabeza
        dato = cabeza.dato
        self._lista._cabeza = cabeza.siguiente
        self._lista._longitud -= 1
        return dato

    def peek(self):
        """
        PRE: la pila no debe estar vacia.
        POST: retorna el dato del tope sin eliminarlo de la pila.
        """
        if self.is_empty():
            raise IndexError("La pila esta vacia")
        return self._lista._cabeza.dato

    def is_empty(self):
        """POST: retorna True si la pila no contiene elementos."""
        return self._lista.esta_vacia()

    def __len__(self):
        return len(self._lista)

    def __str__(self):
        return f"Pila(tope -> {self._lista})"
