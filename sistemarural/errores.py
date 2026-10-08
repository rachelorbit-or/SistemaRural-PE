"""Excepciones propias del sistema, para manejar los errores de forma clara."""


class ErrorDeValidacion(Exception):
    """Se lanza cuando un dato no cumple las reglas (por ejemplo, un DNI inválido)."""


class AccesoDenegado(Exception):
    """Se lanza cuando un usuario intenta ver información que su rol no permite."""


class PacienteDuplicado(Exception):
    """Se lanza al intentar registrar un paciente cuyo DNI ya existe."""


class PacienteNoEncontrado(Exception):
    """Se lanza cuando no existe un paciente con el DNI buscado."""


class ErrorDeAlmacenamiento(Exception):
    """Se lanza cuando el archivo de datos no se puede leer o está dañado."""


class ErrorDeCifrado(Exception):
    """Se lanza cuando un dato cifrado no se puede descifrar con la clave actual."""


class StockInsuficiente(Exception):
    """Se lanza cuando se pide más cantidad de un medicamento que la disponible."""
