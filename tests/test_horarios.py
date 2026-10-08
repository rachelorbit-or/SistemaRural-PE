"""Pruebas de los horarios del personal (RQ-07)."""
from datetime import date

import pytest

from sistemarural.citas import Servicio
from sistemarural.errores import ErrorDeValidacion
from sistemarural.horarios import Horario
from sistemarural.personas import PersonalFactory

NACIMIENTO = date(1990, 5, 20)


def crear_servicio():
    servicio = Servicio("Medicina")
    medico = PersonalFactory.crear_personal("medico", "11111111", "Ana Ruiz", NACIMIENTO, "Jr. Lima 1")
    servicio.agregar_personal(medico)
    return servicio, medico


def test_asignar_personal_a_un_dia_y_turno():
    servicio, medico = crear_servicio()
    servicio.asignar_horario("lunes", "mañana", medico)
    horarios = servicio.listar_horarios()
    assert len(horarios) == 1
    assert horarios[0].listar_personal() == (medico,)


def test_no_se_asigna_dos_veces_a_la_misma_persona_en_el_mismo_turno():
    servicio, medico = crear_servicio()
    servicio.asignar_horario("lunes", "mañana", medico)
    with pytest.raises(ErrorDeValidacion):
        servicio.asignar_horario("lunes", "mañana", medico)


def test_solo_se_asigna_personal_del_servicio():
    servicio, _ = crear_servicio()
    otro = PersonalFactory.crear_personal("medico", "44444444", "Luis Paz", NACIMIENTO, "Jr. Lima 2")
    with pytest.raises(ErrorDeValidacion):
        servicio.asignar_horario("lunes", "mañana", otro)


def test_dia_o_turno_invalido_es_rechazado():
    with pytest.raises(ErrorDeValidacion):
        Horario("domingote", "mañana")
    with pytest.raises(ErrorDeValidacion):
        Horario("lunes", "noche")
