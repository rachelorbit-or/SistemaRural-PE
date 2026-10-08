"""Pruebas del inventario y las recetas (CE-05, RQ-05)."""
from datetime import date

import pytest

from sistemarural.errores import ErrorDeValidacion, StockInsuficiente
from sistemarural.inventario import Inventario, Medicamento, Receta
from sistemarural.personas import Paciente


def crear_inventario():
    inventario = Inventario(umbral=10)
    inventario.agregar_medicamento(Medicamento("M01", "Paracetamol", 50))
    inventario.agregar_medicamento(Medicamento("M02", "Amoxicilina", 8))
    return inventario


def crear_paciente():
    return Paciente("12345678", "Rosa Quispe", date(1990, 5, 20), "Jr. Los Pinos 123")


def test_la_alerta_de_stock_bajo_detecta_los_que_cruzan_el_umbral():
    inventario = crear_inventario()
    assert [m.codigo for m in inventario.stock_bajo()] == ["M02"]
    inventario.registrar_salida("M01", 45)  # Queda en 5, por debajo del umbral.
    assert sorted(m.codigo for m in inventario.stock_bajo()) == ["M01", "M02"]


def test_entrada_y_salida_actualizan_el_stock():
    inventario = crear_inventario()
    inventario.registrar_entrada("M02", 12)
    inventario.registrar_salida("M02", 5)
    assert inventario.obtener("M02").stock == 15


def test_no_se_puede_sacar_mas_de_lo_que_hay():
    inventario = crear_inventario()
    with pytest.raises(StockInsuficiente):
        inventario.registrar_salida("M02", 9)
    assert inventario.obtener("M02").stock == 8


def test_cantidades_y_codigos_invalidos_son_rechazados():
    inventario = crear_inventario()
    with pytest.raises(ErrorDeValidacion):
        inventario.registrar_salida("M01", 0)
    with pytest.raises(ErrorDeValidacion):
        inventario.registrar_salida("NO_EXISTE", 1)
    with pytest.raises(ErrorDeValidacion):
        inventario.agregar_medicamento(Medicamento("M01", "Repetido", 1))


def test_dispensar_una_receta_descuenta_el_stock():
    inventario = crear_inventario()
    receta = Receta.generar(crear_paciente(), [("M01", 10), ("M02", 2)])
    receta.dispensar(inventario)
    assert receta.estado == "dispensada"
    assert inventario.obtener("M01").stock == 40
    assert inventario.obtener("M02").stock == 6


def test_dispensar_es_todo_o_nada():
    inventario = crear_inventario()
    receta = Receta.generar(crear_paciente(), [("M01", 10), ("M02", 99)])
    with pytest.raises(StockInsuficiente):
        receta.dispensar(inventario)
    assert inventario.obtener("M01").stock == 50  # No se descontó nada.
    assert receta.estado == "pendiente"


def test_una_receta_no_se_dispensa_dos_veces():
    inventario = crear_inventario()
    receta = Receta.generar(crear_paciente(), [("M01", 1)])
    receta.dispensar(inventario)
    with pytest.raises(ErrorDeValidacion):
        receta.dispensar(inventario)


def test_receta_vacia_o_con_cantidad_invalida_es_rechazada():
    with pytest.raises(ErrorDeValidacion):
        Receta.generar(crear_paciente(), [])
    with pytest.raises(ErrorDeValidacion):
        Receta.generar(crear_paciente(), [("M01", -3)])
