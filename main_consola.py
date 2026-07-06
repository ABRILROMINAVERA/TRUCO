"""Punto de entrada del programa: crea el GameManager e inicia una partida de Truco vs CPU."""

from game_manager import GameManager
from juegos.estrategia_cpu import crear_estrategia
from juegos.truco import Truco

_DIFICULTADES = {"1": "facil", "2": "media", "3": "dificil"}
_PUNTOS_PARTIDA = {"1": 15, "2": 30}


def _elegir_dificultad():
    while True:
        print("Elegi la dificultad de la CPU:")
        print("  1) Facil")
        print("  2) Media")
        print("  3) Dificil")
        eleccion = input("Opcion (1-3): ").strip()
        if eleccion in _DIFICULTADES:
            return _DIFICULTADES[eleccion]
        print("Opcion invalida, intenta de nuevo.")


def _elegir_puntos_partida():
    while True:
        print("¿A cuantos puntos se juega?")
        print("  1) 15 puntos")
        print("  2) 30 puntos")
        eleccion = input("Opcion (1-2): ").strip()
        if eleccion in _PUNTOS_PARTIDA:
            return _PUNTOS_PARTIDA[eleccion]
        print("Opcion invalida, intenta de nuevo.")


def main():
    print("=== Truco Argentino vs CPU ===")
    nombre_humano = input("Tu nombre: ").strip() or "Jugador"
    dificultad = _elegir_dificultad()
    puntos_partida = _elegir_puntos_partida()

    truco = Truco(nombre_humano, "CPU", puntos_partida=puntos_partida)
    manager = GameManager()
    manager.iniciar_juego(truco)
    manager.configurar_cpu(truco.jugador_en_posicion(1), crear_estrategia(dificultad))
    manager.jugar_truco_por_consola()


if __name__ == "__main__":
    main()
