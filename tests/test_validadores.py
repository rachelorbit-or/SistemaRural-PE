"""Pruebas de la validación de DNI (CE-02)."""
from sistemarural.validadores import validar_dni


def test_dni_validos():
    for dni in ["12345678", "00000001", "87654321"]:
        assert validar_dni(dni) is True


def test_dni_invalidos():
    invalidos = ["", "1234567", "123456789", "1234567A", " 12345678",
                 "12345678 ", "12345678\n", "1234-5678", None, 12345678]
    for dni in invalidos:
        assert validar_dni(dni) is False


def test_convertir_fecha():
    from datetime import date

    import pytest

    from sistemarural.errores import ErrorDeValidacion
    from sistemarural.validadores import convertir_fecha
    assert convertir_fecha(" 2026-10-05 ") == date(2026, 10, 5)
    for texto in ["05/10/2026", "", "2026-13-40"]:
        with pytest.raises(ErrorDeValidacion):
            convertir_fecha(texto)


def test_convertir_items_de_receta():
    import pytest

    from sistemarural.errores import ErrorDeValidacion
    from sistemarural.validadores import convertir_items
    assert convertir_items("M01:2, M03:1") == [("M01", 2), ("M03", 1)]
    for texto in ["M01", "M01:dos", ":3", ""]:
        with pytest.raises(ErrorDeValidacion):
            convertir_items(texto)
