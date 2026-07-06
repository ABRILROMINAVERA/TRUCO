"""
Implementacion del juego de cartas "La Guerra", con el mazo espanol de 48
cartas (sin comodines) ya modelado en cartas.mazo.MazoEspanol.

Este modulo es completamente independiente del Truco: no importa nada de
juegos.truco ni de juegos.estrategia_cpu, y no modifica ninguna clase ya
existente (Carta, Mazo, Pila, etc.); solo las reutiliza por importacion, o
las extiende por herencia (ver PilaGuerra), sin tocar sus archivos
originales. Si esta carpeta se elimina, el resto del proyecto (Truco) sigue
funcionando exactamente igual.
"""

from cartas.mazo import MazoEspanol
from estructuras.lista_enlazada import ListaEnlazada
from estructuras.pila import Pila


class PilaGuerra(Pila):
    """
    Extiende la Pila generica agregando la posibilidad de apilar tambien
    en el fondo (ademas de en el tope). Se necesita en La Guerra: cuando un
    jugador gana una ronda (o una guerra), las cartas ganadas se agregan al
    fondo de su mazo -no al tope- para que no vuelvan a salir de inmediato,
    tal como se hace al jugar a la guerra con cartas reales.

    Invariante: igual que Pila (las cartas solo se pueden sacar por el tope).
    """

    def agregar_al_fondo(self, dato):
        """
        PRE: 'dato' es la carta a agregar.
        POST: 'dato' queda en el fondo de la pila (sera la ultima carta en salir).
        """
        self._lista.insertar_al_final(dato)


class JugadorGuerra:
    """
    Representa a un jugador de La Guerra: un nombre y un mazo de cartas
    boca abajo (su pila de juego). A diferencia del Jugador del Truco, en
    La Guerra no se elige que carta jugar: siempre se juega la de arriba
    del mazo, por eso no tiene una "mano" de cartas elegibles.
    """

    def __init__(self, nombre):
        """POST: se crea un jugador con 'nombre' y el mazo vacio."""
        self.nombre = nombre
        self.mazo = PilaGuerra()

    def tiene_cartas(self):
        """POST: retorna True si al jugador le quedan cartas para jugar."""
        return not self.mazo.is_empty()

    def cartas_restantes(self):
        """POST: retorna la cantidad de cartas que le quedan al jugador."""
        return len(self.mazo)

    def __str__(self):
        return f"{self.nombre} ({self.cartas_restantes()} cartas)"


class JuegoGuerra:
    """
    El juego de cartas "La Guerra", jugado entre 2 jugadores con el mazo
    espanol completo (48 cartas, sin comodines), repartidas en partes
    iguales. En cada ronda ambos jugadores revelan automaticamente la
    carta de arriba de su mazo; gana la ronda quien tira el valor mas alto.
    Si empatan, se juega una "guerra": cada uno pone hasta 3 cartas boca
    abajo mas 1 boca arriba (o las que le queden, si son menos), y se
    vuelve a comparar; el ganador final se lleva todas las cartas puestas
    en juego. El juego termina cuando alguno de los dos se queda sin cartas.

    Invariantes de representacion:
        - self.jugador1 y self.jugador2 son instancias de JugadorGuerra.
        - Mientras 'terminado()' sea False, ambos jugadores tienen al
          menos 1 carta en su mazo.

    Simplificacion: en el caso limite (muy poco frecuente) de que, en
    medio de una guerra, ambos jugadores se queden sin cartas exactamente
    al mismo tiempo, el juego termina sin otorgarle las cartas acumuladas
    a ninguno de los dos (no hay ganador).
    """

    CARTAS_POR_JUGADOR = 24
    CARTAS_BOCA_ABAJO_EN_GUERRA = 3

    def __init__(self, nombre_jugador1="Jugador 1", nombre_jugador2="Jugador 2"):
        """
        PRE: 'nombre_jugador1' y 'nombre_jugador2' son cadenas no vacias.
        POST: se crea la partida con un mazo espanol de 48 cartas (sin
              comodines) barajado y repartido en partes iguales (24 y 24)
              entre ambos jugadores, alternando una carta para cada uno
              como en un reparto real.
        """
        self.jugador1 = JugadorGuerra(nombre_jugador1)
        self.jugador2 = JugadorGuerra(nombre_jugador2)
        mazo = MazoEspanol(con_comodines=False)
        mazo.barajar()
        for _ in range(self.CARTAS_POR_JUGADOR):
            self.jugador1.mazo.push(mazo.robar_carta())
            self.jugador2.mazo.push(mazo.robar_carta())

    def terminado(self):
        """POST: retorna True si alguno de los dos jugadores se quedo sin cartas."""
        return self.jugador1.mazo.is_empty() or self.jugador2.mazo.is_empty()

    def ganador(self):
        """
        POST: retorna el JugadorGuerra que todavia tiene cartas, si el otro
              se quedo sin ninguna; retorna None si el juego no termino
              todavia, o si ambos se quedaron sin cartas a la vez.
        """
        vacio1 = self.jugador1.mazo.is_empty()
        vacio2 = self.jugador2.mazo.is_empty()
        if vacio1 and vacio2:
            return None
        if vacio1:
            return self.jugador2
        if vacio2:
            return self.jugador1
        return None

    def _sacar_cartas_para_guerra(self, jugador):
        """
        POST: retorna una ListaEnlazada con hasta (CARTAS_BOCA_ABAJO_EN_GUERRA + 1)
              cartas sacadas del tope del mazo de 'jugador' (las primeras
              se consideran boca abajo y la ultima boca arriba), o menos
              si no le alcanzan las cartas; queda vacia si no tiene ninguna.
        """
        cartas = ListaEnlazada()
        for _ in range(self.CARTAS_BOCA_ABAJO_EN_GUERRA + 1):
            if jugador.mazo.is_empty():
                break
            cartas.insertar_al_final(jugador.mazo.pop())
        return cartas

    def jugar_ronda(self):
        """
        PRE: el juego no debe estar terminado ('terminado()' debe ser False).
        POST: cada jugador juega la carta superior de su mazo; si empatan
              en valor, se resuelve una guerra (o mas de una encadenada, si
              las cartas boca arriba de la guerra tambien empatan) de hasta
              3 cartas boca abajo + 1 boca arriba por jugador (o las que le
              queden, si son menos); el ganador final se lleva todas las
              cartas que estuvieron en juego, agregandolas al fondo de su
              mazo. Retorna un diccionario con lo sucedido, para mostrarlo:
              'tipo' ('normal', 'guerra', 'guerra_sin_definicion' o
              'terminado'), 'carta1' y 'carta2' (las cartas boca arriba que
              definieron el resultado), 'ganador' (o None), 'cartas_ganadas'
              y 'rondas_de_guerra'.
        """
        if self.terminado():
            return {"tipo": "terminado", "carta1": None, "carta2": None,
                     "ganador": None, "cartas_ganadas": 0, "rondas_de_guerra": 0}

        jugador1, jugador2 = self.jugador1, self.jugador2
        carta1 = jugador1.mazo.pop()
        carta2 = jugador2.mazo.pop()
        acumuladas = ListaEnlazada()
        acumuladas.insertar_al_final(carta1)
        acumuladas.insertar_al_final(carta2)
        rondas_de_guerra = 0
        ganador = None

        while carta1.valor == carta2.valor:
            rondas_de_guerra += 1
            aportes1 = self._sacar_cartas_para_guerra(jugador1)
            aportes2 = self._sacar_cartas_para_guerra(jugador2)
            for carta in aportes1:
                acumuladas.insertar_al_final(carta)
            for carta in aportes2:
                acumuladas.insertar_al_final(carta)

            if len(aportes1) == 0 and len(aportes2) == 0:
                return {"tipo": "guerra_sin_definicion", "carta1": carta1, "carta2": carta2,
                        "ganador": None, "cartas_ganadas": len(acumuladas),
                        "rondas_de_guerra": rondas_de_guerra}
            if len(aportes1) == 0:
                ganador = jugador2
                break
            if len(aportes2) == 0:
                ganador = jugador1
                break

            carta1 = aportes1.obtener(len(aportes1) - 1)
            carta2 = aportes2.obtener(len(aportes2) - 1)
            if carta1.valor > carta2.valor:
                ganador = jugador1
                break
            if carta2.valor > carta1.valor:
                ganador = jugador2
                break
            # si siguen empatados, el while vuelve a entrar (se juega otra guerra)

        if ganador is None:
            ganador = jugador1 if carta1.valor > carta2.valor else jugador2

        for carta in acumuladas:
            ganador.mazo.agregar_al_fondo(carta)

        return {
            "tipo": "guerra" if rondas_de_guerra > 0 else "normal",
            "carta1": carta1,
            "carta2": carta2,
            "ganador": ganador,
            "cartas_ganadas": len(acumuladas),
            "rondas_de_guerra": rondas_de_guerra,
        }

    def __str__(self):
        estado = "terminado" if self.terminado() else "en curso"
        return f"La Guerra ({estado}) - {self.jugador1} vs {self.jugador2}"
