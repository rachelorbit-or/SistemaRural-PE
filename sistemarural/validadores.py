"""Validaciones de datos de entrada del sistema."""
import re

# El DNI peruano tiene exactamente 8 dígitos numéricos.
PATRON_DNI = re.compile(r"\d{8}")


def validar_dni(dni) -> bool:
    """Devuelve True si el valor es un texto de exactamente 8 dígitos."""
    return isinstance(dni, str) and PATRON_DNI.fullmatch(dni) is not None


def convertir_fecha(texto: str):
    """Convierte un texto AAAA-MM-DD en fecha; si no se puede, lanza un error claro."""
    from datetime import date
    from sistemarural.errores import ErrorDeValidacion
    try:
        return date.fromisoformat(str(texto).strip())
    except ValueError as error:
        raise ErrorDeValidacion("Escriba la fecha con el formato AAAA-MM-DD.") from error


def convertir_items(texto: str) -> list:
    """Convierte 'M01:2, M03:1' en [('M01', 2), ('M03', 1)]."""
    from sistemarural.errores import ErrorDeValidacion
    items = []
    for par in str(texto).split(","):
        codigo, separador, cantidad = par.partition(":")
        if not separador or not codigo.strip():
            raise ErrorDeValidacion("Use el formato CÓDIGO:CANTIDAD, por ejemplo M01:2, M03:1.")
        try:
            items.append((codigo.strip(), int(cantidad)))
        except ValueError as error:
            raise ErrorDeValidacion("La cantidad debe ser un número entero.") from error
    return items
