"""Pruebas adicionales del inventario."""
import pytest

from sistemarural.errores import ErrorDeValidacion
from sistemarural.inventario import Inventario, Medicamento


def test_no_se_crea_un_medicamento_con_stock_negativo():
    with pytest.raises(ErrorDeValidacion):
        Medicamento("M09", "Medicamento de prueba", -1)


def test_reponer_con_cantidad_cero_es_rechazado():
    medicamento = Medicamento("M09", "Medicamento de prueba", 5)
    with pytest.raises(ErrorDeValidacion):
        medicamento.reponer(0)
    assert medicamento.stock == 5


def test_con_umbral_cero_solo_alerta_el_stock_agotado():
    inventario = Inventario(umbral=0)
    inventario.agregar_medicamento(Medicamento("M01", "Con stock", 3))
    inventario.agregar_medicamento(Medicamento("M02", "Agotado", 0))
    assert [m.codigo for m in inventario.stock_bajo()] == ["M02"]


def test_un_umbral_negativo_es_rechazado():
    with pytest.raises(ErrorDeValidacion):
        Inventario(umbral=-5)
