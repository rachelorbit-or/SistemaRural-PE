"""Pruebas del reporte para la DIRESA con map, filter y reduce (CE-04, RQ-06)."""
from datetime import date, datetime

import pytest

from sistemarural.cifrador import Cifrador
from sistemarural.errores import ErrorDeValidacion
from sistemarural.historia_clinica import Atencion
from sistemarural.inventario import Inventario, Medicamento
from sistemarural.reportes import GeneradorReporte


def crear_atenciones():
    cifrador = Cifrador(Cifrador.generar_clave())
    datos = [
        (datetime(2026, 9, 30, 9, 0), "resuelto"),
        (datetime(2026, 10, 1, 9, 0), "resuelto"),
        (datetime(2026, 10, 2, 10, 0), "referido"),
        (datetime(2026, 10, 3, 11, 0), "resuelto"),
    ]
    return [Atencion.registrar("Consulta", "Diagnóstico de prueba", cifrador, fecha=f, resolucion=r)
            for f, r in datos]


def test_filtrar_por_fecha_incluye_los_extremos():
    atenciones = crear_atenciones()
    del_periodo = GeneradorReporte.filtrar_por_fecha(atenciones, date(2026, 10, 1), date(2026, 10, 2))
    assert len(del_periodo) == 2


def test_fechas_invertidas_son_rechazadas():
    with pytest.raises(ErrorDeValidacion):
        GeneradorReporte.filtrar_por_fecha(crear_atenciones(), date(2026, 10, 5), date(2026, 10, 1))


def test_cuenta_atenciones_por_resolucion():
    conteo = GeneradorReporte.atenciones_por_resolucion(crear_atenciones())
    assert conteo == {"resuelto": 3, "referido": 1}


def test_totalizar_cuenta_todas_las_atenciones():
    assert GeneradorReporte.totalizar(crear_atenciones()) == 4
    assert GeneradorReporte.totalizar([]) == 0


def test_reporte_diresa_del_periodo():
    reporte = GeneradorReporte.reporte_diresa(crear_atenciones(), date(2026, 10, 1), date(2026, 10, 3))
    assert reporte["total"] == 3
    assert reporte["por_resolucion"] == {"resuelto": 2, "referido": 1}


def test_nombres_a_reponer_y_unidades_en_stock():
    inventario = Inventario(umbral=10)
    inventario.agregar_medicamento(Medicamento("M01", "Paracetamol", 50))
    inventario.agregar_medicamento(Medicamento("M02", "Amoxicilina", 8))
    assert GeneradorReporte.nombres_a_reponer(inventario) == ["Amoxicilina"]
    assert GeneradorReporte.unidades_en_stock(inventario) == 58


def test_las_funciones_no_modifican_la_coleccion_original():
    atenciones = crear_atenciones()
    GeneradorReporte.filtrar_por_fecha(atenciones, date(2026, 10, 1), date(2026, 10, 2))
    assert len(atenciones) == 4
