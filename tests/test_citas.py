"""Pruebas de servicios y citas (RQ-03)."""
from datetime import date

import pytest

from sistemarural.citas import Cita, Servicio
from sistemarural.errores import ErrorDeValidacion
from sistemarural.personas import Paciente, PersonalFactory

HOY = date(2026, 10, 5)
NACIMIENTO = date(1990, 5, 20)


def crear_escenario():
    servicio = Servicio("Medicina")
    medico = PersonalFactory.crear_personal("medico", "11111111", "Ana Ruiz", NACIMIENTO, "Jr. Lima 1")
    servicio.agregar_personal(medico)
    paciente = Paciente("12345678", "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")
    return servicio, medico, paciente


def test_programar_una_cita_valida():
    servicio, medico, paciente = crear_escenario()
    cita = Cita.programar(paciente, servicio, medico, date(2026, 10, 6), "mañana", hoy=HOY)
    assert cita.estado == "programada"
    assert servicio.listar_citas() == [cita]


def test_no_permite_fecha_pasada_ni_turno_invalido():
    servicio, medico, paciente = crear_escenario()
    with pytest.raises(ErrorDeValidacion):
        Cita.programar(paciente, servicio, medico, date(2026, 10, 1), "mañana", hoy=HOY)
    with pytest.raises(ErrorDeValidacion):
        Cita.programar(paciente, servicio, medico, date(2026, 10, 6), "noche", hoy=HOY)


def test_no_permite_dos_citas_del_mismo_paciente_en_el_mismo_turno():
    servicio, medico, paciente = crear_escenario()
    Cita.programar(paciente, servicio, medico, date(2026, 10, 6), "tarde", hoy=HOY)
    with pytest.raises(ErrorDeValidacion):
        Cita.programar(paciente, servicio, medico, date(2026, 10, 6), "tarde", hoy=HOY)


def test_el_personal_debe_pertenecer_al_servicio():
    servicio, _, paciente = crear_escenario()
    otro = PersonalFactory.crear_personal("medico", "44444444", "Luis Paz", NACIMIENTO, "Jr. Lima 2")
    with pytest.raises(ErrorDeValidacion):
        Cita.programar(paciente, servicio, otro, date(2026, 10, 6), "mañana", hoy=HOY)


def test_cancelar_una_cita_la_quita_de_las_programadas():
    servicio, medico, paciente = crear_escenario()
    cita = Cita.programar(paciente, servicio, medico, date(2026, 10, 6), "mañana", hoy=HOY)
    cita.cancelar()
    assert servicio.listar_citas() == []
    with pytest.raises(ErrorDeValidacion):
        cita.cancelar()


def test_listar_citas_filtra_por_fecha():
    servicio, medico, paciente = crear_escenario()
    otra = Paciente("87654321", "Juan Rojas", NACIMIENTO, "Jr. Cusco 5")
    c1 = Cita.programar(paciente, servicio, medico, date(2026, 10, 6), "mañana", hoy=HOY)
    Cita.programar(otra, servicio, medico, date(2026, 10, 7), "mañana", hoy=HOY)
    assert servicio.listar_citas(date(2026, 10, 6)) == [c1]
    assert len(servicio.listar_citas()) == 2
