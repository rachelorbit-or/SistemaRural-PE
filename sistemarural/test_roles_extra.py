"""Pruebas adicionales de personas y cargos."""
from datetime import date

import pytest

from sistemarural.personas import Paciente, PersonalFactory

NACIMIENTO = date(1990, 5, 20)


def test_el_nombre_de_cada_cargo_es_legible():
    esperados = {"medico": "Médico", "tecnico_enfermeria": "Técnico de enfermería",
                 "admisionista": "Admisionista"}
    for codigo, nombre in esperados.items():
        persona = PersonalFactory.crear_personal(codigo, "11111111", "Persona Prueba",
                                                 NACIMIENTO, "Dirección de prueba")
        assert persona.cargo == nombre
        assert persona.tipo() == nombre
        assert persona.codigo_cargo == codigo


def test_el_dni_no_se_puede_cambiar_despues_de_crear_la_persona():
    paciente = Paciente("12345678", "Paciente Prueba", NACIMIENTO, "Dirección de prueba")
    with pytest.raises(AttributeError):
        paciente.dni = "87654321"
    assert paciente.dni == "12345678"


def test_los_nombres_se_limpian_de_espacios_sobrantes():
    paciente = Paciente("12345678", "  Paciente Prueba  ", NACIMIENTO, "Dirección de prueba")
    assert paciente.nombres == "Paciente Prueba"
