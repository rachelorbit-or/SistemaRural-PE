"""Pruebas de las personas y del control por rol (CE-03, RQ-04)."""
from datetime import date

import pytest

from sistemarural.errores import ErrorDeValidacion
from sistemarural.personas import (Admisionista, Medico, Paciente, Persona,
                                   PersonalFactory, TecnicoEnfermeria)

NACIMIENTO = date(1990, 5, 20)


def test_solo_el_medico_puede_ver_diagnosticos():
    medico = PersonalFactory.crear_personal("medico", "11111111", "Ana Ruiz", NACIMIENTO, "Jr. Lima 1")
    tecnico = PersonalFactory.crear_personal("tecnico_enfermeria", "22222222", "Luis Paz", NACIMIENTO, "Jr. Lima 2")
    admisionista = PersonalFactory.crear_personal("admisionista", "33333333", "Eva Gil", NACIMIENTO, "Jr. Lima 3")
    assert isinstance(medico, Medico) and medico.puede_ver_diagnostico() is True
    assert isinstance(tecnico, TecnicoEnfermeria) and tecnico.puede_ver_diagnostico() is False
    assert isinstance(admisionista, Admisionista) and admisionista.puede_ver_diagnostico() is False


def test_cargo_desconocido_lanza_error():
    with pytest.raises(ErrorDeValidacion):
        PersonalFactory.crear_personal("cocinero", "11111111", "Ana Ruiz", NACIMIENTO, "Jr. Lima 1")


def test_dni_invalido_no_permite_crear_persona():
    with pytest.raises(ErrorDeValidacion):
        Paciente("1234", "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")


def test_edad_se_calcula_con_la_fecha_de_nacimiento():
    paciente = Paciente("12345678", "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")
    assert paciente.edad(hoy=date(2026, 5, 19)) == 35
    assert paciente.edad(hoy=date(2026, 5, 20)) == 36


def test_datos_vacios_o_futuros_son_rechazados():
    with pytest.raises(ErrorDeValidacion):
        Paciente("12345678", "   ", NACIMIENTO, "Jr. Los Pinos 123")
    with pytest.raises(ErrorDeValidacion):
        Paciente("12345678", "Rosa Quispe", date(2999, 1, 1), "Jr. Los Pinos 123")


def test_persona_es_abstracta():
    with pytest.raises(TypeError):
        Persona("12345678", "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")


def test_metodos_propios_de_cada_cargo():
    from sistemarural.citas import Servicio
    admisionista = PersonalFactory.crear_personal("admisionista", "33333333", "Eva Gil", NACIMIENTO, "Jr. Lima 3")
    medico = PersonalFactory.crear_personal("medico", "11111111", "Ana Ruiz", NACIMIENTO, "Jr. Lima 1")
    tecnico = PersonalFactory.crear_personal("tecnico_enfermeria", "22222222", "Luis Paz", NACIMIENTO, "Jr. Lima 2")
    paciente = admisionista.registrar_paciente("12345678", "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")
    assert isinstance(paciente, Paciente)
    servicio = Servicio("Medicina")
    servicio.agregar_personal(medico)
    cita = admisionista.programar_cita(paciente, servicio, medico, date(2026, 10, 6), "mañana",
                                       hoy=date(2026, 10, 5))
    assert cita.estado == "programada"
    historia = paciente.abrir_historia("HC-0001")
    resumen = tecnico.apoyar_atencion(historia)
    assert resumen == {"numero": "HC-0001", "total_atenciones": 0, "ultima_atencion": None}
    assert [p.codigo_cargo for p in (admisionista, medico, tecnico)] == [
        "admisionista", "medico", "tecnico_enfermeria"]
