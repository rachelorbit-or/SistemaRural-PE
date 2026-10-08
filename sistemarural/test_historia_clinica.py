"""Pruebas de historia clínica, atenciones y acceso por rol (CE-03, RQ-02, RQ-04)."""
from datetime import date

import pytest

from sistemarural.cifrador import Cifrador
from sistemarural.errores import AccesoDenegado, ErrorDeValidacion
from sistemarural.historia_clinica import Atencion
from sistemarural.personas import Paciente, PersonalFactory

NACIMIENTO = date(1990, 5, 20)


def crear_cifrador():
    return Cifrador(Cifrador.generar_clave())


def crear_personal(cargo, dni):
    return PersonalFactory.crear_personal(cargo, dni, "Nombre Prueba", NACIMIENTO, "Jr. Lima 1")


def crear_paciente():
    return Paciente("12345678", "Rosa Quispe", NACIMIENTO, "Jr. Los Pinos 123")


def test_el_medico_puede_ver_el_diagnostico():
    atencion = Atencion.registrar("Control", "Gastritis leve", crear_cifrador())
    assert atencion.ver_diagnostico(crear_personal("medico", "11111111")) == "Gastritis leve"


def test_otros_cargos_no_pueden_ver_el_diagnostico():
    atencion = Atencion.registrar("Control", "Gastritis leve", crear_cifrador())
    for cargo, dni in [("tecnico_enfermeria", "22222222"), ("admisionista", "33333333")]:
        with pytest.raises(AccesoDenegado):
            atencion.ver_diagnostico(crear_personal(cargo, dni))


def test_un_paciente_tampoco_puede_ver_diagnosticos_ajenos():
    atencion = Atencion.registrar("Control", "Gastritis leve", crear_cifrador())
    with pytest.raises(AccesoDenegado):
        atencion.ver_diagnostico(crear_paciente())


def test_el_diagnostico_no_queda_en_texto_plano():
    atencion = Atencion.registrar("Control", "Gastritis leve", crear_cifrador())
    assert "Gastritis" not in atencion.diagnostico_cifrado


def test_diagnostico_o_motivo_vacio_es_rechazado():
    with pytest.raises(ErrorDeValidacion):
        Atencion.registrar("Control", "   ", crear_cifrador())
    with pytest.raises(ErrorDeValidacion):
        Atencion.registrar("", "Gastritis leve", crear_cifrador())


def test_el_paciente_abre_una_sola_historia():
    paciente = crear_paciente()
    paciente.abrir_historia("HC-0001")
    assert paciente.historia.numero == "HC-0001"
    with pytest.raises(ErrorDeValidacion):
        paciente.abrir_historia("HC-0002")


def test_el_medico_registra_una_atencion_en_la_historia():
    paciente = crear_paciente()
    historia = paciente.abrir_historia("HC-0001")
    medico = crear_personal("medico", "11111111")
    medico.registrar_atencion(historia, "Dolor de cabeza", "Cefalea tensional", crear_cifrador())
    assert len(historia.listar_atenciones()) == 1


def test_la_lista_de_atenciones_es_de_solo_lectura():
    paciente = crear_paciente()
    historia = paciente.abrir_historia("HC-0001")
    assert isinstance(historia.listar_atenciones(), tuple)
    with pytest.raises(ErrorDeValidacion):
        historia.agregar_atencion("no es una atención")


def test_la_resolucion_debe_ser_valida_y_la_atencion_genera_receta():
    with pytest.raises(ErrorDeValidacion):
        Atencion.registrar("Control", "Gastritis leve", crear_cifrador(), resolucion="perdido")
    atencion = Atencion.registrar("Control", "Gastritis leve", crear_cifrador(), resolucion="referido")
    assert atencion.resolucion == "referido"
    receta = atencion.generar_receta(crear_paciente(), [("M01", 2)])
    assert receta.estado == "pendiente"
