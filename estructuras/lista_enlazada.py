"""TAD Lista implementado mediante nodos enlazados (sin usar list/deque)."""

from estructuras.nodo import Nodo


class ListaEnlazada:
    """
    TAD Lista (lista enlazada simple).

    Invariantes de representacion:
        - _cabeza es None si y solo si _longitud == 0.
        - _longitud es siempre igual a la cantidad de nodos alcanzables desde _cabeza
          siguiendo las referencias 'siguiente'.
        - El ultimo nodo de la cadena (si existe) tiene 'siguiente' igual a None.
    """

    def __init__(self):
        """POST: se crea una lista vacia (_cabeza = None, _longitud = 0)."""
        self._cabeza = None
        self._longitud = 0

    def esta_vacia(self):
        """POST: retorna True si la lista no contiene elementos, False en caso contrario."""
        return self._cabeza is None

    def longitud(self):
        """POST: retorna la cantidad de elementos almacenados en la lista."""
        return self._longitud

    def insertar_al_inicio(self, dato):
        """
        PRE: 'dato' es el elemento a insertar.
        POST: 'dato' es el nuevo primer elemento de la lista; la longitud aumenta en 1.
        """
        self._cabeza = Nodo(dato, self._cabeza)
        self._longitud += 1

    def insertar_al_final(self, dato):
        """
        PRE: 'dato' es el elemento a insertar.
        POST: 'dato' queda como ultimo elemento de la lista; la longitud aumenta en 1.
        """
        nuevo = Nodo(dato)
        if self.esta_vacia():
            self._cabeza = nuevo
        else:
            actual = self._cabeza
            while actual.siguiente is not None:
                actual = actual.siguiente
            actual.siguiente = nuevo
        self._longitud += 1

    def eliminar(self, dato):
        """
        PRE: 'dato' es el elemento a buscar y eliminar (puede no estar presente).
        POST: si existia una ocurrencia de 'dato', se elimina la primera encontrada y
              la longitud disminuye en 1, retornando True; si no existia, retorna False
              y la lista queda sin cambios.
        """
        anterior = None
        actual = self._cabeza
        while actual is not None:
            if actual.dato == dato:
                if anterior is None:
                    self._cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                self._longitud -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def buscar(self, dato):
        """PRE: 'dato' es el elemento a buscar. POST: retorna True si esta en la lista."""
        actual = self._cabeza
        while actual is not None:
            if actual.dato == dato:
                return True
            actual = actual.siguiente
        return False

    def obtener(self, indice):
        """
        PRE: 0 <= indice < longitud de la lista.
        POST: retorna el dato almacenado en la posicion 'indice' (basado en 0).
        """
        if indice < 0 or indice >= self._longitud:
            raise IndexError("Indice fuera de rango")
        actual = self._cabeza
        posicion = 0
        while posicion < indice:
            actual = actual.siguiente
            posicion += 1
        return actual.dato

    def __len__(self):
        return self._longitud

    def __iter__(self):
        actual = self._cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def __str__(self):
        elementos = " -> ".join(str(dato) for dato in self)
        return f"[{elementos}]" if elementos else "[]"
