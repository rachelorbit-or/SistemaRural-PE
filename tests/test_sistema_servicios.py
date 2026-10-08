"""Pruebas adicionales del sistema: servicios base y búsquedas sin resultados."""
import pytest

from sistemarural.almacen_datos import AlmacenDatos
from sistemarural.cifrador import Cifrador
from sistemarural.errores import ErrorDeValidacion, PacienteNoEncontrado
from sistemarural.sistema import SistemaChontapaccha


def crear_sistema(tmp_path):
    AlmacenDatos.reiniciar()
    cifrador = Cifrador.desde_archivo(tmp_path / "clave.key")
    almacen = AlmacenDatos.obtener_instancia(tmp_path / "datos.json", cifrador)
    sistema = SistemaChontapaccha(almacen, cifrador)
    sistema.sembrar_datos_demo()
    return sistema


def test_los_servicios_base_existen_y_empiezan_sin_citas(tmp_path):
    sistema = crear_sistema(tmp_path)
    nombres = [s.nombre for s in sistema.listar_servicios()]
    assert nombres == ["Medicina", "Odontología", "Psicología", "Control del niño", "Obstetricia"]
    assert sistema.listar_citas("Medicina") == []


def test_un_servicio_inexistente_es_rechazado(tmp_path):
    with pytest.raises(ErrorDeValidacion):
        crear_sistema(tmp_path).obtener_servicio("Cardiología")


def test_buscar_un_paciente_inexistente_lanza_error(tmp_path):
    with pytest.raises(PacienteNoEncontrado):
        crear_sistema(tmp_path).obtener_paciente("70000009")
