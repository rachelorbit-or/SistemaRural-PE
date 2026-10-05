"""Pruebas del almacén: duplicados, persistencia y datos cifrados (CE-02, CE-06)."""
from datetime import date

import pytest

from sistemarural.almacen_datos import AlmacenDatos
from sistemarural.cifrador import Cifrador
from sistemarural.errores import ErrorDeValidacion, PacienteDuplicado, PacienteNoEncontrado
from sistemarural.personas import Paciente


def nuevo_paciente():
    return Paciente("12345678", "Rosa Quispe", date(1990, 5, 20), "Jr. Los Pinos 123")


def crear_almacen(tmp_path):
    AlmacenDatos.reiniciar()
    cifrador = Cifrador.desde_archivo(tmp_path / "clave.key")
    return AlmacenDatos.obtener_instancia(tmp_path / "datos.json", cifrador)


def test_guardar_y_cargar_paciente(tmp_path):
    almacen = crear_almacen(tmp_path)
    almacen.guardar_paciente(nuevo_paciente())
    cargado = almacen.cargar_paciente("12345678")
    assert cargado.nombres == "Rosa Quispe"
    assert cargado.fecha_nacimiento == date(1990, 5, 20)


def test_no_permite_pacientes_duplicados(tmp_path):
    almacen = crear_almacen(tmp_path)
    almacen.guardar_paciente(nuevo_paciente())
    with pytest.raises(PacienteDuplicado):
        almacen.guardar_paciente(nuevo_paciente())
    assert len(almacen.listar_pacientes()) == 1


def test_los_datos_no_quedan_en_texto_plano(tmp_path):
    almacen = crear_almacen(tmp_path)
    almacen.guardar_paciente(nuevo_paciente())
    contenido = (tmp_path / "datos.json").read_text(encoding="utf-8")
    for dato in ["12345678", "Rosa Quispe", "Jr. Los Pinos 123", "1990-05-20"]:
        assert dato not in contenido


def test_los_datos_persisten_al_reiniciar(tmp_path):
    almacen = crear_almacen(tmp_path)
    almacen.guardar_paciente(nuevo_paciente())
    AlmacenDatos.reiniciar()  # Se simula cerrar y volver a abrir el sistema.
    cifrador = Cifrador.desde_archivo(tmp_path / "clave.key")
    otro = AlmacenDatos.obtener_instancia(tmp_path / "datos.json", cifrador)
    assert otro.existe_paciente("12345678")


def test_singleton_devuelve_siempre_la_misma_instancia(tmp_path):
    almacen = crear_almacen(tmp_path)
    assert AlmacenDatos.obtener_instancia() is almacen


def test_buscar_paciente_inexistente_o_con_dni_invalido(tmp_path):
    almacen = crear_almacen(tmp_path)
    with pytest.raises(PacienteNoEncontrado):
        almacen.cargar_paciente("99999999")
    with pytest.raises(ErrorDeValidacion):
        almacen.cargar_paciente("abc")


def test_las_secciones_se_guardan_cifradas_y_se_recuperan(tmp_path):
    almacen = crear_almacen(tmp_path)
    almacen.guardar_seccion("notas", [{"dni": "12345678", "lista": [1, 2], "publico": "abierto"}],
                            campos_cifrados=("dni", "lista"))
    contenido = (tmp_path / "datos.json").read_text(encoding="utf-8")
    assert "12345678" not in contenido
    assert "abierto" in contenido  # Solo se cifran los campos indicados.
    assert almacen.cargar_seccion("notas") == [{"dni": "12345678", "lista": [1, 2], "publico": "abierto"}]
    assert almacen.cargar_seccion("no_existe") == []
