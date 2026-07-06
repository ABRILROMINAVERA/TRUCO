"""Implementacion de una version del Truco argentino (sin Flor), para 2 jugadores."""

from cartas.carta import Palo
from cartas.mazo import MazoTruco
from estructuras.lista_enlazada import ListaEnlazada
from juegos.juego_cartas import JuegoDeCartas

_PENDIENTE = object()  # sentinel: indica que esa baza todavia no se jugo


def _construir_jerarquia_truco():
    """
    Construye la tabla de jerarquia de cartas del Truco (de mas fuerte a mas debil).
    No incluye los ochos, nueves ni comodines: esas cartas no forman parte del
    mazo de 40 cartas que se usa para jugar (ver cartas.mazo.MazoTruco).
    """
    grupos_de_mas_fuerte_a_mas_debil = (
        ((1, Palo.ESPADA),),  # El Macho
        ((1, Palo.BASTO),),  # La Hembra
        ((7, Palo.ESPADA),),  # Siete bravo
        ((7, Palo.ORO),),
        ((3, Palo.ORO), (3, Palo.COPA), (3, Palo.ESPADA), (3, Palo.BASTO)),
        ((2, Palo.ORO), (2, Palo.COPA), (2, Palo.ESPADA), (2, Palo.BASTO)),
        ((1, Palo.ORO), (1, Palo.COPA)),  # Anchos falsos
        ((12, Palo.ORO), (12, Palo.COPA), (12, Palo.ESPADA), (12, Palo.BASTO)),
        ((11, Palo.ORO), (11, Palo.COPA), (11, Palo.ESPADA), (11, Palo.BASTO)),
        ((10, Palo.ORO), (10, Palo.COPA), (10, Palo.ESPADA), (10, Palo.BASTO)),
        ((7, Palo.COPA), (7, Palo.BASTO)),  # Sietes falsos
        ((6, Palo.ORO), (6, Palo.COPA), (6, Palo.ESPADA), (6, Palo.BASTO)),
        ((5, Palo.ORO), (5, Palo.COPA), (5, Palo.ESPADA), (5, Palo.BASTO)),
        ((4, Palo.ORO), (4, Palo.COPA), (4, Palo.ESPADA), (4, Palo.BASTO)),
    )
    jerarquia = {}
    puntaje = len(grupos_de_mas_fuerte_a_mas_debil)
    for grupo in grupos_de_mas_fuerte_a_mas_debil:
        for clave in grupo:
            jerarquia[clave] = puntaje
        puntaje -= 1
    return jerarquia


class Truco(JuegoDeCartas):
    """
    Version del Truco argentino para 2 jugadores, sin Flor.

    Invariantes de representacion:
        - self.jugadores contiene exactamente 2 jugadores.
        - self.puntos_en_juego es uno de los valores definidos en CANTOS (1, 2, 3 o 4).
        - Los puntos de cada jugador estan entre 0 y PUNTOS_PARTIDA (inclusive).
        - self.envido_nivel_actual, si no es None, es uno de NIVELES_ENVIDO y
          cada nivel sucesivo cantado en una mano es estrictamente superior al anterior.

    Simplificaciones respecto del Truco real (fuera del alcance de este TP):
        - No se implementa Flor.
        - Como esta version de consola muestra ambas manos en pantalla en
          todo momento (no hay informacion oculta entre jugadores), no se
          modela el "son buenas" del Envido ni la obligacion de mostrar las
          cartas al ganar el Envido: esas reglas existen para proteger
          informacion que, en esta implementacion, ya es publica.
    """

    PUNTOS_PARTIDA = 30
    CANTOS = {"truco": 2, "retruco": 3, "vale_cuatro": 4}
    NIVELES_ENVIDO = ("envido", "real_envido", "falta_envido")
    VALORES_ENVIDO = {"envido": 2, "real_envido": 3}

    def __init__(self, nombre_jugador1, nombre_jugador2, puntos_partida=30):
        """
        PRE: 'nombre_jugador1' y 'nombre_jugador2' son cadenas no vacias y distintas;
             'puntos_partida' es 15 o 30 (las "malas" o las "malas"+"buenas" completas).
        POST: se crea la partida con un mazo de Truco (40 cartas) barajado,
              ambos jugadores en 0 puntos, sin cartas repartidas todavia, y
              con 'puntos_partida' como el puntaje necesario para ganar
              (reemplaza al valor de clase PUNTOS_PARTIDA solo para esta partida).
        """
        mazo = MazoTruco()
        mazo.barajar()
        super().__init__(mazo, (nombre_jugador1, nombre_jugador2), cartas_por_mano=3)
        self.PUNTOS_PARTIDA = puntos_partida
        self._jerarquia = _construir_jerarquia_truco()
        self.puntos_en_juego = 1
        self.cartas_jugadas = ListaEnlazada()
        self.resultados_bazas = ListaEnlazada()
        self.ronda_actual = 0
        self._manos_jugadas = 0
        self.indice_mano = 0
        self.lider_baza_index = 0
        self.ultimo_cantor = None
        self._manos_originales = {}
        self.envido_nivel_actual = None
        self.envido_puntos_acumulados = 0
        self.envido_cantor_actual = None
        self.envido_terminado = False

    def valor_truco(self, carta):
        """POST: retorna el valor jerarquico de 'carta' segun las reglas del Truco."""
        return self._jerarquia.get((carta.valor, carta.palo), 0)

    def jugador_en_posicion(self, indice):
        """PRE: indice es 0 o 1. POST: retorna el Jugador ubicado en esa posicion."""
        return self.jugadores.obtener(indice)

    def indice_de_jugador(self, jugador):
        """PRE: 'jugador' participa de la partida. POST: retorna 0 o 1 segun su posicion."""
        return 0 if jugador is self.jugador_en_posicion(0) else 1

    def fase_actual(self):
        """POST: retorna 'Malas' si nadie llego a la mitad de PUNTOS_PARTIDA, 'Buenas' si si."""
        maximo = max(jugador.puntos for jugador in self.jugadores)
        return "Malas" if maximo < self.PUNTOS_PARTIDA // 2 else "Buenas"

    def sortear_mano_inicial(self):
        """
        PRE: se llama una unica vez, antes de jugar la primera mano de la partida.
        POST: se sortea (con cartas al azar de un mazo temporal) quien reparte
              primero -gana el sorteo quien saca la carta de mayor jerarquia,
              repitiendo el sorteo ante empate- y se deja como jugador "mano"
              de la primera mano al rival de quien reparte. Retorna al jugador
              que reparte.
        """
        while True:
            mazo_sorteo = MazoTruco()
            mazo_sorteo.barajar()
            carta_1 = mazo_sorteo.robar_carta()
            carta_2 = mazo_sorteo.robar_carta()
            valor_1, valor_2 = self.valor_truco(carta_1), self.valor_truco(carta_2)
            if valor_1 != valor_2:
                break
        jugador_1, jugador_2 = self.jugador_en_posicion(0), self.jugador_en_posicion(1)
        repartidor = jugador_1 if valor_1 > valor_2 else jugador_2
        self._manos_jugadas = 1 - self.indice_de_jugador(repartidor)
        return repartidor

    def iniciar_mano(self):
        """
        PRE: puede ejecutarse en cualquier momento de la partida.
        POST: se arma un mazo de Truco nuevo (40 cartas) y se baraja, se
              descartan las cartas que le quedaran en la mano a cada jugador
              de la mano anterior, se reparten 3 cartas nuevas a cada uno,
              se rota quien es "mano" respecto de la mano anterior, se
              guarda una copia de las 3 cartas originales de cada jugador
              (para calcular el envido incluso despues de jugar cartas), y
              se reinicia todo el estado de bazas (incluyendo cualquier
              carta que hubiese quedado jugada a mitad de una baza si la
              mano anterior termino de golpe por un "no quiero" o por irse
              al mazo), cantos de truco y de envido.
        """
        self.mazo = MazoTruco()
        self.mazo.barajar()
        for jugador in self.jugadores:
            jugador.mano = ListaEnlazada()
        self.repartir()
        self._manos_originales = {
            jugador.nombre: tuple(jugador.mano) for jugador in self.jugadores
        }
        self.indice_mano = self._manos_jugadas % 2
        self._manos_jugadas += 1
        self.lider_baza_index = self.indice_mano
        self.en_curso = True
        self.puntos_en_juego = 1
        self.ultimo_cantor = None
        self.cartas_jugadas = ListaEnlazada()
        self.resultados_bazas = ListaEnlazada()
        self.ronda_actual = 0
        self.envido_nivel_actual = None
        self.envido_puntos_acumulados = 0
        self.envido_cantor_actual = None
        self.envido_terminado = False

    def jugar_turno(self, jugador, carta):
        """
        PRE: 'jugador' participa de la partida y tiene 'carta' en su mano;
             la baza actual tiene a lo sumo 1 carta jugada.
        POST: 'carta' pasa de la mano de 'jugador' a la baza en curso.
        """
        if len(self.cartas_jugadas) >= 2:
            raise ValueError("Ya se jugaron las 2 cartas de esta baza")
        jugador.jugar_carta(carta)
        self.cartas_jugadas.insertar_al_final((jugador, carta))

    def resolver_baza(self):
        """
        PRE: deben haberse jugado exactamente 2 cartas en la baza actual.
        POST: se determina el ganador de la baza (o None si empatan/"parda"),
              se lo registra en 'resultados_bazas', se reinicia la baza
              actual y aumenta 'ronda_actual' en 1.
        """
        if len(self.cartas_jugadas) != 2:
            raise ValueError("La baza debe tener exactamente 2 cartas jugadas")
        iterador = iter(self.cartas_jugadas)
        jugador1, carta1 = next(iterador)
        jugador2, carta2 = next(iterador)
        valor1, valor2 = self.valor_truco(carta1), self.valor_truco(carta2)

        ganador = None
        if valor1 > valor2:
            ganador = jugador1
        elif valor2 > valor1:
            ganador = jugador2

        self.resultados_bazas.insertar_al_final(ganador)
        self.cartas_jugadas = ListaEnlazada()
        self.ronda_actual += 1
        return ganador

    def jugador_gana_mano(self):
        """
        POST: retorna el Jugador ganador de la mano segun las reglas de "parda":
              - Quien gane 2 bazas gana la mano.
              - Si la 1a baza es parda, gana quien gane la 2a (si tambien es
                parda, decide la 3a; si las tres son pardas, gana el mano).
              - Si la 1a tiene ganador y la 2a es parda, gana quien gano la 1a.
              - Si la 1a y la 2a las ganan jugadores distintos, decide la 3a;
                si esta tambien es parda, gana quien gano la 1a (convencion
                estandar del Truco que completa el caso no cubierto de forma
                explicita por las reglas provistas).
              Retorna None si todavia no puede determinarse con las bazas
              jugadas hasta el momento.
        """
        cantidad = len(self.resultados_bazas)
        r1 = self.resultados_bazas.obtener(0) if cantidad > 0 else _PENDIENTE
        r2 = self.resultados_bazas.obtener(1) if cantidad > 1 else _PENDIENTE
        r3 = self.resultados_bazas.obtener(2) if cantidad > 2 else _PENDIENTE
        jugador_mano = self.jugador_en_posicion(self.indice_mano)

        if r1 is _PENDIENTE or r2 is _PENDIENTE:
            return None
        if r1 is not None and r1 is r2:
            return r1
        if r1 is None and r2 is None:
            if r3 is _PENDIENTE:
                return None
            return r3 if r3 is not None else jugador_mano
        if r1 is None:
            return r2
        if r2 is None:
            return r1
        if r3 is _PENDIENTE:
            return None
        return r3 if r3 is not None else r1

    def proximo_valor_truco(self):
        """POST: retorna el valor de puntos que se pondria en juego con el proximo canto."""
        if self.puntos_en_juego == 1:
            return self.CANTOS["truco"]
        if self.puntos_en_juego == 2:
            return self.CANTOS["retruco"]
        return self.CANTOS["vale_cuatro"]

    def nombre_proximo_canto(self):
        """POST: retorna el nombre legible del proximo canto disponible (truco/retruco/vale cuatro)."""
        valor = self.proximo_valor_truco()
        for nombre, val in self.CANTOS.items():
            if val == valor:
                return nombre.replace("_", " ")
        return ""

    def puede_cantar_truco(self, jugador):
        """
        POST: retorna True si 'jugador' puede cantar el proximo nivel de truco:
              todavia no se llego a "vale cuatro" y, si ya hubo un canto sin
              responder, 'jugador' no es quien lo realizo (le corresponde al
              rival responder o subir la apuesta, respetando el orden real
              del Truco: quien dijo "quiero" tiene el derecho exclusivo de
              subir la apuesta despues).
        """
        if self.puntos_en_juego >= self.CANTOS["vale_cuatro"]:
            return False
        if self.ultimo_cantor is None:
            return True
        return self.ultimo_cantor is not jugador

    def cantar(self, valor_nuevo, jugador):
        """
        PRE: 'valor_nuevo' es uno de los valores de CANTOS y es mayor al
             'puntos_en_juego' actual; 'jugador' puede cantar segun
             'puede_cantar_truco'.
        POST: 'puntos_en_juego' queda establecido en 'valor_nuevo' y 'jugador'
              queda registrado como quien realizo el ultimo canto, a la
              espera de ser aceptado o rechazado mediante 'resolver_canto'.
        """
        if valor_nuevo not in self.CANTOS.values():
            raise ValueError("Canto invalido")
        if valor_nuevo <= self.puntos_en_juego:
            raise ValueError("El nuevo canto debe superar al valor actual en juego")
        self.puntos_en_juego = valor_nuevo
        self.ultimo_cantor = jugador

    def resolver_canto(self, aceptado, jugador_que_no_quiere=None):
        """
        PRE: existe un canto de truco pendiente de resolucion (puntos_en_juego > 1).
        POST: si no se acepta, la mano finaliza y se suma 1 punto menos que lo
              cantado al oponente de quien dijo "no quiero"; si se acepta, la
              mano continua jugandose por 'puntos_en_juego' puntos y el rival
              de 'ultimo_cantor' queda habilitado para subir la apuesta.
        """
        if aceptado:
            return None
        puntos_ganados = max(self.puntos_en_juego - 1, 1)
        for jugador in self.jugadores:
            if jugador is not jugador_que_no_quiere:
                self.sumar_puntos(jugador, puntos_ganados)
        self.en_curso = False
        return puntos_ganados

    def niveles_disponibles_envido(self):
        """POST: retorna los niveles de Envido que todavia se pueden cantar en esta cadena."""
        if self.envido_nivel_actual is None:
            return self.NIVELES_ENVIDO
        indice_actual = self.NIVELES_ENVIDO.index(self.envido_nivel_actual)
        return self.NIVELES_ENVIDO[indice_actual + 1:]

    def puede_cantar_envido(self, jugador):
        """
        POST: retorna True si 'jugador' puede cantar (o subir) el Envido: el
              Envido de esta mano no debe haber terminado, la primera baza
              no debe haberse resuelto todavia (el Envido se puede cantar
              en cualquier momento de la primera baza: antes de que 'mano'
              juegue su carta, o despues, mientras el rival todavia no jugo
              la suya), no debe haberse cantado Truco todavia (el Envido
              tiene prioridad: una vez que alguien canta Truco, ya no se
              puede cantar Envido en esa mano, se haya aceptado o no),
              debe quedar al menos un nivel superior disponible, y (si ya
              hubo un canto) 'jugador' no debe ser quien realizo el ultimo
              canto sin respuesta.
        """
        if self.envido_terminado or self.ronda_actual > 0 or self.puntos_en_juego > 1:
            return False
        if not self.niveles_disponibles_envido():
            return False
        if self.envido_cantor_actual is None:
            return True
        return self.envido_cantor_actual is not jugador

    def valor_envido_nivel(self, nivel):
        """
        PRE: 'nivel' es uno de NIVELES_ENVIDO.
        POST: retorna los puntos que vale ese nivel; para "falta_envido" son
              los puntos que le faltan al jugador con mas puntos para llegar
              a PUNTOS_PARTIDA.
        """
        if nivel == "falta_envido":
            maximo_actual = max(jugador.puntos for jugador in self.jugadores)
            return self.PUNTOS_PARTIDA - maximo_actual
        return self.VALORES_ENVIDO[nivel]

    def cantar_envido(self, nivel, jugador):
        """
        PRE: 'nivel' esta entre los retornados por 'niveles_disponibles_envido';
             'jugador' puede cantar segun 'puede_cantar_envido'.
        POST: si ya habia un nivel cantado, sus puntos quedan confirmados en
              'envido_puntos_acumulados'; 'envido_nivel_actual' pasa a ser
              'nivel' y 'jugador' queda registrado como quien lo canto.
        """
        if nivel not in self.niveles_disponibles_envido():
            raise ValueError("Nivel de Envido invalido en este momento")
        if self.envido_nivel_actual is not None:
            self.envido_puntos_acumulados += self.valor_envido_nivel(self.envido_nivel_actual)
        self.envido_nivel_actual = nivel
        self.envido_cantor_actual = jugador

    def resolver_envido_quiero(self):
        """
        PRE: hay un nivel de Envido pendiente y el rival respondio "Quiero".
        POST: se comparan los valores de Envido (calculados sobre las 3
              cartas originales de cada jugador) y se otorgan al ganador los
              puntos acumulados de toda la cadena de cantos; ante empate,
              gana el jugador "mano". Retorna (ganador, valor_jugador1,
              valor_jugador2, puntos_otorgados).
        """
        valor_en_juego = self.envido_puntos_acumulados + self.valor_envido_nivel(self.envido_nivel_actual)
        jugador1, jugador2 = self.jugador_en_posicion(0), self.jugador_en_posicion(1)
        valor1, valor2 = self.calcular_envido(jugador1), self.calcular_envido(jugador2)
        if valor1 == valor2:
            ganador = self.jugador_en_posicion(self.indice_mano)
        elif valor1 > valor2:
            ganador = jugador1
        else:
            ganador = jugador2
        self.sumar_puntos(ganador, valor_en_juego)
        self.envido_terminado = True
        return ganador, valor1, valor2, valor_en_juego

    def resolver_envido_no_quiero(self, jugador_que_no_quiere):
        """
        PRE: hay un nivel de Envido pendiente y 'jugador_que_no_quiere' respondio "No quiero".
        POST: el rival de 'jugador_que_no_quiere' suma los puntos acumulados
              de los cantos previos ya aceptados mas 1; el Envido de esta
              mano queda terminado. Retorna los puntos otorgados.
        """
        puntos = self.envido_puntos_acumulados + 1
        for jugador in self.jugadores:
            if jugador is not jugador_que_no_quiere:
                self.sumar_puntos(jugador, puntos)
        self.envido_terminado = True
        return puntos

    def calcular_envido(self, jugador):
        """
        PRE: 'jugador' participo del reparto de la mano actual (iniciar_mano
             ya fue invocado).
        POST: retorna el valor de envido del jugador calculado sobre sus 3
              cartas originales (aunque ya haya jugado alguna), como la suma
              de las 2 cartas mas altas del mismo palo mas 20 (usando 0 para
              figuras 10/11/12), o el valor de su carta mas alta si no tiene
              2 cartas de un mismo palo.
        """
        cartas_originales = self._manos_originales.get(jugador.nombre, tuple(jugador.mano))
        mejores_por_palo = {}
        mayor_individual = 0
        for carta in cartas_originales:
            valor = carta.valor if carta.valor <= 7 else 0
            if valor > mayor_individual:
                mayor_individual = valor
            mayor, segundo, cantidad = mejores_por_palo.get(carta.palo, (0, 0, 0))
            if valor >= mayor:
                mayor, segundo = valor, mayor
            elif valor > segundo:
                segundo = valor
            mejores_por_palo[carta.palo] = (mayor, segundo, cantidad + 1)

        mejor_envido = mayor_individual
        for mayor, segundo, cantidad in mejores_por_palo.values():
            if cantidad >= 2:
                envido = mayor + segundo + 20
                if envido > mejor_envido:
                    mejor_envido = envido
        return mejor_envido

    def irse_al_mazo(self, jugador):
        """
        PRE: 'jugador' participa de la mano en curso y la partida esta en curso.
        POST: la mano finaliza inmediatamente; el rival de 'jugador' gana los
              puntos de Truco en juego, mas 1 punto adicional si la fase de
              Envido de esta mano todavia no habia terminado (es decir, la
              primera baza todavia no se resolvio y nadie gano el Envido).
              Retorna (rival, puntos_otorgados).
        """
        rival = self.jugador_en_posicion(1 - self.indice_de_jugador(jugador))
        puntos = self.puntos_en_juego
        if not self.envido_terminado and self.ronda_actual == 0:
            puntos += 1
        self.sumar_puntos(rival, puntos)
        self.en_curso = False
        return rival, puntos

    def sumar_puntos(self, jugador, puntos):
        """
        PRE: 'jugador' participa de la partida; 'puntos' es mayor a 0.
        POST: el puntaje de 'jugador' aumenta en 'puntos'.
        """
        jugador.puntos += puntos

    def verificar_ganador(self):
        """POST: retorna el Jugador con puntos >= PUNTOS_PARTIDA, o None si no lo hay."""
        for jugador in self.jugadores:
            if jugador.puntos >= self.PUNTOS_PARTIDA:
                return jugador
        return None

    def __str__(self):
        estado = "en curso" if self.en_curso else "sin iniciar"
        jugadores_str = ", ".join(str(jugador) for jugador in self.jugadores)
        return (
            f"Truco ({estado}) - En juego: {self.puntos_en_juego} pto(s) - "
            f"Jugadores: {jugadores_str}"
        )
