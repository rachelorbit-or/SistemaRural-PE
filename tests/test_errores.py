"""Pruebas de las excepciones propias del sistema."""
from sistemarural import errores

CLASES = [errores.ErrorDeValidacion, errores.AccesoDenegado, errores.PacienteDuplicado,
          errores.PacienteNoEncontrado, errores.ErrorDeAlmacenamiento, errores.ErrorDeCifrado,
          errores.StockInsuficiente]


def test_todas_las_excepciones_guardan_su_mensaje():
    for clase in CLASES:
        try:
            raise clase("mensaje de prueba")
        except clase as error:
            assert str(error) == "mensaje de prueba"


def test_todas_las_excepciones_tienen_descripcion():
    for clase in CLASES:
        assert clase.__doc__
