"""Punto de entrada: abre SistemaRural-PE con sus datos guardados en la carpeta 'datos'."""
from pathlib import Path

from sistemarural.almacen_datos import AlmacenDatos
from sistemarural.cifrador import Cifrador
from sistemarural.interfaz import Aplicacion
from sistemarural.sistema import SistemaChontapaccha


def main() -> None:
    carpeta = Path("datos")
    cifrador = Cifrador.desde_archivo(carpeta / "clave.key")
    almacen = AlmacenDatos.obtener_instancia(carpeta / "datos.json", cifrador)
    sistema = SistemaChontapaccha(almacen, cifrador)
    sistema.cargar()
    sistema.sembrar_datos_demo()  # Solo crea datos ficticios si el sistema está vacío.
    Aplicacion(sistema).mainloop()


if __name__ == "__main__":
    main()
